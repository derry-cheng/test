"""Exp32: matched aggregate gate contracts and full-runtime capacity stress."""
from __future__ import annotations
import copy
import hashlib
import json
import logging
import inspect
import functools
import warnings
from dataclasses import asdict
from pathlib import Path
import numpy as np
import pandas as pd

from .runtime_capacity import solve_runtime_milp, top_m_mean
from .risk_execution_composition import certify_execution_transfer, fit_risk_simplex
from .utils import write_json, sha256

FOLDER = "exp32_matched_gate_capacity"


def _implementation_hashes(root):
    return {name: sha256(root / "code/src/aicdr" / name) for name in ("matched_gate_capacity.py", "runtime_capacity.py", "risk_execution_composition.py")}


def _digest(*arrays):
    h = hashlib.sha256()
    for a in arrays:
        a = np.ascontiguousarray(a); h.update(str(a.shape).encode()); h.update(str(a.dtype).encode()); h.update(a.tobytes())
    return h.hexdigest()


def _pick_even(indices, limit=8):
    indices = np.asarray(indices, dtype=int)
    if len(indices) <= limit:
        return indices
    return indices[np.linspace(0, len(indices) - 1, limit, dtype=int)]


def _aggregate_fixed(starts, runtime, region, power, nr, nt):
    p = np.zeros((nr, nt))
    for s, r, d, v in zip(starts, runtime, region, power):
        lo, hi = max(0, int(s)), min(nt, int(s + r))
        if hi > lo:
            p[int(d), lo:hi] += v
    return p


def _independent_starts(release, deadline, runtime, region, power, cost, waiting, dt):
    # Deliberately scalar, independent of the sparse MILP column construction.
    starts = []
    for rel, dl, run, reg, p in zip(release, deadline, runtime, region, power):
        candidates = range(max(0, int(rel)), int(dl - run) + 1)
        scores = [float(p * dt * (cost[int(reg), s:s + int(run)].sum() +
                  waiting * sum(s + k - int(rel) for k in range(int(run))))) for s in candidates]
        starts.append(max(0, int(rel)) + int(np.argmin(scores)))
    return np.asarray(starts, dtype=int)


def _day_tensor(p, gate_slot, slots=96):
    full = np.zeros((p.shape[0], int(np.ceil((gate_slot + p.shape[1]) / slots)) * slots))
    full[:, gate_slot:gate_slot + p.shape[1]] = p
    return full.reshape(p.shape[0], -1, slots).transpose(1, 0, 2)


