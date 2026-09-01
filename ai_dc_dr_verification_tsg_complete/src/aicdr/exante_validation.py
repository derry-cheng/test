"""Independent validation of the submit-time job contract."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix

from .data import load_mit_job_ledger, load_mit_submission_ledger


def run_exp25_exante_job_validation(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
) -> None:
    """Audit declaration coverage without feeding telemetry into the LP.

    The experiment is deliberately a validation stage rather than another
    scheduling objective.  It joins the saved submit-time ledger to the
    measured execution ledger only after all declarations are frozen and
    reports central-estimate error, nameplate coverage, and temporal coverage.
    The observed quantities cannot change any Exp19 primal variable.
    """
    folder = root / "experiments/exp25_exante_job_validation"
    final = folder / "results/final"
    final.mkdir(parents=True, exist_ok=True)
    interval_s = int(cfg["project"]["interval_minutes"] * 60)
    n_regions = int(cfg["project"]["number_of_regions"])
    manifest_path = root / cfg["data"]["processed_dir"] / "data_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    calibration = manifest.get("submission_calibration", {})
    if not calibration:
        raise RuntimeError("Exp25 requires the frozen submit-time calibration")
    cap_mw = float(
        cfg["experiments"].get("job_level_declared_per_gpu_power_cap_mw", 1.0e-3)
    )
    runtime_fallback = int(
        cfg["experiments"].get("job_level_unbounded_timelimit_slots", 128)
    )
    queue_buffer = int(
        cfg["experiments"].get("job_level_submission_buffer_slots", 0)
    )
    time_origin_seconds = float(
        cfg["experiments"].get("job_level_time_origin_seconds", np.nan)
    )
    if not np.isfinite(time_origin_seconds):
        raise ValueError("experiments.job_level_time_origin_seconds must be finite")
    submission = load_mit_submission_ledger(
        root / cfg["data"]["mit_scheduler"],
        interval_s,
        None,
        n_regions,
        declared_service_fraction=float(calibration["declared_service_fraction"]),
        declared_per_gpu_power_cap_mw=cap_mw,
        unbounded_timelimit_slots=runtime_fallback,
        submission_buffer_slots=queue_buffer,
        time_origin_seconds=time_origin_seconds,
    )
    execution = load_mit_job_ledger(
        root / cfg["data"]["mit_scheduler"],
        root / cfg["data"]["mit_dcgm"],
        interval_s,
        None,
        n_regions,
        deadline_mode="observed",
        time_origin_seconds=time_origin_seconds,
    )
    execution = execution[["id_job", "time_start", "time_end", "energy_mwh", "job_type"]].copy()
    execution["id_job"] = execution["id_job"].astype(np.int64)
    submission["id_job"] = submission["id_job"].astype(np.int64)
    joined = submission.merge(
        execution,
        on="id_job",
        how="inner",
        suffixes=("_declared", "_observed"),
        validate="one_to_one",
    )
    if joined.empty:
        raise RuntimeError("Exp25 could not match the declaration and execution ledgers")
    joined["central_ratio"] = joined["energy_mwh"] / np.maximum(
        joined["declared_energy_mwh"], 1e-12
    )
    joined["upper_coverage"] = (
        joined["energy_mwh"] <= joined["declared_energy_upper_mwh"] + 1e-12
    )
    origin = float(submission.attrs["time_origin_seconds"])
    joined["observed_start_slot_from_submission_origin"] = np.floor(
        (joined["time_start"] - origin) / float(interval_s)
    ).astype(np.int64)
    joined["observed_end_slot_from_submission_origin"] = np.ceil(
        (joined["time_end"] - origin) / float(interval_s)
    ).astype(np.int64)
    joined["declared_deadline_coverage"] = (
        joined["observed_end_slot_from_submission_origin"] <= joined["deadline_slot"]
    )
    # Exact binding-capacity stress panel.  The cohort is fixed by a declared
    # calendar index before looking at outcomes: every submitted job whose
    # declared window intersects that day's event is retained.  A binary
    # start-time MILP enforces one contiguous service block per job while the
    # regional event-slot rows and the service floor are simultaneously active.
    stress_day = int(cfg["experiments"].get("job_level_stress_panel_day_index", 20))
    slots_per_day = int(cfg["project"]["slots_per_day"])
    event_slots = sorted(int(value) for value in cfg["market"]["event_slots"])
    event_start = stress_day * slots_per_day + min(event_slots)
    event_end = stress_day * slots_per_day + max(event_slots) + 1
    cohort = submission[
        (submission["submit_slot"] < event_end)
        & (submission["deadline_slot"] > event_start)
    ].copy()
    if cohort.empty:
        raise RuntimeError("The predeclared Exp25 stress-day cohort is empty")
    stress_capacity_mw = float(
        cfg["experiments"].get("job_level_stress_panel_capacity_mw", 0.001)
    )
    stress_floor_mwh = float(
        cfg["experiments"].get(
            "job_level_stress_panel_minimum_event_service_mwh", 0.004
        )
    )
    if stress_capacity_mw <= 0.0 or stress_floor_mwh <= 0.0:
        raise ValueError("Exp25 stress capacity and event floor must be positive")
    stress_starts = cohort["submit_slot"].to_numpy(dtype=np.int64)
    stress_ends = cohort["deadline_slot"].to_numpy(dtype=np.int64)
    stress_counts = stress_ends - stress_starts
    required_slots = cohort["required_service_slots"].to_numpy(dtype=np.int64)
    if np.any(required_slots <= 0) or np.any(required_slots > stress_counts):
        raise RuntimeError("Exp25 stress cohort contains an infeasible nonpreemptive declaration")
    stress_slots = np.concatenate(
        [
            np.arange(int(start), int(end), dtype=np.int64)
            for start, end in zip(stress_starts, stress_ends)
        ]
    )
    stress_jobs = np.repeat(np.arange(len(cohort), dtype=np.int64), stress_counts)
    stress_regions = np.repeat(
        cohort["region"].to_numpy(dtype=np.int64), stress_counts
    )
    stress_energy = cohort["declared_energy_mwh"].to_numpy(dtype=float)
    stress_gpus = cohort["requested_gpus"].to_numpy(dtype=float)
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    event_slot_values = np.asarray(
        [stress_day * slots_per_day + slot for slot in event_slots], dtype=np.int64
    )
    event_slot_set = set(event_slot_values.tolist())
    event_position = {
        int(slot): index for index, slot in enumerate(event_slot_values.tolist())
    }
    if not event_slot_values.size:
        raise RuntimeError("The predeclared Exp25 stress cohort has no event slots")

    # Build one binary variable for every admissible start.  The selected start
    # induces a fixed-rate contiguous block, so no fractional pause pattern can
    # satisfy the constraints.  Energies are scaled to micro-MWh for HiGHS
    # numerical stability; all reported residuals are converted back to MWh.
    candidate_job: list[int] = []
    candidate_start: list[int] = []
    candidate_cost: list[float] = []
    candidate_service: list[dict[int, float]] = []
    candidate_offsets = [0]
    wait_cost = float(cfg["workload"]["waiting_cost_per_mwh_slot"][-1])
    event_price = float(cfg["market"]["default_dr_price_per_mwh"])
    for job, (start, end, k, gpus, energy) in enumerate(
        zip(stress_starts, stress_ends, required_slots, stress_gpus, stress_energy)
    ):
        cap_per_slot = float(gpus) * cap_mw * dt_h
        full_slots = max(0, int(k) - 1)
        remainder = float(energy) - full_slots * cap_per_slot
        if remainder <= 1.0e-12:
            remainder = cap_per_slot
        # Capacity and the event-floor constraints see only the event-slot
        # service vector.  Starts with the same vector are therefore exactly
        # interchangeable; retaining the least-cost representative is a
        # dominance reduction, not a heuristic screening rule.
        best_by_event_pattern: dict[tuple[tuple[int, float], ...], tuple[int, float, dict[int, float]]] = {}
        for block_start in range(int(start), int(end) - int(k) + 1):
            amounts: dict[int, float] = {}
            cost = 0.0
            block_capacity_feasible = True
            for offset in range(int(k)):
                amount = cap_per_slot if offset < full_slots else remainder
                slot = block_start + offset
                if slot in event_slot_set and amount > stress_capacity_mw * dt_h + 1.0e-12:
                    # A block that exceeds the declared event-slot capacity is
                    # infeasible for every assignment; removing it is an exact
                    # presolve rule, not a performance-motivated heuristic.
                    block_capacity_feasible = False
                    break
                amounts[slot] = amount
                cost += amount * (
                    wait_cost * float(slot - start)
                    + (event_price if slot % slots_per_day in event_slots else 0.0)
                )
            if not block_capacity_feasible:
                continue
            pattern = tuple(
                sorted(
                    (int(slot), round(float(amount), 15))
                    for slot, amount in amounts.items()
                    if int(slot) in event_slot_set
                )
            )
            previous = best_by_event_pattern.get(pattern)
            if previous is None or cost < previous[1] - 1.0e-15:
                best_by_event_pattern[pattern] = (block_start, cost, amounts)
        for block_start, cost, amounts in best_by_event_pattern.values():
            candidate_job.append(job)
            candidate_start.append(block_start)
            candidate_cost.append(cost)
            candidate_service.append(amounts)
        candidate_offsets.append(len(candidate_job))
    n_candidates = len(candidate_job)
    if n_candidates == 0:
        raise RuntimeError("The predeclared Exp25 stress cohort has no admissible starts")
    logger.info(
        "Exp25 exact stress MILP: %d cohort jobs, %d dominance-reduced start variables",
        len(cohort),
        n_candidates,
    )
    # Subtract each job's least-cost representative from all of its starts.
    # This is an exact objective shift (the assignment equalities add the same
    # constant for every feasible schedule) and gives HiGHS a much tighter
    # branch-and-bound bound around the event-floor decisions.
    candidate_cost_array = np.asarray(candidate_cost, dtype=float)
    for job in range(len(cohort)):
        first = int(candidate_offsets[job])
        last = int(candidate_offsets[job + 1])
        candidate_cost_array[first:last] -= float(np.min(candidate_cost_array[first:last]))
    candidate_cost = candidate_cost_array.tolist()
    scale = 1.0e6
    rows: list[int] = []
    cols: list[int] = []
    values: list[float] = []
    lower_rows: list[float] = []
    upper_rows: list[float] = []
    row_id = 0
    # Exactly one start per job. Candidate starts are appended job by job, so
    # use the recorded offsets instead of an O(|J|*|Y|) ownership scan.
    for job in range(len(cohort)):
        first_candidate = int(candidate_offsets[job])
        last_candidate = int(candidate_offsets[job + 1])
        if last_candidate <= first_candidate:
            raise RuntimeError(f"Stress job {job} has no admissible start variable")
        candidate_indices = np.arange(first_candidate, last_candidate, dtype=np.int64)
        rows.extend([row_id] * len(candidate_indices))
        cols.extend(candidate_indices.tolist())
        values.extend([1.0] * len(candidate_indices))
        lower_rows.append(1.0)
        upper_rows.append(1.0)
        row_id += 1
    # Regional event-slot capacities.
    candidate_regions = np.repeat(
        cohort["region"].to_numpy(dtype=np.int64),
        np.diff(np.asarray(candidate_offsets, dtype=np.int64)),
    )
    capacity_row_lookup = {
        (int(region), int(slot)): row_id + region * len(event_slot_values) + position
        for region in range(n_regions)
        for position, slot in enumerate(event_slot_values)
    }
    for index, (region, amounts) in enumerate(zip(candidate_regions, candidate_service)):
        for slot, amount in amounts.items():
            capacity_row = capacity_row_lookup.get((int(region), int(slot)))
            if capacity_row is not None:
                rows.append(capacity_row)
                cols.append(index)
                values.append(amount * scale)
    for _ in range(n_regions * len(event_slot_values)):
        lower_rows.append(-np.inf)
        upper_rows.append(stress_capacity_mw * dt_h * scale)
        row_id += 1
    # The event service floor is a lower bound, represented as -service <= -floor.
    for index, amounts in enumerate(candidate_service):
        event_amount = sum(amounts.get(int(slot), 0.0) for slot in event_slot_values)
        if event_amount:
            rows.append(row_id)
            cols.append(index)
            values.append(-event_amount * scale)
    lower_rows.append(-np.inf)
    upper_rows.append(-stress_floor_mwh * scale)
    row_id += 1
    a = coo_matrix(
        (np.asarray(values, dtype=float), (np.asarray(rows), np.asarray(cols))),
        shape=(row_id, n_candidates),
    ).tocsr()
    logger.info("Exp25 exact stress MILP matrix: %d rows, %d nonzeros", a.shape[0], a.nnz)
    stress_result = milp(
        c=np.asarray(candidate_cost, dtype=float) * scale,
        integrality=np.ones(n_candidates, dtype=np.int8),
        bounds=Bounds(np.zeros(n_candidates), np.ones(n_candidates)),
        constraints=LinearConstraint(
            a,
            np.asarray(lower_rows, dtype=float),
            np.asarray(upper_rows, dtype=float),
        ),
        options={
            "presolve": True,
            "mip_rel_gap": 0.0,
            "time_limit": float(
                cfg["experiments"].get("job_level_stress_milp_time_limit_s", 120.0)
            ),
        },
    )
    solver_name = "scipy.optimize.milp"
    if stress_result.success:
        selected = np.flatnonzero(np.asarray(stress_result.x) > 0.5)
    else:
        # This panel is a finite assignment model.  If HiGHS reaches its time
        # limit, accept the LP relaxation only when its solution is already
        # integral to numerical tolerance; otherwise fail closed rather than
        # rounding a fractional schedule into a purported certificate.
        eq_mask = np.isclose(np.asarray(lower_rows), np.asarray(upper_rows), rtol=0.0, atol=0.0)
        ub_mask = np.isfinite(np.asarray(upper_rows)) & ~eq_mask
        from scipy.optimize import linprog

        relaxation = linprog(
            np.asarray(candidate_cost, dtype=float) * scale,
            A_ub=a[ub_mask],
            b_ub=np.asarray(upper_rows, dtype=float)[ub_mask],
            A_eq=a[eq_mask],
            b_eq=np.asarray(upper_rows, dtype=float)[eq_mask],
            bounds=(0.0, 1.0),
            method="highs",
        )
        if not relaxation.success:
            raise RuntimeError(
                "Exp25 binding-capacity start-time MILP failed and its LP "
                f"relaxation is infeasible: {stress_result.message}"
            )
        fractional = np.abs(np.asarray(relaxation.x) - np.round(relaxation.x))
        if float(np.max(fractional)) > 1.0e-7:
            raise RuntimeError(
                "Exp25 binding-capacity start-time MILP reached its time limit "
                "with a fractional LP relaxation; no rounded schedule is accepted"
            )
        selected = np.flatnonzero(np.asarray(relaxation.x) > 0.5)
        stress_result = relaxation
        solver_name = "integral LP relaxation (exact assignment certificate)"
    if len(selected) != len(cohort):
        raise RuntimeError("Exp25 MILP did not select exactly one start per stress job")
    selected_by_job = {int(candidate_job[i]): i for i in selected}
    stress_service = np.zeros(len(stress_slots), dtype=float)
    stress_start_slots = np.full(len(cohort), -1, dtype=np.int64)
    stress_slot_counts = np.zeros(len(cohort), dtype=np.int64)
    local_offsets = np.concatenate([[0], np.cumsum(stress_counts, dtype=np.int64)])
    for job, index in selected_by_job.items():
        stress_start_slots[job] = int(candidate_start[index])
        stress_slot_counts[job] = int(required_slots[job])
        for slot, amount in candidate_service[index].items():
            stress_service[int(local_offsets[job] + slot - stress_starts[job])] = amount
    stress_profile = np.bincount(
        stress_regions * (int(stress_ends.max()) + 1) + stress_slots,
        weights=stress_service,
        minlength=n_regions * (int(stress_ends.max()) + 1),
    ).reshape(n_regions, int(stress_ends.max()) + 1)
    stress_capacity_slack = stress_capacity_mw * dt_h - stress_profile[:, event_slot_values]
    stress_job_residual = np.bincount(
        stress_jobs, weights=stress_service, minlength=len(cohort)
    ) - stress_energy
    np.savez_compressed(
        final / "job_level_capacity_stress_solution.npz",
        service_mwh=stress_service,
        event_profile_mwh=stress_profile[:, event_slot_values],
        declared_job_energy_mwh=stress_energy,
        submit_slot=stress_starts,
        deadline_slot=stress_ends,
        region=cohort["region"].to_numpy(dtype=np.int64),
        requested_gpus=stress_gpus,
        stress_day=np.asarray([stress_day], dtype=np.int64),
        selected_start_slot=stress_start_slots,
        service_slot_count=stress_slot_counts,
    )
    stress_summary = pd.DataFrame(
        [
            {"metric": "stress_day_index", "value": stress_day, "unit": "day"},
            {"metric": "cohort_jobs", "value": len(cohort), "unit": "jobs"},
            {"metric": "service_variables", "value": len(stress_slots), "unit": "variables"},
            {"metric": "capacity_mw_per_region", "value": stress_capacity_mw, "unit": "MW"},
            {"metric": "minimum_event_capacity_slack_mwh", "value": float(stress_capacity_slack.min()), "unit": "MWh"},
            {"metric": "active_event_capacity_slot_fraction", "value": float(np.mean(stress_capacity_slack <= 1e-10)), "unit": "fraction"},
            {"metric": "event_service_floor_mwh", "value": stress_floor_mwh, "unit": "MWh"},
            {"metric": "event_service_delivered_mwh", "value": float(stress_profile[:, event_slot_values].sum()), "unit": "MWh"},
            {"metric": "maximum_job_energy_residual_mwh", "value": float(np.max(np.abs(stress_job_residual))), "unit": "MWh"},
            {"metric": "solver_success", "value": 1, "unit": "boolean"},
            {"metric": "binary_start_variables", "value": n_candidates, "unit": "variables"},
            {"metric": "selected_start_variables", "value": int(len(selected)), "unit": "variables"},
            {"metric": "solver_time_limit_seconds", "value": float(cfg["experiments"].get("job_level_stress_milp_time_limit_s", 120.0)), "unit": "seconds"},
        ]
    )
    stress_summary.to_csv(final / "job_level_capacity_stress_summary.csv", index=False)
    pd.DataFrame(
        [
            {
                "event_slot": int(slot),
                "maximum_loading_mw": float(stress_profile[:, slot].max() / dt_h),
                "minimum_capacity_slack_mwh": float(stress_capacity_slack[:, index].min()),
                "event_service_mwh": float(stress_profile[:, slot].sum()),
            }
            for index, slot in enumerate(event_slot_values.tolist())
        ]
    ).to_csv(final / "job_level_capacity_stress_event_slots.csv", index=False)
    summary_rows = [
        {"metric": "submitted_jobs", "value": int(len(submission)), "unit": "jobs"},
        {"metric": "execution_matched_jobs", "value": int(len(joined)), "unit": "jobs"},
        {"metric": "execution_match_fraction", "value": float(len(joined) / max(1, len(submission))), "unit": "fraction"},
        {"metric": "declared_service_fraction", "value": float(calibration["declared_service_fraction"]), "unit": "fraction"},
        {"metric": "observed_to_declared_energy_median", "value": float(joined["central_ratio"].median()), "unit": "ratio"},
        {"metric": "observed_to_declared_energy_q10", "value": float(joined["central_ratio"].quantile(0.10)), "unit": "ratio"},
        {"metric": "observed_to_declared_energy_q90", "value": float(joined["central_ratio"].quantile(0.90)), "unit": "ratio"},
        {"metric": "physical_nameplate_energy_coverage", "value": float(joined["upper_coverage"].mean()), "unit": "fraction"},
        {"metric": "observed_completion_inside_declared_window", "value": float(joined["declared_deadline_coverage"].mean()), "unit": "fraction"},
        {"metric": "maximum_declared_window_infeasible_jobs", "value": int(submission.attrs["declared_window_infeasible_jobs"]), "unit": "jobs"},
        {"metric": "stress_cohort_jobs", "value": int(len(cohort)), "unit": "jobs"},
        {"metric": "stress_active_capacity_slot_fraction", "value": float(np.mean(stress_capacity_slack <= 1e-10)), "unit": "fraction"},
    ]
    pd.DataFrame(summary_rows).to_csv(final / "exante_job_validation_summary.csv", index=False)
    by_type = (
        joined.groupby("job_type_declared", dropna=False)
        .agg(
            jobs=("id_job", "size"),
            median_observed_to_declared_energy=("central_ratio", "median"),
            q90_observed_to_declared_energy=("central_ratio", lambda x: x.quantile(0.9)),
            physical_nameplate_coverage=("upper_coverage", "mean"),
            declared_window_coverage=("declared_deadline_coverage", "mean"),
        )
        .reset_index()
        .rename(columns={"job_type_declared": "job_type"})
    )
    by_type.to_csv(final / "exante_job_validation_by_type.csv", index=False)
    write_metadata = {
        "experiment": "independent submit-time declaration validation",
        "submission_ledger_digest": str(submission.attrs["canonical_submission_ledger_sha256"]),
        "execution_ledger_role": "post-event scoring only",
        "telemetry_used_in_exp19_decision": False,
        "population_rule": "all valid scheduler submissions; execution matching is a post-event audit",
        "submitted_jobs": int(len(submission)),
        "execution_matched_jobs": int(len(joined)),
        "declared_service_fraction": float(calibration["declared_service_fraction"]),
        "physical_upper_service_fraction": float(calibration["physical_upper_service_fraction"]),
        "declared_per_gpu_power_cap_mw": cap_mw,
        "unbounded_timelimit_slots": runtime_fallback,
        "submission_buffer_slots": queue_buffer,
        "time_origin_seconds": time_origin_seconds,
        "results": {
            "summary": "exante_job_validation_summary.csv",
            "by_type": "exante_job_validation_by_type.csv",
            "capacity_stress_summary": "job_level_capacity_stress_summary.csv",
            "capacity_stress_solution": "job_level_capacity_stress_solution.npz",
            "capacity_stress_event_slots": "job_level_capacity_stress_event_slots.csv",
        },
        "capacity_stress_panel": {
            "stress_day_index": int(stress_day),
            "cohort_jobs": int(len(cohort)),
            "service_variables": int(len(stress_service)),
            "binary_start_variables": int(n_candidates),
            "selected_start_variables": int(len(selected)),
            "capacity_mw_per_region": stress_capacity_mw,
            "event_service_floor_mwh": stress_floor_mwh,
            "event_service_delivered_mwh": float(stress_profile[:, event_slot_values].sum()),
            "active_event_capacity_slot_fraction": float(np.mean(stress_capacity_slack <= 1e-10)),
            "minimum_event_capacity_slack_mwh": float(stress_capacity_slack.min()),
            "maximum_job_energy_residual_mwh": float(np.max(np.abs(stress_job_residual))),
            "solver_success": True,
            "solver": solver_name + " with binary start variables and exact contiguous fixed-rate blocks",
            "solution_file": "job_level_capacity_stress_solution.npz",
        },
        "interpretation": (
            "The central declaration is a training-only ex-ante entitlement; the "
            "full requested nameplate is the physical upper bound. Observed DCGM "
            "energy is reported for coverage and cannot alter a release, deadline, "
            "or service equality. The stress panel is solved with one binary "
            "start per job, so capacity and the event-service floor are tested "
            "on an executable nonpreemptive schedule."
        ),
    }
    (final / "experiment_metadata.json").write_text(
        json.dumps(write_metadata, indent=2), encoding="utf-8"
    )
    logger.info(
        "Experiment 25 complete: %d submitted jobs, %d execution matches",
        len(submission),
        len(joined),
    )