def run_capacity_panel(root, cfg, logger):
    final = root / "experiments" / FOLDER / "results/final"; final.mkdir(parents=True, exist_ok=True)
    source = root / "experiments/exp27_executable_common_witness/results/final/runtime_complete_witness.npz"
    with np.load(source, allow_pickle=False) as a:
        release = a["submit_slot"].copy(); deadline = a["deadline_slot"].copy()
        runtime = a["runtime_slots"].copy(); region = a["region"].copy(); gpus = a["requested_gpus"].copy()
        power = gpus * float(a["per_gpu_power_cap_mw"][0]); upper = a["declared_job_energy_upper_mwh"].copy()
    dt = float(cfg["project"]["interval_minutes"]) / 60
    if not np.allclose(upper, runtime * power * dt, atol=1e-10, rtol=0):
        raise ValueError("source runtime/nameplate entitlement mismatch")
    gate_slot = int(cfg["experiments"]["decision_time_event_gate_slot"])
    slots = int(cfg["project"]["slots_per_day"]); nr = int(cfg["project"]["number_of_regions"])
    event_slots = np.asarray(cfg["market"]["event_slots"], dtype=int)
    waiting = float(cfg["workload"]["waiting_cost_per_mwh_slot"][-1])
    price = float(cfg["market"]["default_dr_price_per_mwh"])
    independent_price = float(cfg["experiments"]["independent_event_replay_price_per_mwh"])
    test = np.load(root / "experiments/exp2_baseline_verification/results/intermediate/test_profiles.npz")
    days = test["days"].astype(int); selected_days = days[[0, len(days)//2, len(days)-1]]
    # A fixed possible scheduler state: start at the first gate strictly after
    # submission. This never exceeds the original 96-slot queue allowance.
    historical_start = (np.floor_divide(release - gate_slot, slots) + 1) * slots + gate_slot
    if np.any(historical_start < release) or np.any(historical_start + runtime > deadline):
        raise ValueError("declared gate-state rule violates an original deadline")
    rows, jobs, certificates = [], [], []
    scenario_values = (.20, .80, .98, 1.10)
    for day in selected_days:
        gate = int(day * slots + gate_slot)
        pending = (release < gate) & (historical_start == gate)
        running = (historical_start < gate) & (historical_start + runtime > gate)
        selected = []
        for state_mask in (pending, running):
            for r in range(nr):
                candidates = np.flatnonzero(state_mask & (region == r))
                candidates = candidates[np.lexsort((candidates, release[candidates]))]
                selected.extend(_pick_even(candidates).tolist())
        chosen = np.asarray(sorted(selected), dtype=int)
        pidx = chosen[pending[chosen]]; fidx = chosen[running[chosen]]
        # Close the final calendar day with zero-load slots. This changes no
        # job window, but makes every risk/MSE audit use identical day samples.
        nt = int(np.ceil(np.max(deadline[chosen]) / slots) * slots - gate)
        fixed = _aggregate_fixed(historical_start[fidx] - gate, runtime[fidx], region[fidx], power[fidx], nr, nt)
        reference = fixed + _aggregate_fixed(np.zeros(len(pidx), dtype=int), runtime[pidx], region[pidx], power[pidx], nr, nt)
        event = np.isin((np.arange(nt) + gate_slot) % slots, event_slots)
        objective = np.tile(event * price, (nr, 1))
        meter_start = _independent_starts(release[pidx] - gate, deadline[pidx] - gate, runtime[pidx], region[pidx], power[pidx],
                                          np.tile(event * independent_price, (nr, 1)), waiting, dt)
        modeled_meter = fixed + _aggregate_fixed(meter_start, runtime[pidx], region[pidx], power[pidx], nr, nt)
        # No telemetry and no future outcome enters this hypothetical physical
        # capacity: its denominator is the gate-known immediate-start peak.
        reference_peak = np.max(reference, axis=1)
        if np.any(reference_peak <= 0):
            raise ValueError("capacity cohort contains an empty region")
        cohort_digest = _digest(chosen, release[chosen], deadline[chosen], runtime[chosen], region[chosen], power[chosen])
        for index in chosen:
            jobs.append(dict(day=int(day), source_job_index=int(index), state="pending" if pending[index] else "running",
                             submit_slot=int(release[index]), deadline_slot=int(deadline[index]), runtime_slots=int(runtime[index]),
                             region=int(region[index]), fixed_power_mw=float(power[index]), entitlement_mwh=float(upper[index]),
                             fixed_historical_start=int(historical_start[index]), cohort_sha256=cohort_digest))
        for utilization in scenario_values:
            capacity = reference_peak / utilization
            for method in ("runtime_cost_only", "runtime_direct_total_tail"):
                kwargs = {}
                if method.endswith("total_tail"):
                    kwargs = dict(risk_ceiling_mw=np.maximum(reference, modeled_meter),
                                  risk_day_index=(np.arange(nt) + gate_slot) // slots,
                                  total_budget_mwh=0., tail_budget_mwh=0., tail_level=.75)
                logger.info("Exp32 runtime day=%s nominal utilization=%.2f method=%s", day, utilization, method)
                result = solve_runtime_milp(release[pidx] - gate, deadline[pidx] - gate, runtime[pidx], region[pidx], power[pidx],
                                            objective, capacity, fixed_profile_mw=fixed, dt_h=dt, waiting_cost=waiting,
                                            event_mask=event, time_limit=60., **kwargs)
                row = {key: value for key, value in asdict(result).items() if key not in {"starts", "profile_mw"}}
                row.update(day=int(day), method=method, nominal_reference_peak_utilization=float(utilization),
                           cohort_jobs=len(chosen), pending_jobs=len(pidx), fixed_running_jobs=len(fidx),
                           gate_slot=gate, future_arrivals_used=False, execution_telemetry_used=False,
                           runtime_semantics="all declared runtime slots at fixed requested-GPU nameplate power",
                           capacity_scope="every region and every horizon slot", cohort_sha256=cohort_digest,
                           declared_cohort_energy_mwh=float(upper[chosen].sum()),
                           pending_entitlement_mwh=float(upper[pidx].sum()),
                           original_nameplate_capacity_mw=float(cfg["project"]["flexible_capacity_mw"]),
                           minimum_scenario_capacity_mw=float(capacity.min()), maximum_scenario_capacity_mw=float(capacity.max()),
                           total_risk_budget_mwh=0. if kwargs else np.nan, tail_risk_budget_mwh=0. if kwargs else np.nan)
                if result.success:
                    prof = result.profile_mw
                    mean_delay = float(np.average(result.starts - (release[pidx] - gate), weights=power[pidx] * runtime[pidx]))
                    cert = certify_execution_transfer(_day_tensor(reference, gate_slot, slots), _day_tensor(prof, gate_slot, slots),
                                                      _day_tensor(modeled_meter, gate_slot, slots), _day_tensor(reference, gate_slot, slots),
                                                      dt, event_slots, total_budget_mwh=0. if kwargs else None,
                                                      tail_budget_mwh=0. if kwargs else None)
                    row.update(maximum_achieved_capacity_utilization=float(np.max(prof / capacity[:, None])),
                               active_capacity_slot_fraction=float(np.mean(np.isclose(prof, capacity[:, None], atol=1e-8, rtol=0))),
                               energy_weighted_wait_slots=mean_delay,
                               maximum_completion_deadline_violation_slots=int(max(0, np.max(result.starts + runtime[pidx] - (deadline[pidx] - gate)))),
                               executed_event_mse_mw2=cert["executed_event_mse_mw2"],
                               executed_total_false_credit_mwh=cert["executed_total_false_credit_mwh"],
                               executed_tail_false_credit_mwh=cert["executed_tail_false_credit_mwh"],
                               modeled_payable_credit_mwh=cert["uncapped_credit_mwh"],
                               risk_certificate_accept=bool(cert["execution_certificate_accept"]) if kwargs else False)
                    certificates.append(dict(day=int(day), method=method, nominal_reference_peak_utilization=utilization, **cert))
                    np.savez_compressed(final / f"runtime_day{day}_u{utilization:.2f}_{method}.npz", source_job_index=chosen,
                                        pending_source_job_index=pidx, selected_start_absolute=result.starts + gate,
                                        runtime_slots=runtime[chosen], release=release[chosen], deadline=deadline[chosen], fixed_power_mw=power[chosen],
                                        region=region[chosen], profile_mw=prof, fixed_profile_mw=fixed, reference_mw=reference,
                                        modeled_response_mw=modeled_meter, capacity_mw=capacity, event_mask=event)
                rows.append(row)
                pd.DataFrame(rows).to_csv(final.parent / "intermediate/runtime_capacity_checkpoint.csv", index=False)
    cells = pd.DataFrame(rows); cells.to_csv(final / "runtime_capacity_cells.csv", index=False)
    pd.DataFrame(jobs).to_csv(final / "runtime_capacity_cohort.csv", index=False)
    summary = cells.groupby(["method", "nominal_reference_peak_utilization"], as_index=False).agg(
        expected_cells=("day", "count"), feasible_cells=("success", "sum"), optimal_cells=("optimal", "sum"),
        maximum_elapsed_seconds=("elapsed_seconds", "max"), maximum_mip_gap=("mip_gap", "max"))
    summary.to_csv(final / "runtime_capacity_summary.csv", index=False)
    write_json(final / "runtime_direct_risk_certificates.json", certificates)
    write_json(final / "runtime_capacity_metadata.json", dict(source_sha256=sha256(source), implementation_sha256=_implementation_hashes(root),
        protocol_sha256=sha256(root / "experiments" / FOLDER / "README.md"), selected_locked_days=selected_days.tolist(),
        expected_cells=len(selected_days)*len(scenario_values)*2, retained_cells=len(cells),
        feasible_cells=int(cells.success.sum()), optimal_cells=int(cells.optimal.sum()),
        selection="up to eight evenly spaced release/index-ordered jobs per region and pending/running stratum",
        model="fixed-rate full-runtime blocks and all-slot capacity; no scaled entitlements",
        capacity_normalization="gate-known immediate-start regional peaks divided by predeclared nominal utilization",
        population_scope="small declared representative cohort; no full-scale congested claim",
        scheduler_state="hypothetical first-gate-after-submission state; not observed execution",
        risk_scope="direct deterministic common-reference/common-modeled-response scenario rows, not a future-meter guarantee",
        cpu_workers=1, blas_threads=1, solver_time_limit_seconds=60))
    return cells


def mask_gate_arrivals(arrivals, gate):
    arrivals = np.asarray(arrivals, dtype=float)
    if arrivals.ndim != 3 or not 0 <= gate < arrivals.shape[0]:
        raise ValueError("arrivals must be slot-by-region-by-class and gate valid")
    result = arrivals.copy(); result[gate:] = 0.
    return result



def _single_thread_gate_solvers(function):
    @functools.wraps(function)
    def wrapped(*args, **kwargs):
        from . import optimization
        original = optimization.linprog
        # Reset a scheduler initialized by another pipeline stage, then force
        # all LPs invoked by this gate panel to use the same single thread.
        try:
            from scipy.optimize._highspy._core import _Highs
            _Highs.resetGlobalScheduler(True)
        except ImportError:
            pass
        def bounded(*a, **kw):
            kw["options"] = {**kw.get("options", {}), "threads": 1}
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="Unrecognized options detected.*")
                return original(*a, **kw)
        optimization.linprog = bounded
        try:
            return function(*args, **kwargs)
        finally:
            optimization.linprog = original
    return wrapped


@_single_thread_gate_solvers
def run_matched_gate_panel(root, cfg, logger):
    from .experiments import _inputs, _solve_day_with_buffer, precompute_reference_schedules
    from .baselines import high_x_of_y, predict_causal_metadata_gradient_boosting, baseline_metrics, response_metrics
    from .risk_execution_composition import daily_false_credit, top_m_tail
    final = root / "experiments" / FOLDER / "results/final"; final.mkdir(parents=True, exist_ok=True)
    intermediate = root / "experiments" / FOLDER / "results/intermediate"; intermediate.mkdir(parents=True, exist_ok=True)
    source = root / "experiments/exp2_baseline_verification/results/intermediate"
    validation_days = np.load(source / "validation_profiles.npz")["days"].astype(int)
    test_days = np.load(source / "test_profiles.npz")["days"].astype(int)
    if validation_days.max() >= test_days.min():
        raise ValueError("validation and locked chronology overlap")
    days = np.r_[validation_days, test_days]
    gate = int(cfg["experiments"]["decision_time_event_gate_slot"])
    terminal = int(cfg["experiments"]["decision_time_terminal_completion_index"])
    event = list(map(int, cfg["market"]["event_slots"]))
    participants = list(map(int, cfg["experiments"]["decision_time_participating_data_center_indices"]))
    floor = float(cfg["experiments"]["decision_time_committed_event_service_mwh"])
    fixed = float(cfg["project"]["fixed_facility_load_mw"])
    dt = float(cfg["project"]["interval_minutes"]) / 60
    cap = float(cfg["project"]["flexible_capacity_mw"])
    price = float(cfg["experiments"]["independent_event_replay_price_per_mwh"])
    cfg_gate = copy.deepcopy(cfg); cfg_gate["experiments"]["lookahead_slots"] = 0
    names = ["High-5 feasible w1", "High-5 feasible w3", "High-5 feasible w10",
             "Historical mean feasible w1", "Causal metadata feasible w0.3", "Causal metadata feasible w1", "Causal metadata feasible w3"]
    weights = [1., 3., 10., 1., .3, 1., 3.]
    arrivals, _, valid_days, _, _, prices, _ = _inputs(root, cfg, logger)
    honest, strategic_schedule, _, _ = precompute_reference_schedules(root, cfg, arrivals, valid_days, prices, logger)
    declared = fixed + arrivals.sum(axis=3).transpose(0, 2, 1) / dt
    historical_target = declared + strategic_schedule - honest
    generator_sha256 = hashlib.sha256((
        inspect.getsource(run_matched_gate_panel.__wrapped__) + inspect.getsource(mask_gate_arrivals) +
        inspect.getsource(_single_thread_gate_solvers) + inspect.getsource(_inputs) +
        inspect.getsource(_solve_day_with_buffer) + inspect.getsource(precompute_reference_schedules) +
        inspect.getsource(predict_causal_metadata_gradient_boosting) + inspect.getsource(high_x_of_y) +
        sha256(root / "code/src/aicdr/optimization.py") + sha256(root / "code/src/aicdr/baselines.py")
    ).encode()).hexdigest()
    canonical_config = json.dumps(cfg, sort_keys=True, separators=(",", ":"))
    config_sha256 = hashlib.sha256(canonical_config.encode()).hexdigest()
    input_signature = _digest(arrivals, prices, historical_target, validation_days, test_days, np.asarray(weights),
                             np.asarray([gate, terminal, floor, price]),
                             np.frombuffer(canonical_config.encode(), dtype=np.uint8),
                             np.frombuffer(generator_sha256.encode(), dtype=np.uint8))
    cache = intermediate / "matched_gate_profiles.npz"
    boundary = []
    if cache.exists():
        with np.load(cache, allow_pickle=False) as old_cache:
            previous_signature = str(old_cache["input_signature"][0])
        if previous_signature != input_signature:
            retired = intermediate / f"matched_gate_profiles_retired_{previous_signature[:16]}.npz"
            if retired.exists():
                raise RuntimeError("a stale gate cache archive already exists; refusing to replace evidence")
            cache.rename(retired)
            write_json(intermediate / f"matched_gate_cache_retirement_{previous_signature[:16]}.json",
                       dict(reason="cache signature changed; genuine candidate rebuild required", old_signature=previous_signature,
                            new_signature=input_signature, old_file=retired.name, new_schema_version=2))
    if cache.exists():
        loaded = np.load(cache, allow_pickle=False)
        candidate = loaded["candidate"].copy(); reference = loaded["reference"].copy(); meter = loaded["meter"].copy()
        boundary = pd.read_csv(final / "matched_gate_information_boundary.csv").to_dict("records")
    else:
        candidates_all, reference_all, meter_all = [], [], []
        for day in days:
            masked = mask_gate_arrivals(arrivals[day], gate)
            history_days = valid_days[valid_days < int(day)]
            if len(history_days) < 14:
                raise ValueError("insufficient causal history")
            high = high_x_of_y(historical_target[history_days], event)
            mean = historical_target[history_days[-10:]].mean(axis=0)
            metadata = predict_causal_metadata_gradient_boosting(historical_target, valid_days, int(day), int(cfg["project"]["seed"]),
                                                                 arrivals, arrivals_day_override=masked)
            common = dict(require_all_arrivals_at_terminal=False, terminal_completion_index=terminal,
                          event_slots_override=event, participating_destinations=participants)
            ref = _solve_day_with_buffer(masked, prices, cfg_gate, mode="honest", minimum_participant_event_mwh=floor, **common)
            if not ref.success:
                write_json(final / "matched_gate_blocker.json", dict(day=int(day), stage="eligible_reference", message=ref.solver_message))
                raise RuntimeError(f"Matched eligible reference infeasible on day {day}: {ref.solver_message}")
            upper = np.full_like(ref.power_mw, fixed + cap); lower = np.full_like(upper, fixed)
            upper[:, :gate] = ref.power_mw[:, :gate]; lower[:, :gate] = ref.power_mw[:, :gate]
            meter_upper = upper.copy(); meter_upper[:, event] = ref.power_mw[:, event]
            response = _solve_day_with_buffer(masked, prices, cfg_gate, mode="event_response", dr_price=price,
                                              power_upper_mw=meter_upper, power_lower_mw=lower, **common)
            if not response.success:
                write_json(final / "matched_gate_blocker.json", dict(day=int(day), stage="common_modeled_response", message=response.solver_message))
                raise RuntimeError(f"Matched modeled response failed on day {day}: {response.solver_message}")
            profiles = []
            for name, w, target in zip(names, weights, [high, high, high, mean, metadata, metadata, metadata]):
                out = _solve_day_with_buffer(masked, prices, cfg_gate, mode="honest", target=target, projection_weight=w,
                                             minimum_participant_event_mwh=floor, power_upper_mw=upper, power_lower_mw=lower, **common)
                if not out.success:
                    write_json(final / "matched_gate_blocker.json", dict(day=int(day), method=name, stage="candidate", message=out.solver_message))
                    raise RuntimeError(f"Matched gate candidate failed: {day} {name}: {out.solver_message}")
                profiles.append(out.power_mw)
            profiles = np.asarray(profiles)
            if np.max(np.abs(profiles[:, :, :gate] - ref.power_mw[None, :, :gate])) > 1e-6:
                raise RuntimeError("candidate changed frozen pre-gate aggregate power")
            candidates_all.append(profiles); reference_all.append(ref.power_mw); meter_all.append(response.power_mw)
            boundary.append(dict(day=int(day), split="validation" if day in validation_days else "locked",
                                 gate_slot=gate, latest_history_day=int(history_days.max()),
                                 eligible_ledger_sha256=_digest(masked), frozen_pre_gate_state_sha256=_digest(ref.power_mw[:, :gate]),
                                 common_reference_sha256=_digest(ref.power_mw), common_modeled_response_sha256=_digest(response.power_mw),
                                 eligible_arrivals_mwh=float(masked.sum()), excluded_future_arrivals_mwh=float(arrivals[day, gate:].sum()),
                                 future_arrivals_used=False, execution_telemetry_used=False, participants=";".join(map(str, participants)),
                                 baseline_event_service_floor_mwh=floor, causal_candidates=len(names),
                                 maximum_pre_gate_state_residual_mw=float(np.max(np.abs(profiles[:, :, :gate] - ref.power_mw[None, :, :gate])))))
            logger.info("Exp32 matched gate day=%s completed (%s/%s)", day, len(boundary), len(days))
        candidate = np.asarray(candidates_all); reference = np.asarray(reference_all); meter = np.asarray(meter_all)
        pd.DataFrame(boundary).to_csv(final / "matched_gate_information_boundary.csv", index=False)
        np.savez_compressed(cache, candidate=candidate, reference=reference, meter=meter, days=days, methods=np.asarray(names), input_signature=np.asarray([input_signature]), cache_schema_version=np.asarray([2]),
                            generator_sha256=np.asarray([generator_sha256]), config_sha256=np.asarray([config_sha256]))
    nval = len(validation_days)
    validation_candidate = candidate[:nval]
    errors = np.mean((validation_candidate[:, :, :, event] - reference[:nval, None, :, event]) ** 2, axis=(0, 2, 3))
    anchor_index = min(range(3), key=lambda j: (errors[j], j))
    single_index = min(range(4, 7), key=lambda j: (errors[j], j))
    anchor_profile = validation_candidate[:, anchor_index]
    anchor_daily = daily_false_credit(anchor_profile, meter[:nval], reference[:nval], dt, event)
    total_budget = float(anchor_daily.sum()); tail_budget = top_m_tail(anchor_daily, .75)
    mse_budget = 1.10 * float(errors[anchor_index])
    design = validation_candidate[:, :, :, event].transpose(0, 2, 3, 1).reshape(-1, len(names))
    y = reference[:nval, :, event].reshape(-1); m = meter[:nval, :, event].reshape(-1)
    if design.shape[0] != y.size:
        raise RuntimeError("risk fit sample alignment mismatch")
    fit_specs = {"Gate unconstrained ensemble": (False, False, 0., 0.),
                 "Gate total-only ensemble": (True, False, 1., 0.),
                 "Gate tail-only ensemble": (False, True, 0., .5),
                 "Gate joint ensemble": (True, True, 1., .5)}
    method_profiles = {name: candidate[:, j] for j, name in enumerate(names)}
    method_profiles["Gate selected single projection"] = candidate[:, single_index]
    method_profiles["Gate selected High-5 anchor"] = candidate[:, anchor_index]
    certs, fit_rows = [], []
    for method, (total_on, tail_on, tw, cw) in fit_specs.items():
        a, cert = fit_risk_simplex(design, y, m, nval, dt_h=dt,
                                  total_budget_mwh=total_budget if total_on else None,
                                  tail_budget_mwh=tail_budget if tail_on else None,
                                  mse_budget_mw2=mse_budget, total_weight=tw, tail_weight=cw,
                                  total_scale_mwh=max(total_budget, 1.), tail_scale_mwh=max(tail_budget, 1.))
        method_profiles[method] = np.einsum("dmrt,m->drt", candidate, a)
        certs.append(dict(method=method, **cert))
        fit_rows.extend(dict(method=method, candidate=name, weight=float(value)) for name, value in zip(names, a))
    pd.DataFrame(fit_rows).to_csv(final / "matched_gate_weights.csv", index=False)
    write_json(final / "matched_gate_fit_certificates.json", certs)
    rows = []
    for method, profile in method_profiles.items():
        for i, day in enumerate(days):
            score = response_metrics(profile[i], reference[i], meter[i], event, dt)
            baseline = baseline_metrics(profile[i], reference[i], event)
            row = dict(day=int(day), split="validation" if i < nval else "locked", method=method,
                       **baseline, **score, eligible_ledger_sha256=boundary[i]["eligible_ledger_sha256"],
                       common_reference_sha256=boundary[i]["common_reference_sha256"], common_modeled_response_sha256=boundary[i]["common_modeled_response_sha256"],
                       gate_slot=gate, baseline_event_service_mwh=float(np.maximum(profile[i][participants][:, event] - fixed, 0).sum()*dt),
                       baseline_event_service_floor_mwh=floor,
                       modeled_3mwh_credit_shortfall=bool(score["meter_capped_response_mwh"] < 3. - 1e-8),
                       scoring="same-population baseline-credit audit against common declaration-only modeled response",
                       observed_utility_intervention=False)
            rows.append(row)
    daily = pd.DataFrame(rows); daily.to_csv(final / "matched_gate_daily.csv", index=False)
    summary = daily.groupby(["split", "method"], as_index=False).agg(
        days=("day", "count"), nrmse=("nrmse", "mean"), false_response_mwh=("false_response_mwh", "mean"),
        modeled_payable_response_mwh=("meter_capped_response_mwh", "mean"), underestimation_mwh=("underestimation_mwh", "mean"),
        credit_recall=("credit_recall", "mean"), credit_f1=("credit_f1", "mean"),
        modeled_3mwh_credit_shortfall_rate=("modeled_3mwh_credit_shortfall", "mean"),
        minimum_baseline_event_service_mwh=("baseline_event_service_mwh", "min"))
    summary.to_csv(final / "matched_gate_summary.csv", index=False)
    hull_rows, pair_rows = [], []
    for split, indices in (("validation", np.arange(nval)), ("locked", np.arange(nval, len(days)))):
        panel = candidate[indices][:, :, :, event].transpose(1, 0, 2, 3).reshape(len(names), -1)
        differences = panel[1:] - panel[0]
        singular_values = np.linalg.svd(differences, compute_uv=False)
        unique=[]
        for j in range(len(names)):
            if not any(np.max(np.abs(panel[j]-panel[k])) <= 1e-8 for k in unique): unique.append(j)
        for j in range(len(names)):
            for k in range(j+1,len(names)):
                pair_rows.append(dict(split=split,first_method=names[j],second_method=names[k],
                    event_profile_l2_mw=float(np.linalg.norm(panel[j]-panel[k])),max_absolute_difference_mw=float(np.max(np.abs(panel[j]-panel[k])))))
        split_daily=daily[daily.split==split]
        selected=method_profiles["Gate selected single projection"][indices]
        fitted_difference=max(float(np.max(np.abs(method_profiles[name][indices]-selected))) for name in fit_specs)
        hull_rows.append(dict(split=split,days=len(indices),candidate_count=len(names),distinct_event_profiles=len(unique),
            event_affine_hull_rank=int(np.sum(singular_values>1e-8)),rank_absolute_tolerance=1e-8,
            maximum_pairwise_event_l2_mw=max(r["event_profile_l2_mw"] for r in pair_rows if r["split"]==split),
            all_method_day_cells=len(split_daily),service_floor_binding_cells=int(np.isclose(split_daily.baseline_event_service_mwh,floor,atol=1e-8,rtol=0).sum()),
            maximum_fitted_profile_difference_from_selected_single_mw=fitted_difference,
            interpretation="fixed pre-gate benchmark and binding3MWh event service floor leave a rank2 shape hull; all objectives choose the same vertex, so no incremental risk-module benefit"))
    pd.DataFrame(hull_rows).to_csv(final/"matched_gate_hull_diagnostics.csv",index=False)
    pd.DataFrame(pair_rows).to_csv(final/"matched_gate_candidate_distances.csv",index=False)
    # Every method/day pair remains present; no ranking-dependent denominators.
    expected = len(days) * len(method_profiles)
    if len(daily) != expected or daily.groupby("method").day.nunique().nunique() != 1:
        raise RuntimeError("matched gate method/day denominator mismatch")
    for col in ("eligible_ledger_sha256", "common_reference_sha256", "common_modeled_response_sha256"):
        if daily.groupby("day")[col].nunique().max() != 1:
            raise RuntimeError(f"unmatched gate comparator: {col}")
    write_json(final / "matched_gate_metadata.json", dict(
        validation_days=validation_days.tolist(), locked_days=test_days.tolist(), gate_slot=gate,
        participants=participants, baseline_event_service_floor_mwh=floor, modeled_response_tariff_per_mwh=price,
        candidate_names=names, selected_single=names[single_index], selected_reference_anchor=names[anchor_index],
        total_budget_mwh=total_budget, tail_budget_mwh=tail_budget, validation_mse_budget_mw2=mse_budget,
        fit_accuracy_mode="exact convex MSE, fixed 10% reference neighborhood", expected_daily_rows=expected,
        retained_daily_rows=len(daily), source_profile_role="day identifiers only; legacy baseline/response values are not reused",
        cache_schema_version=2, generator_sha256=generator_sha256, config_sha256=config_sha256, input_signature=input_signature, implementation_sha256=_implementation_hashes(root), protocol_sha256=sha256(root / "experiments" / FOLDER / "README.md"),
        future_arrivals_used=False, current_execution_telemetry_used=False, selection_uses_locked_outcomes=False,
        pre_gate_state="identical benchmark aggregate regional power, not observed job-indexed online state",
        scoring="one baseline-credit definition on matched eligible reference and modeled response",
        modeled_shortfall="supplementary 3-MWh modeled credit threshold; not an observed default or a changed service entitlement",
        runtime_composition_claim=False, observed_meter_claim=False, cpu_workers=1, blas_threads=1))
    np.savez_compressed(final / "matched_gate_frozen_profiles.npz", days=days, methods=np.asarray(list(method_profiles)),
                        profiles=np.stack(list(method_profiles.values()), axis=1), reference=reference, modeled_response=meter)
    return summary


def run_exp32_matched_gate_capacity(root: Path, cfg: dict, logger: logging.Logger, *, part="all"):
    if part not in {"all", "gate", "capacity"}:
        raise ValueError("part must be all, gate, or capacity")
    if part in {"all", "gate"}:
        run_matched_gate_panel(root, cfg, logger)
    if part in {"all", "capacity"}:
        run_capacity_panel(root, cfg, logger)
        run_joint_runtime_diagnostic(root, cfg, logger)
    final = root / "experiments" / FOLDER / "results/final"
    write_json(final / "experiment_metadata.json", dict(experiment=FOLDER, schema_version=1, source_witness_sha256=sha256(root / "experiments/exp27_executable_common_witness/results/final/runtime_complete_witness.npz"),
               panels=[name for name in ("matched_gate_metadata.json", "runtime_capacity_metadata.json", "joint_runtime_risk_mse_metadata.json") if (final/name).exists()],
               protocol_sha256=sha256(root / "experiments" / FOLDER / "README.md"), implementation_sha256=_implementation_hashes(root),
               interpretation="matched aggregate gate evidence and separate small-cohort full-runtime stress; no claim these alone close a deployed measured pipeline"))


def run_joint_runtime_diagnostic(root, cfg, logger):
    """Exact joint risk/MSE rows and minimum-achievable-MSE characterization."""
    final = root / "experiments" / FOLDER / "results/final"
    metadata = json.loads((final / "runtime_capacity_metadata.json").read_text())
    days = metadata["selected_locked_days"]
    event_slots = np.asarray(cfg["market"]["event_slots"], dtype=int)
    slots = int(cfg["project"]["slots_per_day"]); gate_slot = int(cfg["experiments"]["decision_time_event_gate_slot"])
    dt = float(cfg["project"]["interval_minutes"]) / 60
    rows, certificates = [], []
    for day in days:
        gate = day * slots + gate_slot
        for utilization in (.98, 1.10):
            path = final / f"runtime_day{day}_u{utilization:.2f}_runtime_cost_only.npz"
            with np.load(path) as a:
                indices = a["source_job_index"]; pending = a["pending_source_job_index"]
                lookup = {v: j for j, v in enumerate(indices)}
                position = np.asarray([lookup[v] for v in pending], dtype=int)
                rel=a["release"][position]-gate; dl=a["deadline"][position]-gate; run=a["runtime_slots"][position]
                region=a["region"][position]; power=a["fixed_power_mw"][position]
                fixed=a["fixed_profile_mw"].copy(); ref=a["reference_mw"].copy(); meter=a["modeled_response_mw"].copy()
                cap=a["capacity_mw"].copy(); event=a["event_mask"].copy()
            for method in ("joint_zero_risk_exact_mse", "phase_one_minimum_mse_zero_risk"):
                logger.info("Exp32 integrated day=%s utilization=%.2f method=%s", day, utilization, method)
                mse_budget = 0. if method.startswith("joint") else None
                out = solve_runtime_milp(rel,dl,run,region,power,np.tile(event*float(cfg["market"]["default_dr_price_per_mwh"]),(ref.shape[0],1)),cap,
                    fixed_profile_mw=fixed,dt_h=dt,waiting_cost=float(cfg["workload"]["waiting_cost_per_mwh_slot"][-1]),event_mask=event,
                    risk_ceiling_mw=np.maximum(ref,meter),risk_day_index=(np.arange(ref.shape[1])+gate_slot)//slots,
                    total_budget_mwh=0.,tail_budget_mwh=0.,mse_reference_mw=ref,mse_budget_mw2=mse_budget,
                    power_quantum_mw=.001,objective_mode="cost" if method.startswith("joint") else "minimum_mse",time_limit=60.)
                row={k:v for k,v in asdict(out).items() if k not in {"starts","profile_mw"}}
                row.update(day=day,nominal_reference_peak_utilization=utilization,method=method,pending_jobs=len(pending),
                           total_budget_mwh=0.,tail_budget_mwh=0.,mse_budget_mw2=mse_budget,scenario_source_sha256=sha256(path),
                           execution_telemetry_used=False,model="same fixed-rate runtime/capacity/risk/exact-MSE MILP")
                if out.success:
                    cert=certify_execution_transfer(_day_tensor(ref,gate_slot,slots),_day_tensor(out.profile_mw,gate_slot,slots),
                         _day_tensor(meter,gate_slot,slots),_day_tensor(ref,gate_slot,slots),dt,event_slots,
                         total_budget_mwh=0.,tail_budget_mwh=0.,mse_budget_mw2=mse_budget)
                    # The final calendar day is explicitly closed in the
                    # source horizon, so both implementations score exactly
                    # the same day/region/event samples.
                    exact_mse=float(np.mean((out.profile_mw[:,event]-ref[:,event])**2))
                    if abs(exact_mse-out.event_mse_mw2)>1e-12 or abs(exact_mse-cert["executed_event_mse_mw2"])>1e-12:
                        raise RuntimeError("independent MSE reconstruction mismatch")
                    row.update(independently_recomputed_event_mse_mw2=exact_mse,
                               independently_recomputed_total_false_credit_mwh=cert["executed_total_false_credit_mwh"],
                               independently_recomputed_tail_false_credit_mwh=cert["executed_tail_false_credit_mwh"],
                               joint_certificate_accept=bool(cert["execution_certificate_accept"]),
                               maximum_achieved_capacity_utilization=float(np.max(out.profile_mw/cap[:,None])))
                    certificates.append(dict(day=day,method=method,nominal_reference_peak_utilization=utilization,
                                             exact_event_mse_mw2=exact_mse,**cert))
                    np.savez_compressed(final/f"joint_runtime_day{day}_u{utilization:.2f}_{method}.npz",source_job_index=pending,
                        starts_absolute=out.starts+gate,release=rel+gate,deadline=dl+gate,runtime_slots=run,region=region,fixed_power_mw=power,
                        profile_mw=out.profile_mw,fixed_profile_mw=fixed,reference_mw=ref,modeled_response_mw=meter,
                        capacity_mw=cap,event_mask=event)
                rows.append(row);pd.DataFrame(rows).to_csv(final.parent/"intermediate/joint_runtime_checkpoint.csv",index=False)
    table=pd.DataFrame(rows);table.to_csv(final/"joint_runtime_risk_mse_cells.csv",index=False)
    write_json(final/"joint_runtime_risk_mse_certificates.json",certificates)
    write_json(final/"joint_runtime_risk_mse_metadata.json",dict(expected_cells=12,retained_cells=len(table),
        selected_locked_days=days,nominal_reference_peak_utilizations=[.98,1.10],
        joint_cells=6,phase_one_cells=6,power_quantum_mw=.001,epigraph="exact finite tangent maximum on every attainable integer power level",
        total_risk_budget_mwh=0.,tail_risk_budget_mwh=0.,joint_mse_budget_mw2=0.,
        phase_one_objective="minimum exact event MSE subject to same full-runtime, capacity, zero total/tail constraints",
        sequential_diagnostic=True,changed_entitlements=False,selection_uses_risk_outcomes=False,
        modeled_scenario_information="declaration-only schedules known at gate; not a post-event measured outcome",
        feasible_cells=int(table.success.sum()),optimal_cells=int(table.optimal.sum()),
        proven_infeasible_cells=int((table.status==2).sum()),time_limited_cells=int((table.status==1).sum()),
        implementation_sha256=_implementation_hashes(root),
        protocol_sha256=sha256(root/"experiments"/FOLDER/"README.md")))
    return table
