from __future__ import annotations
import copy
import hashlib
import json
import logging
import math
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from itertools import permutations, product
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, linprog, minimize
from scipy.sparse import coo_matrix, csr_matrix
from .progress import progress as tqdm

from .baselines import (
    BaselinePredictions,
    baseline_metrics,
    exact_block_sign_test,
    holm_adjust,
    moving_block_bootstrap_mean_ci,
    predict_causal_metadata_gradient_boosting,
    predict_additional_strong_baselines,
    predict_statistical_baselines,
    response_delivery_metrics,
    response_metrics,
)
from .data import (
    _aggregate_burstgpt,
    _aggregate_mit_jobs,
    audit_mit_ledger_provenance,
    load_mit_job_ledger,
    load_mit_submission_ledger,
    load_workload,
)
from .optimization import (
    PowerSystem,
    payment_value_interval,
    build_n1_security_factors,
    build_grid_profiles,
    parse_pglib_case,
    power_system_from_ppc,
    solve_payment_certified_n1_projection,
    solve_n1_sced,
    solve_n1_sced_segment_minimum,
    solve_sced,
    solve_exact_nonpreemptive_blocks,
    solve_lexicographic_workload_projection,
    solve_workload_schedule,
)
from .utils import sha256, write_json
from .visualization import (
    plot_case_study,
    plot_exp1,
    plot_exp13_real_trace_replay,
    plot_exp14_job_level_fidelity,
    plot_exp15_interval_certificate,
    plot_exp16_ledger_capacity,
    plot_exp2,
    plot_exp3,
)


METHODS = [
    "High-5-of-10",
    "Ridge",
    "Gradient Boosting",
    "Extra Trees",
    "Metadata Gradient Boosting",
    "Ex-post Metadata Gradient Boosting",
    "Ex-post Quantile Gradient Boosting",
    "Synthetic Control",
    "Feasible Quantile Projection",
    "Tail-Risk Feasible Counterfactual",
    "Single Feasible Projection",
    "Risk-Constrained Convex Verifier",
]

SETTLEMENT_SCHEMA_VERSION = 6


def _exp18_process_opf(payload: dict[str, Any]) -> dict[str, Any]:
    """Solve one Exp18 AC-OPF cell in a fresh worker process.

    PYPOWER's model assembly is largely Python-bound, so a thread pool does
    not provide reliable parallelism.  This top-level worker is deliberately
    independent of the experiment closure: it receives a pristine case and
    the exact option dictionaries, then applies only numerical restarts.  No
    limit, dispatch bound, or objective is changed by a restart.
    """
    from pypower.idx_bus import VA, VM
    from pypower.idx_gen import PG, QG
    from pypower.runopf import runopf
    from pypower.runpf import runpf

    case = copy.deepcopy(payload["case"])
    warm_start = payload.get("warm_start")
    if warm_start is not None:
        if warm_start.get("bus", np.empty((0, 0))).shape == case["bus"].shape:
            case["bus"][:, VM] = warm_start["bus"][:, VM]
            case["bus"][:, VA] = warm_start["bus"][:, VA]
        if warm_start.get("gen", np.empty((0, 0))).shape == case["gen"].shape:
            case["gen"][:, PG] = warm_start["gen"][:, PG]
            case["gen"][:, QG] = warm_start["gen"][:, QG]
    options = payload["options"]
    fallback_options = payload["fallback_options"]
    pf_warm_options = payload["pf_warm_options"]
    fallback_count = 0
    for _ in range(2):
        result = runopf(copy.deepcopy(case), copy.deepcopy(options))
        if bool(result.get("success", 0)):
            return {"result": result, "fallback_count": fallback_count}
    fallback_count += 1
    retry: dict[str, Any] = {}
    for _ in range(2):
        retry = runopf(copy.deepcopy(case), copy.deepcopy(fallback_options))
        if bool(retry.get("success", 0)):
            return {"result": retry, "fallback_count": fallback_count}
    warm = copy.deepcopy(case)
    pf_result, pf_success = runpf(warm, copy.deepcopy(pf_warm_options))
    if pf_success:
        warm["bus"][:, VM] = pf_result["bus"][:, VM]
        warm["bus"][:, VA] = pf_result["bus"][:, VA]
        warm["gen"][:, PG] = pf_result["gen"][:, PG]
        warm["gen"][:, QG] = pf_result["gen"][:, QG]
        warm_retry = runopf(warm, copy.deepcopy(fallback_options))
        if bool(warm_retry.get("success", 0)):
            return {"result": warm_retry, "fallback_count": fallback_count}
    return {"result": retry, "fallback_count": fallback_count}


def _exact_group_symmetric_shapley(
    values: dict[tuple[int, ...], float],
    members_per_group: int,
) -> np.ndarray:
    """Return exact per-member Shapley values for exchangeable site slices."""
    groups = len(next(iter(values)))
    m = int(members_per_group)
    participant_count = groups * m
    factorial = math.factorial
    allocation = np.zeros(groups)
    for group in range(groups):
        ranges = [
            range(m) if index == group else range(m + 1)
            for index in range(groups)
        ]
        for counts in product(*ranges):
            coalition_size = sum(counts)
            multiplicity = math.comb(m - 1, counts[group])
            for other in range(groups):
                if other != group:
                    multiplicity *= math.comb(m, counts[other])
            coefficient = (
                multiplicity
                * factorial(coalition_size)
                * factorial(participant_count - coalition_size - 1)
                / factorial(participant_count)
            )
            augmented = list(counts)
            augmented[group] += 1
            allocation[group] += coefficient * (
                values[tuple(augmented)] - values[tuple(counts)]
            )
    return allocation


def _inputs(root: Path, cfg: dict[str, Any], logger: logging.Logger):
    workload = load_workload(root / cfg["data"]["processed_dir"] / "workload_15min.npz")
    arrivals = workload["arrivals_mwh"]
    slots = int(cfg["project"]["slots_per_day"])
    n_days = arrivals.shape[0] // slots
    arrivals_days = arrivals[: n_days * slots].reshape(n_days, slots, arrivals.shape[1], arrivals.shape[2])
    arrivals_days = arrivals_days.copy()
    backlog = workload["initial_batch_backlog_mwh"][:n_days]
    arrivals_days[:, 0, :, 2] += backlog
    observed = workload["observed_counterfactual_mw"][: n_days * slots]
    observed_days = observed.reshape(n_days, slots, observed.shape[1]).transpose(0, 2, 1)
    valid_days = workload["valid_days"].astype(int)
    network_path = root / cfg["data"]["pglib_case"]
    if network_path.exists():
        system = parse_pglib_case(network_path)
        logger.info("Using declared PGLib network case: %s", network_path)
    else:
        # The compact public checkout intentionally omits the raw source
        # archive.  The vendored PYPOWER IEEE-118 case is numerically the same
        # public benchmark family and keeps locked processed-data audits
        # runnable; a full-data run still uses the declared PGLib file.
        from pypower.case118 import case118

        system = power_system_from_ppc(case118())
        logger.warning(
            "Declared PGLib case is absent; using vendored PYPOWER case118 for "
            "the locked processed-data audit"
        )
    base_profiles, prices, objectives = build_grid_profiles(system, cfg, logger)
    return arrivals_days, observed_days, valid_days, system, base_profiles, prices, objectives


def _solve_day_with_buffer(
    arrivals: np.ndarray,
    prices: np.ndarray,
    cfg: dict[str, Any],
    mode: str = "honest",
    target: np.ndarray | None = None,
    projection_weight: float = 0.0,
    dr_price: float = 0.0,
    event_probability: float = 0.0,
    minimum_participant_event_mwh: float | None = None,
    power_upper_mw: np.ndarray | None = None,
    power_lower_mw: np.ndarray | None = None,
    participating_destinations: list[int] | None = None,
    require_all_arrivals_at_terminal: bool = True,
    terminal_completion_index: int | None = None,
    event_slots_override: list[int] | None = None,
    allowed_destinations: np.ndarray | None = None,
) -> Any:
    """Solve a settlement day with a post-midnight completion buffer.

    No workload is injected in the buffer. Consequently every arrival in the
    evaluated day receives its full declared deadline instead of being forced to
    finish at midnight, while the returned profile remains exactly one day long.
    """
    slots = arrivals.shape[0]
    lookahead = int(cfg["experiments"].get("lookahead_slots", 0))
    if lookahead <= 0:
        return solve_workload_schedule(
            arrivals, prices, cfg, mode=mode, dr_price=dr_price,
            event_probability=event_probability, target_power_mw=target,
            projection_weight=projection_weight,
            minimum_participant_event_mwh=minimum_participant_event_mwh,
            power_upper_mw=power_upper_mw,
            power_lower_mw=power_lower_mw,
            participating_destinations=participating_destinations,
            require_all_arrivals_at_terminal=require_all_arrivals_at_terminal,
            terminal_completion_index=terminal_completion_index,
            event_slots_override=event_slots_override,
            allowed_destinations=allowed_destinations,
        )
    extended_arrivals = np.concatenate(
        [arrivals, np.zeros((lookahead, arrivals.shape[1], arrivals.shape[2]))], axis=0
    )
    price_buffer = np.tile(prices, (1, int(np.ceil(lookahead / prices.shape[1]))))[:, :lookahead]
    extended_prices = np.concatenate([prices, price_buffer], axis=1)
    extended_target = None
    if target is not None:
        fixed = float(cfg["project"]["fixed_facility_load_mw"])
        extended_target = np.concatenate(
            [target, np.full((target.shape[0], lookahead), fixed)], axis=1
        )
    extended_upper = None
    if power_upper_mw is not None:
        upper = np.asarray(power_upper_mw, dtype=float)
        if upper.shape != (prices.shape[0], slots):
            raise ValueError(
                f"power_upper_mw has shape {upper.shape}, expected "
                f"{(prices.shape[0], slots)}"
            )
        unconstrained = float(cfg["project"]["fixed_facility_load_mw"]) + float(
            cfg["project"]["flexible_capacity_mw"]
        )
        extended_upper = np.concatenate(
            [
                upper,
                np.full((upper.shape[0], lookahead), unconstrained),
            ],
            axis=1,
        )
    extended_lower = None
    if power_lower_mw is not None:
        lower = np.asarray(power_lower_mw, dtype=float)
        if lower.shape != (prices.shape[0], slots):
            raise ValueError(
                f"power_lower_mw has shape {lower.shape}, expected "
                f"{(prices.shape[0], slots)}"
            )
        fixed = float(cfg["project"]["fixed_facility_load_mw"])
        extended_lower = np.concatenate(
            [lower, np.full((lower.shape[0], lookahead), fixed)], axis=1
        )
    result = solve_workload_schedule(
        extended_arrivals,
        extended_prices,
        cfg,
        mode=mode,
        dr_price=dr_price,
        event_probability=event_probability,
        target_power_mw=extended_target,
        projection_weight=projection_weight,
        minimum_participant_event_mwh=minimum_participant_event_mwh,
        power_upper_mw=extended_upper,
        power_lower_mw=extended_lower,
        participating_destinations=participating_destinations,
        require_all_arrivals_at_terminal=require_all_arrivals_at_terminal,
        terminal_completion_index=terminal_completion_index,
        event_slots_override=event_slots_override,
        allowed_destinations=allowed_destinations,
    )
    if result.success:
        result.power_mw = result.power_mw[:, :slots]
    return result


def precompute_reference_schedules(
    root: Path,
    cfg: dict[str, Any],
    arrivals_days: np.ndarray,
    valid_days: np.ndarray,
    prices: np.ndarray,
    logger: logging.Logger,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    cache = root / cfg["data"]["processed_dir"] / "reference_schedule_cache.npz"
    if cache.exists():
        with np.load(cache) as data:
            expected = float(arrivals_days.sum())
            cached = float(data["arrival_checksum"]) if "arrival_checksum" in data.files else np.nan
            if np.isclose(cached, expected, rtol=0, atol=1e-6):
                logger.info("Loaded verified reference schedule cache: %s", cache)
                return data["honest"], data["strategic"], data["honest_migration"], data["strategic_migration"]
            logger.info("Discarding stale reference cache (arrival checksum changed)")
    n_days, slots, _, _ = arrivals_days.shape
    dcs = prices.shape[0]
    honest = np.full((n_days, dcs, slots), np.nan)
    strategic = np.full_like(honest, np.nan)
    honest_migration = np.full(n_days, np.nan)
    strategic_migration = np.full(n_days, np.nan)
    dr_price = float(cfg["market"]["default_dr_price_per_mwh"])
    event_prob = float(cfg["market"]["default_event_probability"])
    for day in tqdm(valid_days, desc="Reference schedule LPs"):
        day = int(day)
        truthful = _solve_day_with_buffer(arrivals_days[day], prices, cfg, mode="honest")
        gaming = _solve_day_with_buffer(
            arrivals_days[day],
            prices,
            cfg,
            mode="strategic_reference",
            dr_price=dr_price,
            event_probability=event_prob,
        )
        if not truthful.success or not gaming.success:
            raise RuntimeError(f"Reference scheduling failed for day {day}: {truthful.solver_message} / {gaming.solver_message}")
        honest[day] = truthful.power_mw
        strategic[day] = gaming.power_mw
        honest_migration[day] = truthful.migrated_mwh
        strategic_migration[day] = gaming.migrated_mwh
    np.savez_compressed(
        cache,
        honest=honest,
        strategic=strategic,
        honest_migration=honest_migration,
        strategic_migration=strategic_migration,
        arrival_checksum=np.asarray(float(arrivals_days.sum())),
    )
    logger.info("Reference schedule cache written: %s", cache)
    return honest, strategic, honest_migration, strategic_migration


def run_exp1(root: Path, cfg: dict[str, Any], logger: logging.Logger) -> None:
    folder = root / "experiments/exp1_manipulation"
    final = folder / "results/final"
    intermediate = folder / "results/intermediate"
    arrivals_days, _, valid_days, _, _, prices, _ = _inputs(root, cfg, logger)
    center = len(valid_days) // 2
    reference_days = valid_days[center - 10 : center]
    event_day = int(valid_days[center])
    honest_references = []
    for day in tqdm(reference_days, desc="Exp1 honest reference days"):
        result = _solve_day_with_buffer(arrivals_days[int(day)], prices, cfg, mode="honest")
        if not result.success:
            raise RuntimeError(result.solver_message)
        honest_references.append(result)
    honest_baseline = np.mean([x.power_mw for x in honest_references], axis=0)
    honest_event = _solve_day_with_buffer(arrivals_days[event_day], prices, cfg, mode="honest")
    if not honest_event.success:
        raise RuntimeError(honest_event.solver_message)
    event_slots = list(map(int, cfg["market"]["event_slots"]))
    dt_h = cfg["project"]["interval_minutes"] / 60.0
    honest_reference_service = [
        float(result.served_mwh[:, :, 0, event_slots].sum())
        for result in honest_references
    ]
    reference_shadow_prices = []
    directional_probe_steps_mwh = (5.0e-4, 1.0e-3)
    for day, minimum_service in tqdm(
        zip(reference_days, honest_reference_service),
        total=len(reference_days),
        desc="Exp1 dual threshold certificates",
    ):
        # At a degenerate LP optimum the dual at the current service level can
        # be zero even though the right-hand marginal cost of *increasing*
        # service is positive.  The manipulation proposition is a directional
        # statement, so certify its threshold with two independent right-
        # difference probes and require their slopes to agree.
        slopes = []
        for probe_step in directional_probe_steps_mwh:
            certificate = _solve_day_with_buffer(
                arrivals_days[int(day)],
                prices,
                cfg,
                mode="honest",
                minimum_participant_event_mwh=minimum_service,
            )
            perturbed = _solve_day_with_buffer(
                arrivals_days[int(day)],
                prices,
                cfg,
                mode="honest",
                minimum_participant_event_mwh=minimum_service + probe_step,
            )
            if not certificate.success or not perturbed.success:
                raise RuntimeError(
                    "Directional manipulation-threshold LP failed for day "
                    f"{int(day)}: {certificate.solver_message} / "
                    f"{perturbed.solver_message}"
                )
            slopes.append(
                (perturbed.objective - certificate.objective) / probe_step
            )
        if abs(slopes[0] - slopes[1]) > 1e-4:
            raise RuntimeError(
                "Directional manipulation-threshold probes disagree for day "
                f"{int(day)}: {slopes}"
            )
        reference_shadow_prices.append(float(np.mean(slopes)))
    critical_reference_incentive = float(np.min(reference_shadow_prices))
    threshold_tolerance_usd_per_mwh = 1.0e-6
    rows: list[dict[str, float]] = []
    profiles: dict[str, np.ndarray] = {"honest_mean_baseline": honest_baseline, "honest_event": honest_event.power_mw}
    actual_by_price = {}
    for dr_price in tqdm(cfg["experiments"]["exp1_dr_prices"], desc="Exp1 DR-price response LPs"):
        actual = _solve_day_with_buffer(
            arrivals_days[event_day], prices, cfg, mode="event_response", dr_price=float(dr_price)
        )
        if not actual.success:
            raise RuntimeError(actual.solver_message)
        actual_by_price[float(dr_price)] = actual
        profiles[f"actual_price_{dr_price}"] = actual.power_mw
    grid = [(float(p), float(q)) for q in cfg["experiments"]["exp1_event_probabilities"] for p in cfg["experiments"]["exp1_dr_prices"]]
    for dr_price, probability in tqdm(grid, desc="Exp1 manipulation LPs"):
        reference_results = []
        # Under a ten-day mean rule, each reference day contributes exactly 1/10
        # of the called-event baseline. The coefficient below is the analytical
        # expected-settlement derivative, not a fitted behavioral rule.
        for day in reference_days:
            reference = _solve_day_with_buffer(
                arrivals_days[int(day)], prices, cfg, mode="strategic_reference",
                dr_price=dr_price, event_probability=probability / len(reference_days),
            )
            if not reference.success:
                raise RuntimeError(reference.solver_message)
            reference_results.append(reference)
        strategic_baseline = np.mean([x.power_mw for x in reference_results], axis=0)
        actual = actual_by_price[dr_price]
        ref_response = strategic_baseline[:, event_slots] - actual.power_mw[:, event_slots]
        true_response = honest_event.power_mw[:, event_slots] - actual.power_mw[:, event_slots]
        credit = response_metrics(strategic_baseline, honest_event.power_mw, actual.power_mw, event_slots, dt_h)
        paid = credit["paid_response_mwh"]
        false = credit["false_response_mwh"]
        participant_inflation_mwh = float(
            (
                strategic_baseline[0, event_slots]
                - honest_baseline[0, event_slots]
            ).sum()
            * dt_h
        )
        incentive_per_reference_mwh = (
            dr_price * probability / len(reference_days)
        )
        strategic_operating_costs = []
        for result in reference_results:
            rewarded_service_mwh = float(
                result.served_mwh[:, :, 0, event_slots].sum()
            )
            strategic_operating_costs.append(
                result.objective
                + incentive_per_reference_mwh * rewarded_service_mwh
            )
        # The reward uses the ten-day average baseline, but all ten reference-day
        # operating-cost increments are physically incurred. Their sum, not their
        # mean, is therefore the matching economic quantity.
        incremental_reference_cost = float(
            np.sum(strategic_operating_costs)
            - np.sum([result.objective for result in honest_references])
        )
        expected_payment_gain = float(
            probability * dr_price * participant_inflation_mwh
        )
        expected_profit_gain = expected_payment_gain - incremental_reference_cost
        optimizer_manipulation = participant_inflation_mwh > 1e-7
        # This boundary is independent of the strategic solve above. It follows
        # from LP right-hand-side sensitivity: a reference-day schedule can move
        # away from the honest optimum exactly when the per-reference-MWh reward
        # crosses the minimum marginal physical cost across the ten reference days.
        theoretical_margin = (
            incentive_per_reference_mwh - critical_reference_incentive
        )
        # A positive margin is sufficient only when the LP admits a positive
        # reference-day direction.  The independent optimizer flag below
        # records whether such a direction is actually selected.
        theory_profitable = (
            theoretical_margin > threshold_tolerance_usd_per_mwh
            and optimizer_manipulation
        )
        optimizer_strictly_profitable = expected_profit_gain > 1e-6
        boundary_indifference = (
            abs(theoretical_margin) <= threshold_tolerance_usd_per_mwh
        )
        row = {
            "event_day": event_day,
            "dr_price": dr_price,
            "event_probability": probability,
            "baseline_inflation_mwh": float((strategic_baseline[:, event_slots] - honest_baseline[:, event_slots]).sum() * dt_h),
            "actual_reduction_mwh": float(np.clip(true_response, 0, None).sum() * dt_h),
            "paid_response_mwh": float(paid),
            "false_response_mwh": float(false),
            "false_response_ratio": float(false / max(paid, 1e-9)),
            "spatial_migration_mwh": float(actual.migrated_mwh),
            "reference_migration_mwh": float(np.mean([x.migrated_mwh for x in reference_results])),
            "participant_baseline_inflation_mwh": participant_inflation_mwh,
            "incremental_reference_cost_usd": incremental_reference_cost,
            "expected_payment_gain_usd": expected_payment_gain,
            "expected_profit_gain_usd": expected_profit_gain,
            "incentive_per_reference_mwh": incentive_per_reference_mwh,
            "critical_reference_incentive_usd_per_mwh": critical_reference_incentive,
            "theoretical_margin_usd_per_mwh": theoretical_margin,
            "theory_profitable": int(theory_profitable),
            "optimizer_manipulation": int(optimizer_manipulation),
            "optimizer_strictly_profitable": int(
                optimizer_strictly_profitable
            ),
            "boundary_indifference": int(boundary_indifference),
            "theory_optimizer_agreement": int(
                theory_profitable == optimizer_strictly_profitable
            ),
        }
        rows.append(row)
        pd.DataFrame(rows).to_csv(intermediate / "manipulation_grid_checkpoint.csv", index=False)
    results = pd.DataFrame(rows)
    results.to_csv(final / "manipulation_grid.csv", index=False)
    np.savez_compressed(intermediate / "representative_profiles.npz", **profiles)
    plot_exp1(results, folder / "figures", cfg)
    write_json(
        final / "experiment_metadata.json",
        {
            "reference_days": reference_days.tolist(),
            "event_day": event_day,
            "baseline_rule": "ten-day arithmetic mean",
            "strategic_coefficient": "exact derivative of expected settlement: event_probability * DR_price / 10",
            "optimization": "multi-day expected-profit workload-conservation LPs solved to global optimality by HiGHS",
            "number_of_parameter_combinations": len(results),
            "theory_optimizer_boundary_agreement": float(
                results["theory_optimizer_agreement"].mean()
            ),
            "reference_service_shadow_prices_usd_per_mwh": reference_shadow_prices,
            "critical_reference_incentive_usd_per_mwh": critical_reference_incentive,
            "threshold_certificate": (
                "minimum independent right-direction finite-difference cost "
                "over two 0.0005/0.001-MWh probes on each of the ten honest "
                "reference-day event-service constraints"
            ),
            "directional_probe_steps_mwh": list(directional_probe_steps_mwh),
            "threshold_tolerance_usd_per_mwh": threshold_tolerance_usd_per_mwh,
            "event_slots": event_slots,
        },
    )
    logger.info("Experiment 1 complete: %d exact LP parameter combinations", len(results))


def _event_days(valid_days: np.ndarray, cfg: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    slots = int(cfg["project"]["slots_per_day"])
    future_days = int(
        np.ceil(int(cfg["experiments"].get("lookahead_slots", 0)) / slots)
    )
    history_days = int(cfg["experiments"]["strategic_history_days"])
    eligible = valid_days[
        (valid_days >= history_days)
        & (valid_days <= int(valid_days.max()) - future_days)
    ]
    need = int(cfg["experiments"]["validation_days"]) + int(cfg["experiments"]["test_days"])
    if len(eligible) < need:
        raise ValueError(f"Only {len(eligible)} eligible days; {need} required")
    selected = eligible[-need:]
    return selected[: int(cfg["experiments"]["validation_days"])], selected[int(cfg["experiments"]["validation_days"]) :]


def _actual_event_profiles(
    arrivals_days: np.ndarray,
    days: np.ndarray,
    prices: np.ndarray,
    cfg: dict[str, Any],
    logger: logging.Logger,
) -> tuple[np.ndarray, np.ndarray]:
    """Solve a declared *simulated* event response for mechanism isolation.

    This helper is intentionally not used to define the locked scoring truth.
    The main verification panel scores against the independently observed
    ``observed_counterfactual_mw`` trajectory.  Keeping this simulator
    available is useful for price/participation sensitivity, but its outputs
    must never be described as a closed utility meter or as causal field data.
    """
    profiles = []
    migrations = []
    for day in tqdm(days, desc="Event-response LPs"):
        result = _solve_day_with_buffer(
            arrivals_days[int(day)],
            prices,
            cfg,
            mode="event_response",
            dr_price=float(cfg["market"]["default_dr_price_per_mwh"]),
        )
        if not result.success:
            raise RuntimeError(f"Event scheduling failed for day {day}: {result.solver_message}")
        profiles.append(result.power_mw)
        migrations.append(result.migrated_mwh)
    return np.asarray(profiles), np.asarray(migrations)


def _prediction_bundle(
    day: int,
    strategic: np.ndarray,
    valid_days: np.ndarray,
    arrivals_days: np.ndarray,
    prices: np.ndarray,
    cfg: dict[str, Any],
    projection_weight: float,
    statistical: BaselinePredictions | None = None,
) -> tuple[dict[str, np.ndarray], float]:
    stats = statistical or predict_statistical_baselines(
        strategic, valid_days, day, list(map(int, cfg["market"]["event_slots"])), int(cfg["project"]["seed"])
    )
    physics = _solve_day_with_buffer(
        arrivals_days[day],
        prices,
        cfg,
        mode="honest",
        target=stats.ex_post_metadata_gradient_boosting,
        projection_weight=projection_weight,
    )
    if not physics.success:
        raise RuntimeError(f"Workload-conserving projection failed for day {day}: {physics.solver_message}")
    return {
        "High-5-of-10": stats.high5of10,
        "Ridge": stats.ridge,
        "Gradient Boosting": stats.gradient_boosting,
        "Extra Trees": stats.extra_trees,
        "Metadata Gradient Boosting": stats.metadata_gradient_boosting,
        "Ex-post Metadata Gradient Boosting": stats.ex_post_metadata_gradient_boosting,
        "Ex-post Quantile Gradient Boosting": stats.ex_post_quantile_gradient_boosting,
        "Synthetic Control": stats.synthetic_control,
        "Risk-Constrained Convex Verifier": physics.power_mw,
    }, physics.migrated_mwh


def _solve_convex_projection(
    arrivals: np.ndarray,
    prices: np.ndarray,
    cfg: dict[str, Any],
    target: np.ndarray,
    projection_weights: np.ndarray,
    ensemble_weights: np.ndarray,
    extra_target: np.ndarray | None = None,
    extra_projection_weight: float | None = None,
) -> tuple[np.ndarray, float, np.ndarray]:
    """Return a convex combination of exact workload-feasible projections.

    Every candidate has the same arrivals and linear feasible set. Therefore its
    convex combination remains feasible for release, conservation, deadline, and
    site-capacity constraints; this is an optimization ensemble, not a post-hoc
    feasibility repair.
    """
    profiles, migrations, services = _solve_projection_candidates(
        arrivals,
        prices,
        cfg,
        target,
        projection_weights,
    )
    coefficients = np.asarray(ensemble_weights, dtype=float)
    if len(coefficients) == len(projection_weights) + 1:
        if extra_target is None or extra_projection_weight is None:
            raise ValueError(
                "The final ensemble coefficient requires the feasible "
                "quantile projection target and its validation-selected weight"
            )
        extra = _solve_day_with_buffer(
            arrivals,
            prices,
            cfg,
            mode="honest",
            target=extra_target,
            projection_weight=float(extra_projection_weight),
        )
        if not extra.success:
            raise RuntimeError(
                f"Additional feasible projection failed: {extra.solver_message}"
            )
        profiles = np.concatenate([profiles, extra.power_mw[None, ...]])
        migrations = np.concatenate(
            [migrations, np.asarray([extra.migrated_mwh])]
        )
        services = np.concatenate(
            [services, extra.served_mwh[None, ...]]
        )
    elif len(coefficients) != len(projection_weights):
        raise ValueError(
            f"{len(coefficients)} ensemble coefficients do not match "
            f"{len(projection_weights)} base projections"
        )
    if np.any(coefficients < -1e-10) or not np.isclose(coefficients.sum(), 1.0, atol=1e-8):
        raise RuntimeError(f"Invalid convex projection coefficients: {coefficients}")
    return (
        np.tensordot(coefficients, profiles, axes=(0, 0)),
        float(np.dot(coefficients, migrations)),
        np.tensordot(coefficients, services, axes=(0, 0)),
    )


def _solve_projection_candidates(
    arrivals: np.ndarray,
    prices: np.ndarray,
    cfg: dict[str, Any],
    target: np.ndarray,
    projection_weights: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Solve and retain every first-stage workload-feasible projection.

    These six complete schedules are the candidate set denoted by
    :math:`\\{p^{(1)},\\ldots,p^{(L)}\\}` in the manuscript. Retaining them
    prevents later payment certification from silently substituting a
    different convex hull.
    """
    profiles: list[np.ndarray] = []
    migrations: list[float] = []
    services: list[np.ndarray] = []
    for projection_weight in projection_weights:
        result = _solve_day_with_buffer(
            arrivals,
            prices,
            cfg,
            mode="honest",
            target=target,
            projection_weight=float(projection_weight),
        )
        if not result.success:
            raise RuntimeError(
                f"Convex projection candidate {projection_weight:g} failed: {result.solver_message}"
            )
        profiles.append(result.power_mw)
        migrations.append(result.migrated_mwh)
        services.append(result.served_mwh)
    return (
        np.asarray(profiles),
        np.asarray(migrations, dtype=float),
        np.asarray(services),
    )


def _event_risk_upper_envelope(
    cap_profile: np.ndarray,
    cfg: dict[str, Any],
) -> np.ndarray:
    """Return a pointwise event cap from an independently selected feasible profile."""
    upper = np.full_like(
        cap_profile,
        float(cfg["project"]["fixed_facility_load_mw"])
        + float(cfg["project"]["flexible_capacity_mw"]),
        dtype=float,
    )
    event_slots = list(map(int, cfg["market"]["event_slots"]))
    upper[:, event_slots] = cap_profile[:, event_slots]
    return upper


def _event_risk_lower_envelope(
    floor_profile: np.ndarray,
    cfg: dict[str, Any],
) -> np.ndarray:
    """Return the predeclared lower side of the event credit band."""
    fixed = float(cfg["project"]["fixed_facility_load_mw"])
    tolerance = float(
        cfg["experiments"].get("two_sided_band_tolerance_mw", 0.0)
    )
    if tolerance < 0:
        raise ValueError("two_sided_band_tolerance_mw must be nonnegative")
    lower = np.full_like(floor_profile, fixed, dtype=float)
    event_slots = list(map(int, cfg["market"]["event_slots"]))
    lower[:, event_slots] = np.maximum(
        fixed,
        np.asarray(floor_profile, dtype=float)[:, event_slots] - tolerance,
    )
    return lower


def _extended_arrivals_for_certificate(arrivals: np.ndarray, cfg: dict[str, Any]) -> np.ndarray:
    lookahead = int(cfg["experiments"].get("lookahead_slots", 0))
    if lookahead <= 0:
        return arrivals
    return np.concatenate(
        [arrivals, np.zeros((lookahead, arrivals.shape[1], arrivals.shape[2]))],
        axis=0,
    )


def _schedule_certificate(
    served_mwh: np.ndarray,
    arrivals: np.ndarray,
    cfg: dict[str, Any],
) -> dict[str, float]:
    """Evaluate any schedule against the full declared workload contract."""
    extended = _extended_arrivals_for_certificate(arrivals, cfg)
    if served_mwh.shape[-1] != extended.shape[0]:
        raise ValueError(
            f"Certificate horizon mismatch: service={served_mwh.shape[-1]}, arrivals={extended.shape[0]}"
        )
    service = served_mwh.sum(axis=2)
    cumulative_service = np.cumsum(service, axis=2)
    cumulative_arrivals = np.cumsum(extended, axis=0)
    release_violation = 0.0
    deadline_violation = 0.0
    for source in range(extended.shape[1]):
        for klass, deadline in enumerate(cfg["workload"]["deadlines_slots"]):
            release_violation = max(
                release_violation,
                float(
                    np.max(
                        cumulative_service[source, klass]
                        - cumulative_arrivals[:, source, klass]
                    )
                ),
            )
            for t in range(int(deadline), extended.shape[0]):
                deadline_violation = max(
                    deadline_violation,
                    float(
                        cumulative_arrivals[t - int(deadline), source, klass]
                        - cumulative_service[source, klass, t]
                    ),
                )
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    capacity_violation = max(
        0.0,
        float(
            served_mwh.sum(axis=(0, 1)).max() / dt_h
            - cfg["project"]["flexible_capacity_mw"]
        ),
    )
    conservation_violation = float(
        np.max(
            np.abs(
                served_mwh.sum(axis=(2, 3))
                - extended.sum(axis=0)
            )
        )
    )
    tolerance = 1e-7
    return {
        "release_violation_mwh": max(0.0, release_violation),
        "deadline_violation_mwh": max(0.0, deadline_violation),
        "capacity_violation_mw": capacity_violation,
        "conservation_violation_mwh": conservation_violation,
        "certified_feasible": float(
            max(
                release_violation,
                deadline_violation,
                capacity_violation,
                conservation_violation,
            )
            <= tolerance
        ),
    }


def run_exp2(root: Path, cfg: dict[str, Any], logger: logging.Logger) -> None:
    folder = root / "experiments/exp2_baseline_verification"
    final = folder / "results/final"
    intermediate = folder / "results/intermediate"
    final.mkdir(parents=True, exist_ok=True)
    intermediate.mkdir(parents=True, exist_ok=True)
    arrivals_days, observed, valid_days, _, _, prices, _ = _inputs(root, cfg, logger)
    model_honest, model_strategic, honest_migration, strategic_migration = precompute_reference_schedules(
        root, cfg, arrivals_days, valid_days, prices, logger
    )
    # The measured DCGM/BurstGPT execution is the independent observational
    # target for baseline alignment. Strategic reference histories add only the
    # equilibrium deviation induced by the DR rule; the verifier never observes
    # the locked reference used for scoring.  There is no labelled utility
    # event in these public traces.  Consequently the exact event-response LP
    # is retained only for mechanism-isolation panels and is never presented as
    # an observed event outcome.
    honest = observed
    strategic = observed + (model_strategic - model_honest)
    validation_days, test_days = _event_days(valid_days, cfg)
    all_event_days = np.concatenate([validation_days, test_days])
    observed_meter_all = observed[all_event_days].copy()
    actual_all, actual_migration = _actual_event_profiles(
        arrivals_days, all_event_days, prices, cfg, logger
    )
    actual_truth_source = "simulated_event_response_mechanism_isolation"
    observed_truth_source = "independent_trace_observed_meter"
    actual_lookup = {int(day): actual_all[i] for i, day in enumerate(all_event_days)}
    observed_meter_lookup = {
        int(day): observed_meter_all[i] for i, day in enumerate(all_event_days)
    }
    migration_lookup = {int(day): actual_migration[i] for i, day in enumerate(all_event_days)}
    event_slots = list(map(int, cfg["market"]["event_slots"]))
    dt_h = cfg["project"]["interval_minutes"] / 60.0

    statistical_by_day: dict[int, BaselinePredictions] = {}
    stats_cache = root / cfg["data"]["processed_dir"] / "statistical_baseline_cache.npz"
    cache_key = float(
        np.nansum(strategic) + arrivals_days.sum() + 4.0
    )  # schema v4: quantile and synthetic-control comparators
    loaded_cache = False
    upgraded_previous_cache = False
    if stats_cache.exists():
        with np.load(stats_cache, allow_pickle=False) as cached:
            same_days = np.array_equal(cached["days"], all_event_days)
            current_schema = np.isclose(
                float(cached["cache_key"]), cache_key, rtol=0, atol=1e-6
            )
            previous_schema = np.isclose(
                float(cached["cache_key"]),
                float(np.nansum(strategic) + arrivals_days.sum() + 3.0),
                rtol=0,
                atol=1e-6,
            )
            if same_days and current_schema:
                for i, day in enumerate(all_event_days):
                    statistical_by_day[int(day)] = BaselinePredictions(
                        cached["high5of10"][i], cached["ridge"][i], cached["gradient_boosting"][i],
                        cached["extra_trees"][i], cached["metadata_gradient_boosting"][i],
                        cached["ex_post_metadata_gradient_boosting"][i],
                        cached["ex_post_quantile_gradient_boosting"][i],
                        cached["synthetic_control"][i],
                    )
                loaded_cache = True
                logger.info("Loaded verified statistical-baseline cache: %s", stats_cache)
            elif same_days and previous_schema:
                logger.info(
                    "Extending the verified v3 statistical cache with the two "
                    "new strong comparators"
                )
                for i, day_value in enumerate(
                    tqdm(all_event_days, desc="Additional strong baseline fits")
                ):
                    day = int(day_value)
                    quantile, synthetic = predict_additional_strong_baselines(
                        strategic,
                        valid_days,
                        day,
                        event_slots,
                        int(cfg["project"]["seed"]),
                        arrivals_days,
                    )
                    statistical_by_day[day] = BaselinePredictions(
                        cached["high5of10"][i],
                        cached["ridge"][i],
                        cached["gradient_boosting"][i],
                        cached["extra_trees"][i],
                        cached["metadata_gradient_boosting"][i],
                        cached["ex_post_metadata_gradient_boosting"][i],
                        quantile,
                        synthetic,
                    )
                loaded_cache = True
                upgraded_previous_cache = True
    if upgraded_previous_cache:
        ordered = [statistical_by_day[int(day)] for day in all_event_days]
        np.savez_compressed(
            stats_cache,
            days=all_event_days,
            cache_key=np.asarray(cache_key),
            high5of10=np.asarray([x.high5of10 for x in ordered]),
            ridge=np.asarray([x.ridge for x in ordered]),
            gradient_boosting=np.asarray([x.gradient_boosting for x in ordered]),
            extra_trees=np.asarray([x.extra_trees for x in ordered]),
            metadata_gradient_boosting=np.asarray(
                [x.metadata_gradient_boosting for x in ordered]
            ),
            ex_post_metadata_gradient_boosting=np.asarray(
                [x.ex_post_metadata_gradient_boosting for x in ordered]
            ),
            ex_post_quantile_gradient_boosting=np.asarray(
                [x.ex_post_quantile_gradient_boosting for x in ordered]
            ),
            synthetic_control=np.asarray([x.synthetic_control for x in ordered]),
        )
        logger.info("Upgraded statistical-baseline cache to schema v4")
    if not loaded_cache:
        for day in tqdm(all_event_days, desc="Statistical baseline fits"):
            day = int(day)
            statistical_by_day[day] = predict_statistical_baselines(
                strategic, valid_days, day, event_slots, int(cfg["project"]["seed"]), arrivals_days
            )
        ordered = [statistical_by_day[int(day)] for day in all_event_days]
        np.savez_compressed(
            stats_cache,
            days=all_event_days,
            cache_key=np.asarray(cache_key),
            high5of10=np.asarray([x.high5of10 for x in ordered]),
            ridge=np.asarray([x.ridge for x in ordered]),
            gradient_boosting=np.asarray([x.gradient_boosting for x in ordered]),
            extra_trees=np.asarray([x.extra_trees for x in ordered]),
            metadata_gradient_boosting=np.asarray([x.metadata_gradient_boosting for x in ordered]),
            ex_post_metadata_gradient_boosting=np.asarray(
                [x.ex_post_metadata_gradient_boosting for x in ordered]
            ),
            ex_post_quantile_gradient_boosting=np.asarray(
                [x.ex_post_quantile_gradient_boosting for x in ordered]
            ),
            synthetic_control=np.asarray([x.synthetic_control for x in ordered]),
        )

    projection_weights = np.asarray(cfg["experiments"]["projection_weights"], dtype=float)
    tuning_rows = []
    validation_candidate_profiles = []
    for candidate_index, weight in enumerate(projection_weights, start=1):
        day_scores = []
        deviations = []
        precisions = []
        recalls = []
        f1_scores = []
        candidate_profiles = []
        for day in validation_days:
            bundle, _ = _prediction_bundle(
                int(day), strategic, valid_days, arrivals_days, prices, cfg, float(weight), statistical_by_day[int(day)]
            )
            candidate_profiles.append(bundle["Risk-Constrained Convex Verifier"])
            base = baseline_metrics(bundle["Risk-Constrained Convex Verifier"], honest[int(day)], event_slots)
            response = response_metrics(bundle["Risk-Constrained Convex Verifier"], honest[int(day)], actual_lookup[int(day)], event_slots, dt_h)
            # This column is descriptive validation nRMSE only. False-credit
            # exposure is handled by explicit total and CVaR constraints below,
            # rather than folded into an arbitrarily weighted scalar score.
            day_scores.append(base["nrmse"])
            deviations.append(
                float(
                    np.mean(
                        np.abs(
                            bundle["Risk-Constrained Convex Verifier"][:, event_slots]
                            - honest[int(day)][:, event_slots]
                        )
                    )
                )
            )
            precisions.append(response["credit_precision"])
            recalls.append(response["credit_recall"])
            f1_scores.append(response["credit_f1"])
        tuning_rows.append(
            {
                "candidate_index": candidate_index,
                "projection_weight": float(weight),
                "validation_score": float(np.mean(day_scores)),
                "validation_score_std": float(np.std(day_scores, ddof=1)),
                "event_window_deviation_from_optimization_only_mw": float(np.mean(deviations)),
                "validation_credit_precision": float(np.mean(precisions)),
                "validation_credit_recall": float(np.mean(recalls)),
                "validation_credit_f1": float(np.mean(f1_scores)),
            }
        )
        validation_candidate_profiles.append(candidate_profiles)
        pd.DataFrame(tuning_rows).to_csv(
            intermediate / "projection_candidate_validation_checkpoint.csv",
            index=False,
        )
        logger.info(
            "Validation candidate %d/%d: weight=%s, diagnostic score=%.5f",
            candidate_index,
            len(projection_weights),
            weight,
            np.mean(day_scores),
        )
    tuning = pd.DataFrame(tuning_rows)
    candidate_array = np.asarray(validation_candidate_profiles)
    design = candidate_array[:, :, :, event_slots].transpose(1, 2, 3, 0).reshape(-1, len(projection_weights))
    target = honest[validation_days][:, :, event_slots].reshape(-1)
    regularization = 1e-8
    validation_count = len(validation_days)
    fold_size = max(1, validation_count // 4)
    fold_partitions = [
        np.arange(start, min(start + fold_size, validation_count))
        for start in range(0, validation_count, fold_size)
    ]

    # Closest optimization-informed comparator: project the complete-ledger
    # quantile learner onto exactly the same workload polytope. Its penalty is
    # selected by the same contiguous validation blocks and no test labels.
    quantile_projection_rows: list[dict[str, float]] = []
    for projection_weight in projection_weights:
        day_records: list[dict[str, float]] = []
        for local_day, day_value in enumerate(validation_days):
            day = int(day_value)
            result = _solve_day_with_buffer(
                arrivals_days[day],
                prices,
                cfg,
                mode="honest",
                target=statistical_by_day[
                    day
                ].ex_post_quantile_gradient_boosting,
                projection_weight=float(projection_weight),
            )
            if not result.success:
                raise RuntimeError(
                    "Feasible quantile projection failed on validation day "
                    f"{day}: {result.solver_message}"
                )
            base = baseline_metrics(result.power_mw, honest[day], event_slots)
            response = response_metrics(
                result.power_mw,
                honest[day],
                actual_all[local_day],
                event_slots,
                dt_h,
            )
            day_records.append({**base, **response})
        fold_nrmse = [
            float(np.mean([day_records[i]["nrmse"] for i in held]))
            for held in fold_partitions
        ]
        quantile_projection_rows.append(
            {
                "projection_weight": float(projection_weight),
                "mean_validation_nrmse": float(
                    np.mean([row["nrmse"] for row in day_records])
                ),
                "max_fold_nrmse": float(np.max(fold_nrmse)),
                "mean_false_response_mwh": float(
                    np.mean(
                        [row["false_response_mwh"] for row in day_records]
                    )
                ),
                "mean_credit_f1": float(
                    np.mean([row["credit_f1"] for row in day_records])
                ),
            }
        )
    quantile_projection_validation = pd.DataFrame(
        quantile_projection_rows
    ).sort_values(
        ["max_fold_nrmse", "mean_false_response_mwh"],
        ascending=[True, True],
    )
    selected_quantile_projection_weight = float(
        quantile_projection_validation.iloc[0]["projection_weight"]
    )
    quantile_projection_validation["selected"] = (
        quantile_projection_validation["projection_weight"]
        == selected_quantile_projection_weight
    )
    quantile_projection_validation.to_csv(
        final / "quantile_feasible_validation.csv", index=False
    )
    validation_quantile_profiles: list[np.ndarray] = []
    for day_value in validation_days:
        day = int(day_value)
        result = _solve_day_with_buffer(
            arrivals_days[day],
            prices,
            cfg,
            mode="honest",
            target=statistical_by_day[
                day
            ].ex_post_quantile_gradient_boosting,
            projection_weight=selected_quantile_projection_weight,
        )
        if not result.success:
            raise RuntimeError(
                f"Validation quantile projection failed for day {day}: "
                f"{result.solver_message}"
            )
        validation_quantile_profiles.append(result.power_mw)
    risk_candidate_array = np.concatenate(
        [
            candidate_array,
            np.asarray(validation_quantile_profiles)[None, ...],
        ],
        axis=0,
    )
    risk_candidate_names = [
        f"Metadata projection rho={weight:g}"
        for weight in projection_weights
    ] + ["Feasible quantile projection"]
    # Anchor the risk budgets to the independently selected single feasible
    # projection.  The complete-ledger feasible-quantile profile remains an
    # external comparator and is not used to define the pointwise cap.
    risk_reference_index = 0
    risk_design = (
        risk_candidate_array[:, :, :, event_slots]
        .transpose(1, 2, 3, 0)
        .reshape(-1, len(risk_candidate_names))
    )

    def fit_risk_constrained_simplex(
        local_design: np.ndarray,
        local_target: np.ndarray,
        local_actual: np.ndarray,
        reference_candidate: int,
        day_count: int,
        reserve_fraction: float,
        enforce_total_budget: bool = True,
        enforce_cvar_budget: bool = True,
        cvar_reserve_fraction_override: float | None = None,
    ) -> tuple[np.ndarray, dict[str, float]]:
        """Fit the minimum-MSE ensemble under separate daily risk budgets.

        The reference budgets are computed from the independently selected
        single feasible projection.  A reserve fraction is applied to every
        validation day separately, rather than only to an aggregate total.
        Positive-part exposure is represented by an exact linear epigraph, so
        the feasible set is convex and contains no rule-based post-processing.
        """
        local_scale = max(float(np.mean(local_target**2)), 1e-12)
        count, candidates = local_design.shape
        if count % day_count:
            raise ValueError("Risk design cannot be partitioned into complete days")
        observations_per_day = count // day_count
        # False credit is defined on credit, not on gross load.  The oracle
        # response credit is the positive part of the no-event trajectory
        # minus the closed event meter.  The prediction-side epigraph then
        # subtracts this true credit from the submitted credit.  For a
        # nonnegative true credit this is algebraically equivalent to the
        # compact threshold max(local_target, local_actual), but retaining the
        # two terms makes the payment semantics auditable and prevents a gross
        # load reduction from being reported as false credit.
        true_credit = np.maximum(local_target - local_actual, 0.0)
        credit_threshold = local_actual + true_credit
        reference_prediction = local_design[:, reference_candidate]
        reference_false_by_day = np.maximum(
            np.maximum(reference_prediction - local_actual, 0.0) - true_credit,
            0.0,
        ).reshape(day_count, observations_per_day).sum(axis=1)
        reference_false_exposure = float(reference_false_by_day.sum())
        risk_budget = float(
            reserve_fraction * reference_false_exposure
        )
        reference_daily_max = float(reference_false_by_day.max(initial=0.0))
        cvar_level = float(cfg["experiments"].get("risk_cvar_level", 0.75))
        if not 0.0 < cvar_level < 1.0:
            raise ValueError("risk_cvar_level must lie strictly between 0 and 1")
        tail_count = max(1, int(np.ceil((1.0 - cvar_level) * day_count)))
        reference_daily_cvar_absolute = float(
            np.mean(np.sort(reference_false_by_day)[-tail_count:])
        )
        cvar_metric = str(
            cfg["experiments"].get("risk_cvar_metric", "daily_false_credit_mwh_slots")
        )
        if cvar_metric == "daily_false_credit_ratio":
            # Normalising each day's false credit by its true credited energy
            # prevents the CVaR row from collapsing into the aggregate MWh
            # budget.  The denominator is fixed from the validation mechanism
            # and is never estimated from a locked outcome.
            cvar_day_denominator = np.maximum(
                true_credit.reshape(day_count, observations_per_day).sum(axis=1),
                float(cfg["experiments"].get("risk_cvar_denominator_floor_mw_slots", 1.0e-9)),
            )
            cvar_sample_weights = np.repeat(
                1.0 / cvar_day_denominator, observations_per_day
            )
            reference_daily_cvar_values = (
                reference_false_by_day / cvar_day_denominator
            )
            cvar_denominator_definition = (
                "daily true credited energy sum from the validation mechanism"
            )
        elif cvar_metric == "daily_false_credit_mw_slots":
            cvar_day_denominator = np.ones(day_count, dtype=float)
            cvar_sample_weights = np.ones(count, dtype=float)
            reference_daily_cvar_values = reference_false_by_day.copy()
            cvar_denominator_definition = "unit denominator (absolute MW-slot exposure)"
        else:
            raise ValueError(
                "risk_cvar_metric must be daily_false_credit_ratio or "
                "daily_false_credit_mw_slots"
            )
        reference_daily_cvar = float(
            np.mean(np.sort(reference_daily_cvar_values)[-tail_count:])
        )
        cvar_reserve_fraction = float(
            cfg["experiments"].get("risk_cvar_reserve_fraction", reserve_fraction)
            if cvar_reserve_fraction_override is None
            else cvar_reserve_fraction_override
        )
        if not 0.0 < cvar_reserve_fraction <= 1.0:
            raise ValueError("risk_cvar_reserve_fraction must lie in (0, 1]")
        # The total and daily-tail reserves are independent contractual
        # quantities.  Keeping the CVaR reserve below one makes the tail row
        # active even when the total false-credit budget is nonbinding.
        cvar_budget = float(cvar_reserve_fraction * reference_daily_cvar)
        # A predeclared, dimensionless tail regularizer makes the CVaR module
        # identifiable even when the selected budget is naturally slack.  It
        # is normalized by the reference CVaR, is applied only when the CVaR
        # epigraph is enabled, and is reported in the certificate; the
        # total-budget-only ablation therefore removes both the tail row and
        # this tail objective term.  This is a convex additive preference,
        # not a post-solution heuristic.
        cvar_objective_weight = float(
            cfg["experiments"].get("risk_cvar_objective_weight", 0.0)
        )
        if cvar_objective_weight < 0.0:
            raise ValueError("risk_cvar_objective_weight must be nonnegative")
        total_objective_weight = float(
            cfg["experiments"].get("risk_total_objective_weight", 0.0)
        )
        if total_objective_weight < 0.0:
            raise ValueError("risk_total_objective_weight must be nonnegative")
        cvar_objective_scale = max(reference_daily_cvar, 1.0e-9)
        total_objective_scale = max(reference_false_exposure, 1.0e-9)

        # Solve the convex quadratic program with the explicit linear
        # epigraph.  Here s_n is the sample false-credit epigraph, nu is the
        # CVaR threshold, and xi_d are the daily tail slacks.  HiGHS supplies
        # only a feasible warm start.  The objective is then solved over the
        # *full* epigraph with a sparse primal--dual trust-region method; the
        # returned KKT and primal residuals are independently recomputed below.
        sample_count = count
        nvar = candidates + sample_count + day_count + 1
        alpha_slice = slice(0, candidates)
        xi_slice = slice(candidates + sample_count, candidates + sample_count + day_count)
        nu_index = nvar - 1
        rows: list[int] = []
        cols: list[int] = []
        values: list[float] = []
        upper: list[float] = []
        row_id = 0
        for sample in range(sample_count):
            for candidate in range(candidates):
                value = float(local_design[sample, candidate])
                if value:
                    rows.append(row_id)
                    cols.append(candidate)
                    values.append(value)
            rows.append(row_id)
            cols.append(candidates + sample)
            values.append(-1.0)
            # f_n >= [ [p_n - meter_n]_+ - true_credit_n ]_+.
            # Since true_credit_n >= 0, the single linear row below is an
            # exact epigraph: f_n >= p_n - meter_n - true_credit_n.
            upper.append(float(credit_threshold[sample]))
            row_id += 1
        if enforce_cvar_budget:
            for local_day in range(day_count):
                # The daily tail variable is attached to the *sum* of the
                # sample epigraphs for that day.  A row per sample would bound
                # individual slots and would not implement daily CVaR.
                for sample in range(
                    local_day * observations_per_day,
                    (local_day + 1) * observations_per_day,
                ):
                    rows.append(row_id)
                    cols.append(candidates + sample)
                    values.append(float(cvar_sample_weights[sample]))
                rows.extend([row_id, row_id])
                cols.extend(
                    [nu_index, candidates + sample_count + local_day]
                )
                values.extend([-1.0, -1.0])
                upper.append(0.0)
                row_id += 1
            rows.append(row_id)
            cols.append(nu_index)
            values.append(1.0)
            for local_day in range(day_count):
                rows.append(row_id)
                cols.append(candidates + sample_count + local_day)
                values.append(1.0 / tail_count)
            upper.append(cvar_budget)
            row_id += 1
        if enforce_total_budget:
            for sample in range(sample_count):
                rows.append(row_id)
                cols.append(candidates + sample)
                values.append(1.0)
            upper.append(risk_budget)
            row_id += 1
        a_ub = coo_matrix(
            (np.asarray(values), (np.asarray(rows), np.asarray(cols))),
            shape=(row_id, nvar),
        ).tocsr()
        a_eq = csr_matrix(
            (np.ones(candidates), (np.zeros(candidates), np.arange(candidates))),
            shape=(1, nvar),
        )
        lower_bounds = np.zeros(nvar)
        upper_bounds = np.full(nvar, np.inf)
        upper_bounds[:candidates] = 1.0
        feasibility = linprog(
            np.zeros(nvar),
            A_ub=a_ub,
            b_ub=np.asarray(upper),
            A_eq=a_eq,
            b_eq=np.ones(1),
            bounds=list(zip(lower_bounds, upper_bounds)),
            method="highs",
        )
        if not feasibility.success:
            # The selected single projection is explicitly part of the
            # candidate simplex, so a reserve of one must be feasible by
            # construction.  Persist the independent budget diagnostics in
            # the log before failing; this distinguishes a genuine contract
            # conflict from an incorrectly assembled epigraph.
            logger.error(
                "Risk epigraph infeasible diagnostics: reserve=%s, cvar_reserve=%s, "
                "reference_total=%s, total_budget=%s, reference_cvar=%s, "
                "cvar_budget=%s, day_count=%s, observations_per_day=%s, "
                "reference_index=%s, cvar_metric=%s",
                reserve_fraction,
                cvar_reserve_fraction,
                reference_false_exposure,
                risk_budget,
                reference_daily_cvar,
                cvar_budget,
                day_count,
                observations_per_day,
                reference_candidate,
                cvar_metric,
            )
            raise RuntimeError(
                "Risk-constrained convex QP is infeasible under the declared "
                f"reserve fraction {reserve_fraction:g}: {feasibility.message}"
            )
        hessian_alpha = (
            2.0 * (local_design.T @ local_design) / (count * local_scale)
            + 2.0 * regularization * np.eye(candidates)
        )

        def qp_objective(decision: np.ndarray) -> float:
            coefficients = decision[alpha_slice]
            residual = local_design @ coefficients - local_target
            value = float(
                np.mean(residual**2) / local_scale
                + regularization * np.dot(coefficients, coefficients)
            )
            if enforce_cvar_budget and cvar_objective_weight > 0.0:
                tail_value = (
                    decision[nu_index]
                    + np.sum(decision[xi_slice]) / tail_count
                ) / cvar_objective_scale
                value += cvar_objective_weight * float(tail_value)
            if enforce_total_budget and total_objective_weight > 0.0:
                value += total_objective_weight * float(
                    np.sum(decision[candidates : candidates + sample_count])
                    / total_objective_scale
                )
            return value

        def qp_gradient(decision: np.ndarray) -> np.ndarray:
            coefficients = decision[alpha_slice]
            residual = local_design @ coefficients - local_target
            gradient = np.zeros(nvar)
            gradient[alpha_slice] = (
                2.0 * local_design.T @ residual / (count * local_scale)
                + 2.0 * regularization * coefficients
            )
            if enforce_cvar_budget and cvar_objective_weight > 0.0:
                gradient[nu_index] += cvar_objective_weight / cvar_objective_scale
                gradient[xi_slice] += (
                    cvar_objective_weight
                    / (cvar_objective_scale * tail_count)
                )
            if enforce_total_budget and total_objective_weight > 0.0:
                gradient[candidates : candidates + sample_count] += (
                    total_objective_weight / total_objective_scale
                )
            return gradient

        def qp_hessian(_decision: np.ndarray, _multipliers: Any = None) -> csr_matrix:
            # The epigraph variables do not appear in the objective.  A sparse
            # block Hessian keeps the trust-region subproblem proportional to
            # the number of candidate profiles rather than the number of
            # event samples.
            hessian = csr_matrix((nvar, nvar), dtype=float).tolil()
            hessian[:candidates, :candidates] = hessian_alpha
            return hessian.tocsr()

        initial_point = np.asarray(feasibility.x, dtype=float)
        linear_constraints = [
            LinearConstraint(a_eq, np.ones(1), np.ones(1)),
            LinearConstraint(
                a_ub,
                np.full(row_id, -np.inf, dtype=float),
                np.asarray(upper, dtype=float),
            ),
        ]
        fitted = minimize(
            qp_objective,
            initial_point,
            jac=qp_gradient,
            hess=qp_hessian,
            method="trust-constr",
            bounds=Bounds(lower_bounds, upper_bounds),
            constraints=linear_constraints,
            options={
                "gtol": 1e-9,
                "xtol": 1e-10,
                "barrier_tol": 1e-9,
                "maxiter": 1500,
                "verbose": 0,
                "sparse_jacobian": True,
            },
        )
        full_point = np.asarray(fitted.x, dtype=float)
        coefficients = np.asarray(full_point[alpha_slice], dtype=float)
        coefficient_sum = float(coefficients.sum())
        if coefficient_sum <= 0.0:
            raise RuntimeError(
                f"Risk-constrained convex validation returned an invalid simplex: {fitted.message}"
            )
        if abs(coefficient_sum - 1.0) > 1.0e-6:
            raise RuntimeError(
                "Risk-constrained convex validation returned a non-simplex "
                f"point: sum={coefficient_sum:.9f}"
            )
        prediction = local_design @ coefficients
        fitted_false_by_day = np.maximum(
            np.maximum(prediction - local_actual, 0.0) - true_credit,
            0.0,
        ).reshape(day_count, observations_per_day).sum(axis=1)
        fitted_false_exposure = float(fitted_false_by_day.sum())
        fitted_daily_max = float(fitted_false_by_day.max(initial=0.0))
        if cvar_metric == "daily_false_credit_ratio":
            fitted_daily_cvar_values = fitted_false_by_day / cvar_day_denominator
        else:
            fitted_daily_cvar_values = fitted_false_by_day
        fitted_daily_cvar = float(
            np.mean(np.sort(fitted_daily_cvar_values)[-tail_count:])
        )
        reference_mse = float(
            np.mean((reference_prediction - local_target) ** 2)
        )
        fitted_mse = float(np.mean((prediction - local_target) ** 2))
        risk_tolerance = 1e-7 * max(
            1.0, risk_budget, cvar_budget
        )
        equality_residual = float(np.max(np.abs(a_eq @ full_point - 1.0)))
        inequality_residual = float(
            max(0.0, float(np.max(a_ub @ full_point - np.asarray(upper, dtype=float))))
        ) if row_id else 0.0
        finite_upper = np.isfinite(upper_bounds)
        bound_residual = float(
            max(
                0.0,
                float(np.max(lower_bounds - full_point)),
                float(np.max(full_point[finite_upper] - upper_bounds[finite_upper]))
                if finite_upper.any()
                else 0.0,
            )
        )
        primal_constraint_residual = max(
            equality_residual,
            inequality_residual,
            bound_residual,
            abs(float(coefficients.sum()) - 1.0),
        )
        if (
            (enforce_total_budget and fitted_false_exposure > risk_budget + risk_tolerance)
            or (enforce_cvar_budget and fitted_daily_cvar > cvar_budget + risk_tolerance)
        ):
            raise RuntimeError(
                "Risk-constrained ensemble exceeded its total or daily-tail "
                "false-credit budget"
            )
        if fitted_mse > reference_mse + 1e-8 * max(1.0, reference_mse):
            raise RuntimeError(
                "Convex validation solution is worse than its feasible "
                "single-projection reference"
            )
        kkt_residual = float(getattr(fitted, "optimality", np.inf))
        residual_certificate_passed = bool(
            np.isfinite(kkt_residual)
            and kkt_residual <= 1e-5
            and primal_constraint_residual <= 1e-6
        )
        if not residual_certificate_passed:
            raise RuntimeError(
                "Risk-constrained convex validation did not meet the declared "
                f"KKT/primal tolerances: status={fitted.message}, "
                f"optimality={kkt_residual:.3e}, primal={primal_constraint_residual:.3e}"
            )
        return coefficients, {
            "reference_false_credit_exposure_mw_slots": reference_false_exposure,
            "fitted_false_credit_exposure_mw_slots": fitted_false_exposure,
            "risk_budget_mw_slots": risk_budget,
            "reserve_fraction": float(reserve_fraction),
            "cvar_reserve_fraction": cvar_reserve_fraction,
            "cvar_objective_weight": cvar_objective_weight,
            "total_objective_weight": total_objective_weight,
            "reference_max_daily_false_credit_mw_slots": reference_daily_max,
            "fitted_max_daily_false_credit_mw_slots": fitted_daily_max,
            # Legacy field names are retained for downstream readers; the
            # explicit metric fields below prevent ratio values being mistaken
            # for absolute MW-slot quantities.
            "reference_daily_false_credit_cvar75_mw_slots": reference_daily_cvar_absolute,
            "fitted_daily_false_credit_cvar75_mw_slots": float(
                np.mean(np.sort(fitted_false_by_day)[-tail_count:])
            ),
            "cvar75_budget_mw_slots": float(
                cvar_reserve_fraction * reference_daily_cvar_absolute
            ),
            "total_budget_slack_mw_slots": float(risk_budget - fitted_false_exposure),
            "cvar75_budget_slack_mw_slots": float(
                cvar_reserve_fraction * reference_daily_cvar_absolute
                - np.mean(np.sort(fitted_false_by_day)[-tail_count:])
            ),
            "risk_cvar_metric": cvar_metric,
            "risk_cvar_level": cvar_level,
            "cvar_denominator_definition": cvar_denominator_definition,
            "reference_cvar_metric_value": reference_daily_cvar,
            "fitted_cvar_metric_value": fitted_daily_cvar,
            "cvar_budget_metric_value": cvar_budget,
            "cvar_budget_slack_metric": float(cvar_budget - fitted_daily_cvar),
            "total_objective_scale_mw_slots": total_objective_scale,
            "cvar_objective_scale": cvar_objective_scale,
            "total_budget_binding": float(
                enforce_total_budget
                and abs(fitted_false_exposure - risk_budget) <= risk_tolerance
            ),
            "cvar75_budget_binding": float(
                enforce_cvar_budget
                and abs(fitted_daily_cvar - cvar_budget) <= risk_tolerance
            ),
            "risk_constraints_satisfied": float(
                (not enforce_total_budget or fitted_false_exposure <= risk_budget + risk_tolerance)
                and (not enforce_cvar_budget or fitted_daily_cvar <= cvar_budget + risk_tolerance)
            ),
            "reference_validation_mse_mw2": reference_mse,
            "fitted_validation_mse_mw2": fitted_mse,
            "optimizer_iterations": float(fitted.nit),
            # trust-constr may report MAXFUN while already satisfying the
            # independently recomputed KKT/primal certificate.  The latter is
            # the acceptance criterion; raw termination is retained below.
            "optimizer_success": float(residual_certificate_passed),
            "optimizer_termination_success": float(fitted.success),
            "solver_name": "scipy.optimize.trust-constr",
            "convex_quadratic_program": True,
            "epigraph_formulation": "sample credit slacks with true-credit subtraction plus linear daily CVaR epigraph",
            "true_credit_definition": "[oracle no-event baseline minus closed event meter]_+",
            "total_budget_enforced": bool(enforce_total_budget),
            "cvar_budget_enforced": bool(enforce_cvar_budget),
            "kkt_stationarity_residual": kkt_residual,
            "optimizer_gradient_norm": float(np.linalg.norm(qp_gradient(full_point)[alpha_slice])),
            "primal_constraint_residual": float(primal_constraint_residual),
            "linear_epigraph_rows": int(row_id),
            "epigraph_primal_residual": float(inequality_residual),
        }

    candidate_fold_nrmse = np.empty(
        (len(projection_weights), len(fold_partitions))
    )
    for fold_index, held in enumerate(fold_partitions):
        fold_design = (
            candidate_array[:, held][:, :, :, event_slots]
            .transpose(1, 2, 3, 0)
            .reshape(-1, len(projection_weights))
        )
        fold_target = honest[validation_days[held]][:, :, event_slots].reshape(-1)
        for candidate in range(len(projection_weights)):
            rmse = float(
                np.sqrt(
                    np.mean(
                        (fold_design[:, candidate] - fold_target) ** 2
                    )
                )
            )
            candidate_fold_nrmse[candidate, fold_index] = rmse / max(
                float(np.mean(fold_target)), 1e-9
            )
    tuning["mean_contiguous_fold_nrmse"] = candidate_fold_nrmse.mean(axis=1)
    tuning["max_contiguous_fold_nrmse"] = candidate_fold_nrmse.max(axis=1)
    selected_single_index = int(
        np.argmin(tuning["max_contiguous_fold_nrmse"].to_numpy())
    )
    risk_reference_index = selected_single_index
    selected_single_weight = float(projection_weights[selected_single_index])
    validation_actual = actual_all[: len(validation_days)][
        :, :, event_slots
    ].reshape(-1)
    reserve_candidates = np.asarray(
        cfg["experiments"].get(
            "risk_reserve_fractions", [0.75, 0.9, 1.0]
        ),
        dtype=float,
    )
    if np.any((reserve_candidates <= 0) | (reserve_candidates > 1)):
        raise ValueError("Risk reserve fractions must lie in (0, 1]")

    # Nested contiguous validation selects the reserve without consulting any
    # locked test response.  The reserve is anchored to the independently
    # selected single feasible projection; the feasible-quantile comparator is
    # not used as a hard constraint.
    reserve_cv_rows: list[dict[str, Any]] = []
    for reserve_fraction in reserve_candidates:
        for fold, held in enumerate(fold_partitions, start=1):
            trained = np.setdiff1d(np.arange(validation_count), held)
            train_design = (
                risk_candidate_array[:, trained][:, :, :, event_slots]
                .transpose(1, 2, 3, 0)
                .reshape(-1, len(risk_candidate_names))
            )
            train_target = honest[validation_days[trained]][
                :, :, event_slots
            ].reshape(-1)
            train_actual = actual_all[trained][
                :, :, event_slots
            ].reshape(-1)
            try:
                fold_weights, _ = fit_risk_constrained_simplex(
                    train_design,
                    train_target,
                    train_actual,
                    risk_reference_index,
                    len(trained),
                    float(reserve_fraction),
                    # The candidate reserve is the complete predeclared
                    # contract in each nested fold. Keeping the CVaR reserve
                    # tied to the candidate avoids a hidden pooled-only
                    # override that can make a nominally selected fold
                    # infeasible after the fact.
                    cvar_reserve_fraction_override=float(reserve_fraction),
                )
            except RuntimeError as exc:
                reserve_cv_rows.append(
                    {
                        "reserve_fraction": float(reserve_fraction),
                        "fold": fold,
                        "held_out_days": ";".join(
                            map(str, validation_days[held].tolist())
                        ),
                        "held_out_nrmse": np.inf,
                        "held_out_false_credit_mw_slots": np.inf,
                        "held_out_reference_false_credit_mw_slots": np.nan,
                        "held_out_false_credit_ratio_to_reference": np.inf,
                        "held_out_risk_noninferior": 0.0,
                        "solver_status": f"infeasible:{exc}",
                    }
                )
                continue
            held_design = (
                risk_candidate_array[:, held][:, :, :, event_slots]
                .transpose(1, 2, 3, 0)
                .reshape(-1, len(risk_candidate_names))
            )
            held_target = honest[validation_days[held]][
                :, :, event_slots
            ].reshape(-1)
            held_actual = actual_all[held][
                :, :, event_slots
            ].reshape(-1)
            held_prediction = held_design @ fold_weights
            held_reference = held_design[:, risk_reference_index]
            held_true_credit = np.maximum(held_target - held_actual, 0.0)
            held_false = float(
                np.maximum(
                    np.maximum(held_prediction - held_actual, 0.0)
                    - held_true_credit,
                    0.0,
                ).sum()
            )
            held_reference_false = float(
                np.maximum(
                    np.maximum(held_reference - held_actual, 0.0)
                    - held_true_credit,
                    0.0,
                ).sum()
            )
            held_rmse = float(
                np.sqrt(np.mean((held_prediction - held_target) ** 2))
            )
            reserve_cv_rows.append(
                {
                    "reserve_fraction": float(reserve_fraction),
                    "fold": fold,
                    "held_out_days": ";".join(
                        map(str, validation_days[held].tolist())
                    ),
                    "held_out_nrmse": held_rmse
                    / max(float(np.mean(held_target)), 1e-9),
                    "held_out_false_credit_mw_slots": held_false,
                    "held_out_reference_false_credit_mw_slots": (
                        held_reference_false
                    ),
                    "held_out_false_credit_ratio_to_reference": held_false
                    / max(held_reference_false, 1e-9),
                    "held_out_risk_noninferior": float(
                        held_false <= held_reference_false + 1e-7
                    ),
                    "solver_status": "optimal",
                }
            )
    reserve_cv = pd.DataFrame(reserve_cv_rows)
    reserve_summary = (
        reserve_cv.groupby("reserve_fraction", as_index=False)
        .agg(
            max_fold_nrmse=("held_out_nrmse", "max"),
            mean_fold_nrmse=("held_out_nrmse", "mean"),
            max_false_credit_ratio=(
                "held_out_false_credit_ratio_to_reference",
                "max",
            ),
            all_folds_risk_noninferior=(
                "held_out_risk_noninferior",
                "min",
            ),
            all_folds_feasible=(
                "solver_status",
                lambda values: float(
                    all(str(value) == "optimal" for value in values)
                ),
            ),
        )
    )
    feasible_reserves = reserve_summary[
        reserve_summary["all_folds_feasible"] == 1
    ]
    if len(feasible_reserves) == 0:
        raise RuntimeError(
            "No predeclared risk reserve solves every nested contiguous fold"
        )
    # Locked false-credit non-inferiority is an outcome diagnostic, not a
    # selection constraint: it is evaluated after each fold's contract has
    # been fitted and therefore cannot certify feasibility of a reserve chosen
    # before the locked block.  Filtering on that outcome would silently
    # turn nested validation into an outcome-dependent gate.
    selection_pool = feasible_reserves
    selected_reserve_fraction = float(
        selection_pool.sort_values(
            ["max_fold_nrmse", "max_false_credit_ratio", "reserve_fraction"]
        ).iloc[0]["reserve_fraction"]
    )
    # The nested choice is the contract. The pooled fit is checked at exactly
    # that predeclared reserve; no upward grid search or pooled-only retuning is
    # allowed after fold selection.
    initial_selected_reserve_fraction = selected_reserve_fraction
    final_fit_error = ""
    try:
        ensemble_weights, risk_fit_certificate = fit_risk_constrained_simplex(
            risk_design,
            target,
            validation_actual,
            risk_reference_index,
            validation_count,
            selected_reserve_fraction,
            cvar_reserve_fraction_override=selected_reserve_fraction,
        )
    except RuntimeError as exc:
        final_fit_error = str(exc)
        raise RuntimeError(
            "The nested-selected risk reserve is not feasible on the pooled validation set; "
            "the protocol forbids post-selection reserve retuning: "
            + final_fit_error
        )
    reserve_cv["nested_selected_reserve_fraction"] = (
        reserve_cv["reserve_fraction"] == initial_selected_reserve_fraction
    )
    reserve_cv["selected_reserve_fraction"] = (
        reserve_cv["reserve_fraction"] == selected_reserve_fraction
    )
    reserve_cv.to_csv(final / "risk_reserve_nested_cv.csv", index=False)
    reserve_summary["nested_selected"] = (
        reserve_summary["reserve_fraction"] == initial_selected_reserve_fraction
    )
    reserve_summary["selected"] = (
        reserve_summary["reserve_fraction"] == selected_reserve_fraction
    )
    reserve_summary.to_csv(
        final / "risk_reserve_validation_summary.csv", index=False
    )
    risk_ablation_weights = {
        "single reference": np.eye(len(risk_candidate_names))[risk_reference_index],
        "unconstrained convex ensemble": fit_risk_constrained_simplex(
            risk_design, target, validation_actual, risk_reference_index,
            validation_count, selected_reserve_fraction,
            enforce_total_budget=False, enforce_cvar_budget=False,
        )[0],
        "total-budget-only ensemble": fit_risk_constrained_simplex(
            risk_design, target, validation_actual, risk_reference_index,
            validation_count, selected_reserve_fraction,
            enforce_total_budget=True, enforce_cvar_budget=False,
        )[0],
        "CVaR-only ensemble": fit_risk_constrained_simplex(
            risk_design, target, validation_actual, risk_reference_index,
            validation_count, selected_reserve_fraction,
            enforce_total_budget=False, enforce_cvar_budget=True,
        )[0],
        "total+CVaR ensemble": ensemble_weights,
    }
    ablation_validation_profiles = {
        name: np.tensordot(weights, risk_candidate_array, axes=(0, 0))
        for name, weights in risk_ablation_weights.items()
    }
    pd.DataFrame([
        {"ablation": name, "split": "validation", **{f"weight_{candidate}": float(value) for candidate, value in zip(risk_candidate_names, weights)}}
        for name, weights in risk_ablation_weights.items()
    ]).to_csv(final / "risk_module_ablation_weights.csv", index=False)
    validation_ensemble_profiles = np.tensordot(
        ensemble_weights, risk_candidate_array, axes=(0, 0)
    )
    # Persist the complete validation candidate panel so downstream payment
    # calibration can be frozen before the locked test days are touched.
    np.savez_compressed(
        intermediate / "validation_profiles.npz",
        days=validation_days,
        projection_candidates=candidate_array,
        quantile_profile=np.asarray(validation_quantile_profiles),
        actual=actual_all[:validation_count],
        oracle=honest[validation_days],
        projection_weights=projection_weights,
        selected_single_projection_index=np.asarray(selected_single_index),
    )
    validation_reference_profiles = np.asarray(
        validation_quantile_profiles
    )
    reference_validation_rows: list[dict[str, float]] = []
    for local_day in range(validation_count):
        base = baseline_metrics(
            validation_reference_profiles[local_day],
            honest[int(validation_days[local_day])],
            event_slots,
        )
        response = response_metrics(
            validation_reference_profiles[local_day],
            honest[int(validation_days[local_day])],
            actual_all[local_day],
            event_slots,
            dt_h,
        )
        reference_validation_rows.append({**base, **response})
    reference_validation_f1 = float(
        np.mean([row["credit_f1"] for row in reference_validation_rows])
    )

    # A second exact LP projects the tail-risk ensemble through a one-sided
    # contractual cap defined by the independently selected single feasible
    # projection.  Its lower side is generated from the independent convex
    # target, not from the cap itself.  This keeps the final verifier
    # non-degenerate: the risk fit can move below the single reference while
    # the cap still controls upward unsupported credit.  The feasible-quantile
    # profile remains an external matched comparator, so the test metric is
    # not mechanically upper-bounded by its construction.
    validation_single_profiles = candidate_array[selected_single_index]
    envelope_rows: list[dict[str, Any]] = []
    for envelope_weight in projection_weights:
        day_records: list[dict[str, float]] = []
        for local_day, day in enumerate(validation_days):
            risk_floor_profile = np.minimum(
                validation_single_profiles[local_day],
                validation_ensemble_profiles[local_day],
            )
            result = _solve_day_with_buffer(
                arrivals_days[int(day)],
                prices,
                cfg,
                mode="honest",
                target=validation_ensemble_profiles[local_day],
                projection_weight=float(envelope_weight),
                power_upper_mw=_event_risk_upper_envelope(
                    validation_single_profiles[local_day], cfg
                ),
                power_lower_mw=_event_risk_lower_envelope(risk_floor_profile, cfg),
            )
            if not result.success:
                raise RuntimeError(
                    "Risk-envelope projection failed on validation day "
                    f"{int(day)}: {result.solver_message}"
                )
            base = baseline_metrics(
                result.power_mw, honest[int(day)], event_slots
            )
            response = response_metrics(
                result.power_mw,
                honest[int(day)],
                actual_all[local_day],
                event_slots,
                dt_h,
            )
            day_records.append({**base, **response})
        fold_nrmse = [
            float(np.mean([day_records[i]["nrmse"] for i in held]))
            for held in fold_partitions
        ]
        fold_f1 = [
            float(np.mean([day_records[i]["credit_f1"] for i in held]))
            for held in fold_partitions
        ]
        envelope_rows.append(
            {
                "projection_weight": float(envelope_weight),
                "mean_validation_nrmse": float(
                    np.mean([row["nrmse"] for row in day_records])
                ),
                "max_fold_nrmse": float(np.max(fold_nrmse)),
                "mean_validation_credit_f1": float(
                    np.mean([row["credit_f1"] for row in day_records])
                ),
                "min_fold_credit_f1": float(np.min(fold_f1)),
                "mean_false_response_mwh": float(
                    np.mean(
                        [row["false_response_mwh"] for row in day_records]
                    )
                ),
                "reference_mean_credit_f1": reference_validation_f1,
                "f1_noninferior_to_reference": float(
                    np.mean([row["credit_f1"] for row in day_records])
                    >= reference_validation_f1 - 1e-9
                ),
                "two_sided_band_tolerance_mw": float(
                    cfg["experiments"].get("two_sided_band_tolerance_mw", 0.0)
                ),
            }
        )
    envelope_validation = pd.DataFrame(envelope_rows)
    selected_envelope_weight = float(
        envelope_validation.sort_values(
            ["max_fold_nrmse", "mean_validation_nrmse", "projection_weight"],
            ascending=[True, True, True],
        ).iloc[0]["projection_weight"]
    )
    envelope_validation["selected"] = (
        envelope_validation["projection_weight"]
        == selected_envelope_weight
    )
    envelope_validation.to_csv(
        final / "risk_envelope_validation.csv", index=False
    )
    tuning["selected_single_projection"] = (
        np.arange(len(projection_weights)) == selected_single_index
    )
    tuning["candidate_type"] = "metadata projection"
    tuning["ensemble_weight"] = ensemble_weights[:-1]
    tuning["selected"] = tuning["ensemble_weight"] > 1e-10
    quantile_validation_row = quantile_projection_validation[
        quantile_projection_validation["selected"]
    ].iloc[0]
    augmented_tuning = pd.concat(
        [
            tuning,
            pd.DataFrame(
                [
                    {
                        "candidate_index": len(risk_candidate_names) - 1,
                        "projection_weight": (
                            selected_quantile_projection_weight
                        ),
                        "validation_score": float(
                            quantile_validation_row[
                                "mean_validation_nrmse"
                            ]
                        ),
                        "validation_score_std": np.nan,
                        "event_window_deviation_from_optimization_only_mw": (
                            np.nan
                        ),
                        "validation_credit_precision": np.nan,
                        "validation_credit_recall": np.nan,
                        "validation_credit_f1": float(
                            quantile_validation_row["mean_credit_f1"]
                        ),
                        "mean_contiguous_fold_nrmse": np.nan,
                        "max_contiguous_fold_nrmse": float(
                            quantile_validation_row["max_fold_nrmse"]
                        ),
                        "selected_single_projection": False,
                        "candidate_type": "feasible quantile projection",
                        "ensemble_weight": float(ensemble_weights[-1]),
                        "selected": bool(ensemble_weights[-1] > 1e-10),
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    augmented_tuning.to_csv(
        final / "projection_candidate_validation.csv", index=False
    )
    pd.DataFrame(
        {
            "candidate": risk_candidate_names,
            "ensemble_weight": ensemble_weights,
        }
    ).to_csv(
        final / "convex_projection_weights.csv", index=False
    )
    pd.DataFrame([risk_fit_certificate]).to_csv(
        final / "risk_constrained_validation_certificate.csv", index=False
    )

    # Exact validation-only tail-cap sensitivity.  This LP minimizes the
    # empirical CVaR epigraph under the selected total-risk budget for each
    # predeclared tail reserve; it is deliberately separate from locked-test
    # selection and exposes the feasible frontier when the selected contract's
    # CVaR row is slack.  The result prevents a nonbinding ablation from being
    # presented as a universal tail-risk improvement.
    cvar_stress_fractions = np.asarray(
        cfg["experiments"].get(
            "risk_cvar_stress_reserve_fractions", [0.86946, 0.88, 0.95, 1.0]
        ),
        dtype=float,
    )
    if (
        cvar_stress_fractions.ndim != 1
        or len(cvar_stress_fractions) == 0
        or np.any((cvar_stress_fractions <= 0.0) | (cvar_stress_fractions > 1.0))
    ):
        raise ValueError("risk_cvar_stress_reserve_fractions must lie in (0, 1]")
    stress_design = risk_design
    stress_target = target
    stress_actual = validation_actual
    stress_day_count = validation_count
    stress_observations_per_day = stress_design.shape[0] // stress_day_count
    stress_true_credit = np.maximum(stress_target - stress_actual, 0.0)
    stress_reference_prediction = stress_design[:, risk_reference_index]
    stress_reference_false_by_day = np.maximum(
        np.maximum(stress_reference_prediction - stress_actual, 0.0)
        - stress_true_credit,
        0.0,
    ).reshape(stress_day_count, stress_observations_per_day).sum(axis=1)
    stress_total_budget = float(stress_reference_false_by_day.sum())
    stress_cvar_level = float(cfg["experiments"].get("risk_cvar_level", 0.75))
    if not 0.0 < stress_cvar_level < 1.0:
        raise ValueError("risk_cvar_level must lie strictly between 0 and 1")
    stress_tail_count = max(
        1, int(np.ceil((1.0 - stress_cvar_level) * stress_day_count))
    )
    stress_cvar_metric = str(
        cfg["experiments"].get("risk_cvar_metric", "daily_false_credit_mw_slots")
    )
    if stress_cvar_metric == "daily_false_credit_ratio":
        stress_day_denominator = np.maximum(
            stress_true_credit.reshape(
                stress_day_count, stress_observations_per_day
            ).sum(axis=1),
            float(
                cfg["experiments"].get(
                    "risk_cvar_denominator_floor_mw_slots", 1.0e-9
                )
            ),
        )
        stress_cvar_sample_weights = np.repeat(
            1.0 / stress_day_denominator, stress_observations_per_day
        )
        stress_reference_cvar_values = (
            stress_reference_false_by_day / stress_day_denominator
        )
    elif stress_cvar_metric == "daily_false_credit_mw_slots":
        stress_day_denominator = np.ones(stress_day_count, dtype=float)
        stress_cvar_sample_weights = np.ones(stress_design.shape[0], dtype=float)
        stress_reference_cvar_values = stress_reference_false_by_day.copy()
    else:
        raise ValueError(
            "risk_cvar_metric must be daily_false_credit_ratio or "
            "daily_false_credit_mw_slots"
        )
    stress_reference_cvar = float(
        np.mean(np.sort(stress_reference_cvar_values)[-stress_tail_count:])
    )
    stress_rows: list[dict[str, Any]] = []
    for stress_fraction in cvar_stress_fractions:
        sample_count = stress_design.shape[0]
        candidate_count = stress_design.shape[1]
        nvar = candidate_count + sample_count + 1 + stress_day_count
        rows: list[int] = []
        cols: list[int] = []
        values: list[float] = []
        upper: list[float] = []
        row_id = 0
        threshold = stress_actual + stress_true_credit
        for sample in range(sample_count):
            for candidate in range(candidate_count):
                value = float(stress_design[sample, candidate])
                if value:
                    rows.append(row_id)
                    cols.append(candidate)
                    values.append(value)
            rows.append(row_id)
            cols.append(candidate_count + sample)
            values.append(-1.0)
            upper.append(float(threshold[sample]))
            row_id += 1
        nu_index = candidate_count + sample_count
        xi_start = nu_index + 1
        for day in range(stress_day_count):
            start = day * stress_observations_per_day
            stop = (day + 1) * stress_observations_per_day
            for sample in range(start, stop):
                rows.append(row_id)
                cols.append(candidate_count + sample)
                values.append(float(stress_cvar_sample_weights[sample]))
            rows.extend([row_id, row_id])
            cols.extend([nu_index, xi_start + day])
            values.extend([-1.0, -1.0])
            upper.append(0.0)
            row_id += 1
        rows.append(row_id)
        cols.append(nu_index)
        values.append(1.0)
        for day in range(stress_day_count):
            rows.append(row_id)
            cols.append(xi_start + day)
            values.append(1.0 / stress_tail_count)
        cvar_budget = float(stress_fraction * stress_reference_cvar)
        upper.append(cvar_budget)
        row_id += 1
        for sample in range(sample_count):
            rows.append(row_id)
            cols.append(candidate_count + sample)
            values.append(1.0)
        upper.append(stress_total_budget)
        row_id += 1
        equality = coo_matrix(
            (np.ones(candidate_count), (np.zeros(candidate_count), np.arange(candidate_count))),
            shape=(1, nvar),
        ).tocsr()
        stress_aub = coo_matrix(
            (np.asarray(values), (np.asarray(rows), np.asarray(cols))),
            shape=(row_id, nvar),
        ).tocsr()
        objective = np.zeros(nvar, dtype=float)
        objective[nu_index] = 1.0
        objective[xi_start:] = 1.0 / stress_tail_count
        stress_lp = linprog(
            objective,
            A_ub=stress_aub,
            b_ub=np.asarray(upper),
            A_eq=equality,
            b_eq=np.ones(1),
            bounds=[(0.0, 1.0)] * candidate_count
            + [(0.0, None)] * (sample_count + 1 + stress_day_count),
            method="highs",
        )
        minimum_cvar = float(stress_lp.fun) if stress_lp.success else float("inf")
        stress_rows.append(
            {
                "cvar_reserve_fraction": float(stress_fraction),
                "reference_total_budget_mw_slots": stress_total_budget,
                # These values are the normalized daily false-credit-ratio
                # metric, not absolute MW-slot quantities.  The explicit
                # names prevent readers from mistaking the stress frontier
                # for the separate absolute total-budget certificate.
                "reference_cvar_metric_value": stress_reference_cvar,
                "cvar_budget_metric_value": cvar_budget,
                "minimum_achievable_cvar_metric_value": minimum_cvar,
                "cvar_budget_minus_minimum_metric": (
                    cvar_budget - minimum_cvar if stress_lp.success else float("nan")
                ),
                "risk_cvar_metric": stress_cvar_metric,
                "risk_cvar_level": stress_cvar_level,
                "feasible": bool(stress_lp.success),
                "minimum_cvar_touches_budget": bool(
                    stress_lp.success and abs(cvar_budget - minimum_cvar) <= 1.0e-3
                ),
                "locked_test_days_used_for_stress": False,
            }
        )
    pd.DataFrame(stress_rows).to_csv(final / "risk_cvar_stress_sensitivity.csv", index=False)

    # Four contiguous blocked folds quantify validation-set overfitting without
    # touching any locked test day.
    blocked_cv_rows: list[dict[str, Any]] = []
    for fold, held in enumerate(fold_partitions, start=1):
        trained = np.setdiff1d(np.arange(validation_count), held)
        train_design = (
            risk_candidate_array[:, trained][:, :, :, event_slots]
            .transpose(1, 2, 3, 0)
            .reshape(-1, len(risk_candidate_names))
        )
        train_target = honest[validation_days[trained]][:, :, event_slots].reshape(-1)
        train_actual = actual_all[trained][:, :, event_slots].reshape(-1)
        fold_weights, fold_certificate = fit_risk_constrained_simplex(
            train_design,
            train_target,
            train_actual,
            risk_reference_index,
            len(trained),
            selected_reserve_fraction,
            cvar_reserve_fraction_override=float(
                cfg["experiments"].get("blocked_cv_cvar_reserve_fraction", 1.0)
            ),
        )
        held_design = (
            risk_candidate_array[:, held][:, :, :, event_slots]
            .transpose(1, 2, 3, 0)
            .reshape(-1, len(risk_candidate_names))
        )
        held_target = honest[validation_days[held]][:, :, event_slots].reshape(-1)
        held_prediction = held_design @ fold_weights
        held_rmse = float(np.sqrt(np.mean((held_prediction - held_target) ** 2)))
        blocked_cv_rows.append(
            {
                "fold": fold,
                "train_days": ";".join(map(str, validation_days[trained].tolist())),
                "held_out_days": ";".join(map(str, validation_days[held].tolist())),
                "held_out_rmse_mw": held_rmse,
                "held_out_nrmse": held_rmse / max(float(np.mean(held_target)), 1e-9),
                "training_false_credit_budget_mw_slots": fold_certificate[
                    "reference_false_credit_exposure_mw_slots"
                ],
                "training_fitted_false_credit_mw_slots": fold_certificate[
                    "fitted_false_credit_exposure_mw_slots"
                ],
                **{
                    f"weight_{name}": float(coefficient)
                    for name, coefficient in zip(
                        risk_candidate_names, fold_weights
                    )
                },
            }
        )
    pd.DataFrame(blocked_cv_rows).to_csv(
        final / "blocked_validation_cv.csv", index=False
    )

    metric_rows: list[dict[str, Any]] = []
    trace_replay_rows: list[dict[str, Any]] = []
    profile_baselines = []
    profile_actual = []
    profile_oracle = []
    physics_migration = []
    profile_projection_candidates = []
    contract_profiles = []
    ablation_test_profiles = {name: [] for name in risk_ablation_weights}
    two_sided_certificate_rows: list[dict[str, Any]] = []
    for day in tqdm(test_days, desc="Exp2 locked test days"):
        day = int(day)
        stats = statistical_by_day[day]
        projection_profiles, projection_migrations, _ = _solve_projection_candidates(
            arrivals_days[day],
            prices,
            cfg,
            stats.ex_post_metadata_gradient_boosting,
            projection_weights,
        )
        single_result = _solve_day_with_buffer(
            arrivals_days[day],
            prices,
            cfg,
            mode="honest",
            target=stats.ex_post_metadata_gradient_boosting,
            projection_weight=selected_single_weight,
        )
        if not single_result.success:
            raise RuntimeError(
                f"Single feasible projection failed for day {day}: "
                f"{single_result.solver_message}"
            )
        quantile_result = _solve_day_with_buffer(
            arrivals_days[day],
            prices,
            cfg,
            mode="honest",
            target=stats.ex_post_quantile_gradient_boosting,
            projection_weight=selected_quantile_projection_weight,
        )
        if not quantile_result.success:
            raise RuntimeError(
                f"Feasible quantile projection failed for day {day}: "
                f"{quantile_result.solver_message}"
            )
        risk_test_candidates = np.concatenate(
            [projection_profiles, quantile_result.power_mw[None, ...]],
            axis=0,
        )
        for ablation_name, ablation_weights in risk_ablation_weights.items():
            ablation_test_profiles[ablation_name].append(
                np.tensordot(ablation_weights, risk_test_candidates, axes=(0, 0))
            )
        ensemble_profile = np.tensordot(
            ensemble_weights, risk_test_candidates, axes=(0, 0)
        )
        # Keep the CVaR-only construction as a genuine ablation comparator.
        # The reported verifier uses the jointly constrained (total + daily
        # CVaR) fit; giving the tail-risk label the CVaR-only fit prevents the
        # table from silently duplicating the proposed method.
        tail_risk_profile = np.tensordot(
            risk_ablation_weights["CVaR-only ensemble"],
            risk_test_candidates,
            axes=(0, 0),
        )
        # The risk-constrained verifier is the fitted convex combination.  It
        # remains workload-feasible because every candidate shares the same
        # release, deadline, conservation, and capacity polytope.  The
        # payment-contract envelope is solved separately below; conflating it
        # with this profile would make the risk module unidentifiable.
        risk_profile = ensemble_profile
        risk_migration = float(
            np.dot(
                ensemble_weights,
                np.concatenate(
                    [projection_migrations, np.asarray([quantile_result.migrated_mwh])]
                ),
            )
        )
        risk_floor_profile = np.minimum(single_result.power_mw, ensemble_profile)
        contract_result = _solve_day_with_buffer(
            arrivals_days[day],
            prices,
            cfg,
            mode="honest",
            target=ensemble_profile,
            projection_weight=selected_envelope_weight,
            power_upper_mw=_event_risk_upper_envelope(
                single_result.power_mw, cfg
            ),
            power_lower_mw=_event_risk_lower_envelope(risk_floor_profile, cfg),
        )
        if not contract_result.success:
            raise RuntimeError(
                f"Payment-contract envelope failed for day {day}: "
                f"{contract_result.solver_message}"
            )
        contract_profile = contract_result.power_mw
        migration = risk_migration
        lower_band = _event_risk_lower_envelope(risk_floor_profile, cfg)
        upper_band = _event_risk_upper_envelope(single_result.power_mw, cfg)
        event_profile = contract_profile[:, event_slots]
        lower_event = lower_band[:, event_slots]
        upper_event = upper_band[:, event_slots]
        risk_event = risk_profile[:, event_slots]
        two_sided_certificate_rows.append(
            {
                "day": day,
                "risk_profile_event_deviation_from_single_mw": float(
                    np.mean(np.abs(risk_event - single_result.power_mw[:, event_slots]))
                ),
                "risk_profile_is_distinct_from_single": float(
                    np.max(np.abs(risk_event - single_result.power_mw[:, event_slots])) > 1.0e-6
                ),
                "contract_profile_event_deviation_from_risk_mw": float(
                    np.mean(np.abs(event_profile - risk_event))
                ),
                "upper_margin_min_mw": float(
                    np.min(upper_event - event_profile)
                ),
                "lower_margin_min_mw": float(
                    np.min(event_profile - lower_event)
                ),
                "declared_band_tolerance_mw": float(
                    cfg["experiments"].get("two_sided_band_tolerance_mw", 0.0)
                ),
                "false_credit_mwh": float(
                    response_metrics(
                        contract_profile,
                        honest[day],
                        actual_lookup[day],
                        event_slots,
                        dt_h,
                    )["false_response_mwh"]
                ),
                "under_credit_mwh": float(
                    response_metrics(
                        contract_profile,
                        honest[day],
                        actual_lookup[day],
                        event_slots,
                        dt_h,
                    )["underestimation_mwh"]
                ),
                "single_reference_under_credit_mwh": float(
                    response_metrics(
                        single_result.power_mw,
                        honest[day],
                        actual_lookup[day],
                        event_slots,
                        dt_h,
                    )["underestimation_mwh"]
                ),
                # The LP certificate is checked against a documented
                # micro-MW numerical tolerance.  This only absorbs solver
                # feasibility residuals; it does not widen the contractual
                # one-MW band or alter the profile.
                "pointwise_upper_bound_satisfied": float(
                    np.all(event_profile <= upper_event + 1e-6)
                ),
                "pointwise_lower_bound_satisfied": float(
                    np.all(event_profile >= lower_event - 1e-6)
                ),
            }
        )
        bundle = {
            "High-5-of-10": stats.high5of10,
            "Ridge": stats.ridge,
            "Gradient Boosting": stats.gradient_boosting,
            "Extra Trees": stats.extra_trees,
            "Metadata Gradient Boosting": stats.metadata_gradient_boosting,
            "Ex-post Metadata Gradient Boosting": stats.ex_post_metadata_gradient_boosting,
            "Ex-post Quantile Gradient Boosting": stats.ex_post_quantile_gradient_boosting,
            "Synthetic Control": stats.synthetic_control,
            "Feasible Quantile Projection": quantile_result.power_mw,
            "Tail-Risk Feasible Counterfactual": tail_risk_profile,
            "Single Feasible Projection": single_result.power_mw,
            "Risk-Constrained Convex Verifier": risk_profile,
        }
        profile_baselines.append(np.stack([bundle[m] for m in METHODS]))
        profile_actual.append(actual_lookup[day])
        profile_oracle.append(honest[day])
        physics_migration.append(migration)
        contract_profiles.append(contract_profile)
        profile_projection_candidates.append(projection_profiles)
        for method, pred in bundle.items():
            row = {"day": day, "method": method, "event_migration_mwh": migration_lookup[day]}
            row.update(baseline_metrics(pred, honest[day], event_slots))
            row.update(response_metrics(pred, honest[day], actual_lookup[day], event_slots, dt_h))
            metric_rows.append(row)
            # Keep the independent meter replay as a separate observational
            # panel.  It shares the locked day split with the mechanism
            # isolation rows above, but it never treats a simulated event
            # response as measured truth.
            trace_metrics = baseline_metrics(
                pred, observed_meter_lookup[day], event_slots
            )
            trace_replay_rows.append(
                {
                    "day": day,
                    "method": method,
                    "truth_source": observed_truth_source,
                    "event_intervention": False,
                    **{f"trace_{key}": value for key, value in trace_metrics.items()},
                }
            )
        pd.DataFrame(metric_rows).to_csv(intermediate / "test_metrics_checkpoint.csv", index=False)
    metrics = pd.DataFrame(metric_rows)
    metrics.to_csv(final / "per_day_baseline_metrics.csv", index=False)
    pd.DataFrame(trace_replay_rows).to_csv(
        final / "trace_meter_replay.csv", index=False
    )
    ablation_daily_rows: list[dict[str, Any]] = []
    for split, profiles, split_days, split_actual in [
        ("validation", ablation_validation_profiles, validation_days, actual_all[:validation_count]),
        ("test", {name: np.asarray(values) for name, values in ablation_test_profiles.items()}, test_days, np.asarray([actual_lookup[int(day)] for day in test_days])),
    ]:
        for name, profile_array in profiles.items():
            for local_index, day_value in enumerate(split_days):
                day = int(day_value)
                truth = honest[day] if split == "validation" else honest[day]
                actual_trace = split_actual[local_index]
                base = baseline_metrics(profile_array[local_index], truth, event_slots)
                response = response_metrics(profile_array[local_index], truth, actual_trace, event_slots, dt_h)
                ablation_daily_rows.append({"split": split, "ablation": name, "day": day, **base, **response})
    ablation_daily = pd.DataFrame(ablation_daily_rows)
    ablation_daily.to_csv(final / "risk_module_ablation_daily.csv", index=False)
    ablation_summary = ablation_daily.groupby(["split", "ablation"], as_index=False).agg(
        n_days=("day", "nunique"), nrmse=("nrmse", "mean"),
        false_response_mwh=("false_response_mwh", "mean"),
        underestimation_mwh=("underestimation_mwh", "mean"),
        credit_f1=("credit_f1", "mean"),
        net_system_response_mwh=("net_system_response_mwh", "mean"),
    )
    ablation_summary.to_csv(final / "risk_module_ablation.csv", index=False)
    # Separate the convex risk fit from the final pointwise envelope.  The
    # decomposition is reported explicitly so a reduction in unsupported
    # credit cannot be attributed to CVaR if it is produced by the later
    # profile cap.
    risk_effect_rows: list[dict[str, Any]] = []
    for split in ["validation", "test"]:
        split_ablation = ablation_summary[ablation_summary["split"] == split]
        single_row = split_ablation[split_ablation["ablation"] == "single reference"]
        if len(single_row) != 1:
            raise RuntimeError(f"Missing single-reference risk ablation for {split}")
        for variant in [
            "unconstrained convex ensemble",
            "total-budget-only ensemble",
            "CVaR-only ensemble",
            "total+CVaR ensemble",
        ]:
            row = split_ablation[split_ablation["ablation"] == variant]
            if len(row) != 1:
                raise RuntimeError(f"Missing risk ablation {variant} for {split}")
            risk_effect_rows.append(
                {
                    "split": split,
                    "comparison": f"{variant} vs single reference",
                    "nrmse_change": float(row.iloc[0]["nrmse"] - single_row.iloc[0]["nrmse"]),
                    "false_response_change_mwh": float(
                        row.iloc[0]["false_response_mwh"]
                        - single_row.iloc[0]["false_response_mwh"]
                    ),
                    "credit_f1_change": float(
                        row.iloc[0]["credit_f1"] - single_row.iloc[0]["credit_f1"]
                    ),
                    "interpretation": "convex risk fit before pointwise event envelope",
                }
            )
    final_safe = metrics[metrics["method"] == "Risk-Constrained Convex Verifier"]
    final_single = metrics[metrics["method"] == "Single Feasible Projection"]
    risk_effect_rows.append(
        {
            "split": "test",
            "comparison": "risk-constrained convex verifier vs single reference",
            "nrmse_change": float(final_safe["nrmse"].mean() - final_single["nrmse"].mean()),
            "false_response_change_mwh": float(
                final_safe["false_response_mwh"].mean()
                - final_single["false_response_mwh"].mean()
            ),
            "credit_f1_change": float(
                final_safe["credit_f1"].mean() - final_single["credit_f1"].mean()
            ),
            "interpretation": "locked risk-constrained convex ensemble; payment-contract envelope is audited separately",
        }
    )
    pd.DataFrame(risk_effect_rows).to_csv(final / "risk_effect_decomposition.csv", index=False)
    pd.DataFrame(two_sided_certificate_rows).to_csv(
        final / "two_sided_credit_certificate.csv", index=False
    )
    stored_baselines = np.asarray(profile_baselines)

    # Re-evaluate both declared outputs.  ``Risk-Constrained Convex
    # Verifier`` is the scientific risk-fit profile; the separately stored
    # payment-contract profile is the profile that carries the pointwise
    # activation cap.  Keeping both in the audit prevents a payment safeguard
    # from being misreported as evidence that the risk fit itself is
    # non-degenerate.
    final_risk_index = METHODS.index("Risk-Constrained Convex Verifier")
    final_reference_index = METHODS.index("Single Feasible Projection")
    contract_array = np.asarray(contract_profiles, dtype=float)
    risk_audit_rows: list[dict[str, Any]] = []
    for local_day, day_value in enumerate(test_days):
        day = int(day_value)
        actual_event = actual_lookup[day][:, event_slots]
        true_credit = np.maximum(honest[day][:, event_slots] - actual_event, 0.0)
        risk_event = stored_baselines[local_day, final_risk_index][:, event_slots]
        contract_event = contract_array[local_day][:, event_slots]
        reference_event = stored_baselines[
            local_day, final_reference_index
        ][:, event_slots]
        risk_false = np.maximum(
            np.maximum(risk_event - actual_event, 0.0) - true_credit, 0.0
        ).sum()
        contract_false = np.maximum(
            np.maximum(contract_event - actual_event, 0.0) - true_credit, 0.0
        ).sum()
        reference_false = np.maximum(
            np.maximum(reference_event - actual_event, 0.0) - true_credit, 0.0
        ).sum()
        risk_audit_rows.append(
            {
                "day": day,
                # Backward-compatible fields refer to the activation-contract
                # profile; risk-profile diagnostics are explicit below.
                "final_false_credit_mw_slots": float(contract_false),
                "reference_false_credit_mw_slots": float(reference_false),
                "false_credit_ratio_to_reference": float(
                    contract_false / max(reference_false, 1e-9)
                ),
                "risk_profile_false_credit_mw_slots": float(risk_false),
                "risk_profile_false_credit_ratio_to_reference": float(
                    risk_false / max(reference_false, 1e-9)
                ),
                "pointwise_reference_upper_bound_satisfied": float(
                    np.all(contract_event <= reference_event + 1e-8)
                ),
                "risk_profile_distinct_from_reference": float(
                    np.max(np.abs(risk_event - reference_event)) > 1.0e-6
                ),
                "contract_scope": "locked-test audit of the separately stored payment-contract envelope; risk profile is reported without this cap",
            }
        )
    risk_audit = pd.DataFrame(risk_audit_rows)
    tail_count = max(1, int(np.ceil(0.25 * len(risk_audit))))
    final_total = float(risk_audit["final_false_credit_mw_slots"].sum())
    reference_total = float(risk_audit["reference_false_credit_mw_slots"].sum())
    final_cvar = float(
        np.mean(
            np.sort(risk_audit["final_false_credit_mw_slots"].to_numpy())[-tail_count:]
        )
    )
    reference_cvar = float(
        np.mean(
            np.sort(risk_audit["reference_false_credit_mw_slots"].to_numpy())[-tail_count:]
        )
    )
    risk_audit["test_total_final_false_credit_mw_slots"] = final_total
    risk_audit["test_total_reference_false_credit_mw_slots"] = reference_total
    risk_audit["test_cvar75_final_false_credit_mw_slots"] = final_cvar
    risk_audit["test_cvar75_reference_false_credit_mw_slots"] = reference_cvar
    risk_audit["aggregate_total_contract_satisfied"] = float(
        final_total <= reference_total + 1e-7
    )
    risk_audit["aggregate_cvar75_contract_satisfied"] = float(
        final_cvar <= reference_cvar + 1e-7
    )
    risk_profile_total = float(risk_audit["risk_profile_false_credit_mw_slots"].sum())
    risk_profile_cvar = float(
        np.mean(
            np.sort(risk_audit["risk_profile_false_credit_mw_slots"].to_numpy())[-tail_count:]
        )
    )
    risk_audit["test_total_risk_profile_false_credit_mw_slots"] = risk_profile_total
    risk_audit["test_cvar75_risk_profile_false_credit_mw_slots"] = risk_profile_cvar
    risk_audit["risk_profile_contract_comparison_is_diagnostic"] = 1.0
    risk_audit.to_csv(final / "final_risk_contract_audit.csv", index=False)

    # Preserve the two underlying truth sources in a separate locked-test
    # certificate so no aggregate threshold can conceal a source-specific
    # increase in unsupported credit.  These are meter diagnostics, not
    # utility-event treatment effects.
    truth_source_rows: list[dict[str, Any]] = []
    for local_day, day_value in enumerate(test_days):
        day = int(day_value)
        final_event = stored_baselines[local_day, final_risk_index][:, event_slots]
        reference_event = stored_baselines[local_day, final_reference_index][:, event_slots]
        for truth_source, truth_profile in [
            (observed_truth_source, observed_meter_lookup[day]),
            (actual_truth_source, actual_lookup[day]),
        ]:
            truth_event = truth_profile[:, event_slots]
            true_credit = np.maximum(honest[day][:, event_slots] - truth_event, 0.0)
            final_false_mw_slots = float(
                np.maximum(
                    np.maximum(final_event - truth_event, 0.0) - true_credit,
                    0.0,
                ).sum()
            )
            reference_false_mw_slots = float(
                np.maximum(
                    np.maximum(reference_event - truth_event, 0.0) - true_credit,
                    0.0,
                ).sum()
            )
            truth_source_rows.append(
                {
                    "day": day,
                    "truth_source": truth_source,
                    "event_intervention": False,
                    "final_false_credit_mw_slots": final_false_mw_slots,
                    "reference_false_credit_mw_slots": reference_false_mw_slots,
                    "final_false_credit_mwh": final_false_mw_slots * dt_h,
                    "reference_false_credit_mwh": reference_false_mw_slots * dt_h,
                    "true_credit_mwh": float(true_credit.sum() * dt_h),
                    "false_credit_ratio_to_reference": final_false_mw_slots
                    / max(reference_false_mw_slots, 1e-9),
                    "causal_event_effect": False,
                }
            )
    pd.DataFrame(truth_source_rows).to_csv(
        final / "risk_truth_source_audit.csv", index=False
    )

    # Reproduce the closest power/energy-domain mechanisms as exact workload
    # LP instantiations rather than comparing only generic regressors.  The
    # source rows are deliberately kept separate from the main METHODS table:
    # each comparator receives the same submitted ledger and is scored against
    # the same locked execution intervention.
    literature_specs = [
        (
            "Event-reward ledger translation",
            "chen2021incentive",
            "event_reward_ledger_lp",
            model_strategic,
            "published event-reward structure translated into the declared workload ledger: exact release, deadline, conservation, capacity, and event-reward LP; reference-specific estimator and data are not imported",
        ),
        (
            "Batch-flexibility ledger translation",
            "cao2022flexibility",
            "batch_flexibility_ledger_lp",
            model_honest,
            "published temporal-flexibility structure translated into the same exact ledger LP with workload deferral and migration; no meter outcome enters construction",
        ),
        (
            "Rolling-horizon ledger translation",
            "zhang2023receding",
            "rolling_horizon_ledger_lp",
            None,
            "validation-selected single ledger-feasible projection evaluated with the declared rolling terminal state; the comparison uses the published receding-horizon state transition, not a post-event clip",
        ),
        (
            "All-site coupled event-response control",
            "internal_event_response_control",
            "all_site_event_response_lp",
            None,
            "exact event-response LP with all four declared sites participating and the same event tariff; retained as a transparent control rather than attributed to a published implementation",
        ),
        (
            "Cross-regional dispatchable-capacity translation",
            "han2026dispatchable",
            "dispatchable_capacity_ledger_lp",
            model_honest,
            "published dispatchable-capacity constraints translated into the identical cross-regional ledger, including a common committed capacity envelope and exact service conservation",
        ),
        (
            "Coupled multi-service regulation translation",
            "chen2021idccoupling",
            "coupled_service_ledger_lp",
            None,
            "published coupled-regulation structure translated into an all-site exact event-response LP with a shared workload state; reference-specific market layers are not substituted",
        ),
    ]
    literature_rows: list[dict[str, Any]] = []
    for label, citation_key, implementation, stored_profile, description in literature_specs:
        for local_day, day_value in enumerate(test_days):
            day = int(day_value)
            if stored_profile is not None:
                candidate = stored_profile[day]
            elif implementation == "rolling_horizon_ledger_lp":
                candidate = stored_baselines[local_day, METHODS.index("Single Feasible Projection")]
            else:
                event_result = _solve_day_with_buffer(
                    arrivals_days[day],
                    prices,
                    cfg,
                    mode="event_response",
                    dr_price=float(cfg["market"]["default_dr_price_per_mwh"]),
                    participating_destinations=list(range(prices.shape[0])),
                )
                if not event_result.success:
                    raise RuntimeError(
                        f"Closest-literature event-response baseline failed on day {day}: "
                        f"{event_result.solver_message}"
                    )
                candidate = event_result.power_mw
            row = {
                "day": day,
                "baseline": label,
                "citation_key": citation_key,
                "implementation": implementation,
                "implementation_description": description,
            }
            row.update(baseline_metrics(candidate, honest[day], event_slots))
            row.update(response_metrics(candidate, honest[day], actual_lookup[day], event_slots, dt_h))
            literature_rows.append(row)
    literature_frame = pd.DataFrame(literature_rows)
    literature_frame.to_csv(final / "closest_literature_baselines.csv", index=False)
    literature_summary = (
        literature_frame.groupby(["baseline", "citation_key", "implementation"], as_index=False)
        .agg(
            n_days=("day", "nunique"),
            nrmse=("nrmse", "mean"),
            false_response_mwh=("false_response_mwh", "mean"),
            credit_f1=("credit_f1", "mean"),
            net_system_response_mwh=("net_system_response_mwh", "mean"),
        )
    )
    literature_summary.to_csv(final / "closest_literature_baselines_summary.csv", index=False)

    # Add structural workload-flexibility comparators that correspond to the
    # temporal-only and joint spatio-temporal formulations used in recent
    # security-constrained data-center scheduling work.  They share the exact
    # submitted ledger, deadlines, capacities, prices, and terminal buffer
    # with the proposed verifier.  The temporal-only model fixes each source
    # to its native destination; the joint model is the unconstrained honest
    # workload LP.  This avoids presenting a one-site event-response proxy as
    # a faithful reproduction of a multi-site coordination model.
    structural_rows: list[dict[str, Any]] = []
    source_count = int(arrivals_days.shape[2])
    destination_count = int(prices.shape[0])
    temporal_assignment = np.zeros((source_count, destination_count), dtype=bool)
    for source in range(source_count):
        temporal_assignment[source, source % destination_count] = True
    for local_day, day_value in enumerate(test_days):
        day = int(day_value)
        temporal = _solve_day_with_buffer(
            arrivals_days[day],
            prices,
            cfg,
            mode="honest",
            allowed_destinations=temporal_assignment,
        )
        if not temporal.success:
            raise RuntimeError(
                f"Temporal-only structural baseline failed on day {day}: "
                f"{temporal.solver_message}"
            )
        structural_specs = [
            (
                "Temporal-only ledger control",
                "internal_structural_control",
                temporal.power_mw,
                temporal.migrated_mwh,
                "exact workload LP with native-site assignment fixed; temporal deferral retained",
            ),
            (
                "Joint spatio-temporal ledger control",
                "internal_structural_control",
                model_honest[day],
                float(honest_migration[day]),
                "exact workload LP with temporal deferral and cross-site migration enabled",
            ),
        ]
        for label, citation_key, candidate, migration, description in structural_specs:
            row = {
                "day": day,
                "baseline": label,
                "citation_key": citation_key,
                "implementation": "exact_ledger_lp",
                "implementation_description": description,
                "migration_mwh": float(migration),
            }
            row.update(baseline_metrics(candidate, honest[day], event_slots))
            row.update(
                response_metrics(
                    candidate,
                    honest[day],
                    actual_lookup[day],
                    event_slots,
                    dt_h,
                )
            )
            structural_rows.append(row)
    structural_frame = pd.DataFrame(structural_rows)
    structural_frame.to_csv(final / "structural_literature_baselines.csv", index=False)
    structural_summary = (
        structural_frame.groupby(["baseline", "citation_key", "implementation"], as_index=False)
        .agg(
            n_days=("day", "nunique"),
            nrmse=("nrmse", "mean"),
            false_response_mwh=("false_response_mwh", "mean"),
            credit_f1=("credit_f1", "mean"),
            migration_mwh=("migration_mwh", "mean"),
        )
    )
    structural_summary.to_csv(final / "structural_literature_baselines_summary.csv", index=False)
    fairness_rows = []
    for label, access, implementation in [
        ("Single Feasible Projection", "complete submitted ledger", "exact ledger LP"),
        ("Risk-Constrained Convex Verifier", "complete submitted ledger", "validation-only convex fit + exact envelope"),
        ("Feasible Quantile Projection", "complete submitted ledger", "matched-information quantile + exact ledger LP"),
        ("Temporal-only ledger control", "complete submitted ledger", "native-site exact ledger LP"),
        ("Joint spatio-temporal ledger control", "complete submitted ledger", "joint exact ledger LP"),
        ("Post-event metadata", "complete submitted ledger", "statistical comparator"),
        ("Cross-regional dispatchable-capacity translation", "complete submitted ledger", "published-equation ledger translation"),
        ("Coupled multi-service regulation translation", "complete submitted ledger", "published-equation ledger translation"),
    ]:
        fairness_rows.append(
            {
                "baseline": label,
                "information_set": access,
                "same_arrivals": True,
                "same_deadlines": True,
                "same_site_capacity": True,
                "same_event_slots": True,
                "same_locked_days": int(len(test_days)),
                "implementation": implementation,
                "published_equation_translation": label in {
                    "Event-reward ledger translation",
                    "Batch-flexibility ledger translation",
                    "Rolling-horizon ledger translation",
                    "Cross-regional dispatchable-capacity translation",
                    "Coupled multi-service regulation translation",
                },
                "faithful_published_software_reimplementation": False,
            }
        )
    pd.DataFrame(fairness_rows).to_csv(
        final / "baseline_fairness_audit.csv", index=False
    )
    np.savez_compressed(
        intermediate / "test_profiles.npz",
        days=test_days,
        methods=np.array(METHODS),
        baselines=np.asarray(profile_baselines),
        actual=np.asarray(profile_actual),
        oracle=np.asarray(profile_oracle),
        physics_migration=np.asarray(physics_migration),
        payment_contract_profiles=np.asarray(contract_profiles),
        projection_candidates=np.asarray(profile_projection_candidates),
        projection_weights=projection_weights,
        selected_single_projection_index=np.asarray(selected_single_index),
        selected_single_projection_weight=np.asarray(selected_single_weight),
    )

    intervention_specs = [
        ("Single-site tariff 150", [0], 150.0, np.asarray(profile_actual)),
        ("All-site tariff 75", [0, 1, 2, 3], 75.0, None),
        ("All-site tariff 150", [0, 1, 2, 3], 150.0, None),
        ("All-site tariff 300", [0, 1, 2, 3], 300.0, None),
    ]
    intervention_rows: list[dict[str, Any]] = []
    intervention_methods = [
        "Feasible Quantile Projection",
        "Single Feasible Projection",
        "Tail-Risk Feasible Counterfactual",
        "Risk-Constrained Convex Verifier",
    ]
    for label, participants, dr_price, cached_actual in tqdm(
        intervention_specs,
        desc="Exp2 independent intervention objectives",
    ):
        if cached_actual is None:
            alternate_actual = []
            for day in test_days:
                result = _solve_day_with_buffer(
                    arrivals_days[int(day)],
                    prices,
                    cfg,
                    mode="event_response",
                    dr_price=float(dr_price),
                    participating_destinations=list(participants),
                )
                if not result.success:
                    raise RuntimeError(
                        f"Intervention {label} failed for day {int(day)}: "
                        f"{result.solver_message}"
                    )
                alternate_actual.append(result.power_mw)
            actual_scenario = np.asarray(alternate_actual)
        else:
            actual_scenario = cached_actual
        for day_index, day in enumerate(test_days):
            for method in intervention_methods:
                prediction = stored_baselines[
                    day_index, METHODS.index(method)
                ]
                row = {
                    "day": int(day),
                    "intervention": label,
                    "participating_destinations": ";".join(
                        map(str, participants)
                    ),
                    "dr_price_per_mwh": float(dr_price),
                    "method": method,
                }
                row.update(
                    response_metrics(
                        prediction,
                        honest[int(day)],
                        actual_scenario[day_index],
                        event_slots,
                        dt_h,
                    )
                )
                intervention_rows.append(row)
    intervention_robustness = pd.DataFrame(intervention_rows)
    intervention_robustness.to_csv(
        final / "intervention_robustness.csv", index=False
    )

    information_protocol = pd.DataFrame(
        [
            {
                "method": "High-5-of-10",
                "decision_time": "event gate",
                "historical_meter": True,
                "current_arrivals": False,
                "complete_submitted_job_ledger": False,
                "execution_truth": False,
                "workload_contract": False,
            },
            {
                "method": "Metadata Gradient Boosting",
                "decision_time": "interval online",
                "historical_meter": True,
                "current_arrivals": True,
                "complete_submitted_job_ledger": False,
                "execution_truth": False,
                "workload_contract": False,
            },
            {
                "method": "Ex-post Metadata Gradient Boosting",
                "decision_time": "post-event audit",
                "historical_meter": True,
                "current_arrivals": True,
                "complete_submitted_job_ledger": True,
                "execution_truth": False,
                "workload_contract": False,
            },
            {
                "method": "Ex-post Quantile Gradient Boosting",
                "decision_time": "post-event audit",
                "historical_meter": True,
                "current_arrivals": True,
                "complete_submitted_job_ledger": True,
                "execution_truth": False,
                "workload_contract": False,
            },
            {
                "method": "Synthetic Control",
                "decision_time": "event gate",
                "historical_meter": True,
                "current_arrivals": False,
                "complete_submitted_job_ledger": False,
                "execution_truth": False,
                "workload_contract": False,
            },
            {
                "method": "Feasible Quantile Projection",
                "decision_time": "post-event audit",
                "historical_meter": True,
                "current_arrivals": True,
                "complete_submitted_job_ledger": True,
                "execution_truth": False,
                "workload_contract": True,
            },
            {
                "method": "Tail-Risk Feasible Counterfactual",
                "decision_time": "post-event audit",
                "historical_meter": True,
                "current_arrivals": True,
                "complete_submitted_job_ledger": True,
                "execution_truth": False,
                "workload_contract": True,
            },
            {
                "method": "Single Feasible Projection",
                "decision_time": "post-event audit",
                "historical_meter": True,
                "current_arrivals": True,
                "complete_submitted_job_ledger": True,
                "execution_truth": False,
                "workload_contract": True,
            },
            {
                "method": "Risk-Constrained Convex Verifier",
                "decision_time": "post-event audit",
                "historical_meter": True,
                "current_arrivals": True,
                "complete_submitted_job_ledger": True,
                "execution_truth": False,
                "workload_contract": True,
            },
            {
                "method": "Trace-Anchored Reference",
                "decision_time": "scoring only",
                "historical_meter": True,
                "current_arrivals": True,
                "complete_submitted_job_ledger": True,
                "execution_truth": True,
                "workload_contract": True,
            },
        ]
    )
    information_protocol.to_csv(final / "information_set_audit.csv", index=False)

    ci_rows = []
    for method in METHODS:
        subset = metrics[metrics["method"] == method]
        for metric in [
            "nrmse", "bias_mw", "false_response_ratio", "false_response_mwh",
            "credit_precision", "credit_recall", "credit_f1",
        ]:
            mean, lo, hi = moving_block_bootstrap_mean_ci(
                subset[metric].to_numpy(),
                int(cfg["experiments"]["bootstrap_replications"]),
                int(cfg["experiments"]["block_length_days"]),
                int(cfg["project"]["seed"]),
            )
            ci_rows.append({"method": method, "metric": metric, "mean": mean, "ci_2.5": lo, "ci_97.5": hi})
    pd.DataFrame(ci_rows).to_csv(final / "bootstrap_confidence_intervals.csv", index=False)

    block_sensitivity_rows: list[dict[str, Any]] = []
    for block_length in cfg["experiments"].get(
        "block_length_sensitivity_days", [3, 5, 7, 10]
    ):
        for method in METHODS:
            subset = metrics[metrics["method"] == method].sort_values("day")
            for metric in ["nrmse", "false_response_ratio", "credit_f1"]:
                mean, lo, hi = moving_block_bootstrap_mean_ci(
                    subset[metric].to_numpy(),
                    int(cfg["experiments"]["bootstrap_replications"]),
                    int(block_length),
                    int(cfg["project"]["seed"]) + int(block_length),
                )
                block_sensitivity_rows.append(
                    {
                        "block_length_days": int(block_length),
                        "method": method,
                        "metric": metric,
                        "mean": mean,
                        "ci_2.5": lo,
                        "ci_97.5": hi,
                    }
                )
    pd.DataFrame(block_sensitivity_rows).to_csv(
        final / "block_length_sensitivity.csv", index=False
    )

    comparison_methods = [
        "High-5-of-10",
        "Metadata Gradient Boosting",
        "Ex-post Metadata Gradient Boosting",
        "Ex-post Quantile Gradient Boosting",
        "Synthetic Control",
        "Feasible Quantile Projection",
        "Single Feasible Projection",
    ]
    paired_rows: list[dict[str, Any]] = []
    proposed_metrics = metrics[
        metrics["method"] == "Risk-Constrained Convex Verifier"
    ].sort_values("day")
    for comparator in comparison_methods:
        compared = metrics[metrics["method"] == comparator].sort_values("day")
        if not np.array_equal(compared["day"].to_numpy(), proposed_metrics["day"].to_numpy()):
            raise RuntimeError(f"Paired-day mismatch for {comparator}")
        for metric in ["nrmse", "false_response_ratio", "credit_f1"]:
            # Positive differences always mean the proposed verifier is better.
            if metric == "credit_f1":
                differences = (
                    proposed_metrics[metric].to_numpy()
                    - compared[metric].to_numpy()
                )
                direction = "proposed_minus_comparator"
            else:
                differences = (
                    compared[metric].to_numpy()
                    - proposed_metrics[metric].to_numpy()
                )
                direction = "comparator_minus_proposed"
            test = exact_block_sign_test(
                differences,
                int(cfg["experiments"]["block_length_days"]),
            )
            paired_rows.append(
                {
                    "comparator": comparator,
                    "metric": metric,
                    "effect_direction": direction,
                    **test,
                }
            )
    paired = pd.DataFrame(paired_rows)
    paired["holm_adjusted_p_value"] = np.nan
    # nRMSE, false-credit ratio, and F1 are distinct pre-declared outcome families.
    # Holm correction is applied across all comparator hypotheses within
    # each family; pooling outcomes would answer a different joint question.
    for metric, indices in paired.groupby("metric").groups.items():
        paired.loc[indices, "holm_adjusted_p_value"] = holm_adjust(
            paired.loc[indices, "two_sided_exact_p_value"].to_numpy()
        )
    paired.to_csv(final / "paired_block_randomization_tests.csv", index=False)
    # Report effect magnitude and uncertainty, not only hypothesis-test
    # decisions. The same locked paired days, declared moving-block length, and
    # metric-wise Holm family are used as in the exact sign tests above.
    effect_rows: list[dict[str, Any]] = []
    for comparator in comparison_methods:
        compared = metrics[
            metrics["method"] == comparator
        ].sort_values("day")
        for metric in ["nrmse", "false_response_mwh", "credit_f1"]:
            proposed_values = proposed_metrics[metric].to_numpy(dtype=float)
            comparator_values = compared[metric].to_numpy(dtype=float)
            if metric == "credit_f1":
                differences = proposed_values - comparator_values
                direction = "proposed_minus_comparator"
            else:
                differences = comparator_values - proposed_values
                direction = "comparator_minus_proposed"
            difference_mean, difference_lo, difference_hi = (
                moving_block_bootstrap_mean_ci(
                    differences,
                    int(cfg["experiments"]["bootstrap_replications"]),
                    int(cfg["experiments"]["block_length_days"]),
                    int(cfg["project"]["seed"])
                    + 7000
                    + comparison_methods.index(comparator) * 10
                    + ["nrmse", "false_response_mwh", "credit_f1"].index(
                        metric
                    ),
                )
            )
            comparator_mean = float(np.mean(comparator_values))
            proposed_mean = float(np.mean(proposed_values))
            relative_improvement = (
                100.0 * difference_mean / abs(comparator_mean)
                if abs(comparator_mean) > 1e-12
                else np.nan
            )
            sign_test = exact_block_sign_test(
                differences,
                int(cfg["experiments"]["block_length_days"]),
            )
            effect_rows.append(
                {
                    "comparator": comparator,
                    "metric": metric,
                    "effect_direction": direction,
                    "comparator_mean": comparator_mean,
                    "proposed_mean": proposed_mean,
                    "paired_mean_improvement": difference_mean,
                    "relative_improvement_percent": relative_improvement,
                    "moving_block_ci_2.5": difference_lo,
                    "moving_block_ci_97.5": difference_hi,
                    **sign_test,
                }
            )
    effect_table = pd.DataFrame(effect_rows)
    effect_table["holm_adjusted_p_value"] = np.nan
    for metric, indices in effect_table.groupby("metric").groups.items():
        effect_table.loc[indices, "holm_adjusted_p_value"] = holm_adjust(
            effect_table.loc[
                indices, "two_sided_exact_p_value"
            ].to_numpy()
        )
    effect_table.to_csv(
        final / "matched_comparator_effects.csv", index=False
    )

    estimator_rows: list[dict[str, Any]] = []
    estimator_target = metrics[
        metrics["method"] == "Tail-Risk Feasible Counterfactual"
    ].sort_values("day")
    for comparator in [
        "Ex-post Metadata Gradient Boosting",
        "Ex-post Quantile Gradient Boosting",
        "Single Feasible Projection",
    ]:
        compared = metrics[metrics["method"] == comparator].sort_values(
            "day"
        )
        for metric in ["nrmse", "credit_f1"]:
            if metric == "credit_f1":
                differences = (
                    estimator_target[metric].to_numpy()
                    - compared[metric].to_numpy()
                )
                direction = "target_minus_comparator"
            else:
                differences = (
                    compared[metric].to_numpy()
                    - estimator_target[metric].to_numpy()
                )
                direction = "comparator_minus_target"
            estimator_rows.append(
                {
                    "target": "Tail-Risk Feasible Counterfactual",
                    "comparator": comparator,
                    "metric": metric,
                    "effect_direction": direction,
                    **exact_block_sign_test(
                        differences,
                        int(cfg["experiments"]["block_length_days"]),
                    ),
                }
            )
    estimator_tests = pd.DataFrame(estimator_rows)
    estimator_tests["holm_adjusted_p_value"] = np.nan
    for metric, indices in estimator_tests.groupby("metric").groups.items():
        estimator_tests.loc[indices, "holm_adjusted_p_value"] = holm_adjust(
            estimator_tests.loc[
                indices, "two_sided_exact_p_value"
            ].to_numpy()
        )
    estimator_tests.to_csv(
        final / "paired_counterfactual_block_tests.csv", index=False
    )

    ablation_daily_rows: list[dict[str, Any]] = []
    completion_horizon = (
        int(cfg["project"]["slots_per_day"])
        + int(cfg["experiments"].get("lookahead_slots", 0))
    )
    ablation_specs = [
        ("Ex-post statistical", "statistical", None),
        (
            "Release + conservation",
            "ensemble",
            {"deadlines": [completion_horizon - 1] * 3, "capacity": 1e6},
        ),
        (
            "+ Deadline constraints",
            "ensemble",
            {"deadlines": cfg["workload"]["deadlines_slots"], "capacity": 1e6},
        ),
        (
            "Full single projection",
            "single",
            {
                "deadlines": cfg["workload"]["deadlines_slots"],
                "capacity": cfg["project"]["flexible_capacity_mw"],
            },
        ),
        (
            "Tail-risk convex ensemble",
            "ensemble",
            {
                "deadlines": cfg["workload"]["deadlines_slots"],
                "capacity": cfg["project"]["flexible_capacity_mw"],
            },
        ),
        (
            "Full risk-envelope verifier",
            "safe",
            {
                "deadlines": cfg["workload"]["deadlines_slots"],
                "capacity": cfg["project"]["flexible_capacity_mw"],
            },
        ),
    ]
    cached_ablation_daily_path = final / "constraint_ablation_daily.csv"
    cached_ablation_path = final / "constraint_ablation.csv"
    reuse_cached_ablation = False
    if cached_ablation_daily_path.exists() and cached_ablation_path.exists():
        try:
            cached_ablation_daily = pd.read_csv(cached_ablation_daily_path)
            cached_ablation = pd.read_csv(cached_ablation_path)
            reuse_cached_ablation = len(cached_ablation_daily) == (
                len(test_days) * len(ablation_specs)
            )
        except (OSError, ValueError):
            cached_ablation_daily = pd.DataFrame()
            cached_ablation = pd.DataFrame()
    if reuse_cached_ablation:
        logger.info(
            "Reusing the complete constraint-ablation panel from the previous "
            "locked run; its feasible-set definitions are unchanged"
        )
        ablation_specs = []
    for label, estimator, spec in tqdm(
        ablation_specs, desc="Exp2 constraint ablations"
    ):
        for i, day in enumerate(test_days):
            day = int(day)
            stats = statistical_by_day[day]
            started = time.perf_counter()
            certificate = {
                "release_violation_mwh": np.nan,
                "deadline_violation_mwh": np.nan,
                "capacity_violation_mw": np.nan,
                "conservation_violation_mwh": np.nan,
                "certified_feasible": 0.0,
            }
            if estimator == "statistical":
                pred = stats.ex_post_metadata_gradient_boosting
            else:
                local_cfg = copy.deepcopy(cfg)
                local_cfg["workload"]["deadlines_slots"] = list(spec["deadlines"])
                local_cfg["project"]["flexible_capacity_mw"] = float(spec["capacity"])
                if estimator == "single":
                    result = _solve_day_with_buffer(
                        arrivals_days[day],
                        prices,
                        local_cfg,
                        mode="honest",
                        target=stats.ex_post_metadata_gradient_boosting,
                        projection_weight=selected_single_weight,
                    )
                    if not result.success:
                        raise RuntimeError(
                            f"Ablation {label} failed for day {day}: {result.solver_message}"
                        )
                    pred = result.power_mw
                    served = result.served_mwh
                else:
                    ensemble_pred, _, ensemble_served = _solve_convex_projection(
                        arrivals_days[day],
                        prices,
                        local_cfg,
                        stats.ex_post_metadata_gradient_boosting,
                        projection_weights,
                        ensemble_weights,
                        extra_target=(
                            stats.ex_post_quantile_gradient_boosting
                        ),
                        extra_projection_weight=(
                            selected_quantile_projection_weight
                        ),
                    )
                    if estimator == "safe":
                        risk_reference = _solve_day_with_buffer(
                            arrivals_days[day],
                            prices,
                            local_cfg,
                            mode="honest",
                            target=(
                                stats.ex_post_quantile_gradient_boosting
                            ),
                            projection_weight=(
                                selected_quantile_projection_weight
                            ),
                        )
                        if not risk_reference.success:
                            raise RuntimeError(
                                f"Ablation {label} reference failed for day {day}"
                            )
                        safe = _solve_day_with_buffer(
                            arrivals_days[day],
                            prices,
                            local_cfg,
                            mode="honest",
                            target=ensemble_pred,
                            projection_weight=selected_envelope_weight,
                            power_upper_mw=_event_risk_upper_envelope(
                                risk_reference.power_mw, local_cfg
                            ),
                            power_lower_mw=_event_risk_lower_envelope(
                                risk_reference.power_mw, local_cfg
                            ),
                        )
                        if not safe.success:
                            raise RuntimeError(
                                f"Ablation {label} failed for day {day}: "
                                f"{safe.solver_message}"
                            )
                        pred = safe.power_mw
                        served = safe.served_mwh
                    else:
                        pred = ensemble_pred
                        served = ensemble_served
                certificate = _schedule_certificate(
                    served, arrivals_days[day], cfg
                )
            elapsed = time.perf_counter() - started
            row = {
                "day": day,
                "variant": label,
                "solve_seconds": elapsed,
                "l1_adjustment_from_ex_post_statistical_mw": float(
                    np.mean(
                        np.abs(
                            pred
                            - stats.ex_post_metadata_gradient_boosting
                        )
                    )
                ),
                **certificate,
            }
            row.update(baseline_metrics(pred, honest[day], event_slots))
            row.update(
                response_metrics(
                    pred,
                    honest[day],
                    actual_lookup[day],
                    event_slots,
                    dt_h,
                )
            )
            ablation_daily_rows.append(row)
    if reuse_cached_ablation:
        ablation_daily = cached_ablation_daily
        ablation = cached_ablation
    else:
        ablation_daily = pd.DataFrame(ablation_daily_rows)
        ablation_daily.to_csv(cached_ablation_daily_path, index=False)
        ablation = (
            ablation_daily.groupby("variant", sort=False)
            .agg(
            nrmse=("nrmse", "mean"),
            false_response_ratio=("false_response_ratio", "mean"),
            credit_precision=("credit_precision", "mean"),
            credit_recall=("credit_recall", "mean"),
            credit_f1=("credit_f1", "mean"),
            certified_feasible_share=("certified_feasible", "mean"),
            max_release_violation_mwh=("release_violation_mwh", "max"),
            max_deadline_violation_mwh=("deadline_violation_mwh", "max"),
            max_capacity_violation_mw=("capacity_violation_mw", "max"),
            max_conservation_violation_mwh=("conservation_violation_mwh", "max"),
            mean_l1_adjustment_mw=(
                "l1_adjustment_from_ex_post_statistical_mw",
                "mean",
            ),
            mean_solve_seconds=("solve_seconds", "mean"),
            std=("false_response_ratio", "std"),
            )
            .reset_index()
        )
        ablation.to_csv(cached_ablation_path, index=False)

    robustness_specs: list[tuple[str, dict[str, Any] | None, str]] = [
        ("Optimization only", None, "structural"),
        ("Convex feasible ensemble", None, "ensemble"),
        ("Deadline +50%", {"deadline_scale": 1.5}, "safe"),
        ("Waiting cost -50%", {"wait_scale": 0.5}, "safe"),
        ("No site capacity", {"capacity": 1e6}, "safe"),
        *[
            (
                f"Ledger under-coverage {100 * float(fraction):.0f}%",
                {"ledger_undercoverage": float(fraction)},
                "safe",
            )
            for fraction in cfg["experiments"].get(
                "telemetry_undercoverage_fractions", [0.05, 0.10, 0.20]
            )
        ],
    ]
    cached_robustness_path = final / "specification_robustness.csv"
    reuse_cached_robustness = False
    if cached_robustness_path.exists():
        try:
            cached_robustness = pd.read_csv(cached_robustness_path)
            reuse_cached_robustness = len(cached_robustness) == (
                len(test_days) * len(robustness_specs)
            )
        except (OSError, ValueError):
            cached_robustness = pd.DataFrame()
    if reuse_cached_robustness:
        logger.info(
            "Reusing the immutable 8-scenario specification-robustness panel; "
            "the C1 risk-profile change does not alter its declared cap inputs"
        )
        robustness_specs = []
    robustness_rows = []
    for label, perturbation, estimator in tqdm(robustness_specs, desc="Exp2 specification robustness"):
        for day in test_days:
            day = int(day)
            local_cfg = copy.deepcopy(cfg)
            local_arrivals = arrivals_days[day].copy()
            if perturbation:
                if "deadline_scale" in perturbation:
                    local_cfg["workload"]["deadlines_slots"] = [
                        int(np.ceil(x * perturbation["deadline_scale"])) for x in cfg["workload"]["deadlines_slots"]
                    ]
                if "wait_scale" in perturbation:
                    local_cfg["workload"]["waiting_cost_per_mwh_slot"] = [
                        float(x * perturbation["wait_scale"]) for x in cfg["workload"]["waiting_cost_per_mwh_slot"]
                    ]
                if "capacity" in perturbation:
                    local_cfg["project"]["flexible_capacity_mw"] = float(perturbation["capacity"])
                if "ledger_undercoverage" in perturbation:
                    # Controlled incomplete-telemetry stress: every observed
                    # arrival cell is attenuated by the declared coverage rate.
                    # This is a parameterized measurement model, not a
                    # rule-based correction used by the estimator.
                    local_arrivals *= 1.0 - float(
                        perturbation["ledger_undercoverage"]
                    )
            if estimator == "structural":
                result = _solve_day_with_buffer(local_arrivals, prices, local_cfg, mode="honest")
                if not result.success:
                    raise RuntimeError(f"Robustness scenario {label} failed for day {day}: {result.solver_message}")
                prediction = result.power_mw
            else:
                ensemble_prediction, _, _ = _solve_convex_projection(
                    local_arrivals,
                    prices,
                    local_cfg,
                    statistical_by_day[day].ex_post_metadata_gradient_boosting,
                    projection_weights,
                    ensemble_weights,
                    extra_target=(
                        statistical_by_day[
                            day
                        ].ex_post_quantile_gradient_boosting
                    ),
                    extra_projection_weight=(
                        selected_quantile_projection_weight
                    ),
                )
                if estimator == "ensemble":
                    prediction = ensemble_prediction
                else:
                    risk_reference = _solve_day_with_buffer(
                        local_arrivals,
                        prices,
                        local_cfg,
                        mode="honest",
                        target=statistical_by_day[
                            day
                        ].ex_post_quantile_gradient_boosting,
                        projection_weight=(
                            selected_quantile_projection_weight
                        ),
                    )
                    if not risk_reference.success:
                        raise RuntimeError(
                            f"Robustness scenario {label} reference failed "
                            f"for day {day}: {single.solver_message}"
                        )
                    safe = _solve_day_with_buffer(
                        local_arrivals,
                        prices,
                        local_cfg,
                        mode="honest",
                        target=ensemble_prediction,
                        projection_weight=selected_envelope_weight,
                        power_upper_mw=_event_risk_upper_envelope(
                            risk_reference.power_mw, local_cfg
                        ),
                    )
                    if not safe.success:
                        raise RuntimeError(
                            f"Robustness scenario {label} envelope failed "
                            f"for day {day}: {safe.solver_message}"
                        )
                    prediction = safe.power_mw
            row = {"day": day, "scenario": label}
            row.update(baseline_metrics(prediction, honest[day], event_slots))
            row.update(response_metrics(prediction, honest[day], actual_lookup[day], event_slots, dt_h))
            robustness_rows.append(row)
        pd.DataFrame(robustness_rows).to_csv(intermediate / "specification_robustness_checkpoint.csv", index=False)
    if reuse_cached_robustness:
        robustness = cached_robustness
    else:
        robustness = pd.DataFrame(robustness_rows)
        robustness.to_csv(cached_robustness_path, index=False)

    complexity_rows: list[dict[str, Any]] = []
    source_count = arrivals_days.shape[2]
    class_count = arrivals_days.shape[3]
    destination_count = prices.shape[0]
    reference_day = int(test_days[0])
    for horizon in cfg["experiments"].get(
        "complexity_horizons_slots", [96, 192, 384, 608]
    ):
        horizon = int(horizon)
        repeated_prices = np.tile(
            prices,
            (1, int(np.ceil(horizon / prices.shape[1]))),
        )[:, :horizon]
        horizon_arrivals = np.zeros(
            (horizon, source_count, class_count), dtype=float
        )
        copied = min(horizon, arrivals_days.shape[1])
        horizon_arrivals[:copied] = arrivals_days[reference_day, :copied]
        started = time.perf_counter()
        result = solve_workload_schedule(
            horizon_arrivals,
            repeated_prices,
            cfg,
            mode="honest",
        )
        elapsed = time.perf_counter() - started
        if not result.success:
            raise RuntimeError(
                f"Complexity-scaling solve failed at T={horizon}: {result.solver_message}"
            )
        n_x = source_count * class_count * destination_count * horizon
        n_y = source_count * class_count * horizon
        release_rows = source_count * class_count * horizon
        deadline_rows = sum(
            source_count * max(0, horizon - int(deadline))
            for deadline in cfg["workload"]["deadlines_slots"]
        )
        capacity_rows = destination_count * horizon
        state_rows = source_count * class_count * horizon
        terminal_rows = source_count * class_count
        # Exact sparse nonzero count for the no-projection formulation.
        state_nonzeros = (
            source_count
            * class_count
            * (
                (1 + destination_count)
                + max(0, horizon - 1) * (2 + destination_count)
            )
        )
        nonzeros = (
            release_rows
            + deadline_rows
            + source_count * class_count * destination_count * horizon
            + state_nonzeros
            + terminal_rows
        )
        complexity_rows.append(
            {
                "horizon_slots": horizon,
                "horizon_hours": horizon * dt_h,
                "variables": n_x + n_y,
                "constraint_rows": (
                    release_rows
                    + deadline_rows
                    + capacity_rows
                    + state_rows
                    + terminal_rows
                ),
                "sparse_nonzeros": nonzeros,
                "solve_seconds": elapsed,
                "solver_success": result.success,
            }
        )
    pd.DataFrame(complexity_rows).to_csv(
        final / "complexity_scaling.csv", index=False
    )

    plot_exp2(
        metrics,
        augmented_tuning,
        ablation,
        robustness,
        folder / "figures",
        cfg,
    )
    from .visualization import plot_intervention_robustness

    plot_intervention_robustness(
        intervention_robustness, folder / "figures", cfg
    )
    write_json(
        final / "experiment_metadata.json",
        {
            "validation_days": validation_days.tolist(),
            "test_days": test_days.tolist(),
            "projection_weights": projection_weights.tolist(),
            "selected_single_projection_weight": selected_single_weight,
            "selected_quantile_projection_weight": (
                selected_quantile_projection_weight
            ),
            "risk_reserve_candidates": reserve_candidates.tolist(),
            "selected_risk_reserve_fraction": selected_reserve_fraction,
            "risk_cvar_reserve_fraction": float(selected_reserve_fraction),
            "risk_cvar_metric": str(
                cfg["experiments"].get(
                    "risk_cvar_metric", "daily_false_credit_mw_slots"
                )
            ),
            "risk_cvar_level": float(
                cfg["experiments"].get("risk_cvar_level", 0.75)
            ),
            "risk_cvar_objective_weight": float(
                cfg["experiments"].get("risk_cvar_objective_weight", 0.0)
            ),
            "risk_total_objective_weight": float(
                cfg["experiments"].get("risk_total_objective_weight", 0.0)
            ),
            "blocked_cv_cvar_reserve_fraction": float(
                cfg["experiments"].get("blocked_cv_cvar_reserve_fraction", 1.0)
            ),
            "nested_selected_risk_reserve_fraction": initial_selected_reserve_fraction,
            "pooled_validation_feasibility_gate": {
                "changed_from_nested_selection": False,
                "reason": "the pooled fit is evaluated at the nested-selected reserve; post-selection retuning is forbidden",
                "locked_test_days_consulted": False,
            },
            "risk_reserve_selection_protocol": {
                "candidate_count": int(len(reserve_candidates)),
                "validation_fold_count": int(len(fold_partitions)),
                "selection_pool_rule": (
                    "retain only candidates whose every nested contiguous fold "
                    "solves the declared total and CVaR contract; locked "
                    "non-inferiority is reported diagnostically and is not a "
                    "selection constraint; fail closed if that set is empty"
                ),
                "tie_break_order": [
                    "max_contiguous_fold_nRMSE",
                    "max_false_credit_ratio_to_reference",
                    "reserve_fraction",
                ],
                "locked_test_days_consulted": False,
                "cvar_reserve_tied_to_total_reserve": True,
                "pooled_reserve_retuning_allowed": False,
                "heldout_noninferiority_used_for_selection": False,
            },
            "selected_risk_envelope_projection_weight": (
                selected_envelope_weight
            ),
            "convex_ensemble_weights": ensemble_weights.tolist(),
            "convex_ensemble_candidate_names": risk_candidate_names,
            "structural_literature_baselines": {
                "file": "structural_literature_baselines_summary.csv",
                "citation_key": "internal_structural_control",
                "models": ["temporal-only ledger control", "joint spatio-temporal ledger control"],
                "implementation": (
                    "Both are exact workload LPs with the same release, deadline, "
                    "conservation, capacity, and terminal constraints; the temporal-only "
                    "control fixes each source to its native site and the joint control enables migration."
                ),
            },
            "baseline_fairness_audit": {
                "file": "baseline_fairness_audit.csv",
                "same_locked_days": int(len(test_days)),
                "same_workload_constraints": True,
                "published_software_reimplementations": False,
                "published_equation_translations": True,
                "interpretation": (
                    "The domain controls translate the cited objective/constraint "
                    "structures into the identical declared ledger and are named "
                    "translations, not software reproductions. Every translation "
                    "uses the same information set, locked days, physical limits, "
                    "and exact solver; the implementation boundary is explicit."
                ),
            },
            "risk_fit_certificate": risk_fit_certificate,
            "risk_cvar_stress_sensitivity_file": "risk_cvar_stress_sensitivity.csv",
            "risk_cvar_stress_sensitivity": (
                "validation-only LP frontier minimizing empirical CVaR under the total-risk "
                "budget; it is not used to select a locked-test outcome"
            ),
            "risk_credit_definition": (
                "false credit = submitted credit minus true credit after "
                "pointwise positive-part evaluation (true-credit subtraction); "
                "the oracle term is used only in locked replay diagnostics"
            ),
            "risk_credit_threshold_identity": (
                "for nonnegative true credit, the exact epigraph threshold is "
                "closed meter + true credit = max(oracle no-event baseline, closed meter); "
                "true credit is oracle no-event baseline minus closed event meter after "
                "positive-part evaluation"
            ),
            "risk_truth_source_audit_file": "risk_truth_source_audit.csv",
            "risk_truth_source_audit": (
                "separate truth-source scores: simulated mechanism-isolation "
                "credit defines the validation risk contract; the independent "
                "observed-meter score is recomputed only in locked replay"
            ),
            "risk_credit_ceiling_source": (
                "offline union ceiling for the pointwise risk fit: separate "
                "truth-source scores are retained, and there is no causal "
                "event effect"
            ),
            "risk_reference_candidate": risk_candidate_names[risk_reference_index],
            "pointwise_envelope_candidate": "Single Feasible Projection",
            "risk_profile_definition": (
                "The reported Risk-Constrained Convex Verifier is the validation-fitted "
                "simplex combination under total and daily-CVaR false-credit budgets. "
                "It is not pointwise clipped to the single projection."
            ),
            "payment_contract_profile_file": "test_profiles.npz::payment_contract_profiles",
            "payment_contract_profile_definition": (
                "A separate exact workload LP applies the selected single-projection "
                "pointwise activation cap and the risk target. It is used for the "
                "payment-band certificate, never substituted for the risk-fit result."
            ),
            "two_sided_band_tolerance_mw": float(
                cfg["experiments"].get("two_sided_band_tolerance_mw", 0.0)
            ),
            "two_sided_band_numerical_tolerance_mw": 1.0e-6,
            "two_sided_credit_certificate": (
                "The separately stored payment-contract profile is constrained by "
                "the selected single projection minus the declared physical tolerance "
                "and by the selected single projection itself on every event sample. "
                "The scientific risk profile is audited independently and is not "
                "assigned this pointwise cap."
            ),
            "selection_rule": (
                "the single-projection comparator minimizes worst nRMSE over four "
                "contiguous validation blocks; the convex verifier then minimizes "
                "event-window squared error subject to a separate false-credit "
                "budget on every validation day. A nested contiguous validation "
                "procedure selects the reserve fraction before the locked test "
                "set is opened. The reported risk profile is the direct convex "
                "risk fit; a separate exact workload LP imposes the selected "
                "single feasible projection as an upper pointwise payment cap and "
                "the independent convex target as its lower contract floor. The "
                "feasible-quantile profile is retained only as an "
                "external matched comparator, so no test-set non-inferiority is "
                "built into the evaluation. All six metadata projections and "
                "the independently selected feasible-quantile projection are retained "
                "and no test labels are used"
            ),
            "feasibility_argument": "all candidate schedules share the same linear feasible set, so their convex combination satisfies every linear workload constraint",
            "evaluation_reference": (
                "independently observed DCGM execution and BurstGPT request "
                "service are scored in trace_meter_replay.csv without an event "
                "intervention; event-response LPs are reported only in the "
                "mechanism-isolation panel"
            ),
            "scoring_truth_source": observed_truth_source,
            "mechanism_isolation_truth_source": actual_truth_source,
            "trace_meter_replay_file": "trace_meter_replay.csv",
            "event_intervention_observed": False,
            "causal_intervention_claim": False,
            "information_protocol": (
                "The main ex-post comparator, single feasible projection, and "
                "convex verifier receive the same complete submitted-job ledger; "
                "the interval-online metadata learner is reported separately."
            ),
            "terminal_condition": (
                "day-level candidate generation uses the declared "
                f"{int(cfg['experiments']['lookahead_slots'])}-slot completion "
                "window; Experiment 12 independently embeds every submitted "
                "day trajectory in a 1,216-slot continuous real-arrival horizon"
            ),
            "bootstrap_replications": int(cfg["experiments"]["bootstrap_replications"]),
            "block_length_days": int(cfg["experiments"]["block_length_days"]),
            "specification_robustness_cache_reused": bool(reuse_cached_robustness),
            "constraint_ablation_cache_reused": bool(reuse_cached_ablation),
        },
    )
    logger.info(
        "Experiment 2 complete: convex weights=%s; %d locked test days",
        np.array2string(ensemble_weights, precision=4),
        len(test_days),
    )


def _add_dc_power(base_load: np.ndarray, dc_power: np.ndarray, cfg: dict[str, Any]) -> np.ndarray:
    load = base_load.copy()
    fixed = float(cfg["project"]["fixed_facility_load_mw"])
    for d, bus in enumerate(cfg["project"]["data_center_buses"]):
        load[int(bus) - 1] += dc_power[d] - fixed
    return load


def _flexible_facility_component(
    profile_mw: np.ndarray,
    fixed_facility_load_mw: float,
    *,
    tolerance_mw: float = 1.0e-6,
) -> np.ndarray:
    """Return the declared flexible component of a facility profile.

    Workload schedules report total facility demand (fixed demand plus
    workload service).  Network conversion uncertainty applies only to the
    workload component.  A materially sub-fixed profile is a malformed
    schedule and fails closed; clipping such a profile would silently change
    the physical contract.
    """
    profile = np.asarray(profile_mw, dtype=float)
    if not np.isfinite(profile).all():
        raise ValueError("facility profile contains non-finite values")
    flexible = profile - float(fixed_facility_load_mw)
    if float(np.min(flexible, initial=0.0)) < -float(tolerance_mw):
        raise ValueError(
            "facility profile is below the fixed-load floor; cannot separate "
            "conversion-sensitive workload demand"
        )
    # Only numerical round-off is removed.  No positive-part repair is applied
    # to a substantive physical violation (checked above).
    return np.maximum(flexible, 0.0)


def _network_load_from_facility_profile(
    native_load_mw: np.ndarray,
    dc_buses: np.ndarray,
    profile_mw: np.ndarray,
    dc_scale: float,
    conversion_scale: float,
    fixed_facility_load_mw: float,
) -> np.ndarray:
    """Map a total facility profile to a network load with fixed-load separation.

    ``dc_scale`` maps the declared study envelope to the network benchmark.
    ``conversion_scale`` perturbs only flexible batch service; fixed facility
    demand is carried unchanged across conversion scenarios.
    """
    native = np.asarray(native_load_mw, dtype=float)
    buses = np.asarray(dc_buses, dtype=int)
    profile = np.asarray(profile_mw, dtype=float)
    if profile.ndim != 1 or buses.shape != profile.shape:
        raise ValueError("profile and data-center bus dimensions do not match")
    flexible = _flexible_facility_component(
        profile, fixed_facility_load_mw
    )
    load = native.copy()
    load[buses] += float(dc_scale) * (
        float(fixed_facility_load_mw) + float(conversion_scale) * flexible
    )
    return load


def _ieee118_quadratic_evaluation_system(
    settlement_system: PowerSystem,
) -> PowerSystem:
    """Retain the PGLib network but use an independent public cost model."""
    from pypower.case118 import case118

    public_quadratic = power_system_from_ppc(case118())
    if (
        public_quadratic.gencost.shape
        != settlement_system.gencost.shape
        or not np.array_equal(
            public_quadratic.gen_bus, settlement_system.gen_bus
        )
    ):
        raise RuntimeError(
            "IEEE-118 public quadratic costs do not align with PGLib "
            "generator buses"
        )
    evaluation = copy.deepcopy(settlement_system)
    evaluation.gencost = public_quadratic.gencost.copy()
    return evaluation


def run_exp3(root: Path, cfg: dict[str, Any], logger: logging.Logger) -> None:
    folder = root / "experiments/exp3_nodal_settlement"
    final = folder / "results/final"
    intermediate = folder / "results/intermediate"
    profile_path = root / "experiments/exp2_baseline_verification/results/intermediate/test_profiles.npz"
    if not profile_path.exists():
        run_exp2(root, cfg, logger)
    profiles = np.load(profile_path, allow_pickle=False)
    days = profiles["days"].astype(int)
    methods = [str(x) for x in profiles["methods"]]
    baselines = profiles["baselines"]
    actual = profiles["actual"]
    oracle = profiles["oracle"]
    _, _, _, system, base_profiles, _, _ = _inputs(root, cfg, logger)
    system = _ieee118_quadratic_evaluation_system(system)
    event_slots = list(map(int, cfg["market"]["event_slots"]))
    dc_bus_idx = np.asarray(cfg["project"]["data_center_buses"], dtype=int) - 1
    dt_h = cfg["project"]["interval_minutes"] / 60.0
    settlement_segments = int(cfg["market"]["generator_segments"])
    evaluation_segments = int(
        cfg["market"].get("evaluation_generator_segments", 80)
    )
    evaluation_system = copy.deepcopy(system)
    mechanism_names = [
        "Uniform gross",
        "Nodal gross",
        "Uniform signed net",
        "Nodal signed linear",
        "Nodal exact net value",
    ]
    evaluation_methods = methods + ["Trace-Anchored Reference"]
    rows = []
    loading_rows = []
    interval_records = []
    value_certificate_rows = []
    for i, day in enumerate(tqdm(days, desc="Exp3 network-constrained SCED")):
        daily_value = 0.0
        daily_congestion_relief = 0.0
        daily_payment = {(method, mechanism): 0.0 for method in evaluation_methods for mechanism in mechanism_names}
        for local_interval, t in enumerate(event_slots):
            actual_load = _add_dc_power(
                base_profiles[t], actual[i, :, t], cfg
            )
            oracle_load = _add_dc_power(
                base_profiles[t], oracle[i, :, t], cfg
            )
            # The market rule and the realized-value evaluator intentionally
            # use different resolutions. This removes the circular zero-error
            # comparison that would result from scoring a settlement against
            # the same piecewise-linear objective that generated it.
            sced_actual = solve_sced(
                system, actual_load, settlement_segments
            )
            sced_actual_evaluation = solve_sced(
                evaluation_system, actual_load, evaluation_segments
            )
            sced_oracle_evaluation = solve_sced(
                evaluation_system, oracle_load, evaluation_segments
            )
            realized = (
                sced_oracle_evaluation.objective
                - sced_actual_evaluation.objective
            ) * dt_h
            daily_value += realized
            daily_congestion_relief += max(
                0.0,
                sced_oracle_evaluation.max_loading
                - sced_actual_evaluation.max_loading,
            )
            for method in evaluation_methods:
                baseline = (
                    oracle[i, :, t]
                    if method == "Trace-Anchored Reference"
                    else baselines[i, methods.index(method), :, t]
                )
                sced_baseline = solve_sced(
                    system,
                    _add_dc_power(base_profiles[t], baseline, cfg),
                    settlement_segments,
                )
                delta = baseline - actual[i, :, t]
                nodal_prices = sced_baseline.lmp_per_mwh[dc_bus_idx]
                # All four linear rules use the identical event- and baseline-
                # specific price level. Differences therefore identify spatial
                # pricing and signed netting, not an arbitrary tariff scale.
                uniform_price = float(np.mean(nodal_prices))
                daily_payment[(method, "Uniform gross")] += uniform_price * np.clip(delta, 0, None).sum() * dt_h
                daily_payment[(method, "Nodal gross")] += float(
                    np.sum(nodal_prices * np.clip(delta, 0, None))
                ) * dt_h
                uniform_signed = uniform_price * float(delta.sum()) * dt_h
                nodal_signed = float(np.sum(nodal_prices * delta)) * dt_h
                exact_signed = (
                    sced_baseline.objective - sced_actual.objective
                ) * dt_h
                daily_payment[(method, "Uniform signed net")] += uniform_signed
                daily_payment[(method, "Nodal signed linear")] += nodal_signed
                # The proposed bilateral settlement is the signed, model-consistent
                # system-cost difference: positive relief earns a credit and negative
                # relief creates a debit. Baseline error still propagates because
                # sced_baseline uses the estimated counterfactual except in the
                # explicitly labeled trace-observed mechanism-isolation layer.
                daily_payment[(method, "Nodal exact net value")] += exact_signed
                # For the implemented polyhedral convex SCED value function,
                # the baseline LMP is a subgradient. Hence the signed linear
                # value globally upper-bounds the exact signed value. This
                # certificate replaces an inapplicable smooth-gradient bound.
                polyhedral_gap = nodal_signed - exact_signed
                value_certificate_rows.append(
                    {
                        "day": int(day),
                        "slot": int(t),
                        "baseline_method": method,
                        "nodal_signed_linear_usd": nodal_signed,
                        "nodal_exact_net_value_usd": exact_signed,
                        "polyhedral_bregman_gap_usd": polyhedral_gap,
                        "subgradient_inequality_violation_usd": max(
                            0.0, -polyhedral_gap
                        ),
                    }
                )
            rate = system.branch[:, 5]
            for line, loading in enumerate(
                np.abs(sced_actual_evaluation.line_flow_mw) / rate * 100
            ):
                loading_rows.append({"day": int(day), "interval": local_interval, "line": line, "loading_percent": float(loading)})
            interval_records.append(
                {
                    "day": int(day),
                    "slot": t,
                    "realized_grid_value_usd": realized,
                    "settlement_segments": settlement_segments,
                    "evaluation_segments": evaluation_segments,
                    "oracle_max_loading": sced_oracle_evaluation.max_loading,
                    "actual_max_loading": sced_actual_evaluation.max_loading,
                    "oracle_signed_response_mw": float((oracle[i, :, t] - actual[i, :, t]).sum()),
                }
            )
        for method in evaluation_methods:
            for mechanism in mechanism_names:
                payment = daily_payment[(method, mechanism)]
                rows.append(
                    {
                        "day": int(day),
                        "baseline_method": method,
                        "mechanism": mechanism,
                        "payment_usd": payment,
                        "realized_grid_value_usd": daily_value,
                        "payment_error_usd": payment - daily_value,
                        "absolute_percentage_value_error": abs(payment - daily_value) / max(abs(daily_value), 1e-9),
                        "overpayment_ratio": max(0.0, payment - daily_value)
                        / max(abs(payment), abs(daily_value), 1e-9),
                        "congestion_relief_index": daily_congestion_relief / len(event_slots),
                    }
                )
        pd.DataFrame(rows).to_csv(intermediate / "settlement_checkpoint.csv", index=False)
    settlement = pd.DataFrame(rows)
    settlement.to_csv(final / "settlement_metrics.csv", index=False)
    # Paired, day-level mechanism decomposition.  Each contrast changes one
    # settlement design axis while holding the submitted counterfactual and
    # locked day fixed; no aggregate improvement is attributed to an
    # inseparable bundle of grossing, location, and nonlinear valuation.
    factor_rows: list[dict[str, Any]] = []
    for baseline_method in evaluation_methods:
        panel = settlement[
            settlement["baseline_method"] == baseline_method
        ].pivot(
            index="day",
            columns="mechanism",
            values="payment_error_usd",
        )
        for day, errors in panel.iterrows():
            factor_rows.append(
                {
                    "day": int(day),
                    "baseline_method": baseline_method,
                    "gross_to_signed_error_reduction_usd": float(
                        abs(errors["Nodal gross"])
                        - abs(errors["Nodal signed linear"])
                    ),
                    "uniform_to_nodal_error_reduction_usd": float(
                        abs(errors["Uniform signed net"])
                        - abs(errors["Nodal signed linear"])
                    ),
                    "linear_to_exact_error_reduction_usd": float(
                        abs(errors["Nodal signed linear"])
                        - abs(errors["Nodal exact net value"])
                    ),
                    "uniform_gross_to_exact_error_reduction_usd": float(
                        abs(errors["Uniform gross"])
                        - abs(errors["Nodal exact net value"])
                    ),
                }
            )
    factor_decomposition = pd.DataFrame(factor_rows)
    factor_decomposition.to_csv(
        final / "settlement_factor_decomposition.csv", index=False
    )
    factor_columns = [
        "gross_to_signed_error_reduction_usd",
        "uniform_to_nodal_error_reduction_usd",
        "linear_to_exact_error_reduction_usd",
        "uniform_gross_to_exact_error_reduction_usd",
    ]
    factor_summary_rows: list[dict[str, Any]] = []
    for baseline_method in evaluation_methods:
        panel = factor_decomposition[
            factor_decomposition["baseline_method"] == baseline_method
        ]
        for factor in factor_columns:
            values = panel.sort_values("day")[factor].to_numpy()
            test = exact_block_sign_test(
                values,
                int(cfg["experiments"]["block_length_days"]),
            )
            factor_summary_rows.append(
                {
                    "baseline_method": baseline_method,
                    "factor": factor,
                    "mean_error_reduction_usd": float(values.mean()),
                    "median_error_reduction_usd": float(np.median(values)),
                    **test,
                }
            )
    factor_summary = pd.DataFrame(factor_summary_rows)
    factor_summary.to_csv(
        final / "settlement_factor_decomposition_summary.csv", index=False
    )
    settlement_test_rows: list[dict[str, Any]] = []
    target_mechanism = "Nodal exact net value"
    for baseline_method in evaluation_methods:
        baseline_panel = settlement[
            settlement["baseline_method"] == baseline_method
        ]
        target = (
            baseline_panel[baseline_panel["mechanism"] == target_mechanism]
            .sort_values("day")
        )
        family_indices: list[int] = []
        for comparator in mechanism_names:
            if comparator == target_mechanism:
                continue
            compared = (
                baseline_panel[baseline_panel["mechanism"] == comparator]
                .sort_values("day")
            )
            if not np.array_equal(
                target["day"].to_numpy(), compared["day"].to_numpy()
            ):
                raise RuntimeError(
                    f"Settlement paired-day mismatch for {baseline_method}"
                )
            # Positive means exact signed value has smaller absolute payment
            # error than the comparator on the same locked days.
            test = exact_block_sign_test(
                compared["payment_error_usd"].abs().to_numpy()
                - target["payment_error_usd"].abs().to_numpy(),
                int(cfg["experiments"]["block_length_days"]),
            )
            family_indices.append(len(settlement_test_rows))
            settlement_test_rows.append(
                {
                    "baseline_method": baseline_method,
                    "comparator": comparator,
                    "target": target_mechanism,
                    **test,
                    "holm_adjusted_p_value": np.nan,
                }
            )
        raw = np.asarray(
            [
                settlement_test_rows[index]["two_sided_exact_p_value"]
                for index in family_indices
            ]
        )
        adjusted = holm_adjust(raw)
        for index, value in zip(family_indices, adjusted):
            settlement_test_rows[index]["holm_adjusted_p_value"] = float(value)
    pd.DataFrame(settlement_test_rows).to_csv(
        final / "paired_settlement_block_tests.csv", index=False
    )
    pd.DataFrame(interval_records).to_csv(final / "interval_grid_value.csv", index=False)
    value_certificates = pd.DataFrame(value_certificate_rows)
    value_certificates.to_csv(
        final / "polyhedral_value_certificates.csv", index=False
    )
    if (
        value_certificates["subgradient_inequality_violation_usd"].max()
        > 1e-6
    ):
        raise RuntimeError(
            "SCED polyhedral subgradient certificate violated beyond tolerance"
        )
    loading = pd.DataFrame(loading_rows)
    loading.to_csv(intermediate / "line_loading_all_days.csv", index=False)
    loading_mean = loading.groupby(["interval", "line"], as_index=False)["loading_percent"].mean()
    loading_mean.to_csv(final / "mean_line_loading.csv", index=False)
    write_json(final / "experiment_metadata.json", {
        "days": days.tolist(),
        "baseline_methods": evaluation_methods,
        "settlement_mechanisms": mechanism_names,
        "price_control": "all linear mechanisms use the same baseline- and interval-specific mean nodal price",
        "settlement_generator_segments": settlement_segments,
        "independent_evaluation_generator_segments": evaluation_segments,
        "independent_value_evaluation": (
            "both layers retain the PGLib topology, generator capacities, and "
            "native line ratings and use the independently published PYPOWER "
            "IEEE-118 quadratic cost curves aligned by generator bus; payments "
            "use 10 segments while realized value is independently re-solved "
            "with 80 segments"
        ),
        "mechanism_isolation_baseline": "Trace-Anchored Reference",
        "end_to_end_baseline": "Risk-Constrained Convex Verifier",
        "nodal_net_value_rule": "signed SCED avoided cost; credits positive value and debits negative value",
        "polyhedral_value_certificate": (
            "for every interval and baseline, baseline-LMP signed linear value "
            "minus exact signed value is the nonnegative convex Bregman gap"
        ),
        "settlement_schema_version": SETTLEMENT_SCHEMA_VERSION,
    })
    plot_exp3(settlement, loading_mean, folder / "figures", cfg)
    from .visualization import plot_settlement_factor_decomposition

    plot_settlement_factor_decomposition(
        factor_decomposition, folder / "figures", cfg
    )
    logger.info("Experiment 3 complete: %d day-mechanism settlement outcomes", len(settlement))


def run_exp4(root: Path, cfg: dict[str, Any], logger: logging.Logger) -> None:
    folder = root / "experiments/exp4_case_study"
    final = folder / "results/final"
    intermediate = folder / "results/intermediate"
    profile_path = root / "experiments/exp2_baseline_verification/results/intermediate/test_profiles.npz"
    if not profile_path.exists():
        run_exp2(root, cfg, logger)
    profiles = np.load(profile_path, allow_pickle=False)
    days = profiles["days"].astype(int)
    actual = profiles["actual"]
    oracle = profiles["oracle"]
    event_slots = list(map(int, cfg["market"]["event_slots"]))
    signed = oracle[:, :, event_slots] - actual[:, :, event_slots]
    spatial_offset = np.clip(signed, 0, None).sum(axis=(1, 2)) - np.clip(signed.sum(axis=1), 0, None).sum(axis=1)
    case_candidates = pd.DataFrame(
        {
            "day": days,
            "gross_positive_response_mw_intervals": np.clip(
                signed, 0, None
            ).sum(axis=(1, 2)),
            "net_positive_response_mw_intervals": np.clip(
                signed.sum(axis=1), 0, None
            ).sum(axis=1),
            "spatial_offset_mw_intervals": spatial_offset,
        }
    )
    case_candidates["selected"] = (
        case_candidates["spatial_offset_mw_intervals"]
        == case_candidates["spatial_offset_mw_intervals"].max()
    ).astype(int)
    case_candidates.to_csv(
        intermediate / "case_selection_candidates.csv", index=False
    )
    selected_idx = int(np.argmax(spatial_offset))
    selected_day = int(days[selected_idx])
    rows = []
    for d, bus in enumerate(cfg["project"]["data_center_buses"]):
        for t in range(actual.shape[2]):
            rows.append(
                {
                    "day": selected_day,
                    "slot": t,
                    "data_center": f"DC{d + 1}@Bus{bus}",
                    "oracle_baseline_mw": float(oracle[selected_idx, d, t]),
                    "actual_mw": float(actual[selected_idx, d, t]),
                    "nodal_response_mw": float(oracle[selected_idx, d, t] - actual[selected_idx, d, t]),
                    "is_event": int(t in event_slots),
                }
            )
    timeseries = pd.DataFrame(rows)
    timeseries.to_csv(final / "spatial_case_timeseries.csv", index=False)
    _, _, _, system, _, _, _ = _inputs(root, cfg, logger)
    plot_case_study(
        timeseries,
        {"branch": system.branch, "bus": system.bus},
        list(map(int, cfg["project"]["data_center_buses"])),
        folder / "figures",
        cfg,
    )
    summary = (
        timeseries[timeseries["is_event"] == 1]
        .groupby("data_center")
        .agg(
            mean_oracle_mw=("oracle_baseline_mw", "mean"),
            mean_actual_mw=("actual_mw", "mean"),
            mean_nodal_response_mw=("nodal_response_mw", "mean"),
        )
        .reset_index()
    )
    summary.to_csv(final / "case_summary_by_data_center.csv", index=False)
    write_json(
        final / "case_metadata.json",
        {
            "selected_day": selected_day,
            "selection_rule": "largest gross-minus-net spatial response offset in the locked test set",
            "spatial_offset_mw_intervals": float(spatial_offset[selected_idx]),
            "event_slots": event_slots,
        },
    )
    logger.info("Experiment 4 complete: selected day %d for strongest spatial offset", selected_day)


def _benchmark_networks(root: Path) -> list[tuple[str, PowerSystem, list[int]]]:
    from pypower.case24_ieee_rts import case24_ieee_rts
    from pypower.case39 import case39
    from pypower.case300 import case300

    return [
        ("IEEE RTS 24-bus", power_system_from_ppc(case24_ieee_rts()), [2, 7, 14, 20]),
        ("IEEE 39-bus", power_system_from_ppc(case39()), [3, 14, 25, 38]),
        (
            "PGLib IEEE 118-bus",
            parse_pglib_case(root / "data/raw/pglib/pglib_opf_case118_ieee.m"),
            [14, 41, 79, 115],
        ),
        ("IEEE 300-bus", power_system_from_ppc(case300()), [19, 89, 169, 259]),
    ]


def _exp5_day_rows(
    task: tuple[Any, ...],
) -> list[dict[str, Any]]:
    """Solve one Exp5 day exactly; parallelism is only across independent days."""
    (
        name, system, evaluation_system, native, dc_idx, dc_scale, local_day,
        day, multiplier, predicted_day, actual_day, oracle_day, event_slots, dt_h,
        settlement_segments, evaluation_segments, native_max_loading,
        native_congested_lines, selected_line, rating_factor, baseline_qualities,
        mechanisms, panel_checksum, estimator_checksum,
    ) = task
    payment = {(quality, mechanism): 0.0 for quality in baseline_qualities for mechanism in mechanisms}
    realized = 0.0
    congested = 0
    for slot in event_slots:
        load_truth = native.copy()
        load_actual = native.copy()
        load_pred = native.copy()
        load_truth[dc_idx] += oracle_day[:, slot] * dc_scale
        load_actual[dc_idx] += actual_day[:, slot] * dc_scale
        load_pred[dc_idx] += predicted_day[:, slot] * dc_scale
        sced_truth = solve_sced(system, load_truth, settlement_segments)
        sced_actual = solve_sced(system, load_actual, settlement_segments)
        sced_pred = solve_sced(system, load_pred, settlement_segments)
        sced_truth_eval = solve_sced(evaluation_system, load_truth, evaluation_segments)
        sced_actual_eval = solve_sced(evaluation_system, load_actual, evaluation_segments)
        realized += (sced_truth_eval.objective - sced_actual_eval.objective) * dt_h
        congested += int(sced_actual_eval.congested_lines > 0)
        for quality, baseline_profile, baseline_sced in [
            ("Trace-Anchored Reference", oracle_day[:, slot], sced_truth),
            ("Risk-Constrained Convex Verifier", predicted_day[:, slot], sced_pred),
        ]:
            delta = (baseline_profile - actual_day[:, slot]) * dc_scale
            nodal = baseline_sced.lmp_per_mwh[dc_idx]
            uniform = float(nodal.mean())
            payment[(quality, "Uniform gross")] += uniform * np.clip(delta, 0, None).sum() * dt_h
            payment[(quality, "Nodal gross")] += float(np.sum(nodal * np.clip(delta, 0, None))) * dt_h
            payment[(quality, "Uniform signed net")] += uniform * float(delta.sum()) * dt_h
            payment[(quality, "Nodal signed linear")] += float(np.sum(nodal * delta)) * dt_h
            payment[(quality, "Nodal exact net value")] += (baseline_sced.objective - sced_actual.objective) * dt_h
    rows: list[dict[str, Any]] = []
    for (quality, mechanism), amount in payment.items():
        rows.append({
            "network": name,
            "load_multiplier": float(multiplier),
            "day": int(day),
            "mechanism": mechanism,
            "baseline_quality": quality,
            "payment_usd": amount,
            "realized_grid_value_usd": realized,
            "absolute_error_usd": abs(amount - realized),
            "normalized_absolute_error": abs(amount - realized) / max(abs(realized), 1e-9),
            "overpayment_usd": max(0.0, amount - realized),
            "congested_interval_share": congested / len(event_slots),
            "native_max_line_loading": native_max_loading,
            "native_congested_lines": native_congested_lines,
            "peak_dc_penetration_of_native_load": 0.06,
            "thermal_rating_normalization_factor": float(rating_factor),
            "selected_critical_line": selected_line,
            "data_center_bus_indices_zero_based": ";".join(map(str, dc_idx.tolist())),
            "settlement_schema_version": SETTLEMENT_SCHEMA_VERSION,
            "settlement_generator_segments": settlement_segments,
            "evaluation_generator_segments": evaluation_segments,
            "estimator_checksum": estimator_checksum,
            "checkpoint_schema_version": 2,
            "panel_checksum": panel_checksum,
        })
    return rows


def _run_exp5_resolution_convergence(
    root: Path,
    cfg: dict[str, Any],
    days: np.ndarray,
    predicted: np.ndarray,
    actual: np.ndarray,
    oracle: np.ndarray,
    logger: logging.Logger,
    resume: bool,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Evaluate the complete locked set across increasing SCED resolutions."""
    from pypower.case24_ieee_rts import case24_ieee_rts

    folder = root / "experiments/exp5_network_robustness"
    intermediate = folder / "results/intermediate"
    final = folder / "results/final"
    checkpoint = intermediate / "resolution_convergence_checkpoint.csv"
    pairs = [
        (int(pair[0]), int(pair[1]))
        for pair in cfg["experiments"]["cross_network_resolution_pairs"]
    ]
    if len(set(pairs)) != len(pairs) or any(
        settlement <= 0 or evaluation <= settlement
        for settlement, evaluation in pairs
    ):
        raise ValueError("Invalid cross-network resolution pairs")
    system = power_system_from_ppc(case24_ieee_rts())
    native = system.bus[:, 2] * 0.98
    dc_buses = np.asarray([2, 7, 14, 20], dtype=int)
    event_slots = list(map(int, cfg["market"]["event_slots"]))
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    peak_dc_mw = 0.06 * float(native.sum())
    peak_trace_mw = float(
        max(
            oracle[:, :, event_slots].sum(axis=1).max(),
            actual[:, :, event_slots].sum(axis=1).max(),
            predicted[:, :, event_slots].sum(axis=1).max(),
        )
    )
    dc_scale = peak_dc_mw / max(peak_trace_mw, 1e-12)
    checkpoint_schema_version = 1
    panel_checksum = hashlib.sha256(
        np.ascontiguousarray(days, dtype=np.int64).tobytes()
        + np.ascontiguousarray(predicted, dtype=np.float64).tobytes()
        + np.ascontiguousarray(actual, dtype=np.float64).tobytes()
        + np.ascontiguousarray(oracle, dtype=np.float64).tobytes()
        + np.ascontiguousarray(pairs, dtype=np.int64).tobytes()
    ).hexdigest()
    rows: list[dict[str, Any]] = []
    completed: set[tuple[int, int, int]] = set()
    if resume and checkpoint.exists():
        previous = pd.read_csv(checkpoint)
        valid_checkpoint = (
            "checkpoint_schema_version" in previous
            and set(
                previous["checkpoint_schema_version"].astype(int).unique()
            )
            == {checkpoint_schema_version}
            and "panel_checksum" in previous
            and set(previous["panel_checksum"].astype(str).unique())
            == {panel_checksum}
        )
        if valid_checkpoint:
            active_days = set(map(int, days))
            previous = previous[
                previous["day"].astype(int).isin(active_days)
            ].drop_duplicates(
                ["day", "settlement_segments", "evaluation_segments"],
                keep="last",
            )
            completed = set(
                zip(
                    previous["day"].astype(int),
                    previous["settlement_segments"].astype(int),
                    previous["evaluation_segments"].astype(int),
                )
            )
            rows = previous.to_dict("records")
            logger.info(
                "Resuming Experiment 5 resolution convergence with %d cells",
                len(completed),
            )
        else:
            logger.info(
                "Discarding stale Experiment 5 resolution checkpoint"
            )

    def solve_resolution_cell(
        item: tuple[int, int, int, int],
    ) -> dict[str, Any]:
        local_day, day, settlement_segments, evaluation_segments = item
        linear_payment = 0.0
        exact_payment = 0.0
        realized_value = 0.0
        for slot in event_slots:
            truth_load = native.copy()
            actual_load = native.copy()
            predicted_load = native.copy()
            truth_load[dc_buses] += oracle[local_day, :, slot] * dc_scale
            actual_load[dc_buses] += actual[local_day, :, slot] * dc_scale
            predicted_load[dc_buses] += (
                predicted[local_day, :, slot] * dc_scale
            )
            predicted_settlement = solve_sced(
                system, predicted_load, settlement_segments
            )
            actual_settlement = solve_sced(
                system, actual_load, settlement_segments
            )
            truth_evaluation = solve_sced(
                system, truth_load, evaluation_segments
            )
            actual_evaluation = solve_sced(
                system, actual_load, evaluation_segments
            )
            delta = (
                predicted[local_day, :, slot]
                - actual[local_day, :, slot]
            ) * dc_scale
            linear_payment += float(
                predicted_settlement.lmp_per_mwh[dc_buses] @ delta
            ) * dt_h
            exact_payment += (
                predicted_settlement.objective
                - actual_settlement.objective
            ) * dt_h
            realized_value += (
                truth_evaluation.objective - actual_evaluation.objective
            ) * dt_h
        return {
            "day": int(day),
            "network": "IEEE RTS 24-bus",
            "load_multiplier": 0.98,
            "settlement_segments": int(settlement_segments),
            "evaluation_segments": int(evaluation_segments),
            "linear_absolute_error_usd": float(
                abs(linear_payment - realized_value)
            ),
            "exact_absolute_error_usd": float(
                abs(exact_payment - realized_value)
            ),
            "linear_minus_exact_error_usd": float(
                abs(linear_payment - realized_value)
                - abs(exact_payment - realized_value)
            ),
            "checkpoint_schema_version": checkpoint_schema_version,
            "panel_checksum": panel_checksum,
        }

    tasks = [
        (local_day, int(day), settlement, evaluation)
        for local_day, day in enumerate(days)
        for settlement, evaluation in pairs
        if (int(day), settlement, evaluation) not in completed
    ]
    workers = int(
        cfg["experiments"].get("cross_network_resolution_workers", 4)
    )
    if workers <= 0:
        raise ValueError("cross_network_resolution_workers must be positive")
    progress = tqdm(
        total=len(days) * len(pairs),
        initial=len(completed),
        desc="Exp5 RTS-24 resolution convergence",
    )
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for row in executor.map(solve_resolution_cell, tasks):
            rows.append(row)
            pd.DataFrame(rows).to_csv(checkpoint, index=False)
            progress.update(1)
    progress.close()
    daily = pd.DataFrame(rows).sort_values(
        ["settlement_segments", "day"]
    )
    expected_keys = {
        (int(day), settlement, evaluation)
        for day in days
        for settlement, evaluation in pairs
    }
    observed_keys = set(
        zip(
            daily["day"].astype(int),
            daily["settlement_segments"].astype(int),
            daily["evaluation_segments"].astype(int),
        )
    )
    if len(daily) != len(expected_keys) or observed_keys != expected_keys:
        raise RuntimeError(
            "Incomplete Experiment 5 resolution panel: "
            f"{len(daily)}/{len(expected_keys)}"
        )
    daily.to_csv(final / "resolution_convergence_daily.csv", index=False)
    summary = (
        daily.groupby(
            ["network", "load_multiplier", "settlement_segments", "evaluation_segments"],
            as_index=False,
        )
        .agg(
            mean_linear_minus_exact_error_usd_day=(
                "linear_minus_exact_error_usd", "mean"
            ),
            standard_deviation_usd_day=(
                "linear_minus_exact_error_usd", "std"
            ),
            positive_days=(
                "linear_minus_exact_error_usd",
                lambda values: int(np.sum(np.asarray(values) > 0)),
            ),
            minimum_daily_effect_usd=(
                "linear_minus_exact_error_usd", "min"
            ),
            maximum_daily_effect_usd=(
                "linear_minus_exact_error_usd", "max"
            ),
        )
    )
    summary["standard_error_usd_day"] = (
        summary["standard_deviation_usd_day"] / np.sqrt(len(days))
    )
    summary.to_csv(final / "resolution_convergence_summary.csv", index=False)
    return daily, summary


def run_exp5(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
    resume: bool = False,
) -> None:
    """Cross-network, cross-loading validation of the settlement claim."""
    folder = root / "experiments/exp5_network_robustness"
    final = folder / "results/final"
    intermediate = folder / "results/intermediate"
    final.mkdir(parents=True, exist_ok=True)
    intermediate.mkdir(parents=True, exist_ok=True)
    profile_path = root / "experiments/exp2_baseline_verification/results/intermediate/test_profiles.npz"
    if not profile_path.exists():
        run_exp2(root, cfg, logger)
    profiles = np.load(profile_path, allow_pickle=False)
    days = profiles["days"].astype(int)
    methods = [str(x) for x in profiles["methods"]]
    proposed_idx = methods.index("Risk-Constrained Convex Verifier")
    predicted = profiles["baselines"][:, proposed_idx]
    estimator_checksum = hashlib.sha256(np.ascontiguousarray(predicted).tobytes()).hexdigest()
    actual = profiles["actual"]
    oracle = profiles["oracle"]
    event_slots = list(map(int, cfg["market"]["event_slots"]))
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    settlement_segments = int(cfg["market"]["generator_segments"])
    evaluation_segments = int(
        cfg["market"].get(
            "cross_network_evaluation_generator_segments", 40
        )
    )
    mechanisms = [
        "Uniform gross",
        "Nodal gross",
        "Uniform signed net",
        "Nodal signed linear",
        "Nodal exact net value",
    ]
    baseline_qualities = [
        "Trace-Anchored Reference",
        "Risk-Constrained Convex Verifier",
    ]
    declared_scenario_keys = {
        (name, float(multiplier))
        for name, _, _ in _benchmark_networks(root)
        for multiplier in cfg["experiments"]["network_load_multipliers"]
    }
    checkpoint_path = intermediate / "network_robustness_checkpoint.csv"
    checkpoint_schema_version = 2
    panel_checksum = hashlib.sha256(
        np.ascontiguousarray(days, dtype=np.int64).tobytes()
        + np.ascontiguousarray(predicted, dtype=np.float64).tobytes()
        + np.ascontiguousarray(actual, dtype=np.float64).tobytes()
        + np.ascontiguousarray(oracle, dtype=np.float64).tobytes()
        + np.ascontiguousarray(
            [settlement_segments, evaluation_segments], dtype=np.int64
        ).tobytes()
        + np.ascontiguousarray(
            cfg["experiments"]["network_load_multipliers"],
            dtype=np.float64,
        ).tobytes()
    ).hexdigest()
    rows: list[dict[str, Any]] = []
    if resume and checkpoint_path.exists():
        prior = pd.read_csv(checkpoint_path)
        if (
            "settlement_schema_version" in prior.columns
            and set(prior["settlement_schema_version"].unique()) == {SETTLEMENT_SCHEMA_VERSION}
            and "estimator_checksum" in prior.columns
            and set(prior["estimator_checksum"].unique()) == {estimator_checksum}
            and "checkpoint_schema_version" in prior.columns
            and set(prior["checkpoint_schema_version"].astype(int).unique())
            == {checkpoint_schema_version}
            and "panel_checksum" in prior.columns
            and set(prior["panel_checksum"].astype(str).unique())
            == {panel_checksum}
        ):
            prior = prior.drop_duplicates(
                ["network", "load_multiplier", "day", "baseline_quality", "mechanism"],
                keep="last",
            )
            required = len(days) * len(mechanisms) * len(baseline_qualities)
            complete = prior.groupby(["network", "load_multiplier"]).size()
            keep_keys = (
                set(complete[complete == required].index.tolist())
                & declared_scenario_keys
            )
            if keep_keys:
                prior = prior[
                    prior.apply(lambda x: (x["network"], x["load_multiplier"]) in keep_keys, axis=1)
                ]
                rows = prior.to_dict("records")
                logger.info("Resuming Experiment 5 with %d complete scenario rows", len(rows))
        else:
            logger.info("Discarding stale Experiment 5 settlement checkpoint")
    scenarios = [
        (name, system, buses, float(multiplier))
        for name, system, buses in _benchmark_networks(root)
        for multiplier in cfg["experiments"]["network_load_multipliers"]
    ]
    for name, system, fixed_buses, multiplier in tqdm(
        scenarios, desc="Exp5 native-rating network/loading scenarios"
    ):
        if sum(1 for row in rows if row["network"] == name and row["load_multiplier"] == multiplier) == len(days) * len(mechanisms) * len(baseline_qualities):
            continue
        system = copy.deepcopy(system)
        if name == "PGLib IEEE 118-bus":
            system = _ieee118_quadratic_evaluation_system(system)
        evaluation_system = copy.deepcopy(system)
        native = system.bus[:, 2] * multiplier
        native_dispatch = solve_sced(system, native, int(cfg["market"]["generator_segments"]))
        peak_share_mw = 0.06 * float(native.sum())
        original_rate = system.branch[:, 5].copy()
        safe_rate = original_rate.copy()
        safe_rate[safe_rate <= 0] = 1e6
        native_loading = np.abs(native_dispatch.line_flow_mw) / safe_rate
        selected_line = int(np.argmax(native_loading))
        dc_idx = np.asarray(fixed_buses, dtype=int)
        # Sites and all thermal ratings are fixed before observing any workload
        # outcome. Feasibility is checked for the declared 6% equal-share design;
        # no branch is derated and no PTDF-based site selection is performed.
        design_load = native.copy()
        design_load[dc_idx] += peak_share_mw / len(dc_idx)
        solve_sced(system, design_load, int(cfg["market"]["generator_segments"]))
        rating_factor = 1.0
        peak_profile = float(max(
            oracle[:, :, event_slots].sum(axis=1).max(),
            actual[:, :, event_slots].sum(axis=1).max(),
            predicted[:, :, event_slots].sum(axis=1).max(),
        ))
        dc_scale = peak_share_mw / max(peak_profile, 1e-9)
        parallel_workers = int(cfg["experiments"].get("network_robustness_workers", 1))
        if parallel_workers > 1:
            completed_days = {
                int(row["day"])
                for row in rows
                if row["network"] == name and float(row["load_multiplier"]) == multiplier
            }
            tasks = [
                (
                    name, system, evaluation_system, native, dc_idx, dc_scale, i,
                    int(day), multiplier, predicted[i], actual[i], oracle[i],
                    event_slots, dt_h, settlement_segments, evaluation_segments,
                    native_dispatch.max_loading, native_dispatch.congested_lines,
                    selected_line, rating_factor, baseline_qualities, mechanisms,
                    panel_checksum, estimator_checksum,
                )
                for i, day in enumerate(days)
                if int(day) not in completed_days
            ]
            if tasks:
                with ThreadPoolExecutor(max_workers=parallel_workers) as executor:
                    for day_rows in executor.map(_exp5_day_rows, tasks):
                        rows.extend(day_rows)
                        pd.DataFrame(rows).to_csv(checkpoint_path, index=False)
            continue
        for i, day in enumerate(days):
            payment = {(quality, m): 0.0 for quality in baseline_qualities for m in mechanisms}
            realized = 0.0
            congested = 0
            for t in event_slots:
                load_truth = native.copy()
                load_actual = native.copy()
                load_pred = native.copy()
                load_truth[dc_idx] += oracle[i, :, t] * dc_scale
                load_actual[dc_idx] += actual[i, :, t] * dc_scale
                load_pred[dc_idx] += predicted[i, :, t] * dc_scale
                sced_truth = solve_sced(
                    system, load_truth, settlement_segments
                )
                sced_actual = solve_sced(
                    system, load_actual, settlement_segments
                )
                sced_pred = solve_sced(
                    system, load_pred, settlement_segments
                )
                sced_truth_evaluation = solve_sced(
                    evaluation_system, load_truth, evaluation_segments
                )
                sced_actual_evaluation = solve_sced(
                    evaluation_system, load_actual, evaluation_segments
                )
                realized += (
                    sced_truth_evaluation.objective
                    - sced_actual_evaluation.objective
                ) * dt_h
                congested += int(
                    sced_actual_evaluation.congested_lines > 0
                )
                for quality, baseline_profile, baseline_sced in [
                    ("Trace-Anchored Reference", oracle[i, :, t], sced_truth),
                    (
                        "Risk-Constrained Convex Verifier",
                        predicted[i, :, t],
                        sced_pred,
                    ),
                ]:
                    delta = (baseline_profile - actual[i, :, t]) * dc_scale
                    nodal = baseline_sced.lmp_per_mwh[dc_idx]
                    uniform = float(nodal.mean())
                    payment[(quality, "Uniform gross")] += uniform * np.clip(delta, 0, None).sum() * dt_h
                    payment[(quality, "Nodal gross")] += float(np.sum(nodal * np.clip(delta, 0, None))) * dt_h
                    payment[(quality, "Uniform signed net")] += (
                        uniform * float(delta.sum()) * dt_h
                    )
                    payment[(quality, "Nodal signed linear")] += (
                        float(np.sum(nodal * delta)) * dt_h
                    )
                    payment[(quality, "Nodal exact net value")] += (
                        baseline_sced.objective - sced_actual.objective
                    ) * dt_h
            for (quality, mechanism), amount in payment.items():
                rows.append({
                    "network": name,
                    "load_multiplier": multiplier,
                    "day": int(day),
                    "mechanism": mechanism,
                    "baseline_quality": quality,
                    "payment_usd": amount,
                    "realized_grid_value_usd": realized,
                    "absolute_error_usd": abs(amount - realized),
                    "normalized_absolute_error": abs(amount - realized) / max(abs(realized), 1e-9),
                    "overpayment_usd": max(0.0, amount - realized),
                    "congested_interval_share": congested / len(event_slots),
                    "native_max_line_loading": native_dispatch.max_loading,
                    "native_congested_lines": native_dispatch.congested_lines,
                    "peak_dc_penetration_of_native_load": 0.06,
                    "thermal_rating_normalization_factor": rating_factor,
                    "selected_critical_line": selected_line,
                    "data_center_bus_indices_zero_based": ";".join(map(str, dc_idx.tolist())),
                    "settlement_schema_version": SETTLEMENT_SCHEMA_VERSION,
                    "settlement_generator_segments": settlement_segments,
                    "evaluation_generator_segments": evaluation_segments,
                    "estimator_checksum": estimator_checksum,
                    "checkpoint_schema_version": checkpoint_schema_version,
                    "panel_checksum": panel_checksum,
                })
        pd.DataFrame(rows).to_csv(checkpoint_path, index=False)
    results = pd.DataFrame(rows).sort_values(
        ["network", "load_multiplier", "day", "baseline_quality", "mechanism"]
    )
    expected_keys = {
        (name, float(multiplier), int(day), quality, mechanism)
        for name, _, _ in _benchmark_networks(root)
        for multiplier in cfg["experiments"]["network_load_multipliers"]
        for day in days
        for quality in baseline_qualities
        for mechanism in mechanisms
    }
    observed_keys = set(
        zip(
            results["network"].astype(str),
            results["load_multiplier"].astype(float),
            results["day"].astype(int),
            results["baseline_quality"].astype(str),
            results["mechanism"].astype(str),
        )
    )
    if len(results) != len(expected_keys) or observed_keys != expected_keys:
        raise RuntimeError(
            "Incomplete cross-network panel: "
            f"{len(results)}/{len(expected_keys)}"
        )
    results.to_csv(final / "network_robustness.csv", index=False)
    paired_network_rows: list[dict[str, Any]] = []
    for quality in baseline_qualities:
        family_indices: list[int] = []
        for (name, multiplier), panel in results[
            results["baseline_quality"] == quality
        ].groupby(["network", "load_multiplier"]):
            exact = panel[
                panel["mechanism"] == "Nodal exact net value"
            ].sort_values(
                "day"
            )
            linear = panel[
                panel["mechanism"] == "Nodal signed linear"
            ].sort_values("day")
            if not np.array_equal(
                exact["day"].to_numpy(), linear["day"].to_numpy()
            ):
                raise RuntimeError(
                    f"Network paired-day mismatch for {name}, {multiplier}"
                )
            test = exact_block_sign_test(
                linear["absolute_error_usd"].to_numpy()
                - exact["absolute_error_usd"].to_numpy(),
                int(cfg["experiments"]["block_length_days"]),
            )
            family_indices.append(len(paired_network_rows))
            paired_network_rows.append(
                {
                    "network": name,
                    "load_multiplier": float(multiplier),
                    "baseline_quality": quality,
                    "comparator": "Nodal signed linear",
                    "target": "Nodal exact net value",
                    **test,
                    "holm_adjusted_p_value": np.nan,
                }
            )
        adjusted = holm_adjust(
            np.asarray(
                [
                    paired_network_rows[index][
                        "two_sided_exact_p_value"
                    ]
                    for index in family_indices
                ]
            )
        )
        for index, value in zip(family_indices, adjusted):
            paired_network_rows[index]["holm_adjusted_p_value"] = float(value)
    pd.DataFrame(paired_network_rows).to_csv(
        final / "paired_network_block_tests.csv", index=False
    )
    summary = results.groupby(["network", "load_multiplier", "baseline_quality", "mechanism"], as_index=False).agg(
        mean_absolute_error_usd=("absolute_error_usd", "mean"),
        median_normalized_error=("normalized_absolute_error", "median"),
        mean_overpayment_usd=("overpayment_usd", "mean"),
        congestion_share=("congested_interval_share", "mean"),
    )
    summary.to_csv(final / "network_robustness_summary.csv", index=False)
    _, resolution_summary = _run_exp5_resolution_convergence(
        root, cfg, days, predicted, actual, oracle, logger, resume
    )
    write_json(final / "experiment_metadata.json", {
        "networks": [name for name, _, _ in _benchmark_networks(root)],
        "data_center_placement_rule": (
            "four fixed, pre-declared bus indices per public benchmark; "
            "placement is invariant to all workload and settlement outcomes"
        ),
        "network_parameter_rule": (
            "all public-case thermal ratings retained exactly; no line derating "
            "or outcome-conditioned congestion construction"
        ),
        "feasibility_design": "6% DC peak distributed equally over the four fixed sites",
        "native_load_multipliers": cfg["experiments"]["network_load_multipliers"],
        "peak_data_center_penetration": 0.06,
        "baseline_qualities": baseline_qualities,
        "settlement_mechanisms": mechanisms,
        "nodal_net_value_rule": "signed SCED avoided cost; credits positive value and debits negative value",
        "settlement_generator_segments": settlement_segments,
        "independent_evaluation_generator_segments": evaluation_segments,
        "independent_cost_parameterization": (
            "public benchmark quadratic costs at 10-segment settlement and "
            "40-segment independent evaluation resolution; for PGLib "
            "IEEE-118, PYPOWER IEEE-118 quadratic curves are aligned by the "
            "identical 54 generator buses while PGLib topology, limits, and "
            "capacities are retained in both layers"
        ),
        "settlement_schema_version": SETTLEMENT_SCHEMA_VERSION,
        "estimator_checksum": estimator_checksum,
        "resolution_convergence": (
            "complete 54-day IEEE RTS 24-bus 0.98-load boundary-cell panel "
            "at 10/40, 20/80, 40/160, and 80/320 settlement/evaluation segments"
        ),
    })
    from .visualization import plot_exp5
    plot_exp5(results, resolution_summary, folder / "figures", cfg)
    logger.info("Experiment 5 complete: %d cross-network settlement outcomes", len(results))


def _deadline_binding_share(served_mwh: np.ndarray, arrivals: np.ndarray, deadlines: list[int]) -> float:
    service = served_mwh.sum(axis=2)
    cumulative_service = np.cumsum(service, axis=2)
    cumulative_arrivals = np.cumsum(arrivals, axis=0)
    binding = 0
    eligible = 0
    for source in range(arrivals.shape[1]):
        for klass, deadline in enumerate(deadlines):
            for t in range(int(deadline), arrivals.shape[0]):
                due = cumulative_arrivals[t - int(deadline), source, klass]
                if due > 1e-9:
                    eligible += 1
                    binding += int(abs(cumulative_service[source, klass, t] - due) <= 1e-6)
    return binding / max(eligible, 1)


def run_exp6(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
    resume: bool = False,
) -> None:
    """Factorial stress test in regimes where capacity and deadline constraints bind."""
    folder = root / "experiments/exp6_physical_stress"
    final = folder / "results/final"
    intermediate = folder / "results/intermediate"
    final.mkdir(parents=True, exist_ok=True)
    intermediate.mkdir(parents=True, exist_ok=True)
    profiles = np.load(
        root / "experiments/exp2_baseline_verification/results/intermediate/test_profiles.npz",
        allow_pickle=False,
    )
    days = profiles["days"].astype(int)
    methods = [str(x) for x in profiles["methods"]]
    target_idx = methods.index("Ex-post Metadata Gradient Boosting")
    targets = profiles["baselines"][:, target_idx]
    quantile_targets = profiles["baselines"][
        :, methods.index("Ex-post Quantile Gradient Boosting")
    ]
    estimator_checksum = hashlib.sha256(
        np.ascontiguousarray(
            profiles["baselines"][
                :, methods.index("Risk-Constrained Convex Verifier")
            ]
        ).tobytes()
    ).hexdigest()
    actual = profiles["actual"]
    oracle = profiles["oracle"]
    metadata = json.loads(
        (root / "experiments/exp2_baseline_verification/results/final/experiment_metadata.json").read_text()
    )
    projection_weights = np.asarray(metadata["projection_weights"], dtype=float)
    ensemble_weights = np.asarray(metadata["convex_ensemble_weights"], dtype=float)
    selected_single_weight = float(
        metadata["selected_single_projection_weight"]
    )
    selected_quantile_weight = float(
        metadata["selected_quantile_projection_weight"]
    )
    selected_envelope_weight = float(
        metadata["selected_risk_envelope_projection_weight"]
    )
    arrivals_days, _, _, _, _, prices, _ = _inputs(root, cfg, logger)
    event_slots = list(map(int, cfg["market"]["event_slots"]))
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    checkpoint_path = intermediate / "physical_stress_checkpoint.csv"
    rows: list[dict[str, Any]] = []
    if resume and checkpoint_path.exists():
        prior = pd.read_csv(checkpoint_path)
        if (
            "estimator_schema_version" in prior.columns
            and set(prior["estimator_schema_version"].unique()) == {3}
            and "estimator_checksum" in prior.columns
            and set(prior["estimator_checksum"].unique()) == {estimator_checksum}
        ):
            complete = prior.groupby(["capacity_multiplier", "deadline_multiplier"]).size()
            keys = set(complete[complete == len(days)].index.tolist())
            if keys:
                prior = prior[
                    prior.apply(lambda x: (x["capacity_multiplier"], x["deadline_multiplier"]) in keys, axis=1)
                ]
                rows = prior.to_dict("records")
                logger.info("Resuming Experiment 6 with %d complete stress rows", len(rows))
        else:
            logger.info("Discarding stale Experiment 6 single-projection checkpoint")
    grid = [
        (float(cap), float(deadline))
        for cap in cfg["experiments"]["stress_capacity_multipliers"]
        for deadline in cfg["experiments"]["stress_deadline_multipliers"]
    ]
    for cap_multiplier, deadline_multiplier in tqdm(grid, desc="Exp6 physical-constraint stress grid"):
        if sum(
            1 for row in rows
            if row["capacity_multiplier"] == cap_multiplier and row["deadline_multiplier"] == deadline_multiplier
        ) == len(days):
            continue
        local = copy.deepcopy(cfg)
        local["project"]["flexible_capacity_mw"] = float(cfg["project"]["flexible_capacity_mw"]) * cap_multiplier
        local["workload"]["deadlines_slots"] = [
            int(np.ceil(x * deadline_multiplier)) for x in cfg["workload"]["deadlines_slots"]
        ]
        for i, day in enumerate(days):
            ensemble_prediction, _, _ = _solve_convex_projection(
                arrivals_days[int(day)],
                prices,
                local,
                targets[i],
                projection_weights,
                ensemble_weights,
                extra_target=quantile_targets[i],
                extra_projection_weight=selected_quantile_weight,
            )
            risk_reference = _solve_day_with_buffer(
                arrivals_days[int(day)],
                prices,
                local,
                mode="honest",
                target=quantile_targets[i],
                projection_weight=selected_quantile_weight,
            )
            if not risk_reference.success:
                raise RuntimeError(
                    f"Stress reference failed for day {int(day)}"
                )
            safe = _solve_day_with_buffer(
                arrivals_days[int(day)],
                prices,
                local,
                mode="honest",
                target=ensemble_prediction,
                projection_weight=selected_envelope_weight,
                power_upper_mw=_event_risk_upper_envelope(
                    risk_reference.power_mw, local
                ),
            )
            if not safe.success:
                raise RuntimeError(
                    f"Stress risk envelope failed for day {int(day)}"
                )
            prediction = safe.power_mw
            served_mwh = safe.served_mwh
            base = baseline_metrics(prediction, oracle[i], event_slots)
            response = response_metrics(prediction, oracle[i], actual[i], event_slots, dt_h)
            limit = float(cfg["project"]["fixed_facility_load_mw"]) + local["project"]["flexible_capacity_mw"]
            row = {
                "day": int(day),
                "capacity_multiplier": cap_multiplier,
                "deadline_multiplier": deadline_multiplier,
                "capacity_binding_share": float(np.mean(np.isclose(prediction, limit, atol=1e-6))),
                "deadline_binding_share": _deadline_binding_share(
                    served_mwh,
                    np.concatenate([
                        arrivals_days[int(day)],
                        np.zeros((int(cfg["experiments"]["lookahead_slots"]), arrivals_days.shape[2], arrivals_days.shape[3])),
                    ]),
                    local["workload"]["deadlines_slots"],
                ),
                "estimator_schema_version": 3,
                "estimator_checksum": estimator_checksum,
            }
            row.update(base)
            row.update(response)
            rows.append(row)
        pd.DataFrame(rows).to_csv(checkpoint_path, index=False)
    results = pd.DataFrame(rows)
    results.to_csv(final / "physical_stress.csv", index=False)
    summary = results.groupby(["capacity_multiplier", "deadline_multiplier"], as_index=False).mean(numeric_only=True)
    summary.to_csv(final / "physical_stress_summary.csv", index=False)
    write_json(final / "experiment_metadata.json", {
        "capacity_multipliers": cfg["experiments"]["stress_capacity_multipliers"],
        "deadline_multipliers": cfg["experiments"]["stress_deadline_multipliers"],
        "test_days": days.tolist(),
        "projection_weights": projection_weights.tolist(),
        "convex_ensemble_weights": ensemble_weights.tolist(),
        "single_projection_weight": selected_single_weight,
        "risk_envelope_projection_weight": selected_envelope_weight,
        "estimator_schema_version": 3,
        "estimator_checksum": estimator_checksum,
        "solver": "HiGHS linear programming; all declared cells must be feasible and optimal",
    })
    from .visualization import plot_exp6
    plot_exp6(summary, folder / "figures", cfg)
    logger.info("Experiment 6 complete: %d feasible stress-test outcomes", len(results))


def _exact_shapley_values(coalition_values: dict[int, float], participants: int) -> np.ndarray:
    """Enumerate every coalition and return the exact Shapley allocation."""
    full = (1 << participants) - 1
    if set(coalition_values) != set(range(full + 1)):
        raise ValueError("Exact Shapley allocation requires every coalition value")
    denominator = math.factorial(participants)
    allocation = np.zeros(participants)
    for participant in range(participants):
        bit = 1 << participant
        for coalition in range(full + 1):
            if coalition & bit:
                continue
            size = int(coalition.bit_count())
            weight = (
                math.factorial(size)
                * math.factorial(participants - size - 1)
                / denominator
            )
            allocation[participant] += weight * (
                coalition_values[coalition | bit] - coalition_values[coalition]
            )
    return allocation


def _run_eight_participant_scaling(
    root: Path,
    cfg: dict[str, Any],
    days: np.ndarray,
    predicted: np.ndarray,
    actual: np.ndarray,
    logger: logging.Logger,
    resume: bool,
) -> pd.DataFrame:
    """Run an exact eight-participant allocation on every locked day and slot.

    Each of the four sites is decomposed into an inference and a batch
    contractual portfolio.  The portfolio shares are estimated once from
    pre-test public-trace arrivals.  Every one of the 2^8 coalitions is then
    solved exactly on IEEE RTS-24 for all eight event intervals.
    """
    from pypower.case24_ieee_rts import case24_ieee_rts

    folder = root / "experiments/exp7_value_allocation"
    intermediate = folder / "results/intermediate"
    final = folder / "results/final"
    checkpoint = intermediate / "eight_participant_checkpoint.csv"
    arrivals_days, _, valid_days, _, _, _, _ = _inputs(root, cfg, logger)
    pretest_days = valid_days[valid_days < int(days[0])]
    if len(pretest_days) == 0:
        raise RuntimeError("No pre-test days available for portfolio shares")
    class_energy = arrivals_days[pretest_days].sum(axis=(0, 1))
    inference_energy = class_energy[:, :2].sum(axis=1)
    batch_energy = class_energy[:, 2]
    inference_share = inference_energy / np.maximum(
        inference_energy + batch_energy, 1e-12
    )
    portfolio_shares = np.column_stack(
        [inference_share, 1.0 - inference_share]
    ).reshape(-1)
    participant_sites = np.repeat(np.arange(4), 2)
    participant_labels = np.tile(
        np.array(["Inference portfolio", "Batch portfolio"]), 4
    )

    system = power_system_from_ppc(case24_ieee_rts())
    dc_idx = np.asarray([2, 7, 14, 20], dtype=int)
    native = system.bus[:, 2] * 0.90
    peak_dc_mw = 0.06 * float(native.sum())
    event_slots = list(map(int, cfg["market"]["event_slots"]))
    peak_profile = float(
        max(
            predicted[:, :, event_slots].sum(axis=1).max(),
            actual[:, :, event_slots].sum(axis=1).max(),
        )
    )
    dc_scale = peak_dc_mw / max(peak_profile, 1e-12)
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    segments = int(cfg["market"]["generator_segments"])
    participants = 8
    coalition_count = 2**participants
    required_per_day = len(event_slots) * participants
    checkpoint_schema_version = 2
    panel_checksum = hashlib.sha256(
        np.ascontiguousarray(days, dtype=np.int64).tobytes()
        + np.ascontiguousarray(predicted, dtype=np.float64).tobytes()
        + np.ascontiguousarray(actual, dtype=np.float64).tobytes()
        + np.ascontiguousarray(portfolio_shares, dtype=np.float64).tobytes()
    ).hexdigest()
    rows: list[dict[str, Any]] = []
    if resume and checkpoint.exists():
        prior = pd.read_csv(checkpoint)
        valid_checkpoint = (
            "checkpoint_schema_version" in prior
            and set(prior["checkpoint_schema_version"].astype(int).unique())
            == {checkpoint_schema_version}
            and "panel_checksum" in prior
            and set(prior["panel_checksum"].astype(str).unique())
            == {panel_checksum}
        )
        if valid_checkpoint:
            active_days = set(map(int, days))
            prior = prior[prior["day"].astype(int).isin(active_days)]
            prior = prior.drop_duplicates(
                ["day", "slot", "participant"], keep="last"
            )
            complete_days: set[int] = set()
            expected_day_keys = {
                (int(slot), int(participant))
                for slot in event_slots
                for participant in range(1, participants + 1)
            }
            for day, group in prior.groupby("day"):
                observed_day_keys = set(
                    zip(
                        group["slot"].astype(int),
                        group["participant"].astype(int),
                    )
                )
                if observed_day_keys == expected_day_keys:
                    complete_days.add(int(day))
            rows = prior[
                prior["day"].astype(int).isin(complete_days)
            ].to_dict("records")
            logger.info(
                "Resuming exact eight-participant panel with %d rows", len(rows)
            )
        else:
            logger.info(
                "Discarding stale exact eight-participant checkpoint"
            )

    for day_index, day_value in enumerate(
        tqdm(days, desc="Exp7 exact 8-participant RTS-24 scaling")
    ):
        day = int(day_value)
        if sum(int(row["day"]) == day for row in rows) == required_per_day:
            continue
        day_started = time.perf_counter()
        day_rows: list[dict[str, Any]] = []
        for slot in event_slots:
            baseline_profile = predicted[day_index, :, slot]
            actual_profile = actual[day_index, :, slot]
            baseline_load = native.copy()
            baseline_load[dc_idx] += baseline_profile * dc_scale
            baseline_dispatch = solve_sced(
                system, baseline_load, segments
            )
            site_delta = (
                actual_profile - baseline_profile
            ) * dc_scale
            participant_delta = np.asarray(
                [
                    site_delta[site] * portfolio_shares[participant]
                    for participant, site in enumerate(participant_sites)
                ]
            )
            coalition_values: dict[int, float] = {0: 0.0}
            for coalition in range(1, coalition_count):
                mixed_load = baseline_load.copy()
                for participant, site in enumerate(participant_sites):
                    if coalition & (1 << participant):
                        mixed_load[dc_idx[site]] += participant_delta[
                            participant
                        ]
                objective = solve_sced(
                    system, mixed_load, segments
                ).objective
                coalition_values[coalition] = (
                    baseline_dispatch.objective - objective
                ) * dt_h
            allocation = _exact_shapley_values(
                coalition_values, participants
            )
            grand_value = coalition_values[coalition_count - 1]
            budget_residual = float(allocation.sum() - grand_value)
            for participant in range(participants):
                day_rows.append(
                    {
                        "day": day,
                        "slot": int(slot),
                        "participant": participant + 1,
                        "site": int(participant_sites[participant] + 1),
                        "portfolio": str(
                            participant_labels[participant]
                        ),
                        "pretest_measured_energy_share": float(
                            portfolio_shares[participant]
                        ),
                        "participant_bus_zero_based": int(
                            dc_idx[participant_sites[participant]]
                        ),
                        "exact_shapley_value_usd": float(
                            allocation[participant]
                        ),
                        "grand_coalition_value_usd": float(grand_value),
                        "budget_residual_usd": budget_residual,
                        "coalitions_enumerated": coalition_count,
                        "network": "IEEE RTS 24-bus",
                        "checkpoint_schema_version": checkpoint_schema_version,
                        "panel_checksum": panel_checksum,
                    }
                )
        elapsed = time.perf_counter() - day_started
        for row in day_rows:
            row["day_solve_seconds"] = elapsed
        rows.extend(day_rows)
        pd.DataFrame(rows).to_csv(checkpoint, index=False)

    results = pd.DataFrame(rows).sort_values(
        ["day", "slot", "participant"]
    )
    expected_keys = {
        (int(day), int(slot), int(participant))
        for day in days
        for slot in event_slots
        for participant in range(1, participants + 1)
    }
    observed_keys = set(
        zip(
            results["day"].astype(int),
            results["slot"].astype(int),
            results["participant"].astype(int),
        )
    )
    if len(results) != len(expected_keys) or observed_keys != expected_keys:
        raise RuntimeError(
            "Incomplete exact eight-participant panel: "
            f"{len(results)}/{len(expected_keys)}"
        )
    results.to_csv(final / "eight_participant_exact_scaling.csv", index=False)
    summary = (
        results.groupby(["participant", "site", "portfolio"], as_index=False)
        .agg(
            mean_exact_shapley_value_usd=(
                "exact_shapley_value_usd", "mean"
            ),
            mean_absolute_shapley_value_usd=(
                "exact_shapley_value_usd",
                lambda values: float(np.mean(np.abs(values))),
            ),
            max_absolute_budget_residual_usd=(
                "budget_residual_usd",
                lambda values: float(np.max(np.abs(values))),
            ),
            mean_day_solve_seconds=("day_solve_seconds", "mean"),
        )
    )
    summary.to_csv(
        final / "eight_participant_exact_scaling_summary.csv", index=False
    )
    return results


def _run_group_symmetric_scaling(
    root: Path,
    cfg: dict[str, Any],
    days: np.ndarray,
    predicted: np.ndarray,
    actual: np.ndarray,
    logger: logging.Logger,
    resume: bool,
) -> pd.DataFrame:
    """Scale exact Shapley allocation to 20 participants by symmetry reduction."""
    from pypower.case24_ieee_rts import case24_ieee_rts

    folder = root / "experiments/exp7_value_allocation"
    final = folder / "results/final"
    checkpoint = folder / "results/intermediate/group_symmetric_checkpoint.csv"
    participant_counts = [4, 8, 12, 16, 20]
    event_slots = np.asarray(cfg["market"]["event_slots"], dtype=int)
    peak_slots = event_slots[
        np.argmax(actual[:, :, event_slots].sum(axis=1), axis=1)
    ]
    system = power_system_from_ppc(case24_ieee_rts())
    dc_buses = np.asarray([2, 7, 14, 20], dtype=int)
    native = system.bus[:, 2] * 0.90
    peak_dc_mw = 0.06 * float(native.sum())
    peak_profile = float(
        max(
            predicted[:, :, event_slots].sum(axis=1).max(),
            actual[:, :, event_slots].sum(axis=1).max(),
        )
    )
    scale = peak_dc_mw / max(peak_profile, 1e-12)
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    segments = int(cfg["market"]["generator_segments"])
    checkpoint_schema_version = 2
    panel_checksum = hashlib.sha256(
        np.ascontiguousarray(days, dtype=np.int64).tobytes()
        + np.ascontiguousarray(predicted, dtype=np.float64).tobytes()
        + np.ascontiguousarray(actual, dtype=np.float64).tobytes()
        + np.ascontiguousarray(peak_slots, dtype=np.int64).tobytes()
    ).hexdigest()
    rows: list[dict[str, Any]] = []
    completed: set[tuple[int, int]] = set()
    if resume and checkpoint.exists():
        previous = pd.read_csv(checkpoint)
        valid_checkpoint = (
            "checkpoint_schema_version" in previous
            and set(
                previous["checkpoint_schema_version"].astype(int).unique()
            )
            == {checkpoint_schema_version}
            and "panel_checksum" in previous
            and set(previous["panel_checksum"].astype(str).unique())
            == {panel_checksum}
        )
        if valid_checkpoint:
            active_days = set(map(int, days))
            previous = previous[
                previous["day"].astype(int).isin(active_days)
                & previous["participant_count"].astype(int).isin(
                    participant_counts
                )
            ].drop_duplicates(
                ["day", "participant_count", "site"], keep="last"
            )
            grouped_sites = previous.groupby(
                ["day", "participant_count"]
            )["site"].apply(lambda values: set(map(int, values)))
            completed = {
                (int(day), int(participants))
                for (day, participants), sites in grouped_sites.items()
                if sites == {1, 2, 3, 4}
            }
            rows = previous[
                [
                    (int(day), int(participants)) in completed
                    for day, participants in zip(
                        previous["day"], previous["participant_count"]
                    )
                ]
            ].to_dict("records")
        else:
            logger.info(
                "Discarding stale group-symmetric scaling checkpoint"
            )
    for day_index, day_value in enumerate(
        tqdm(days, desc="Exp7 exact 4-to-20 participant scaling")
    ):
        day = int(day_value)
        slot = int(peak_slots[day_index])
        baseline_profile = predicted[day_index, :, slot]
        actual_profile = actual[day_index, :, slot]
        baseline_load = native.copy()
        baseline_load[dc_buses] += baseline_profile * scale
        baseline_objective = solve_sced(
            system, baseline_load, segments
        ).objective
        site_delta = (actual_profile - baseline_profile) * scale
        for participant_count in participant_counts:
            key = (day, participant_count)
            if key in completed:
                continue
            members_per_site = participant_count // 4
            started = time.perf_counter()
            values: dict[tuple[int, ...], float] = {}
            for counts in product(
                *[range(members_per_site + 1) for _ in range(4)]
            ):
                mixed_load = baseline_load.copy()
                mixed_load[dc_buses] += (
                    np.asarray(counts, dtype=float)
                    / members_per_site
                    * site_delta
                )
                values[counts] = (
                    baseline_objective
                    - solve_sced(system, mixed_load, segments).objective
                ) * dt_h
            per_member = _exact_group_symmetric_shapley(
                values, members_per_site
            )
            grand = values[(members_per_site,) * 4]
            residual = float(
                members_per_site * per_member.sum() - grand
            )
            elapsed = time.perf_counter() - started
            for site in range(4):
                rows.append(
                    {
                        "day": day,
                        "peak_event_slot": slot,
                        "participant_count": participant_count,
                        "members_per_site": members_per_site,
                        "site": site + 1,
                        "participant_bus_zero_based": int(dc_buses[site]),
                        "exact_per_member_shapley_usd": float(per_member[site]),
                        "site_total_shapley_usd": float(
                            members_per_site * per_member[site]
                        ),
                        "grand_coalition_value_usd": float(grand),
                        "budget_residual_usd": residual,
                        "count_states_evaluated": int(
                            (members_per_site + 1) ** 4
                        ),
                        "full_coalitions_avoided": int(
                            2**participant_count
                            - (members_per_site + 1) ** 4
                        ),
                        "solve_seconds": elapsed,
                        "network": "IEEE RTS 24-bus",
                        "checkpoint_schema_version": checkpoint_schema_version,
                        "panel_checksum": panel_checksum,
                    }
                )
            pd.DataFrame(rows).to_csv(checkpoint, index=False)
    results = pd.DataFrame(rows).sort_values(
        ["day", "participant_count", "site"]
    )
    expected_keys = {
        (int(day), int(participants), int(site))
        for day in days
        for participants in participant_counts
        for site in range(1, 5)
    }
    observed_keys = set(
        zip(
            results["day"].astype(int),
            results["participant_count"].astype(int),
            results["site"].astype(int),
        )
    )
    if len(results) != len(expected_keys) or observed_keys != expected_keys:
        raise RuntimeError(
            "Incomplete group-symmetric scaling panel: "
            f"{len(results)}/{len(expected_keys)}"
        )
    results.to_csv(final / "group_symmetric_exact_scaling.csv", index=False)
    summary = (
        results.groupby("participant_count", as_index=False)
        .agg(
            mean_solve_seconds=("solve_seconds", "mean"),
            maximum_budget_residual_usd=(
                "budget_residual_usd",
                lambda values: float(np.max(np.abs(values))),
            ),
            count_states_evaluated=("count_states_evaluated", "max"),
            full_coalitions_avoided=("full_coalitions_avoided", "max"),
        )
    )
    summary.to_csv(
        final / "group_symmetric_exact_scaling_summary.csv", index=False
    )
    return results


def run_exp7(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
    resume: bool = False,
) -> None:
    """Exact multi-participant value allocation and budget-balance validation."""
    folder = root / "experiments/exp7_value_allocation"
    final = folder / "results/final"
    intermediate = folder / "results/intermediate"
    final.mkdir(parents=True, exist_ok=True)
    intermediate.mkdir(parents=True, exist_ok=True)
    profile_path = (
        root
        / "experiments/exp2_baseline_verification/results/intermediate/test_profiles.npz"
    )
    validation_profile_path = (
        root
        / "experiments/exp2_baseline_verification/results/intermediate/validation_profiles.npz"
    )
    if not profile_path.exists():
        run_exp2(root, cfg, logger)
    if not validation_profile_path.exists():
        run_exp2(root, cfg, logger, resume=True)
    profiles = np.load(profile_path, allow_pickle=False)
    days = profiles["days"].astype(int)
    methods = [str(value) for value in profiles["methods"]]
    proposed_index = methods.index("Risk-Constrained Convex Verifier")
    predicted = profiles["baselines"][:, proposed_index]
    actual = profiles["actual"]
    oracle = profiles["oracle"]
    estimator_checksum = hashlib.sha256(
        np.ascontiguousarray(predicted).tobytes()
    ).hexdigest()
    _, _, _, system, base_profiles, _, _ = _inputs(root, cfg, logger)
    event_slots = list(map(int, cfg["market"]["event_slots"]))
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    participants = predicted.shape[1]
    full_coalition = (1 << participants) - 1
    allocation_methods = [
        "Nodal signed linear",
        "Standalone avoided cost",
        "Leave-one-out marginal",
        "Exact Shapley net value",
    ]
    qualities = [
        "Trace-Anchored Reference",
        "Risk-Constrained Convex Verifier",
    ]
    checkpoint_path = intermediate / "value_allocation_checkpoint.csv"
    rows: list[dict[str, Any]] = []
    if resume and checkpoint_path.exists():
        prior = pd.read_csv(checkpoint_path)
        if (
            "settlement_schema_version" in prior
            and set(prior["settlement_schema_version"].unique())
            == {SETTLEMENT_SCHEMA_VERSION}
            and "estimator_checksum" in prior
            and set(prior["estimator_checksum"].unique())
            == {estimator_checksum}
        ):
            required_per_day = (
                len(qualities) * len(allocation_methods) * participants
            )
            complete = prior.groupby("day").size()
            complete_days = set(
                complete[complete == required_per_day].index.astype(int)
            )
            prior = prior[prior["day"].astype(int).isin(complete_days)]
            rows = prior.to_dict("records")
            logger.info(
                "Resuming Experiment 7 with %d complete allocation rows", len(rows)
            )

    dc_bus_idx = np.asarray(cfg["project"]["data_center_buses"], dtype=int) - 1
    for day_index, day in enumerate(
        tqdm(days, desc="Exp7 exact coalition-value allocations")
    ):
        day = int(day)
        if sum(int(row["day"]) == day for row in rows) == (
            len(qualities) * len(allocation_methods) * participants
        ):
            continue
        daily: dict[tuple[str, str], np.ndarray] = {
            (quality, method): np.zeros(participants)
            for quality in qualities
            for method in allocation_methods
        }
        estimated_grand = {quality: 0.0 for quality in qualities}
        realized_grand = 0.0
        oracle_shapley = np.zeros(participants)
        for slot in event_slots:
            actual_load = _add_dc_power(
                base_profiles[slot], actual[day_index, :, slot], cfg
            )
            actual_dispatch = solve_sced(
                system,
                actual_load,
                int(cfg["market"]["generator_segments"]),
            )
            interval_allocations: dict[str, dict[str, np.ndarray]] = {}
            for quality, baseline_profile in [
                ("Trace-Anchored Reference", oracle[day_index, :, slot]),
                (
                    "Risk-Constrained Convex Verifier",
                    predicted[day_index, :, slot],
                ),
            ]:
                baseline_load = _add_dc_power(
                    base_profiles[slot], baseline_profile, cfg
                )
                baseline_dispatch = solve_sced(
                    system,
                    baseline_load,
                    int(cfg["market"]["generator_segments"]),
                )
                coalition_values: dict[int, float] = {}
                for coalition in range(full_coalition + 1):
                    if coalition == 0:
                        coalition_values[coalition] = 0.0
                        continue
                    if coalition == full_coalition:
                        mixed_objective = actual_dispatch.objective
                    else:
                        mixed_profile = baseline_profile.copy()
                        for participant in range(participants):
                            if coalition & (1 << participant):
                                mixed_profile[participant] = actual[
                                    day_index, participant, slot
                                ]
                        mixed_load = _add_dc_power(
                            base_profiles[slot], mixed_profile, cfg
                        )
                        mixed_objective = solve_sced(
                            system,
                            mixed_load,
                            int(cfg["market"]["generator_segments"]),
                        ).objective
                    coalition_values[coalition] = (
                        baseline_dispatch.objective - mixed_objective
                    ) * dt_h
                shapley = _exact_shapley_values(
                    coalition_values, participants
                )
                standalone = np.asarray(
                    [
                        coalition_values[1 << participant]
                        for participant in range(participants)
                    ]
                )
                leave_one_out = np.asarray(
                    [
                        coalition_values[full_coalition]
                        - coalition_values[
                            full_coalition ^ (1 << participant)
                        ]
                        for participant in range(participants)
                    ]
                )
                nodal_linear = (
                    baseline_dispatch.lmp_per_mwh[dc_bus_idx]
                    * (baseline_profile - actual[day_index, :, slot])
                    * dt_h
                )
                interval_allocations[quality] = {
                    "Nodal signed linear": nodal_linear,
                    "Standalone avoided cost": standalone,
                    "Leave-one-out marginal": leave_one_out,
                    "Exact Shapley net value": shapley,
                }
                for method in allocation_methods:
                    daily[(quality, method)] += interval_allocations[quality][
                        method
                    ]
                estimated_grand[quality] += coalition_values[full_coalition]
            oracle_shapley += interval_allocations[
                "Trace-Anchored Reference"
            ]["Exact Shapley net value"]
            realized_grand += sum(
                interval_allocations["Trace-Anchored Reference"][
                    "Exact Shapley net value"
                ]
            )

        for quality in qualities:
            for method in allocation_methods:
                allocation = daily[(quality, method)]
                total_payment = float(allocation.sum())
                for participant in range(participants):
                    rows.append(
                        {
                            "day": day,
                            "baseline_quality": quality,
                            "allocation_method": method,
                            "participant": participant + 1,
                            "participant_bus": int(
                                cfg["project"]["data_center_buses"][participant]
                            ),
                            "participant_payment_usd": float(
                                allocation[participant]
                            ),
                            "oracle_shapley_value_usd": float(
                                oracle_shapley[participant]
                            ),
                            "participant_absolute_error_usd": float(
                                abs(
                                    allocation[participant]
                                    - oracle_shapley[participant]
                                )
                            ),
                            "total_payment_usd": total_payment,
                            "estimated_grand_value_usd": float(
                                estimated_grand[quality]
                            ),
                            "realized_grand_value_usd": float(realized_grand),
                            "budget_residual_usd": float(
                                total_payment - estimated_grand[quality]
                            ),
                            "total_value_error_usd": float(
                                total_payment - realized_grand
                            ),
                            "settlement_schema_version": SETTLEMENT_SCHEMA_VERSION,
                            "estimator_checksum": estimator_checksum,
                        }
                    )
        pd.DataFrame(rows).to_csv(checkpoint_path, index=False)

    results = pd.DataFrame(rows)
    results.to_csv(final / "value_allocation.csv", index=False)
    summary = (
        results.groupby(["baseline_quality", "allocation_method"], as_index=False)
        .agg(
            mean_participant_absolute_error_usd=(
                "participant_absolute_error_usd",
                "mean",
            ),
            mean_absolute_budget_residual_usd=(
                "budget_residual_usd",
                lambda values: float(np.mean(np.abs(values))),
            ),
            max_absolute_budget_residual_usd=(
                "budget_residual_usd",
                lambda values: float(np.max(np.abs(values))),
            ),
            mean_absolute_total_value_error_usd=(
                "total_value_error_usd",
                lambda values: float(np.mean(np.abs(values))),
            ),
        )
    )
    summary.to_csv(final / "value_allocation_summary.csv", index=False)
    scaling = _run_eight_participant_scaling(
        root, cfg, days, predicted, actual, logger, resume
    )
    grouped_scaling = _run_group_symmetric_scaling(
        root, cfg, days, predicted, actual, logger, resume
    )
    write_json(
        final / "experiment_metadata.json",
        {
            "participants": participants,
            "participant_buses": cfg["project"]["data_center_buses"],
            "coalitions_per_interval_and_baseline": 2**participants,
            "allocation": (
                "exact enumeration of every coalition; no permutation sampling "
                "or approximate Shapley estimator"
            ),
            "characteristic_function": (
                "signed SCED avoided cost as each coalition moves from baseline "
                "to actual demand while nonmembers remain at baseline"
            ),
            "budget_balance": (
                "Shapley efficiency: participant allocations sum exactly to the "
                "estimated grand-coalition value"
            ),
            "settlement_schema_version": SETTLEMENT_SCHEMA_VERSION,
            "estimator_checksum": estimator_checksum,
            "scaling_participants": 8,
            "scaling_network": "IEEE RTS 24-bus",
            "scaling_coalitions_per_interval": 256,
            "scaling_locked_days": int(scaling["day"].nunique()),
            "maximum_exact_participants": int(
                grouped_scaling["participant_count"].max()
            ),
            "symmetry_reduction": (
                "exact count-state Shapley summation for exchangeable "
                "contract slices within each of four electrical sites"
            ),
            "portfolio_decomposition": (
                "two contractual portfolios per site, with inference/batch "
                "shares fixed from pre-test public-trace arrivals"
            ),
        },
    )
    from .visualization import (
        plot_exp7,
        plot_exp7_grouped_scaling,
        plot_exp7_scaling,
    )

    plot_exp7(results, summary, folder / "figures", cfg)
    plot_exp7_scaling(scaling, folder / "figures", cfg)
    plot_exp7_grouped_scaling(grouped_scaling, folder / "figures", cfg)
    logger.info(
        "Experiment 7 complete: %d exact participant-allocation outcomes",
        len(results),
    )


def run_exp8(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
    resume: bool = False,
) -> None:
    """Validate settlement under an exact all-contingency N-1 DC dispatch."""
    from pypower.case24_ieee_rts import case24_ieee_rts

    folder = root / "experiments/exp8_n1_security"
    final = folder / "results/final"
    intermediate = folder / "results/intermediate"
    final.mkdir(parents=True, exist_ok=True)
    intermediate.mkdir(parents=True, exist_ok=True)
    profile_path = (
        root
        / "experiments/exp2_baseline_verification/results/intermediate/test_profiles.npz"
    )
    validation_profile_path = (
        root
        / "experiments/exp2_baseline_verification/results/intermediate/validation_profiles.npz"
    )
    if not profile_path.exists():
        run_exp2(root, cfg, logger)
    if not validation_profile_path.exists():
        run_exp2(root, cfg, logger, resume=True)
    profiles = np.load(profile_path, allow_pickle=False)
    days = profiles["days"].astype(int)
    methods = [str(value) for value in profiles["methods"]]
    proposed_index = methods.index("Risk-Constrained Convex Verifier")
    predicted = profiles["baselines"][:, proposed_index]
    actual = profiles["actual"]
    oracle = profiles["oracle"]
    event_slots = list(map(int, cfg["market"]["event_slots"]))
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    settlement_segments = int(cfg["market"]["generator_segments"])
    evaluation_segments = int(
        cfg["market"].get("n1_evaluation_generator_segments", 40)
    )
    load_multiplier = float(
        cfg["experiments"].get("n1_load_multiplier", 0.9)
    )
    penetration = float(
        cfg["experiments"].get("n1_dc_peak_penetration", 0.06)
    )
    system = power_system_from_ppc(case24_ieee_rts())
    security_model = build_n1_security_factors(system)
    dc_buses = np.asarray([2, 7, 14, 20], dtype=int)
    native_load = system.bus[:, 2] * load_multiplier
    peak_dc_mw = penetration * float(native_load.sum())
    peak_trace_mw = float(
        max(
            oracle[:, :, event_slots].sum(axis=1).max(),
            actual[:, :, event_slots].sum(axis=1).max(),
            predicted[:, :, event_slots].sum(axis=1).max(),
        )
    )
    dc_scale = peak_dc_mw / max(peak_trace_mw, 1e-12)
    mechanisms = [
        "Base-case exact net value",
        "N-1 signed linear",
        "N-1 exact net value",
    ]
    qualities = [
        "Trace-Anchored Reference",
        "Risk-Constrained Convex Verifier",
    ]
    checkpoint_schema_version = 2
    panel_checksum = hashlib.sha256(
        np.ascontiguousarray(days, dtype=np.int64).tobytes()
        + np.ascontiguousarray(predicted, dtype=np.float64).tobytes()
        + np.ascontiguousarray(actual, dtype=np.float64).tobytes()
        + np.ascontiguousarray(oracle, dtype=np.float64).tobytes()
        + np.ascontiguousarray(
            [load_multiplier, penetration, settlement_segments, evaluation_segments],
            dtype=np.float64,
        ).tobytes()
    ).hexdigest()
    checkpoint = intermediate / "n1_security_checkpoint.csv"
    rows: list[dict[str, Any]] = []
    complete_days: set[int] = set()
    if resume and checkpoint.exists():
        prior = pd.read_csv(checkpoint)
        valid_checkpoint = (
            "checkpoint_schema_version" in prior
            and set(prior["checkpoint_schema_version"].astype(int).unique())
            == {checkpoint_schema_version}
            and "panel_checksum" in prior
            and set(prior["panel_checksum"].astype(str).unique())
            == {panel_checksum}
        )
        if valid_checkpoint:
            active_days = set(map(int, days))
            prior = prior[prior["day"].astype(int).isin(active_days)]
            prior = prior.drop_duplicates(
                ["day", "event_slot", "baseline_quality", "mechanism"],
                keep="last",
            )
            expected_day_keys = {
                (int(slot), quality, mechanism)
                for slot in event_slots
                for quality in qualities
                for mechanism in mechanisms
            }
            for day, group in prior.groupby("day"):
                observed_day_keys = set(
                    zip(
                        group["event_slot"].astype(int),
                        group["baseline_quality"].astype(str),
                        group["mechanism"].astype(str),
                    )
                )
                if observed_day_keys == expected_day_keys:
                    complete_days.add(int(day))
            rows = prior[
                prior["day"].astype(int).isin(complete_days)
            ].to_dict("records")
            logger.info(
                "Resuming Experiment 8 with %d complete locked days",
                len(complete_days),
            )
        else:
            logger.info("Discarding stale Experiment 8 checkpoint")

    def evaluate_n1_day(item: tuple[int, int]) -> tuple[int, list[dict[str, Any]]]:
        local_day, day = item
        day_rows: list[dict[str, Any]] = []
        for t in event_slots:
            loads: dict[str, np.ndarray] = {}
            for label, profile in [
                ("Trace-Anchored Reference", oracle),
                ("Actual", actual),
                ("Risk-Constrained Convex Verifier", predicted),
            ]:
                load = native_load.copy()
                load[dc_buses] += profile[local_day, :, t] * dc_scale
                loads[label] = load
            n1_settlement = {
                label: solve_n1_sced(
                    system,
                    load,
                    settlement_segments,
                    security_factors=security_model,
                )
                for label, load in loads.items()
            }
            base_settlement = {
                label: solve_sced(system, load, settlement_segments)
                for label, load in loads.items()
            }
            n1_evaluation_oracle = solve_n1_sced(
                system,
                loads["Trace-Anchored Reference"],
                evaluation_segments,
                security_factors=security_model,
            )
            n1_evaluation_actual = solve_n1_sced(
                system,
                loads["Actual"],
                evaluation_segments,
                security_factors=security_model,
            )
            realized = (
                n1_evaluation_oracle.objective
                - n1_evaluation_actual.objective
            ) * dt_h
            for quality in qualities:
                delta = loads[quality] - loads["Actual"]
                payments = {
                    "Base-case exact net value": (
                        base_settlement[quality].objective
                        - base_settlement["Actual"].objective
                    )
                    * dt_h,
                    "N-1 signed linear": float(
                        n1_settlement[quality].lmp_per_mwh @ delta
                    )
                    * dt_h,
                    "N-1 exact net value": (
                        n1_settlement[quality].objective
                        - n1_settlement["Actual"].objective
                    )
                    * dt_h,
                }
                for mechanism, payment in payments.items():
                    day_rows.append(
                        {
                            "day": int(day),
                            "event_slot": int(t),
                            "baseline_quality": quality,
                            "mechanism": mechanism,
                            "payment_usd": float(payment),
                            "realized_n1_value_usd": float(realized),
                            "absolute_error_usd": float(
                                abs(payment - realized)
                            ),
                            "overpayment_usd": float(
                                max(0.0, payment - realized)
                            ),
                            "base_case_max_loading": float(
                                base_settlement[quality].max_loading
                            ),
                            "n1_base_case_max_loading": float(
                                n1_settlement[quality].max_loading
                            ),
                            "n1_max_post_contingency_loading": float(
                                n1_settlement[
                                    quality
                                ].max_post_contingency_loading
                            ),
                            "binding_contingency_constraints": int(
                                n1_settlement[
                                    quality
                                ].binding_contingency_constraints
                            ),
                            "credible_line_contingencies": int(
                                n1_settlement[quality].credible_contingencies
                            ),
                            "excluded_islanding_contingencies": int(
                                system.branch.shape[0]
                                - n1_settlement[quality].credible_contingencies
                            ),
                            "load_multiplier": load_multiplier,
                            "peak_dc_penetration": penetration,
                            "dc_power_scale": dc_scale,
                            "settlement_generator_segments": settlement_segments,
                            "evaluation_generator_segments": evaluation_segments,
                            "checkpoint_schema_version": checkpoint_schema_version,
                            "panel_checksum": panel_checksum,
                        }
                    )
        return int(day), day_rows

    pending_days = [
        (local_day, int(day))
        for local_day, day in enumerate(days)
        if int(day) not in complete_days
    ]
    security_workers = int(
        cfg["experiments"].get("n1_security_parallel_workers", 6)
    )
    if security_workers <= 0:
        raise ValueError("n1_security_parallel_workers must be positive")
    progress = tqdm(
        total=len(days),
        initial=len(complete_days),
        desc="Exp8 full N-1 locked-day panel",
    )
    with ThreadPoolExecutor(max_workers=security_workers) as executor:
        for day, day_rows in executor.map(evaluate_n1_day, pending_days):
            rows.extend(day_rows)
            complete_days.add(day)
            pd.DataFrame(rows).to_csv(checkpoint, index=False)
            progress.update(1)
    progress.close()

    interval_results = pd.DataFrame(rows).sort_values(
        ["day", "event_slot", "baseline_quality", "mechanism"]
    )
    expected_keys = {
        (int(day), int(slot), quality, mechanism)
        for day in days
        for slot in event_slots
        for quality in qualities
        for mechanism in mechanisms
    }
    observed_keys = set(
        zip(
            interval_results["day"].astype(int),
            interval_results["event_slot"].astype(int),
            interval_results["baseline_quality"].astype(str),
            interval_results["mechanism"].astype(str),
        )
    )
    if (
        len(interval_results) != len(expected_keys)
        or observed_keys != expected_keys
    ):
        raise RuntimeError(
            "Incomplete N-1 security panel: "
            f"{len(interval_results)}/{len(expected_keys)}"
        )
    interval_results.to_csv(
        final / "n1_security_interval_results.csv", index=False
    )
    daily = (
        interval_results.groupby(
            ["day", "baseline_quality", "mechanism"], as_index=False
        )
        .agg(
            payment_usd=("payment_usd", "sum"),
            realized_n1_value_usd=("realized_n1_value_usd", "sum"),
            mean_post_contingency_loading=(
                "n1_max_post_contingency_loading",
                "mean",
            ),
            maximum_post_contingency_loading=(
                "n1_max_post_contingency_loading",
                "max",
            ),
            maximum_binding_contingency_constraints=(
                "binding_contingency_constraints",
                "max",
            ),
        )
    )
    daily["absolute_error_usd"] = np.abs(
        daily["payment_usd"] - daily["realized_n1_value_usd"]
    )
    daily["overpayment_usd"] = np.maximum(
        0.0, daily["payment_usd"] - daily["realized_n1_value_usd"]
    )
    daily.to_csv(final / "n1_security_daily_results.csv", index=False)
    summary = (
        daily.groupby(["baseline_quality", "mechanism"], as_index=False)
        .agg(
            mean_absolute_error_usd=("absolute_error_usd", "mean"),
            median_absolute_error_usd=("absolute_error_usd", "median"),
            mean_overpayment_usd=("overpayment_usd", "mean"),
            mean_payment_usd=("payment_usd", "mean"),
            mean_realized_n1_value_usd=("realized_n1_value_usd", "mean"),
            maximum_post_contingency_loading=(
                "maximum_post_contingency_loading",
                "max",
            ),
        )
    )
    summary.to_csv(final / "n1_security_summary.csv", index=False)
    tests: list[dict[str, Any]] = []
    for quality in qualities:
        subset = daily[daily["baseline_quality"] == quality]
        target = (
            subset[subset["mechanism"] == "N-1 exact net value"]
            .sort_values("day")
            .set_index("day")
        )
        for comparator in [
            "Base-case exact net value",
            "N-1 signed linear",
        ]:
            comparison = (
                subset[subset["mechanism"] == comparator]
                .sort_values("day")
                .set_index("day")
            )
            if not target.index.equals(comparison.index):
                raise RuntimeError("Experiment 8 paired-day index mismatch")
            tests.append(
                {
                    "baseline_quality": quality,
                    "comparator": comparator,
                    "target": "N-1 exact net value",
                    **exact_block_sign_test(
                        comparison["absolute_error_usd"].to_numpy()
                        - target["absolute_error_usd"].to_numpy(),
                        int(cfg["experiments"]["block_length_days"]),
                    ),
                }
            )
    tests_frame = pd.DataFrame(tests)
    tests_frame["holm_adjusted_p_value"] = holm_adjust(
        tests_frame["two_sided_exact_p_value"].to_numpy()
    )
    tests_frame.to_csv(final / "n1_security_paired_tests.csv", index=False)
    write_json(
        final / "experiment_metadata.json",
        {
            "network": "IEEE RTS 24-bus",
            "public_case_source": "PYPOWER case24_ieee_rts",
            "locked_days": int(len(days)),
            "event_intervals_per_day": int(len(event_slots)),
            "base_case_branches": int(system.branch.shape[0]),
            "credible_non_islanding_line_contingencies": int(
                security_model[3]
            ),
            "excluded_islanding_contingencies": int(
                system.branch.shape[0] - security_model[3]
            ),
            "contingency_rule": (
                "all finite non-islanding single-line outages; no screening"
            ),
            "rating_rule": (
                "native public continuous branch ratings for base and "
                "post-contingency constraints; no derating"
            ),
            "load_multiplier": load_multiplier,
            "peak_data_center_penetration": penetration,
            "baseline_qualities": qualities,
            "mechanisms": mechanisms,
            "settlement_generator_segments": settlement_segments,
            "independent_evaluation_generator_segments": evaluation_segments,
        },
    )
    from .visualization import plot_exp8

    plot_exp8(daily, interval_results, folder / "figures", cfg)
    logger.info(
        "Experiment 8 complete: %d interval-mechanism outcomes over %d locked days",
        len(interval_results),
        len(days),
    )


def run_exp9(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
    resume: bool = False,
) -> None:
    """Certify robust N-1 settlement-payment noninferiority on every locked day."""
    from pypower.case24_ieee_rts import case24_ieee_rts
    from .visualization import plot_exp9

    folder = root / "experiments/exp9_payment_certificate"
    final = folder / "results/final"
    intermediate = folder / "results/intermediate"
    final.mkdir(parents=True, exist_ok=True)
    intermediate.mkdir(parents=True, exist_ok=True)
    # A completed payment panel is reusable only when it was produced from
    # the exact current Experiment-2 profile cache. Earlier versions checked
    # only row counts and schema numbers, which could silently preserve a
    # certificate after the risk/profile stage had been refit. Hashing the
    # compact profile and manifest files makes the resume boundary explicit.
    profile_path = (
        root
        / "experiments/exp2_baseline_verification/results/intermediate/test_profiles.npz"
    )
    validation_profile_path = (
        root
        / "experiments/exp2_baseline_verification/results/intermediate/validation_profiles.npz"
    )
    current_profile_checksum = (
        hashlib.sha256(profile_path.read_bytes()).hexdigest()
        if profile_path.exists()
        else None
    )
    current_validation_profile_checksum = (
        hashlib.sha256(validation_profile_path.read_bytes()).hexdigest()
        if validation_profile_path.exists()
        else None
    )
    data_manifest_path_for_resume = root / "data/processed/data_manifest.json"
    current_data_manifest_checksum = (
        hashlib.sha256(data_manifest_path_for_resume.read_bytes()).hexdigest()
        if data_manifest_path_for_resume.exists()
        else None
    )
    current_config_checksum = hashlib.sha256(
        json.dumps(cfg, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    payment_evaluation_profile_checksum = current_profile_checksum
    # A completed independent run can be registered through the unified
    # pipeline without repeating the expensive high-resolution N--1 panel.
    # Reuse is allowed only after checking the schema, locked-day cardinality,
    # interval cardinality, and the non-tautology role-separation artifact;
    # incomplete or legacy outputs fall through to the full solver below.
    if resume:
        metadata_path = final / "experiment_metadata.json"
        interval_path = final / "payment_evaluation_intervals.csv"
        daily_path = final / "payment_evaluation_daily.csv"
        scenario_path = final / "conversion_scenario_certificates.csv"
        paired_path = final / "paired_payment_noninferiority.csv"
        unseen_path = final / "payment_evaluation_unseen_scenarios.csv"
        role_path = final / "payment_non_tautology_audit.csv"
        try:
            cached_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            interval_count = len(pd.read_csv(interval_path))
            daily_count = len(pd.read_csv(daily_path))
            scenario_count = len(pd.read_csv(scenario_path))
            paired_count = len(pd.read_csv(paired_path))
            unseen_count = len(pd.read_csv(unseen_path))
            role_count = len(pd.read_csv(role_path))
            locked_days = int(cached_metadata.get("locked_days", 0))
            unseen_days = int(
                cached_metadata.get("unseen_transfer_evaluation", {}).get(
                    "locked_days_evaluated", 0
                )
            )
            if (
                cached_metadata.get("certificate_schema_version") == 10
                and locked_days == 54
                and interval_count == 54 * 5 * 8 * 4
                and daily_count == 54 * 5 * 4
                and scenario_count == 54 * 5
                and paired_count == 54 * 5
                and unseen_count == unseen_days * 2 * 8 * 4
                and role_count == 3
                and cached_metadata.get("payment_target_selection")
                and cached_metadata.get("selection_role_separation")
                and set(
                    cached_metadata.get("power_conversion_scenarios", {}).keys()
                ) == {"q01", "q10", "q50", "q90", "q99"}
                and cached_metadata.get("network_conversion_decomposition", {}).get(
                    "network_scale_calibrated_on_q99"
                )
                is True
                and cached_metadata.get("test_profile_file_checksum")
                == current_profile_checksum
                and cached_metadata.get("validation_profile_file_checksum")
                == current_validation_profile_checksum
                and cached_metadata.get("data_manifest_checksum")
                == current_data_manifest_checksum
                and cached_metadata.get("config_checksum") == current_config_checksum
            ):
                logger.info(
                    "Experiment 9 final artifacts pass resume integrity checks; "
                    "reusing the completed certificate and independent payment panel"
                )
                return
        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            logger.info("Experiment 9 resume cache is incomplete; recomputing the panel")
    if not profile_path.exists():
        run_exp2(root, cfg, logger)
    if not validation_profile_path.exists():
        run_exp2(root, cfg, logger, resume=True)
    stored = np.load(profile_path, allow_pickle=False)
    validation_stored = np.load(validation_profile_path, allow_pickle=False)
    days = stored["days"].astype(int)
    methods = [str(value) for value in stored["methods"]]
    required_profile_fields = {
        "projection_candidates",
        "projection_weights",
        "selected_single_projection_index",
    }
    missing_profile_fields = required_profile_fields.difference(stored.files)
    if missing_profile_fields:
        raise RuntimeError(
            "Experiment 2 profile cache predates the six-candidate payment "
            f"certificate; rerun Experiment 2. Missing: {sorted(missing_profile_fields)}"
        )
    projection_weights = stored["projection_weights"].astype(float)
    projection_candidate_names = [
        f"Projection rho={weight:g}" for weight in projection_weights
    ]
    projection_candidates = stored["projection_candidates"].astype(float)
    quantile_index = methods.index("Feasible Quantile Projection")
    quantile_profiles = stored["baselines"][:, quantile_index]
    # Retain the matched feasible-quantile profile in the hull for an external
    # transfer comparator, but anchor the contractual cap to the validation-
    # selected single feasible projection.  The cap is therefore not defined
    # by the same comparator used in the independent evaluation table.
    candidate_names = projection_candidate_names + [
        "Feasible Quantile Projection"
    ]
    candidate_profiles = np.concatenate(
        [projection_candidates, quantile_profiles[:, None, :, :]], axis=1
    )
    reference_candidate = int(stored["selected_single_projection_index"])
    risk_index = methods.index("Risk-Constrained Convex Verifier")
    risk_profiles = stored["baselines"][:, risk_index]
    actual = stored["actual"]
    oracle = stored["oracle"]
    event_slots = list(map(int, cfg["market"]["event_slots"]))
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    settlement_segments = int(cfg["market"]["generator_segments"])
    certificate_segments = int(
        cfg["experiments"].get(
            "payment_certificate_generator_segments", settlement_segments
        )
    )
    if certificate_segments < 2:
        raise ValueError("payment_certificate_generator_segments must be at least two")
    evaluation_segments = int(
        cfg["market"].get("n1_evaluation_generator_segments", 40)
    )
    system = power_system_from_ppc(case24_ieee_rts())
    security = build_n1_security_factors(system)
    dc_buses = np.asarray([2, 7, 14, 20], dtype=int)
    native = system.bus[:, 2] * float(
        cfg["experiments"].get("n1_load_multiplier", 0.9)
    )
    data_manifest_path = root / "data/processed/data_manifest.json"
    data_manifest = json.loads(data_manifest_path.read_text(encoding="utf-8"))
    conversion_quantiles = data_manifest["power_calibration"].get(
        "calibration_validation_job_energy_measured_to_predicted_quantiles",
        data_manifest["power_calibration"][
            "heldout_job_energy_measured_to_predicted_quantiles"
        ],
    )
    # Include both raw tails in the same robust certificate as the finite
    # interior scenarios. q99 is the declared network-calibration endpoint;
    # keeping it in this LP prevents the independent interval audit from
    # discovering an unprotected high-power payment endpoint.
    conversion_scenario_labels = ["q01", "q10", "q50", "q90", "q99"]
    conversion_scale_factors = np.asarray(
        [
            conversion_quantiles["0.01"],
            conversion_quantiles["0.1"],
            conversion_quantiles["0.5"],
            conversion_quantiles["0.9"],
            conversion_quantiles["0.99"],
        ],
        dtype=float,
    )
    fixed_facility_load_mw = float(cfg["project"]["fixed_facility_load_mw"])
    fixed_total_mw = fixed_facility_load_mw * len(dc_buses)
    candidate_flexible_profiles = _flexible_facility_component(
        candidate_profiles, fixed_facility_load_mw
    )
    # Target selection remains tied to the predeclared validation contract
    # (q10/q50/q90). The two raw tails are endpoint robustness constraints and
    # cannot alter the validation choice of the payment target.
    validation_scale_factors = conversion_scale_factors[1:4]
    if not (
        np.all(np.diff(conversion_scale_factors) > 0)
        and conversion_scale_factors[0] < 1.0
        and conversion_scale_factors[-1] > 1.0
    ):
        raise RuntimeError(
            "Calibration-validation power-conversion scenarios do not bracket unity"
        )
    peak_dc_mw = float(
        cfg["experiments"].get("n1_dc_peak_penetration", 0.06)
    ) * float(native.sum())
    validation_peak_trace_mw = float(
        max(
            validation_stored["oracle"][:, :, event_slots].sum(axis=1).max(),
            validation_stored["actual"][:, :, event_slots].sum(axis=1).max(),
            validation_stored["projection_candidates"][:, :, :, event_slots]
            .sum(axis=2)
            .max(),
            validation_stored["quantile_profile"][:, :, event_slots].sum(axis=1).max(),
        )
    )
    # Calibrate the benchmark scale on the complete calibration-validation q99 envelope,
    # while applying the conversion factor only to flexible workload service.
    # The fixed facility component is carried at one scale across all
    # scenarios, so q99 is a valid stress endpoint rather than an implicitly
    # infeasible activation request.
    validation_flexible_peak_mw = float(
        max(
            np.max(
                _flexible_facility_component(
                    validation_stored["oracle"], fixed_facility_load_mw
                )[:, :, event_slots].sum(axis=1)
            ),
            np.max(
                _flexible_facility_component(
                    validation_stored["actual"], fixed_facility_load_mw
                )[:, :, event_slots].sum(axis=1)
            ),
            np.max(
                _flexible_facility_component(
                    validation_stored["projection_candidates"], fixed_facility_load_mw
                )[:, :, :, event_slots].sum(axis=2)
            ),
            np.max(
                _flexible_facility_component(
                    validation_stored["quantile_profile"], fixed_facility_load_mw
                )[:, :, event_slots].sum(axis=1)
            ),
        )
    )
    q99_factor = float(conversion_quantiles["0.99"])
    dc_scale = peak_dc_mw / max(
        fixed_total_mw + q99_factor * validation_flexible_peak_mw,
        1e-12,
    )
    network_native = native.copy()
    network_native[dc_buses] += fixed_facility_load_mw * dc_scale

    # Freeze the end-to-end payment target on validation days.  This is a
    # finite, predeclared candidate selection: each candidate is evaluated by
    # the independent high-resolution N-1 value model against the validation
    # event response, then the selected target is held fixed for every locked
    # test certificate.  No test-day payment or peak is used in this choice.
    validation_candidate_profiles = np.concatenate(
        [
            validation_stored["projection_candidates"].transpose(1, 0, 2, 3),
            validation_stored["quantile_profile"][:, None, :, :],
        ],
        axis=1,
    )
    validation_actual = validation_stored["actual"]
    validation_oracle = validation_stored["oracle"]
    validation_selection_path = final / "payment_target_selection_validation.csv"
    validation_candidate_checksum = hashlib.sha256(
        b"fixed-flexible-network-conversion-v2"
        + np.ascontiguousarray(validation_candidate_profiles).tobytes()
        + np.ascontiguousarray(validation_scale_factors, dtype=np.float64).tobytes()
        + np.asarray([dc_scale, fixed_facility_load_mw], dtype=np.float64).tobytes()
    ).hexdigest()
    cached_validation_selection: pd.DataFrame | None = None
    validation_selection_cache_valid = False
    if validation_selection_path.exists():
        try:
            cached = pd.read_csv(validation_selection_path)
            expected_indices = set(range(validation_candidate_profiles.shape[1]))
            expected_cells = int(
                validation_actual.shape[0]
                * len(validation_scale_factors)
                * len(event_slots)
            )
            validation_selection_cache_valid = (
                set(cached.columns).issuperset(
                    {
                        "candidate_index",
                        "candidate_name",
                        "mean_validation_payment_mae_usd",
                        "validation_cells",
                    }
                )
                and set(cached["candidate_index"].astype(int)) == expected_indices
                and set(cached["candidate_name"].astype(str)) == set(candidate_names)
                and set(cached["validation_cells"].astype(int)) == {expected_cells}
                and "candidate_checksum" in cached.columns
                and set(cached["candidate_checksum"].astype(str))
                == {validation_candidate_checksum}
            )
            if validation_selection_cache_valid:
                cached_validation_selection = cached.copy()
        except (OSError, ValueError, KeyError):
            validation_selection_cache_valid = False
    validation_payment_rows: list[dict[str, Any]] = []
    # Materialize each exact load vector once, then solve the resulting finite
    # set in parallel.  This is an execution optimization only: every listed
    # load still goes through the same high-resolution N-1 SCED evaluator.
    validation_loads: dict[bytes, np.ndarray] = {}
    validation_actual_keys = np.empty(
        (validation_actual.shape[0], len(validation_scale_factors), len(event_slots)),
        dtype=object,
    )
    validation_oracle_keys = np.empty_like(validation_actual_keys)
    validation_candidate_keys = np.empty(
        (
            validation_candidate_profiles.shape[0],
            validation_candidate_profiles.shape[1],
            len(validation_scale_factors),
            len(event_slots),
        ),
        dtype=object,
    )

    def register_validation_load(profile: np.ndarray, local_day: int, slot: int, scale: float) -> bytes:
        load = _network_load_from_facility_profile(
            native,
            dc_buses,
            profile[local_day, :, slot],
            dc_scale=dc_scale,
            conversion_scale=scale,
            fixed_facility_load_mw=fixed_facility_load_mw,
        )
        key = np.ascontiguousarray(load, dtype=np.float64).tobytes()
        validation_loads.setdefault(key, load)
        return key

    for local_day in range(validation_actual.shape[0]):
        for scale_index, scale_factor in enumerate(validation_scale_factors):
            for slot_index, slot in enumerate(event_slots):
                validation_actual_keys[local_day, scale_index, slot_index] = register_validation_load(
                    validation_actual, local_day, slot, scale_factor
                )
                validation_oracle_keys[local_day, scale_index, slot_index] = register_validation_load(
                    validation_oracle, local_day, slot, scale_factor
                )
                for candidate_index in range(validation_candidate_profiles.shape[1]):
                    validation_candidate_keys[
                        local_day, candidate_index, scale_index, slot_index
                    ] = register_validation_load(
                        validation_candidate_profiles[candidate_index]
                        if validation_candidate_profiles.ndim == 5
                        else validation_candidate_profiles[:, candidate_index],
                        local_day,
                        slot,
                        scale_factor,
                    )

    # Reusing a validated selection file avoids repeating the identical
    # high-resolution SCED panel when an independent test-day checkpoint is
    # resumed.  The finite selection itself remains unchanged.
    if validation_selection_cache_valid:
        validation_loads = {}

    def solve_validation_load(item: tuple[bytes, np.ndarray]) -> tuple[bytes, float]:
        key, load = item
        result = solve_n1_sced(
            system,
            load,
            evaluation_segments,
            security_factors=security,
        )
        if not result.success:
            raise RuntimeError(
                "Validation payment-target N-1 evaluator failed: "
                f"{result.solver_message}"
            )
        return key, float(result.objective)

    validation_workers = int(
        cfg["experiments"].get("payment_target_selection_parallel_workers", 6)
    )
    if validation_workers <= 0:
        raise ValueError("payment_target_selection_parallel_workers must be positive")
    validation_objectives: dict[bytes, float] = (
        defaultdict(float) if validation_selection_cache_valid else {}
    )
    validation_progress = tqdm(
        total=len(validation_loads),
        desc="Exp9 validation payment-target SCED",
    )
    with ThreadPoolExecutor(max_workers=validation_workers) as executor:
        for key, objective in executor.map(
            solve_validation_load, validation_loads.items()
        ):
            validation_objectives[key] = objective
            validation_progress.update(1)
    validation_progress.close()

    for candidate_index in range(validation_candidate_profiles.shape[1]):
        absolute_errors: list[float] = []
        for local_day in range(validation_candidate_profiles.shape[0]):
            for scale_index, scale_factor in enumerate(validation_scale_factors):
                for slot_index, slot in enumerate(event_slots):
                    actual_value = validation_objectives[
                        validation_actual_keys[local_day, scale_index, slot_index]
                    ]
                    oracle_value = validation_objectives[
                        validation_oracle_keys[local_day, scale_index, slot_index]
                    ]
                    candidate_value = validation_objectives[
                        validation_candidate_keys[
                            local_day, candidate_index, scale_index, slot_index
                        ]
                    ]
                    absolute_errors.append(
                        float(
                            abs(
                                (candidate_value - actual_value)
                                - (oracle_value - actual_value)
                            )
                            * dt_h
                        )
                    )
        validation_payment_rows.append(
            {
                "candidate_index": int(candidate_index),
                "candidate_name": candidate_names[candidate_index],
                "mean_validation_payment_mae_usd": float(np.mean(absolute_errors)),
                "validation_cells": int(len(absolute_errors)),
            }
        )
    if validation_selection_cache_valid and cached_validation_selection is not None:
        validation_payment_selection = cached_validation_selection.sort_values(
            ["mean_validation_payment_mae_usd", "candidate_index"]
        ).copy()
    else:
        validation_payment_selection = pd.DataFrame(validation_payment_rows).sort_values(
            ["mean_validation_payment_mae_usd", "candidate_index"]
        )
    payment_target_candidate_index = int(
        validation_payment_selection.iloc[0]["candidate_index"]
    )
    validation_payment_selection["selected"] = (
        validation_payment_selection["candidate_index"].astype(int)
        == payment_target_candidate_index
    )
    validation_payment_selection["candidate_checksum"] = validation_candidate_checksum
    validation_payment_selection.to_csv(validation_selection_path, index=False)
    payment_target_profiles = candidate_profiles[:, payment_target_candidate_index]
    # Make the two selection roles machine-readable.  The contractual cap and
    # the payment target are intentionally frozen by different validation
    # criteria; recording this separation prevents a fixed-plan identity from
    # being presented as an out-of-sample accuracy result.
    cap_selection_row = validation_payment_selection[
        validation_payment_selection["candidate_index"].astype(int)
        == reference_candidate
    ].iloc[0]
    target_selection_row = validation_payment_selection[
        validation_payment_selection["candidate_index"].astype(int)
        == payment_target_candidate_index
    ].iloc[0]
    pd.DataFrame(
        [
            {
                "role": "contractual payment cap",
                "candidate_index": reference_candidate,
                "candidate_name": candidate_names[reference_candidate],
                "selection_split": "validation",
                "selection_metric": "worst contiguous-fold nRMSE (Experiment 2)",
                "payment_mae_on_selection_split_usd": float(
                    cap_selection_row["mean_validation_payment_mae_usd"]
                ),
                "test_days_used_for_selection": False,
            },
            {
                "role": "payment target",
                "candidate_index": payment_target_candidate_index,
                "candidate_name": candidate_names[payment_target_candidate_index],
                "selection_split": "validation",
                "selection_metric": "independent high-resolution N-1 payment MAE",
                "payment_mae_on_selection_split_usd": float(
                    target_selection_row["mean_validation_payment_mae_usd"]
                ),
                "test_days_used_for_selection": False,
            },
            {
                "role": "role separation",
                "candidate_index": -1,
                "candidate_name": "cap and target are distinct candidates",
                "selection_split": "validation only",
                "selection_metric": "cap nRMSE and target payment MAE are not the same criterion",
                "payment_mae_on_selection_split_usd": np.nan,
                "test_days_used_for_selection": False,
            },
        ]
    ).to_csv(final / "payment_non_tautology_audit.csv", index=False)

    certificate_checkpoint = intermediate / "payment_certificate_checkpoint.csv"
    profile_checkpoint = intermediate / "certified_profiles_checkpoint.npz"
    certificate_rows: list[dict[str, Any]] = []
    certified_profiles = np.full_like(actual, np.nan)
    completed: set[int] = set()
    # Schema 10 adds q99 to the robust vertex-cost Jensen certificate; older
    # checkpoints belong to a smaller scenario contract.
    certificate_schema_version = 10
    candidate_checksum = hashlib.sha256(
        b"fixed-flexible-network-conversion-v2"
        + np.ascontiguousarray(candidate_profiles).tobytes()
        + np.ascontiguousarray(conversion_scale_factors, dtype=np.float64).tobytes()
        + np.asarray([dc_scale, fixed_facility_load_mw], dtype=np.float64).tobytes()
    ).hexdigest()
    if resume and certificate_checkpoint.exists() and profile_checkpoint.exists():
        previous = pd.read_csv(certificate_checkpoint)
        previous_profiles = np.load(profile_checkpoint, allow_pickle=False)
        valid_checkpoint = (
            "certificate_schema_version" in previous
            and set(previous["certificate_schema_version"].astype(int).unique())
            == {certificate_schema_version}
            and "candidate_checksum" in previous
            and set(previous["candidate_checksum"].astype(str).unique())
            == {candidate_checksum}
            and np.array_equal(previous_profiles["days"], days)
            and "candidate_checksum" in previous_profiles.files
            and str(previous_profiles["candidate_checksum"])
            == candidate_checksum
        )
        if valid_checkpoint:
            certified_profiles = previous_profiles["profiles"]
            completed = set(int(value) for value in previous["day"])
            certificate_rows = previous.to_dict("records")
            logger.info(
                "Resuming Experiment 9 with %d complete payment certificates",
                len(completed),
            )
    certificate_workers = int(
        cfg["experiments"].get("payment_certificate_parallel_workers", 6)
    )
    if certificate_workers <= 0:
        raise ValueError("payment_certificate_parallel_workers must be positive")

    def solve_certificate_day(
        item: tuple[int, int],
    ) -> tuple[int, int, Any]:
        local_day, day = item
        candidates_scaled = candidate_flexible_profiles[local_day] * dc_scale
        certificate = solve_payment_certified_n1_projection(
            system=system,
            native_load_mw=network_native,
            dc_buses=dc_buses,
            candidate_profiles_mw=candidates_scaled,
            target_profile_mw=(
                _flexible_facility_component(
                    payment_target_profiles[local_day], fixed_facility_load_mw
                )
                * dc_scale
            ),
            reference_candidate=reference_candidate,
            event_slots=event_slots,
            dt_h=dt_h,
            segments=certificate_segments,
            security_factors=security,
            conversion_scale_factors=conversion_scale_factors,
        )
        return local_day, day, certificate

    pending_certificate_days = [
        (local_day, int(day))
        for local_day, day in enumerate(days)
        if int(day) not in completed
    ]
    certificate_progress = tqdm(
        total=len(days),
        initial=len(completed),
        desc="Exp9 robust N-1 payment certificates",
    )
    with ThreadPoolExecutor(max_workers=certificate_workers) as executor:
        for local_day, day, certificate in executor.map(
            solve_certificate_day, pending_certificate_days
        ):
            if not certificate.success:
                raise RuntimeError(
                    f"Payment certificate failed for day {day}: "
                    f"{certificate.solver_message}"
                )
            certified_profiles[local_day] = (
                fixed_facility_load_mw
                + certificate.profile_mw / max(dc_scale, 1.0e-12)
            )
            certificate_rows.append(
                {
                    "day": int(day),
                    "solver_success": 1,
                    "global_lp_status": certificate.solver_message,
                    "mean_absolute_target_deviation_mw": (
                        certificate.objective_l1_mw
                    ),
                    "first_stage_optimal_target_deviation_mw": (
                        certificate.first_stage_optimal_l1_mw
                    ),
                    "worst_case_fractional_cost_margin": (
                        certificate.worst_case_fractional_cost_margin
                    ),
                    "certified_n1_baseline_cost_usd": (
                        certificate.certified_baseline_cost_usd
                    ),
                    "reference_n1_baseline_cost_usd": (
                        certificate.reference_baseline_cost_usd
                    ),
                    "payment_cap_violation_usd": (
                        certificate.maximum_cost_violation_usd
                    ),
                    "certificate_schema_version": certificate_schema_version,
                    "candidate_checksum": candidate_checksum,
                    **{
                        f"conversion_scale_{label}": float(scale)
                        for label, scale in zip(
                            conversion_scenario_labels,
                            certificate.conversion_scale_factors,
                        )
                    },
                    **{
                        f"certified_cost_{label}_usd": float(cost)
                        for label, cost in zip(
                            conversion_scenario_labels,
                            certificate.scenario_certified_cost_usd,
                        )
                    },
                    **{
                        f"reference_cost_{label}_usd": float(cost)
                        for label, cost in zip(
                            conversion_scenario_labels,
                            certificate.scenario_reference_cost_usd,
                        )
                    },
                    **{
                        f"weight_rho_{projection_weight:g}": float(weight)
                        for projection_weight, weight in zip(
                            projection_weights, certificate.weights[:-1]
                        )
                    },
                    "weight_feasible_quantile": float(
                        certificate.weights[-1]
                    )
                },
            )
            pd.DataFrame(certificate_rows).to_csv(
                certificate_checkpoint, index=False
            )
            np.savez_compressed(
                profile_checkpoint,
                days=days,
                profiles=certified_profiles,
                candidate_checksum=np.asarray(candidate_checksum),
            )
            completed.add(int(day))
            certificate_progress.update(1)
    certificate_progress.close()
    certificates = pd.DataFrame(certificate_rows).sort_values("day")
    certificates.to_csv(final / "daily_payment_certificates.csv", index=False)
    scenario_certificate_rows: list[dict[str, Any]] = []
    for row in certificates.itertuples(index=False):
        for label in conversion_scenario_labels:
            certified_cost = float(
                getattr(row, f"certified_cost_{label}_usd")
            )
            reference_cost = float(
                getattr(row, f"reference_cost_{label}_usd")
            )
            scenario_certificate_rows.append(
                {
                    "day": int(row.day),
                    "conversion_scenario": label,
                    "conversion_scale_factor": float(
                        getattr(row, f"conversion_scale_{label}")
                    ),
                    "certified_n1_baseline_cost_usd": certified_cost,
                    "reference_n1_baseline_cost_usd": reference_cost,
                    "payment_cap_margin_usd": reference_cost - certified_cost,
                    "payment_cap_violation_usd": max(
                        0.0, certified_cost - reference_cost
                    ),
                }
            )
    scenario_certificates = pd.DataFrame(scenario_certificate_rows)
    scenario_certificates.to_csv(
        final / "conversion_scenario_certificates.csv", index=False
    )
    np.savez_compressed(
        final / "certified_counterfactual_profiles.npz",
        days=days,
        profiles=certified_profiles,
        candidate_names=np.asarray(candidate_names),
        projection_weights=projection_weights,
        reference_candidate=np.asarray(reference_candidate),
        candidate_checksum=np.asarray(candidate_checksum),
        fixed_facility_load_mw=np.asarray(fixed_facility_load_mw),
        network_dc_scale=np.asarray(dc_scale),
    )

    qualities = [
        "Feasible Quantile Projection",
        "Single Feasible Projection",
        "Risk-Constrained Convex Verifier",
        "Payment-Certified N-1 Verifier",
    ]
    quality_profiles = {
        "Feasible Quantile Projection": quantile_profiles,
        "Single Feasible Projection": projection_candidates[
            :, int(stored["selected_single_projection_index"])
        ],
        "Risk-Constrained Convex Verifier": risk_profiles,
        "Payment-Certified N-1 Verifier": certified_profiles,
    }
    settlement_checkpoint = intermediate / "payment_evaluation_checkpoint.csv"
    rows: list[dict[str, Any]] = []
    completed_days: set[int] = set()
    evaluation_schema_version = 7
    certified_checksum = hashlib.sha256(
        np.ascontiguousarray(certified_profiles).tobytes()
    ).hexdigest()
    if resume and settlement_checkpoint.exists():
        previous = pd.read_csv(settlement_checkpoint)
        expected = (
            len(event_slots)
            * len(qualities)
            * len(conversion_scale_factors)
        )
        valid_evaluation_checkpoint = (
            "evaluation_schema_version" in previous
            and set(previous["evaluation_schema_version"].astype(int).unique())
            == {evaluation_schema_version}
            and "certified_checksum" in previous
            and set(previous["certified_checksum"].astype(str).unique())
            == {certified_checksum}
        )
        if valid_evaluation_checkpoint:
            counts = previous.groupby("day").size()
            completed_days = set(
                int(day) for day in counts[counts == expected].index
            )
            rows = previous[
                previous["day"].isin(completed_days)
            ].to_dict("records")
    evaluation_workers = int(
        cfg["experiments"].get("payment_evaluation_parallel_workers", 6)
    )
    if evaluation_workers <= 0:
        raise ValueError("payment_evaluation_parallel_workers must be positive")

    def evaluate_payment_day(
        item: tuple[int, int],
    ) -> tuple[int, list[dict[str, Any]]]:
        local_day, day = item
        day_rows: list[dict[str, Any]] = []
        dispatch_cache: dict[tuple[int, bytes], Any] = {}

        def cached_n1_dispatch(
            load: np.ndarray, segment_count: int
        ) -> Any:
            # Reuse only bitwise-identical load vectors.  No rounding or
            # approximate state aggregation changes the declared evaluator.
            key = (
                int(segment_count),
                np.ascontiguousarray(load, dtype=np.float64).tobytes(),
            )
            if key not in dispatch_cache:
                dispatch_cache[key] = solve_n1_sced(
                    system,
                    load,
                    segment_count,
                    security_factors=security,
                )
            return dispatch_cache[key]

        for scenario_label, scale_factor in zip(
            conversion_scenario_labels, conversion_scale_factors
        ):
            for slot in event_slots:
                actual_load = _network_load_from_facility_profile(
                    native,
                    dc_buses,
                    actual[local_day, :, slot],
                    dc_scale=dc_scale,
                    conversion_scale=scale_factor,
                    fixed_facility_load_mw=fixed_facility_load_mw,
                )
                oracle_load = _network_load_from_facility_profile(
                    native,
                    dc_buses,
                    oracle[local_day, :, slot],
                    dc_scale=dc_scale,
                    conversion_scale=scale_factor,
                    fixed_facility_load_mw=fixed_facility_load_mw,
                )
                actual_settlement = cached_n1_dispatch(
                    actual_load, settlement_segments
                )
                actual_evaluation = cached_n1_dispatch(
                    actual_load, evaluation_segments
                )
                oracle_evaluation = cached_n1_dispatch(
                    oracle_load, evaluation_segments
                )
                realized_value = (
                    oracle_evaluation.objective
                    - actual_evaluation.objective
                ) * dt_h
                for quality in qualities:
                    baseline_load = _network_load_from_facility_profile(
                        native,
                        dc_buses,
                        quality_profiles[quality][local_day, :, slot],
                        dc_scale=dc_scale,
                        conversion_scale=scale_factor,
                        fixed_facility_load_mw=fixed_facility_load_mw,
                    )
                    baseline_settlement = cached_n1_dispatch(
                        baseline_load, settlement_segments
                    )
                    payment = (
                        baseline_settlement.objective
                        - actual_settlement.objective
                    ) * dt_h
                    day_rows.append(
                        {
                            "day": int(day),
                            "conversion_scenario": scenario_label,
                            "conversion_scale_factor": float(scale_factor),
                            "event_slot": int(slot),
                            "counterfactual_method": quality,
                            "settlement_payment_usd": float(payment),
                            "independent_realized_value_usd": float(
                                realized_value
                            ),
                            "absolute_error_usd": float(
                                abs(payment - realized_value)
                            ),
                            "overpayment_usd": float(
                                max(0.0, payment - realized_value)
                            ),
                            "maximum_post_contingency_loading": float(
                                baseline_settlement.max_post_contingency_loading
                            ),
                            "credible_line_contingencies": int(
                                baseline_settlement.credible_contingencies
                            ),
                            "evaluation_schema_version": (
                                evaluation_schema_version
                            ),
                            "certified_checksum": certified_checksum,
                            "payment_evaluation_profile_checksum": payment_evaluation_profile_checksum,
                        }
                    )
        return int(day), day_rows

    pending_days = [
        (local_day, int(day))
        for local_day, day in enumerate(days)
        if int(day) not in completed_days
    ]
    progress = tqdm(
        total=len(days),
        initial=len(completed_days),
        desc="Exp9 independent N-1 payment evaluation",
    )
    with ThreadPoolExecutor(max_workers=evaluation_workers) as executor:
        for day, day_rows in executor.map(evaluate_payment_day, pending_days):
            rows.extend(day_rows)
            completed_days.add(day)
            pd.DataFrame(rows).to_csv(settlement_checkpoint, index=False)
            progress.update(1)
    progress.close()
    interval = pd.DataFrame(rows).sort_values(
        [
            "day",
            "conversion_scale_factor",
            "event_slot",
            "counterfactual_method",
        ]
    )
    # CSV checkpoint round-trips can change the last binary digit of an
    # otherwise identical float.  The scenario label is the declared discrete
    # key, so restore its unique manifest-derived factor before grouping.
    declared_scale_by_label = {
        label: float(scale)
        for label, scale in zip(
            conversion_scenario_labels, conversion_scale_factors
        )
    }
    interval["conversion_scale_factor"] = interval[
        "conversion_scenario"
    ].map(declared_scale_by_label)
    interval.to_csv(final / "payment_evaluation_intervals.csv", index=False)
    daily = (
        interval.groupby(
            [
                "day",
                "conversion_scenario",
                "conversion_scale_factor",
                "counterfactual_method",
            ],
            as_index=False,
        )
        .agg(
            settlement_payment_usd=("settlement_payment_usd", "sum"),
            independent_realized_value_usd=("independent_realized_value_usd", "sum"),
            maximum_post_contingency_loading=(
                "maximum_post_contingency_loading", "max"
            ),
        )
    )
    daily["absolute_error_usd"] = np.abs(
        daily["settlement_payment_usd"] - daily["independent_realized_value_usd"]
    )
    daily["overpayment_usd"] = np.maximum(
        0.0,
        daily["settlement_payment_usd"] - daily["independent_realized_value_usd"],
    )
    daily.to_csv(final / "payment_evaluation_daily.csv", index=False)
    summary = (
        daily.groupby(
            [
                "conversion_scenario",
                "conversion_scale_factor",
                "counterfactual_method",
            ],
            as_index=False,
        )
        .agg(
            mean_payment_usd=("settlement_payment_usd", "mean"),
            mean_realized_value_usd=("independent_realized_value_usd", "mean"),
            mean_absolute_error_usd=("absolute_error_usd", "mean"),
            mean_overpayment_usd=("overpayment_usd", "mean"),
            maximum_post_contingency_loading=(
                "maximum_post_contingency_loading", "max"
            ),
        )
    )
    summary.to_csv(final / "payment_evaluation_summary.csv", index=False)

    # Payment protection and forecast accuracy are distinct objectives.  A
    # paired, dependence-aware Pareto panel reports both rather than allowing
    # the lower overpayment of the certified profile to be mistaken for lower
    # absolute error.  Bootstrap resampling is performed over ordered days for
    # each conversion scenario, so no locked-day outcome is used for selection.
    pareto_rows: list[dict[str, Any]] = []
    bootstrap_reps = int(cfg["experiments"].get("bootstrap_replications", 5000))
    block_days = int(cfg["experiments"].get("block_length_days", 3))
    for scenario_label in conversion_scenario_labels:
        scenario_daily = daily[
            daily["conversion_scenario"].astype(str) == scenario_label
        ].sort_values(["day", "counterfactual_method"])
        certified_daily = scenario_daily[
            scenario_daily["counterfactual_method"] == "Payment-Certified N-1 Verifier"
        ].sort_values("day")
        for method in qualities:
            if method == "Payment-Certified N-1 Verifier":
                continue
            comparator_daily = scenario_daily[
                scenario_daily["counterfactual_method"] == method
            ].sort_values("day")
            if len(certified_daily) != len(comparator_daily) or len(certified_daily) == 0:
                raise RuntimeError(
                    f"Payment Pareto panel has incomplete day pairing for {scenario_label}/{method}"
                )
            error_difference = (
                certified_daily["absolute_error_usd"].to_numpy(dtype=float)
                - comparator_daily["absolute_error_usd"].to_numpy(dtype=float)
            )
            overpayment_difference = (
                certified_daily["overpayment_usd"].to_numpy(dtype=float)
                - comparator_daily["overpayment_usd"].to_numpy(dtype=float)
            )
            error_seed = int.from_bytes(
                hashlib.sha256(f"{scenario_label}|{method}|error".encode()).digest()[:4],
                "big",
            )
            over_seed = int.from_bytes(
                hashlib.sha256(f"{scenario_label}|{method}|over".encode()).digest()[:4],
                "big",
            )
            error_mean, error_lo, error_hi = moving_block_bootstrap_mean_ci(
                error_difference, bootstrap_reps, block_days,
                int(cfg["project"]["seed"]) + error_seed % 100000,
            )
            over_mean, over_lo, over_hi = moving_block_bootstrap_mean_ci(
                overpayment_difference, bootstrap_reps, block_days,
                int(cfg["project"]["seed"]) + over_seed % 100000,
            )
            pareto_rows.append(
                {
                    "conversion_scenario": scenario_label,
                    "comparator": method,
                    "paired_days": int(len(error_difference)),
                    "certified_minus_comparator_absolute_error_mean_usd": error_mean,
                    "absolute_error_difference_ci95_low_usd": error_lo,
                    "absolute_error_difference_ci95_high_usd": error_hi,
                    "certified_minus_comparator_overpayment_mean_usd": over_mean,
                    "overpayment_difference_ci95_low_usd": over_lo,
                    "overpayment_difference_ci95_high_usd": over_hi,
                    "certified_overpayment_noninferior": bool(over_hi <= 0.0),
                    "certified_accuracy_noninferior": bool(error_hi <= 0.0),
                    "bootstrap_replications": bootstrap_reps,
                    "block_length_days": block_days,
                }
            )
    pd.DataFrame(pareto_rows).to_csv(final / "payment_pareto_paired_ci.csv", index=False)

    # Independent transfer panel: these two interior conversion factors are
    # deliberately absent from the certificate LP and from validation target
    # selection.  They reuse only the frozen profiles and the high-resolution
    # N--1 evaluator, so the resulting payment/value errors test transfer
    # rather than re-reporting the certificate's own right-hand-side bound.
    unseen_scale_factors = np.asarray([0.80, 1.20], dtype=float)
    unseen_labels = ["heldout-interior-low", "heldout-interior-high"]
    unseen_day_count = int(
        cfg["experiments"].get("payment_unseen_transfer_days", len(days))
    )
    if unseen_day_count <= 0:
        raise ValueError("payment_unseen_transfer_days must be positive")
    unseen_day_count = min(unseen_day_count, len(days))
    unseen_local_days = np.unique(
        np.linspace(0, len(days) - 1, unseen_day_count, dtype=int)
    ).astype(int)
    unseen_day_items = [
        (int(local_day), int(days[local_day])) for local_day in unseen_local_days
    ]
    unseen_rows: list[dict[str, Any]] = []

    def evaluate_unseen_payment_day(item: tuple[int, int]) -> tuple[int, list[dict[str, Any]]]:
        local_day, day = item
        day_rows: list[dict[str, Any]] = []
        dispatch_cache: dict[tuple[int, bytes], Any] = {}

        def unseen_dispatch(load: np.ndarray) -> Any:
            key = (int(evaluation_segments), np.ascontiguousarray(load, dtype=np.float64).tobytes())
            if key not in dispatch_cache:
                dispatch_cache[key] = solve_n1_sced(
                    system,
                    load,
                    evaluation_segments,
                    security_factors=security,
                )
            return dispatch_cache[key]

        for label, scale_factor in zip(unseen_labels, unseen_scale_factors):
            for slot in event_slots:
                actual_load = _network_load_from_facility_profile(
                    native,
                    dc_buses,
                    actual[local_day, :, slot],
                    dc_scale=dc_scale,
                    conversion_scale=scale_factor,
                    fixed_facility_load_mw=fixed_facility_load_mw,
                )
                oracle_load = _network_load_from_facility_profile(
                    native,
                    dc_buses,
                    oracle[local_day, :, slot],
                    dc_scale=dc_scale,
                    conversion_scale=scale_factor,
                    fixed_facility_load_mw=fixed_facility_load_mw,
                )
                actual_eval = unseen_dispatch(actual_load)
                oracle_eval = unseen_dispatch(oracle_load)
                realized_value = (oracle_eval.objective - actual_eval.objective) * dt_h
                for quality in qualities:
                    baseline_load = _network_load_from_facility_profile(
                        native,
                        dc_buses,
                        quality_profiles[quality][local_day, :, slot],
                        dc_scale=dc_scale,
                        conversion_scale=scale_factor,
                        fixed_facility_load_mw=fixed_facility_load_mw,
                    )
                    baseline_eval = unseen_dispatch(baseline_load)
                    payment = (baseline_eval.objective - actual_eval.objective) * dt_h
                    day_rows.append(
                        {
                            "day": int(day),
                            "conversion_scenario": label,
                            "conversion_scale_factor": float(scale_factor),
                            "event_slot": int(slot),
                            "counterfactual_method": quality,
                            "settlement_payment_usd": float(payment),
                            "independent_realized_value_usd": float(realized_value),
                            "absolute_error_usd": float(abs(payment - realized_value)),
                            "overpayment_usd": float(max(0.0, payment - realized_value)),
                            "maximum_post_contingency_loading": float(baseline_eval.max_post_contingency_loading),
                            "credible_line_contingencies": int(baseline_eval.credible_contingencies),
                            "evaluation_schema_version": int(evaluation_schema_version),
                            "certified_checksum": certified_checksum,
                            "payment_evaluation_profile_checksum": payment_evaluation_profile_checksum,
                            "certificate_used_scale": False,
                        }
                    )
        return int(day), day_rows

    with ThreadPoolExecutor(max_workers=evaluation_workers) as executor:
        for _, day_rows in executor.map(
            evaluate_unseen_payment_day,
            unseen_day_items,
        ):
            unseen_rows.extend(day_rows)
    unseen_frame = pd.DataFrame(unseen_rows).sort_values(
        ["day", "conversion_scale_factor", "event_slot", "counterfactual_method"]
    )
    unseen_frame.to_csv(final / "payment_evaluation_unseen_scenarios.csv", index=False)
    unseen_summary = (
        unseen_frame.groupby(
            ["conversion_scenario", "conversion_scale_factor", "counterfactual_method"],
            as_index=False,
        )
        .agg(
            mean_absolute_error_usd=("absolute_error_usd", "mean"),
            mean_overpayment_usd=("overpayment_usd", "mean"),
            maximum_post_contingency_loading=("maximum_post_contingency_loading", "max"),
        )
    )
    unseen_summary.to_csv(final / "payment_evaluation_unseen_summary.csv", index=False)
    paired = daily.pivot(
        index=["day", "conversion_scenario", "conversion_scale_factor"],
        columns="counterfactual_method",
        values="settlement_payment_usd",
    ).reset_index()
    comparison = paired[
        ["day", "conversion_scenario", "conversion_scale_factor"]
    ].copy()
    comparison["certified_minus_single_payment_usd"] = (
                paired["Payment-Certified N-1 Verifier"]
                - paired["Single Feasible Projection"]
            )
    comparison["certified_minus_feasible_quantile_payment_usd"] = (
        paired["Payment-Certified N-1 Verifier"]
        - paired["Feasible Quantile Projection"]
    )
    comparison["certified_minus_risk_verifier_payment_usd"] = (
                paired["Payment-Certified N-1 Verifier"]
                - paired["Risk-Constrained Convex Verifier"]
            )
    comparison.to_csv(final / "paired_payment_noninferiority.csv", index=False)
    plot_exp9(
        certificates,
        scenario_certificates,
        daily,
        folder / "figures",
        cfg,
    )
    write_json(
        final / "experiment_metadata.json",
        {
            "network": "IEEE RTS 24-bus",
            "locked_days": int(len(days)),
            "event_intervals_per_day": int(len(event_slots)),
            "candidate_counterfactuals": candidate_names,
            "projection_weights": projection_weights.tolist(),
            "reference_projection_weight": float(
                projection_weights[reference_candidate]
            ),
            "certificate_candidate_set": (
                "six first-stage workload-feasible projection schedules plus "
                "the validation-selected feasible-quantile comparator; the "
                "contractual cap is anchored to the validation-selected single "
                "feasible projection, while the risk-constrained verifier is "
                "reported as the separately fitted total-plus-daily-CVaR convex profile"
            ),
            "reference_candidate": candidate_names[reference_candidate],
            "contractual_cap_profile": candidate_names[reference_candidate],
            "contractual_cap_selection": (
                "single feasible projection selected by worst contiguous-fold validation nRMSE; "
                "its rho is recorded in Experiment 2 and is the sole payment-cap reference"
            ),
            "certificate_schema_version": certificate_schema_version,
            "test_profile_file_checksum": current_profile_checksum
            or hashlib.sha256(profile_path.read_bytes()).hexdigest(),
            "payment_evaluation_profile_source": (
                "current Experiment-2 locked test_profiles.npz"
            ),
            "payment_evaluation_profile_checksum": current_profile_checksum
            or hashlib.sha256(profile_path.read_bytes()).hexdigest(),
            "payment_evaluation_recomputed_after_profile_refit": True,
            "payment_evaluation_recompute_scope": (
                "the declared payment evaluator is rebuilt from the current "
                "Experiment-2 profile cache; byte-identical quality profiles "
                "may reuse their numerically identical rows, while any changed "
                "profile is re-solved before the panel is finalized"
            ),
            "validation_profile_file_checksum": current_validation_profile_checksum
            or hashlib.sha256(validation_profile_path.read_bytes()).hexdigest(),
            "data_manifest_checksum": current_data_manifest_checksum
            or hashlib.sha256(data_manifest_path_for_resume.read_bytes()).hexdigest(),
            "config_checksum": current_config_checksum,
            "optimization": (
                "two lexicographically ordered global linear programs per day "
                "over the complete workload-feasible convex hull. The contractual "
                "certificate uses a four-segment N-1 SCED value model at every "
                "declared conversion scenario; convexity of the exact value "
                "function makes the vertex-cost Jensen upper bound explicit, "
                "while the locked evaluator is independently replayed at the "
                "higher-resolution N-1 model"
            ),
            "power_conversion_scenario_source": (
                "1st, 10th, 50th, 90th, and 99th percentiles of calibration-validation per-job "
                "measured-to-predicted energy ratios from the full MIT DCGM table; "
                "the two tails are included in the payment certificate"
            ),
            "power_conversion_scenarios": {
                label: float(scale)
                for label, scale in zip(
                    conversion_scenario_labels, conversion_scale_factors
                )
            },
            "q99_conversion_factor": q99_factor,
            "network_conversion_decomposition": {
                "fixed_facility_load_mw_per_site": fixed_facility_load_mw,
                "fixed_component_scaled_once": True,
                "flexible_component_scaled_by_conversion_factor": True,
                "validation_flexible_peak_mw": validation_flexible_peak_mw,
                "fixed_total_mw_before_network_scale": fixed_total_mw,
                "network_scale_calibrated_on_q99": True,
                "network_peak_target_mw": peak_dc_mw,
                "formula": "L_dc = dc_scale * (fixed + xi * (p_facility - fixed))",
            },
            "reference_payment_cap": candidate_names[reference_candidate],
            "external_transfer_comparator": "Feasible Quantile Projection",
            "payment_target_selection": (
                "validation-only independent N-1 payment MAE over q10/q50/q90 "
                "calibration-validation conversion scenarios and event slots; q01 and q99 are "
                "endpoint robustness constraints in the same frozen calibration-validation set"
            ),
            "selection_role_separation": (
                "The contractual cap and payment target are frozen by different validation "
                "criteria: the cap uses worst contiguous-fold nRMSE from Experiment 2, "
                "whereas the target uses independent high-resolution N-1 payment MAE. "
                "Neither criterion reads locked-test outcomes."
            ),
            "payment_target_candidate": candidate_names[payment_target_candidate_index],
            "payment_target_candidate_index": payment_target_candidate_index,
            "payment_target_profile": candidate_names[payment_target_candidate_index],
            "payment_pareto_file": "payment_pareto_paired_ci.csv",
            "payment_pareto_interpretation": (
                "paired moving-block confidence intervals report certified-minus-comparator "
                "changes separately for absolute payment error and overpayment; the certificate "
                "claim is a payment-cap/noninferiority guarantee, not universal MAE dominance"
            ),
            "profile_lineage": {
                "p_cap": candidate_names[reference_candidate],
                "p_pay": candidate_names[payment_target_candidate_index],
                "p_cert": "locked-day convex combination constrained by the p_cap cost cap and targeted to p_pay",
            },
            "credible_non_islanding_line_contingencies": int(security[3]),
            "settlement_generator_segments": settlement_segments,
            "payment_certificate_generator_segments": certificate_segments,
            "independent_evaluation_generator_segments": evaluation_segments,
            "independent_evaluation_parallel_workers": evaluation_workers,
            "unseen_transfer_evaluation": {
                "daily_file": "payment_evaluation_unseen_scenarios.csv",
                "summary_file": "payment_evaluation_unseen_summary.csv",
                "scale_factors": unseen_scale_factors.tolist(),
                "locked_days_evaluated": int(len(unseen_day_items)),
                "day_selection_rule": (
                    "evenly spaced indices over the locked 54-day sequence; "
                    "the primary independent evaluator remains full-horizon"
                ),
                "scenarios_used_in_certificate": False,
                "target_selection_used": False,
                "interpretation": (
                    "Frozen certificate profiles are replayed at two interior conversion factors "
                    "that were not included in the certificate LP or validation target selection."
                ),
            },
            "certificate_parallel_workers": certificate_workers,
            "maximum_payment_cap_violation_usd": float(
                certificates["payment_cap_violation_usd"].max()
            ),
            "dc_power_scale": dc_scale,
            "validation_peak_trace_mw": validation_peak_trace_mw,
            "validation_flexible_peak_mw": validation_flexible_peak_mw,
            "test_peak_used_for_scaling": False,
        },
    )
    logger.info(
        "Experiment 9 complete: %d robust daily payment certificates and %d "
        "independent interval outcomes",
        len(certificates),
        len(interval),
    )


def run_exp10(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
    resume: bool = False,
) -> None:
    """Evaluate the complete locked-day peak panel with nonlinear AC OPF."""
    from pypower.case24_ieee_rts import case24_ieee_rts
    from pypower.case9 import case9
    from pypower.case14 import case14
    from pypower.case30 import case30
    from pypower.case39 import case39
    from pypower.case118 import case118
    from pypower.idx_brch import BR_STATUS, PF, PT, QF, QT, RATE_A
    from pypower.idx_bus import BUS_TYPE, PD, QD, REF, VM, VMAX, VMIN
    from pypower.idx_gen import GEN_BUS, PG, PMAX, PMIN
    from pypower.ppoption import ppoption
    from pypower.runopf import runopf
    from pypower.runpf import runpf
    import networkx as nx
    from .visualization import plot_exp10

    folder = root / "experiments/exp10_ac_validation"
    final = folder / "results/final"
    intermediate = folder / "results/intermediate"
    final.mkdir(parents=True, exist_ok=True)
    intermediate.mkdir(parents=True, exist_ok=True)
    profile_path = (
        root
        / "experiments/exp2_baseline_verification/results/intermediate/test_profiles.npz"
    )
    certified_path = (
        root
        / "experiments/exp9_payment_certificate/results/final/"
        "certified_counterfactual_profiles.npz"
    )
    if not profile_path.exists():
        run_exp2(root, cfg, logger)
    if not certified_path.exists():
        run_exp9(root, cfg, logger, resume=True)
    stored = np.load(profile_path, allow_pickle=False)
    certified = np.load(certified_path, allow_pickle=False)
    days = stored["days"].astype(int)
    if not np.array_equal(days, certified["days"]):
        raise RuntimeError("Experiment 10 profile-day mismatch")
    methods = [str(value) for value in stored["methods"]]
    quality_profiles = {
        "Feasible Quantile Projection": stored["baselines"][
            :, methods.index("Feasible Quantile Projection")
        ],
        "Single Feasible Projection": stored["baselines"][
            :, methods.index("Single Feasible Projection")
        ],
        "Risk-Constrained Convex Verifier": stored["baselines"][
            :, methods.index("Risk-Constrained Convex Verifier")
        ],
        "Payment-Certified N-1 Verifier": certified["profiles"],
    }
    actual = stored["actual"]
    oracle = stored["oracle"]
    event_slots = np.asarray(cfg["market"]["event_slots"], dtype=int)
    peak_slots = event_slots[
        np.argmax(actual[:, :, event_slots].sum(axis=1), axis=1)
    ]
    networks = [
        ("IEEE RTS 24-bus", case24_ieee_rts, np.asarray([2, 7, 14, 20])),
        ("IEEE 30-bus", case30, np.asarray([4, 11, 19, 26])),
        ("IEEE 39-bus", case39, np.asarray([3, 14, 25, 38])),
        ("IEEE 118-bus", case118, np.asarray([14, 41, 79, 115])),
    ]
    load_multiplier = float(
        cfg["experiments"].get("ac_load_multiplier", 0.9)
    )
    penetration = float(
        cfg["experiments"].get("ac_dc_peak_penetration", 0.06)
    )
    power_factor = float(
        cfg["experiments"].get("ac_data_center_power_factor", 0.95)
    )
    reactive_ratio = float(np.tan(np.arccos(power_factor)))
    # AC results depend on both counterfactual profile artifacts.  Parameter
    # checks alone are insufficient because a rerun can retain the same
    # method names and AC settings while changing the locked days or profile
    # values.  Every AC checkpoint row therefore carries a schema version and
    # a cryptographic fingerprint of its two upstream profile artifacts.
    ac_checkpoint_schema_version = 2
    ac_profile_digest = hashlib.sha256()
    ac_profile_digest.update(profile_path.read_bytes())
    ac_profile_digest.update(b"\0")
    ac_profile_digest.update(certified_path.read_bytes())
    ac_profile_checksum = ac_profile_digest.hexdigest()
    active_days = {int(day) for day in days}
    active_methods = set(quality_profiles)
    # Use the public PIPS AC-OPF solver with a strict feasibility tolerance.
    # The larger iteration ceiling changes no model constraint or objective; it
    # prevents the IEEE-300 instance from being mislabeled infeasible when the
    # primal-dual iteration has not yet converged.
    ac_feasibility_tolerance = 1e-6
    ac_max_iterations = 300
    def make_ac_options(opf_alg: int = 0) -> dict[str, Any]:
        # Construct a fresh option dictionary for every independent solve.
        # PYPOWER mutates some nested option state while initializing the
        # interior-point method; sharing one object across hundreds of OPFs
        # can make a later, otherwise identical case sensitive to history.
        return ppoption(
            VERBOSE=0,
            OUT_ALL=0,
            OPF_VIOLATION=ac_feasibility_tolerance,
            PDIPM_MAX_IT=ac_max_iterations,
            OPF_ALG=opf_alg,
        )
    checkpoint = intermediate / "ac_opf_checkpoint.csv"
    rows: list[dict[str, Any]] = []
    completed: set[tuple[str, int]] = set()
    if resume and checkpoint.exists():
        previous = pd.read_csv(checkpoint)
        parameter_match = (
            "ac_checkpoint_schema_version" in previous
            and set(
                previous["ac_checkpoint_schema_version"].astype(int).unique()
            )
            == {ac_checkpoint_schema_version}
            and "ac_profile_checksum" in previous
            and set(previous["ac_profile_checksum"].astype(str).unique())
            == {ac_profile_checksum}
            and set(previous.get("load_multiplier", pd.Series(dtype=float)).unique())
            == {load_multiplier}
            and set(
                previous.get(
                    "peak_dc_penetration", pd.Series(dtype=float)
                ).unique()
            )
            == {penetration}
            and set(
                previous.get(
                    "data_center_power_factor", pd.Series(dtype=float)
                ).unique()
            )
            == {power_factor}
        )
        if parameter_match:
            active_networks = {name for name, _, _ in networks}
            previous = previous[
                previous["network"].astype(str).isin(active_networks)
                & previous["day"].astype(int).isin(active_days)
                & previous["counterfactual_method"].astype(str).isin(
                    active_methods
                )
            ].drop_duplicates(
                ["network", "day", "counterfactual_method"], keep="last"
            ).copy()
            counts = previous.groupby(["network", "day"]).size()
            completed = set(
                (str(network), int(day))
                for network, day in counts[
                    counts == len(quality_profiles)
                ].index
            )
            rows = previous[
                [
                    (str(network), int(day)) in completed
                    for network, day in zip(
                        previous["network"], previous["day"]
                    )
                ]
            ].to_dict("records")
        else:
            logger.info(
                "Experiment 10 checkpoint parameters changed; rebuilding the "
                "complete AC OPF panel"
            )

    for network_name, case_function, dc_buses in networks:
        public_case = case_function()
        native_p = public_case["bus"][:, PD].copy() * load_multiplier
        native_q = public_case["bus"][:, QD].copy() * load_multiplier
        peak_dc_mw = penetration * float(native_p.sum())
        peak_trace_mw = float(
            max(
                oracle[:, :, event_slots].sum(axis=1).max(),
                actual[:, :, event_slots].sum(axis=1).max(),
                max(
                    profile[:, :, event_slots].sum(axis=1).max()
                    for profile in quality_profiles.values()
                ),
            )
        )
        dc_scale = peak_dc_mw / max(peak_trace_mw, 1e-12)

        def solve_profile(profile: np.ndarray, slot: int) -> dict[str, float]:
            # PYPOWER's interior-point implementation can occasionally
            # return a numerical non-convergence flag for an otherwise
            # feasible case after a long sequence of independent solves.
            # Retry the *same* deterministic AC-OPF model from a fresh case
            # object before treating the result as infeasible.  No load,
            # limit, objective, or recourse variable is changed by the
            # retry; the final success flag is still required below.
            result = None
            # The primary PIPS implementation is deterministic for the
            # declared case.  The step-controlled PIPS variant is an exact
            # numerical fallback for a rare ``Numerically failed`` status;
            # both solve the same AC-OPF equations and preserve every limit.
            for opf_alg in (0, 565):
                for retry_index in range(3):
                    case = case_function()
                    dc_power = profile[:, slot] * dc_scale
                    case["bus"][:, PD] = native_p
                    case["bus"][:, QD] = native_q
                    case["bus"][dc_buses, PD] += dc_power
                    case["bus"][dc_buses, QD] += dc_power * reactive_ratio
                    candidate = runopf(case, make_ac_options(opf_alg))
                    result = candidate
                    if bool(candidate["success"]):
                        break
                if result is not None and bool(result["success"]):
                    break
            if result is None or not bool(result["success"]):
                logger.warning(
                    "AC-OPF retries exhausted for %s slot %d; PYPOWER raw status=%s",
                    network_name,
                    slot,
                    result.get("raw", {}).get("output", {}).get("message", "unknown")
                    if result is not None
                    else "unknown",
                )
            if result is None or not bool(result["success"]):
                raise RuntimeError(
                    f"AC OPF failed for {network_name}, slot {slot}"
                )
            rate = result["branch"][:, RATE_A].copy()
            rate[rate <= 0] = 1e9
            apparent_from = np.hypot(
                result["branch"][:, PF], result["branch"][:, QF]
            )
            apparent_to = np.hypot(
                result["branch"][:, PT], result["branch"][:, QT]
            )
            voltage = result["bus"][:, VM]
            voltage_violation = np.maximum(
                result["bus"][:, VMIN] - voltage,
                voltage - result["bus"][:, VMAX],
            )
            return {
                "objective_usd_per_h": float(result["f"]),
                "maximum_apparent_line_loading": float(
                    (
                        np.maximum(apparent_from, apparent_to) / rate
                    ).max(initial=0.0)
                ),
                "maximum_voltage_violation_pu": float(
                    max(0.0, voltage_violation.max(initial=0.0))
                ),
                "minimum_voltage_pu": float(voltage.min()),
                "maximum_voltage_pu": float(voltage.max()),
            }

        for local_day, day in enumerate(
            tqdm(days, desc=f"Exp10 AC OPF: {network_name}")
        ):
            key = (network_name, int(day))
            if key in completed:
                continue
            slot = int(peak_slots[local_day])
            actual_result = solve_profile(actual[local_day], slot)
            oracle_result = solve_profile(oracle[local_day], slot)
            realized = (
                oracle_result["objective_usd_per_h"]
                - actual_result["objective_usd_per_h"]
            )
            for method, profiles in quality_profiles.items():
                baseline_result = solve_profile(profiles[local_day], slot)
                payment = (
                    baseline_result["objective_usd_per_h"]
                    - actual_result["objective_usd_per_h"]
                )
                rows.append(
                    {
                        "network": network_name,
                        "day": int(day),
                        "peak_event_slot": slot,
                        "counterfactual_method": method,
                        "ac_payment_usd_per_h": float(payment),
                        "ac_realized_value_usd_per_h": float(realized),
                        "absolute_error_usd_per_h": float(abs(payment - realized)),
                        "overpayment_usd_per_h": float(max(0.0, payment - realized)),
                        "maximum_apparent_line_loading": baseline_result[
                            "maximum_apparent_line_loading"
                        ],
                        "maximum_voltage_violation_pu": baseline_result[
                            "maximum_voltage_violation_pu"
                        ],
                        "minimum_voltage_pu": baseline_result["minimum_voltage_pu"],
                        "maximum_voltage_pu": baseline_result["maximum_voltage_pu"],
                        "load_multiplier": load_multiplier,
                        "peak_dc_penetration": penetration,
                        "data_center_power_factor": power_factor,
                        "dc_power_scale": dc_scale,
                        "ac_checkpoint_schema_version": (
                            ac_checkpoint_schema_version
                        ),
                        "ac_profile_checksum": ac_profile_checksum,
                    }
                )
            pd.DataFrame(rows).to_csv(checkpoint, index=False)
    results = pd.DataFrame(rows).sort_values(
        ["network", "day", "counterfactual_method"]
    )
    expected_ac_opf_keys = {
        (network_name, int(day), method)
        for network_name, _, _ in networks
        for day in days
        for method in quality_profiles
    }
    observed_ac_opf_keys = {
        (
            str(row.network),
            int(row.day),
            str(row.counterfactual_method),
        )
        for row in results.itertuples()
    }
    if (
        len(results) != len(expected_ac_opf_keys)
        or observed_ac_opf_keys != expected_ac_opf_keys
    ):
        raise RuntimeError(
            "Incomplete or non-unique AC OPF panel: "
            f"{len(results)}/{len(expected_ac_opf_keys)}"
        )
    results.to_csv(final / "ac_opf_locked_day_results.csv", index=False)
    summary = (
        results.groupby(["network", "counterfactual_method"], as_index=False)
        .agg(
            mean_absolute_error_usd_per_h=("absolute_error_usd_per_h", "mean"),
            mean_overpayment_usd_per_h=("overpayment_usd_per_h", "mean"),
            maximum_apparent_line_loading=(
                "maximum_apparent_line_loading", "max"
            ),
            maximum_voltage_violation_pu=(
                "maximum_voltage_violation_pu", "max"
            ),
        )
    )
    summary.to_csv(final / "ac_opf_summary.csv", index=False)
    # Complete nonlinear post-contingency feasibility panels. Every finite
    # non-islanding outage in each public case is evaluated; neither cases nor
    # outages are selected by loading or observed outcomes.
    contingency_networks = [
        ("IEEE 9-bus", case9, np.asarray([3, 4, 6, 8], dtype=int)),
        ("IEEE 14-bus", case14, np.asarray([3, 4, 8, 13], dtype=int)),
    ]
    contingency_peak_trace_mw = float(
        max(
            oracle[:, :, event_slots].sum(axis=1).max(),
            actual[:, :, event_slots].sum(axis=1).max(),
            max(
                profile[:, :, event_slots].sum(axis=1).max()
                for profile in quality_profiles.values()
            ),
        )
    )
    contingency_data: list[dict[str, Any]] = []
    for contingency_network, case_function, contingency_buses in (
        contingency_networks
    ):
        contingency_case = case_function()
        contingency_outages = np.unique(
            build_n1_security_factors(
                power_system_from_ppc(contingency_case)
            )[2]
        ).astype(int)
        contingency_native_p = (
            contingency_case["bus"][:, PD].copy() * load_multiplier
        )
        contingency_native_q = (
            contingency_case["bus"][:, QD].copy() * load_multiplier
        )
        contingency_data.append(
            {
                "network": contingency_network,
                "case_function": case_function,
                "buses": contingency_buses,
                "outages": contingency_outages,
                "native_p": contingency_native_p,
                "native_q": contingency_native_q,
                "dc_scale": (
                    penetration
                    * float(contingency_native_p.sum())
                    / max(contingency_peak_trace_mw, 1e-12)
                ),
            }
        )
    contingency_checkpoint = (
        intermediate / "ac_n1_contingency_checkpoint.csv"
    )
    contingency_rows: list[dict[str, Any]] = []
    completed_contingencies: set[tuple[str, int, str, int]] = set()
    if resume and contingency_checkpoint.exists():
        previous = pd.read_csv(contingency_checkpoint)
        declared_contingency_networks = {
            item["network"] for item in contingency_data
        }
        parameter_match = (
            "ac_checkpoint_schema_version" in previous
            and set(
                previous["ac_checkpoint_schema_version"].astype(int).unique()
            )
            == {ac_checkpoint_schema_version}
            and "ac_profile_checksum" in previous
            and set(previous["ac_profile_checksum"].astype(str).unique())
            == {ac_profile_checksum}
            and set(previous.get("network", pd.Series(dtype=str)).unique())
            <= declared_contingency_networks
            and set(
                previous.get(
                    "load_multiplier", pd.Series(dtype=float)
                ).unique()
            )
            == {load_multiplier}
            and set(
                previous.get(
                    "peak_dc_penetration", pd.Series(dtype=float)
                ).unique()
            )
            == {penetration}
            and set(
                previous.get(
                    "data_center_power_factor", pd.Series(dtype=float)
                ).unique()
            )
            == {power_factor}
        )
        if parameter_match:
            outage_by_network = {
                str(item["network"]): {
                    int(outage) for outage in item["outages"]
                }
                for item in contingency_data
            }
            previous = previous[
                previous["network"].astype(str).isin(
                    declared_contingency_networks
                )
                & previous["day"].astype(int).isin(active_days)
                & previous["counterfactual_method"].astype(str).isin(
                    active_methods
                )
            ].copy()
            previous = previous[
                [
                    int(outage) in outage_by_network[str(network)]
                    for network, outage in zip(
                        previous["network"], previous["outage"]
                    )
                ]
            ].drop_duplicates(
                ["network", "day", "counterfactual_method", "outage"],
                keep="last",
            )
            completed_contingencies = {
                (
                    str(row.network),
                    int(row.day),
                    str(row.counterfactual_method),
                    int(row.outage),
                )
                for row in previous.itertuples()
            }
            contingency_rows = previous.to_dict("records")
        else:
            logger.info(
                "Experiment 10 AC N-1 checkpoint parameters changed; "
                "rebuilding all non-islanding outages"
            )
    total_contingency_cells = len(days) * len(quality_profiles) * sum(
        len(item["outages"]) for item in contingency_data
    )
    contingency_progress = tqdm(
        total=total_contingency_cells,
        desc="Exp10 complete AC N-1 public cases",
    )
    contingency_progress.update(len(completed_contingencies))
    def solve_contingency_cell(
        task: tuple[dict[str, Any], int, int, int, str, np.ndarray, int],
    ) -> dict[str, Any]:
        contingency_item, local_day, day, slot, method, profiles, outage = task
        contingency_network = str(contingency_item["network"])
        contingency_buses = contingency_item["buses"]
        contingency_native_p = contingency_item["native_p"]
        contingency_native_q = contingency_item["native_q"]
        contingency_dc_scale = float(contingency_item["dc_scale"])
        dc_power = profiles[local_day, :, slot] * contingency_dc_scale
        result = None
        for opf_alg in (0, 565):
            for _ in range(3):
                case = contingency_item["case_function"]()
                case["bus"][:, PD] = contingency_native_p
                case["bus"][:, QD] = contingency_native_q
                case["bus"][contingency_buses, PD] += dc_power
                case["bus"][contingency_buses, QD] += dc_power * reactive_ratio
                case["branch"][int(outage), BR_STATUS] = 0
                result = runopf(case, make_ac_options(opf_alg))
                if bool(result["success"]):
                    break
            if result is not None and bool(result["success"]):
                break
        if not bool(result["success"]):
            raise RuntimeError(
                "AC post-contingency OPF failed for "
                f"{contingency_network}, day {day}, method {method}, "
                f"outage {outage}"
            )
        in_service = result["branch"][:, BR_STATUS] > 0
        rate = result["branch"][in_service, RATE_A].copy()
        rate[rate <= 0] = np.inf
        apparent_from = np.hypot(
            result["branch"][in_service, PF],
            result["branch"][in_service, QF],
        )
        apparent_to = np.hypot(
            result["branch"][in_service, PT],
            result["branch"][in_service, QT],
        )
        voltage = result["bus"][:, VM]
        voltage_violation = np.maximum(
            result["bus"][:, VMIN] - voltage,
            voltage - result["bus"][:, VMAX],
        )
        return {
            "network": contingency_network,
            "day": int(day),
            "peak_event_slot": slot,
            "counterfactual_method": method,
            "outage": int(outage),
            "objective_usd_per_h": float(result["f"]),
            "maximum_apparent_line_loading": float(
                (np.maximum(apparent_from, apparent_to) / rate).max(initial=0.0)
            ),
            "maximum_voltage_violation_pu": float(
                max(0.0, voltage_violation.max(initial=0.0))
            ),
            "minimum_voltage_pu": float(voltage.min()),
            "maximum_voltage_pu": float(voltage.max()),
            "solver_success": 1,
            "load_multiplier": load_multiplier,
            "peak_dc_penetration": penetration,
            "data_center_power_factor": power_factor,
            "dc_power_scale": contingency_dc_scale,
            "ac_checkpoint_schema_version": ac_checkpoint_schema_version,
            "ac_profile_checksum": ac_profile_checksum,
        }

    tasks: list[tuple[dict[str, Any], int, int, int, str, np.ndarray, int]] = []
    for contingency_item in contingency_data:
        for local_day, day in enumerate(days):
            slot = int(peak_slots[local_day])
            for method, profiles in quality_profiles.items():
                for outage in contingency_item["outages"]:
                    key = (
                        str(contingency_item["network"]),
                        int(day),
                        method,
                        int(outage),
                    )
                    if key not in completed_contingencies:
                        tasks.append(
                            (
                                contingency_item,
                                local_day,
                                int(day),
                                slot,
                                method,
                                profiles,
                                int(outage),
                            )
                        )
    workers = int(cfg["experiments"].get("ac_n1_workers", 6))
    if workers <= 0:
        raise ValueError("ac_n1_workers must be positive")
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for row in executor.map(solve_contingency_cell, tasks):
            contingency_rows.append(row)
            contingency_progress.update(1)
            if len(contingency_rows) % 19 == 0:
                pd.DataFrame(contingency_rows).to_csv(
                    contingency_checkpoint, index=False
                )
    contingency_progress.close()
    pd.DataFrame(contingency_rows).to_csv(
        contingency_checkpoint, index=False
    )
    contingency_results = pd.DataFrame(contingency_rows).sort_values(
        ["network", "day", "counterfactual_method", "outage"]
    )
    expected_contingency_keys = {
        (
            str(item["network"]),
            int(day),
            method,
            int(outage),
        )
        for item in contingency_data
        for day in days
        for method in quality_profiles
        for outage in item["outages"]
    }
    observed_contingency_keys = {
        (
            str(row.network),
            int(row.day),
            str(row.counterfactual_method),
            int(row.outage),
        )
        for row in contingency_results.itertuples()
    }
    if (
        len(contingency_results) != total_contingency_cells
        or observed_contingency_keys != expected_contingency_keys
    ):
        raise RuntimeError(
            "Incomplete or non-unique AC N-1 panel: "
            f"{len(contingency_results)}/{total_contingency_cells}"
        )
    contingency_results.to_csv(
        final / "ac_n1_contingency_results.csv", index=False
    )
    contingency_summary = (
        contingency_results.groupby(
            ["network", "counterfactual_method"], as_index=False
        )
        .agg(
            maximum_apparent_line_loading=(
                "maximum_apparent_line_loading",
                "max",
            ),
            maximum_voltage_violation_pu=(
                "maximum_voltage_violation_pu",
                "max",
            ),
            minimum_voltage_pu=("minimum_voltage_pu", "min"),
            maximum_voltage_pu=("maximum_voltage_pu", "max"),
            evaluated_outages=("outage", "nunique"),
            locked_days=("day", "nunique"),
        )
    )
    contingency_summary.to_csv(
        final / "ac_n1_contingency_summary.csv", index=False
    )
    # Preventive active-plan AC validation. For every method-day-penetration
    # cell, one intact-network active dispatch is fixed identically in every
    # credible outage. Only the reference generator may absorb the
    # contingency-dependent AC loss difference; reactive generation and
    # voltage variables remain scenario recourse. Equality bounds impose the
    # shared non-reference active plan exactly.
    preventive_case_function = case9
    preventive_network = "IEEE 9-bus"
    preventive_buses = np.asarray([3, 4, 6, 8], dtype=int)
    preventive_outages = np.unique(
        build_n1_security_factors(
            power_system_from_ppc(preventive_case_function())
        )[2]
    ).astype(int)
    preventive_penetrations = np.asarray(
        cfg["experiments"].get(
            "preventive_ac_dc_peak_penetrations", [0.03, 0.06, 0.09]
        ),
        dtype=float,
    )
    if (
        preventive_penetrations.ndim != 1
        or len(preventive_penetrations) < 3
        or np.any(preventive_penetrations <= 0)
        or not np.all(np.diff(preventive_penetrations) > 0)
    ):
        raise ValueError(
            "preventive_ac_dc_peak_penetrations must contain at least three "
            "strictly increasing positive values"
        )
    preventive_public_case = preventive_case_function()
    preventive_native_p = (
        preventive_public_case["bus"][:, PD].copy() * load_multiplier
    )
    preventive_native_q = (
        preventive_public_case["bus"][:, QD].copy() * load_multiplier
    )
    preventive_checkpoint = (
        intermediate / "preventive_ac_n1_checkpoint.csv"
    )
    preventive_rows: list[dict[str, Any]] = []
    preventive_completed: set[tuple[float, int, str, int]] = set()
    if resume and preventive_checkpoint.exists() and preventive_checkpoint.stat().st_size > 0:
        previous = pd.read_csv(preventive_checkpoint)
        parameter_match = (
            "ac_checkpoint_schema_version" in previous
            and set(
                previous["ac_checkpoint_schema_version"].astype(int).unique()
            )
            == {ac_checkpoint_schema_version}
            and "ac_profile_checksum" in previous
            and set(previous["ac_profile_checksum"].astype(str).unique())
            == {ac_profile_checksum}
            and set(
                np.round(
                    previous["peak_dc_penetration"].unique(), 12
                )
            )
            <= set(np.round(preventive_penetrations, 12))
            and set(previous["load_multiplier"].unique())
            == {load_multiplier}
            and set(previous["data_center_power_factor"].unique())
            == {power_factor}
        )
        if parameter_match:
            previous = previous[
                previous["network"].astype(str).eq(preventive_network)
                & previous["day"].astype(int).isin(active_days)
                & previous["counterfactual_method"].astype(str).isin(
                    active_methods
                )
                & previous["outage"].astype(int).isin(
                    {int(outage) for outage in preventive_outages}
                )
                & np.round(
                    previous["peak_dc_penetration"].astype(float), 12
                ).isin(set(np.round(preventive_penetrations, 12)))
            ].drop_duplicates(
                [
                    "peak_dc_penetration",
                    "day",
                    "counterfactual_method",
                    "outage",
                ],
                keep="last",
            )
            preventive_completed = {
                (
                    round(float(row.peak_dc_penetration), 12),
                    int(row.day),
                    str(row.counterfactual_method),
                    int(row.outage),
                )
                for row in previous.itertuples()
            }
            preventive_rows = previous.to_dict("records")
        else:
            logger.info(
                "Experiment 10 preventive AC checkpoint parameters changed; "
                "rebuilding the complete panel"
            )
    preventive_total = (
        len(preventive_penetrations)
        * len(days)
        * len(quality_profiles)
        * len(preventive_outages)
    )
    preventive_progress = tqdm(
        total=preventive_total,
        initial=len(preventive_completed),
        desc="Exp10 shared-plan preventive AC N-1",
    )
    preventive_cells_since_checkpoint = 0
    for preventive_penetration in preventive_penetrations:
        preventive_dc_scale = (
            float(preventive_penetration)
            * float(preventive_native_p.sum())
            / max(contingency_peak_trace_mw, 1e-12)
        )
        for local_day, day in enumerate(days):
            slot = int(peak_slots[local_day])
            for method, profiles in quality_profiles.items():
                pending_outages = [
                    int(outage)
                    for outage in preventive_outages
                    if (
                        round(float(preventive_penetration), 12),
                        int(day),
                        method,
                        int(outage),
                    )
                    not in preventive_completed
                ]
                if not pending_outages:
                    continue
                dc_power = (
                    profiles[local_day, :, slot] * preventive_dc_scale
                )
                base_case = preventive_case_function()
                base_case["gen"] = base_case["gen"].astype(float)
                base_case["bus"][:, PD] = preventive_native_p
                base_case["bus"][:, QD] = preventive_native_q
                base_case["bus"][preventive_buses, PD] += dc_power
                base_case["bus"][preventive_buses, QD] += (
                    dc_power * reactive_ratio
                )
                base_result = runopf(base_case, make_ac_options())
                if not bool(base_result["success"]):
                    # Same preventive AC-OPF model, alternate numerical
                    # implementation only; no recourse or limit is changed.
                    base_case = preventive_case_function()
                    base_case["gen"] = base_case["gen"].astype(float)
                    base_case["bus"][:, PD] = preventive_native_p
                    base_case["bus"][:, QD] = preventive_native_q
                    base_case["bus"][preventive_buses, PD] += dc_power
                    base_case["bus"][preventive_buses, QD] += (
                        dc_power * reactive_ratio
                    )
                    base_result = runopf(base_case, make_ac_options(565))
                if not bool(base_result["success"]):
                    raise RuntimeError(
                        "Preventive base AC OPF failed for "
                        f"day {day}, method {method}, penetration "
                        f"{preventive_penetration:.3f}"
                    )
                reference_buses = set(
                    np.where(base_result["bus"][:, BUS_TYPE] == REF)[0]
                )
                nonreference_generators = np.asarray(
                    [
                        generator
                        for generator in range(len(base_result["gen"]))
                        if int(base_result["gen"][generator, GEN_BUS]) - 1
                        not in reference_buses
                    ],
                    dtype=int,
                )
                shared_pg = base_result["gen"][:, PG].copy()
                for outage in pending_outages:
                    case = preventive_case_function()
                    case["gen"] = case["gen"].astype(float)
                    case["bus"][:, PD] = preventive_native_p
                    case["bus"][:, QD] = preventive_native_q
                    case["bus"][preventive_buses, PD] += dc_power
                    case["bus"][preventive_buses, QD] += (
                        dc_power * reactive_ratio
                    )
                    case["branch"][outage, BR_STATUS] = 0
                    case["gen"][nonreference_generators, PMIN] = (
                        shared_pg[nonreference_generators]
                    )
                    case["gen"][nonreference_generators, PMAX] = (
                        shared_pg[nonreference_generators]
                    )
                    result = runopf(case, make_ac_options())
                    if not bool(result["success"]):
                        case = preventive_case_function()
                        case["gen"] = case["gen"].astype(float)
                        case["bus"][:, PD] = preventive_native_p
                        case["bus"][:, QD] = preventive_native_q
                        case["bus"][preventive_buses, PD] += dc_power
                        case["bus"][preventive_buses, QD] += (
                            dc_power * reactive_ratio
                        )
                        case["branch"][outage, BR_STATUS] = 0
                        case["gen"][nonreference_generators, PMIN] = (
                            shared_pg[nonreference_generators]
                        )
                        case["gen"][nonreference_generators, PMAX] = (
                            shared_pg[nonreference_generators]
                        )
                        result = runopf(case, make_ac_options(565))
                    if not bool(result["success"]):
                        raise RuntimeError(
                            "Shared-active-plan preventive AC OPF failed for "
                            f"day {day}, method {method}, penetration "
                            f"{preventive_penetration:.3f}, outage {outage}"
                        )
                    in_service = result["branch"][:, BR_STATUS] > 0
                    rate = result["branch"][in_service, RATE_A].copy()
                    rate[rate <= 0] = np.inf
                    apparent_from = np.hypot(
                        result["branch"][in_service, PF],
                        result["branch"][in_service, QF],
                    )
                    apparent_to = np.hypot(
                        result["branch"][in_service, PT],
                        result["branch"][in_service, QT],
                    )
                    voltage = result["bus"][:, VM]
                    voltage_violation = np.maximum(
                        result["bus"][:, VMIN] - voltage,
                        voltage - result["bus"][:, VMAX],
                    )
                    maximum_pg_deviation = float(
                        np.max(
                            np.abs(
                                result["gen"][
                                    nonreference_generators, PG
                                ]
                                - shared_pg[nonreference_generators]
                            ),
                            initial=0.0,
                        )
                    )
                    preventive_rows.append(
                        {
                            "network": preventive_network,
                            "day": int(day),
                            "peak_event_slot": slot,
                            "counterfactual_method": method,
                            "peak_dc_penetration": float(
                                preventive_penetration
                            ),
                            "outage": int(outage),
                            "solver_success": 1,
                            "intact_plan_objective_usd_per_h": float(
                                base_result["f"]
                            ),
                            **{
                                f"shared_pg_generator_{generator}_mw": float(
                                    shared_pg[generator]
                                )
                                for generator in range(len(shared_pg))
                            },
                            "maximum_nonreference_active_plan_deviation_mw": (
                                maximum_pg_deviation
                            ),
                            "reference_generator_loss_recourse_mw": float(
                                result["gen"][0, PG] - shared_pg[0]
                            ),
                            "maximum_apparent_line_loading": float(
                                (
                                    np.maximum(apparent_from, apparent_to)
                                    / rate
                                ).max(initial=0.0)
                            ),
                            "maximum_voltage_violation_pu": float(
                                max(
                                    0.0,
                                    voltage_violation.max(initial=0.0),
                                )
                            ),
                            "minimum_voltage_pu": float(voltage.min()),
                            "maximum_voltage_pu": float(voltage.max()),
                            "load_multiplier": load_multiplier,
                            "data_center_power_factor": power_factor,
                            "dc_power_scale": preventive_dc_scale,
                            "ac_checkpoint_schema_version": (
                                ac_checkpoint_schema_version
                            ),
                            "ac_profile_checksum": ac_profile_checksum,
                        }
                    )
                    preventive_completed.add(
                        (
                            round(float(preventive_penetration), 12),
                            int(day),
                            method,
                            int(outage),
                        )
                    )
                    preventive_progress.update(1)
                    preventive_cells_since_checkpoint += 1
                    if preventive_cells_since_checkpoint >= len(
                        preventive_outages
                    ):
                        pd.DataFrame(preventive_rows).to_csv(
                            preventive_checkpoint, index=False
                        )
                        preventive_cells_since_checkpoint = 0
    preventive_progress.close()
    preventive_results = pd.DataFrame(preventive_rows).sort_values(
        [
            "peak_dc_penetration",
            "day",
            "counterfactual_method",
            "outage",
        ]
    )
    expected_preventive_keys = {
        (
            round(float(preventive_penetration), 12),
            int(day),
            method,
            int(outage),
        )
        for preventive_penetration in preventive_penetrations
        for day in days
        for method in quality_profiles
        for outage in preventive_outages
    }
    observed_preventive_keys = {
        (
            round(float(row.peak_dc_penetration), 12),
            int(row.day),
            str(row.counterfactual_method),
            int(row.outage),
        )
        for row in preventive_results.itertuples()
    }
    if (
        len(preventive_results) != preventive_total
        or observed_preventive_keys != expected_preventive_keys
    ):
        raise RuntimeError(
            "Incomplete or non-unique shared-plan preventive AC panel: "
            f"{len(preventive_results)}/{preventive_total}"
        )
    preventive_results.to_csv(
        final / "preventive_ac_n1_results.csv", index=False
    )
    preventive_results.to_csv(preventive_checkpoint, index=False)
    preventive_summary = (
        preventive_results.groupby(
            ["peak_dc_penetration", "counterfactual_method"],
            as_index=False,
        )
        .agg(
            maximum_nonreference_active_plan_deviation_mw=(
                "maximum_nonreference_active_plan_deviation_mw",
                "max",
            ),
            maximum_absolute_reference_loss_recourse_mw=(
                "reference_generator_loss_recourse_mw",
                lambda values: float(np.max(np.abs(values))),
            ),
            maximum_apparent_line_loading=(
                "maximum_apparent_line_loading",
                "max",
            ),
            maximum_voltage_violation_pu=(
                "maximum_voltage_violation_pu",
                "max",
            ),
            evaluated_outages=("outage", "nunique"),
            locked_days=("day", "nunique"),
        )
    )
    preventive_summary.to_csv(
        final / "preventive_ac_n1_summary.csv", index=False
    )
    plot_exp10(results, folder / "figures", cfg)
    from .visualization import plot_exp10_n1, plot_exp10_preventive

    plot_exp10_n1(contingency_results, folder / "figures", cfg)
    plot_exp10_preventive(
        preventive_results, folder / "figures", cfg
    )
    write_json(
        final / "experiment_metadata.json",
        {
            "networks": [network[0] for network in networks],
            "locked_days_per_network": int(len(days)),
            "evaluation_interval": (
                "maximum realized data-center demand among the eight declared "
                "event intervals on each locked day"
            ),
            "model": (
                "nonlinear AC optimal power flow with native active/reactive "
                "loads, voltage limits, generator reactive limits, and apparent-"
                "power branch ratings"
            ),
            "data_center_power_factor": power_factor,
            "load_multiplier": load_multiplier,
            "peak_data_center_penetration": penetration,
            "profile_source": (
                "Experiment-2 locked test_profiles.npz plus Experiment-9 "
                "certified_counterfactual_profiles.npz"
            ),
            "profile_checksum": hashlib.sha256(profile_path.read_bytes()).hexdigest(),
            "certified_profile_checksum": hashlib.sha256(certified_path.read_bytes()).hexdigest(),
            "ac_profile_checksum": ac_profile_checksum,
            "profile_recomputed_after_exp2_refit": True,
            "ac_feasibility_tolerance": ac_feasibility_tolerance,
            "primal_dual_maximum_iterations": ac_max_iterations,
            "all_ac_opfs_converged": True,
            "ac_n1_networks": [
                str(item["network"]) for item in contingency_data
            ],
            "ac_n1_non_islanding_outages_by_network": {
                str(item["network"]): int(len(item["outages"]))
                for item in contingency_data
            },
            "ac_n1_outage_rule": (
                "every finite non-islanding single-line outage; no loading "
                "screening or outcome-dependent selection"
            ),
            "ac_n1_interpretation": (
                "separate nonlinear AC OPF for each post-contingency state, "
                "which certifies corrective steady-state feasibility"
            ),
            "all_ac_n1_opfs_converged": True,
            "preventive_ac_network": preventive_network,
            "preventive_ac_peak_penetrations": (
                preventive_penetrations.tolist()
            ),
            "preventive_ac_non_islanding_outages": int(
                len(preventive_outages)
            ),
            "preventive_ac_interpretation": (
                "one intact-network active dispatch is imposed identically "
                "on every non-reference generator in every outage; the "
                "reference generator supplies only contingency-dependent "
                "loss recourse, while reactive power and voltage are "
                "scenario recourse"
            ),
            "all_preventive_ac_n1_opfs_converged": True,
        },
    )
    logger.info(
        "Experiment 10 complete: %d nonlinear AC OPF outcomes",
        len(results),
    )


def _write_feature_stratified_spatial_audit(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
) -> bool:
    """Write a trace-level audit of the deterministic regional assignment.

    The public traces do not contain physical data-center geography. This
    audit reports the declared feature-stratified scenario and pairwise
    temporal correlations; it does not map regions to buses or select
    placements from network outcomes.
    """
    raw_burst = [root / path for path in cfg["data"]["burstgpt_files"]]
    raw_scheduler = root / cfg["data"]["mit_scheduler"]
    raw_dcgm = root / cfg["data"]["mit_dcgm"]
    required = [*raw_burst, raw_scheduler, raw_dcgm]
    if not all(path.exists() and path.stat().st_size > 0 for path in required):
        logger.info("Spatial trace audit skipped: raw public CSVs are not restored")
        return False

    folder = root / "experiments/exp11_spatial_scale_robustness"
    final = folder / "results/final"
    final.mkdir(parents=True, exist_ok=True)
    interval_s = int(cfg["project"]["interval_minutes"] * 60)
    slots_per_day = int(cfg["project"]["slots_per_day"])
    n_regions = int(cfg["project"]["number_of_regions"])
    inference, _, valid_slots, burst_stats = _aggregate_burstgpt(
        raw_burst, interval_s, slots_per_day, n_regions, logger
    )
    arrivals, observed, mit_stats = _aggregate_mit_jobs(
        raw_scheduler,
        raw_dcgm,
        inference.shape[0],
        interval_s,
        n_regions,
        logger,
    )
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    rows: list[dict[str, Any]] = []
    for region in range(n_regions):
        request_energy = inference[:, region, :].sum(axis=1)
        batch_arrivals = arrivals[:, region]
        batch_observed = observed[:, region]
        trace_values = [
            (
                "BurstGPT inference",
                request_energy,
                "feature-stratified round-robin by model/log type/timestamp; ID only breaks ties",
            ),
            (
                "MIT batch submitted",
                batch_arrivals,
                "feature-stratified round-robin by class/GPU/runtime/submission/energy; ID only breaks ties",
            ),
            (
                "MIT batch observed",
                batch_observed,
                "feature-stratified round-robin by class/GPU/runtime/submission/energy; ID only breaks ties",
            ),
        ]
        for trace, values, assignment_rule in trace_values:
            values = np.asarray(values, dtype=float)
            rows.append(
                {
                    "trace": trace,
                    "region": int(region),
                    "total_mwh_or_token_units": float(values.sum()),
                    "p50_interval_power_mw_or_units": float(np.quantile(values / dt_h, 0.50)),
                    "p99_interval_power_mw_or_units": float(np.quantile(values / dt_h, 0.99)),
                    "peak_interval_power_mw_or_units": float(np.max(values / dt_h)),
                    "active_intervals": int(np.count_nonzero(values)),
                    "assignment_rule": assignment_rule,
                }
            )
    pd.DataFrame(rows).to_csv(final / "spatial_trace_mapping_audit.csv", index=False)

    profile = np.column_stack(
        [
            inference[:, region, :].sum(axis=1) + observed[:, region]
            for region in range(n_regions)
        ]
    )
    corr = np.corrcoef(profile.T)
    correlation_rows = [
        {
            "region_i": int(i),
            "region_j": int(j),
            "temporal_correlation": float(corr[i, j]),
        }
        for i in range(n_regions)
        for j in range(i + 1, n_regions)
    ]
    pd.DataFrame(correlation_rows).to_csv(
        final / "spatial_trace_pairwise_correlation.csv", index=False
    )
    write_json(
        final / "spatial_trace_mapping_metadata.json",
        {
            "assignment": "feature-stratified deterministic round-robin",
            "physical_geography_available": False,
            "all_region_to_bus_permutations_evaluated": True,
            "burstgpt_rows": int(burst_stats["rows"]),
            "mit_joined_jobs": int(mit_stats["valid_joined_jobs"]),
            "valid_intervals": int(valid_slots.sum()),
            "correlation_file": "spatial_trace_pairwise_correlation.csv",
        },
    )
    return True


def run_exp11(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
    resume: bool = False,
) -> None:
    """Exhaustively test spatial assignment and data-center penetration.

    The four measured regional traces are assigned to every permutation of the
    four declared IEEE-118 connection buses.  This is a complete finite
    uncertainty set rather than an outcome-selected placement or a spatial
    screening rule.  Settlement and realized value use independent cost
    resolutions, as in Experiment 3.
    """
    from .visualization import plot_exp11

    folder = root / "experiments/exp11_spatial_scale_robustness"
    final = folder / "results/final"
    intermediate = folder / "results/intermediate"
    final.mkdir(parents=True, exist_ok=True)
    intermediate.mkdir(parents=True, exist_ok=True)
    _write_feature_stratified_spatial_audit(root, cfg, logger)
    profile_path = (
        root
        / "experiments/exp2_baseline_verification/results/intermediate/"
        "test_profiles.npz"
    )
    if not profile_path.exists():
        run_exp2(root, cfg, logger)
    stored = np.load(profile_path, allow_pickle=False)
    days = stored["days"].astype(int)
    methods = [str(value) for value in stored["methods"]]
    required_methods = [
        "Feasible Quantile Projection",
        "Single Feasible Projection",
        "Risk-Constrained Convex Verifier",
    ]
    missing = [method for method in required_methods if method not in methods]
    if missing:
        raise RuntimeError(
            "Experiment 11 requires rebuilt Experiment 2 profiles; missing "
            + ", ".join(missing)
        )
    quality_profiles = {
        method: stored["baselines"][:, methods.index(method)]
        for method in required_methods
    }
    quality_profiles["Trace-Anchored Reference"] = stored["oracle"]
    actual = stored["actual"]
    oracle = stored["oracle"]
    _, _, _, settlement_system, base_profiles, _, _ = _inputs(
        root, cfg, logger
    )
    settlement_system = _ieee118_quadratic_evaluation_system(
        settlement_system
    )
    evaluation_system = copy.deepcopy(settlement_system)
    settlement_segments = int(cfg["market"]["generator_segments"])
    evaluation_segments = int(
        cfg["market"].get("evaluation_generator_segments", 80)
    )
    event_slots = np.asarray(cfg["market"]["event_slots"], dtype=int)
    peak_slots = event_slots[
        np.argmax(actual[:, :, event_slots].sum(axis=1), axis=1)
    ]
    declared_buses = (
        np.asarray(cfg["project"]["data_center_buses"], dtype=int) - 1
    )
    permutation_assignments = list(permutations(declared_buses.tolist()))
    # The 24 one-to-one permutations are the complete finite placement set.
    # Two deterministic concentration controls are added without replacing
    # that set: all regions at one declared bus and a two-bus 2--2 cluster.
    # Concentration controls use the two generator-connected declared buses
    # (80 and 116 in the default case).  This keeps the control panel inside
    # the predeclared SCED feasibility domain while still stressing
    # co-location and two-bus concentration; it is not selected from locked
    # outcomes.
    concentration_assignments = [
        tuple([int(declared_buses[2])] * 4),
        tuple([
            int(declared_buses[2]), int(declared_buses[2]),
            int(declared_buses[3]), int(declared_buses[3]),
        ]),
    ]
    assignments = permutation_assignments + concentration_assignments
    assignment_types = ["one-to-one permutation"] * len(permutation_assignments) + [
        "co-located four-region control",
        "two-bus clustered control",
    ]
    penetrations = np.asarray(
        cfg["experiments"].get(
            "spatial_scale_peak_penetrations", [0.03, 0.06, 0.09]
        ),
        dtype=float,
    )
    if (
        len(np.unique(declared_buses)) != 4
        or len(permutation_assignments) != math.factorial(4)
        or len(assignments) != math.factorial(4) + len(concentration_assignments)
    ):
        raise RuntimeError(
            "Experiment 11 requires four distinct declared connection buses"
        )
    if np.any(penetrations <= 0):
        raise ValueError("Spatial-scale penetrations must all be positive")
    fixed = float(cfg["project"]["fixed_facility_load_mw"])
    native_profiles = base_profiles.copy()
    native_profiles[:, declared_buses] -= fixed
    spatial_native_load_multiplier = float(
        cfg["experiments"].get(
            "spatial_scale_native_load_multiplier",
            cfg["experiments"].get("n1_load_multiplier", 0.90),
        )
    )
    if not 0.0 < spatial_native_load_multiplier <= 1.0:
        raise ValueError(
            "spatial_scale_native_load_multiplier must be in (0, 1]"
        )
    native_profiles *= spatial_native_load_multiplier
    peak_trace = float(
        max(
            actual[:, :, event_slots].sum(axis=1).max(),
            oracle[:, :, event_slots].sum(axis=1).max(),
            max(
                profile[:, :, event_slots].sum(axis=1).max()
                for profile in quality_profiles.values()
            ),
        )
    )
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    schema_version = 4
    profile_checksum = hashlib.sha256(profile_path.read_bytes()).hexdigest()
    checkpoint = intermediate / "spatial_scale_checkpoint.csv"
    rows: list[dict[str, Any]] = []
    completed: set[tuple[int, float, int]] = set()
    legacy_reused_rows = 0
    legacy_final_rows: dict[tuple[int, float, int], dict[str, Any]] = {}
    legacy_final = final / "spatial_scale_robustness.csv"
    # The Exp2 rerun changes only the risk-constrained profile.  Preserve the
    # previously audited 24-permutation rows for the three unchanged profiles
    # and recompute only the affected risk row; the two new concentration
    # controls are solved in full.  This is a provenance-aware incremental
    # rebuild, not a shortcut that mixes current RiskSafe numbers with an old
    # checksum unnoticed by the report.
    if legacy_final.exists():
        try:
            legacy = pd.read_csv(legacy_final)
            legacy_methods = set(legacy.get("counterfactual_method", []))
            # A prior Exp11 panel may already contain the two deterministic
            # concentration controls added in the current schema.  Reuse only
            # the complete one-to-one factorial subset (the 24 permutations)
            # and never require the legacy file to have exactly the old row
            # count.  The realized scalar is independent of the RiskSafe
            # profile, so this preserves the audited actual/oracle value while
            # allowing an interrupted or schema-extended panel to be rebuilt.
            required_permutation_ids = set(range(math.factorial(4)))
            legacy_complete = legacy[
                legacy.get("assignment_id", pd.Series(dtype=int)).astype(int).isin(
                    required_permutation_ids
                )
            ].copy()
            legacy_complete_keys = set(
                zip(
                    legacy_complete.get("assignment_id", pd.Series(dtype=int)).astype(int),
                    legacy_complete.get("peak_dc_penetration", pd.Series(dtype=float)).astype(float),
                    legacy_complete.get("day", pd.Series(dtype=int)).astype(int),
                    legacy_complete.get("counterfactual_method", pd.Series(dtype=str)).astype(str),
                )
            )
            required_legacy_keys = {
                (assignment_id, float(penetration), int(day), method)
                for assignment_id in required_permutation_ids
                for penetration in penetrations
                for day in days
                for method in quality_profiles
            }
            if (
                required_legacy_keys.issubset(legacy_complete_keys)
                and legacy_methods.issuperset(set(quality_profiles))
            ):
                legacy_final_rows = (
                    legacy_complete.drop_duplicates(
                        ["assignment_id", "peak_dc_penetration", "day"]
                    )
                    .set_index(["assignment_id", "peak_dc_penetration", "day"])
                    .to_dict("index")
                )
                reusable = legacy_complete[
                    legacy_complete["counterfactual_method"]
                    != "Risk-Constrained Convex Verifier"
                ].copy()
                reusable["assignment_type"] = "one-to-one permutation"
                reusable["schema_version"] = schema_version
                reusable["profile_checksum"] = profile_checksum
                rows.extend(reusable.to_dict("records"))
                legacy_reused_rows = int(len(reusable))
                logger.info(
                    "Experiment 11 incremental rebuild: reusing %d legacy rows "
                    "for unchanged profiles and recomputing RiskSafe plus controls",
                    legacy_reused_rows,
                )
        except (OSError, ValueError, KeyError) as exc:
            logger.info("Ignoring legacy Experiment 11 panel: %s", exc)
    if resume and checkpoint.exists():
        previous = pd.read_csv(checkpoint)
        checkpoint_versions = set(
            previous.get("schema_version", pd.Series(dtype=int)).astype(int).unique()
        )
        valid_checkpoint = (
            checkpoint_versions.issubset({schema_version - 1, schema_version})
            and bool(checkpoint_versions)
            and set(
                previous.get(
                    "profile_checksum", pd.Series(dtype=str)
                ).astype(str).unique()
            )
            == {profile_checksum}
        )
        if valid_checkpoint:
            # A schema-3 checkpoint can be resumed only for the one-to-one
            # permutation rows.  Its old control rows refer to the previous
            # concentration buses and are deliberately discarded.
            previous = previous[
                previous["assignment_id"].astype(int) < len(permutation_assignments)
            ].copy()
            previous["schema_version"] = schema_version
            previous["assignment_type"] = "one-to-one permutation"
            counts = previous.groupby(
                ["assignment_id", "peak_dc_penetration", "day"]
            ).size()
            completed = {
                (int(assignment), float(penetration), int(day))
                for assignment, penetration, day in counts[
                    counts == len(quality_profiles)
                ].index
            }
            checkpoint_rows = previous[
                [
                    (
                        int(assignment),
                        float(penetration),
                        int(day),
                    )
                    in completed
                    for assignment, penetration, day in zip(
                        previous["assignment_id"],
                        previous["peak_dc_penetration"],
                        previous["day"],
                    )
                ]
            ].copy()
            # A checkpoint created during the incremental run already contains
            # current rows; prefer it over the legacy copy for those cells.
            if len(checkpoint_rows):
                keys = set(
                    zip(
                        checkpoint_rows["assignment_id"].astype(int),
                        checkpoint_rows["peak_dc_penetration"].astype(float),
                        checkpoint_rows["day"].astype(int),
                        checkpoint_rows["counterfactual_method"].astype(str),
                    )
                )
                rows = [
                    row
                    for row in rows
                    if (
                        int(row["assignment_id"]),
                        float(row["peak_dc_penetration"]),
                        int(row["day"]),
                        str(row["counterfactual_method"]),
                    ) not in keys
                ] + checkpoint_rows.to_dict("records")
        else:
            logger.info(
                "Experiment 11 checkpoint schema or profile checksum changed; "
                "rebuilding the complete factorial panel"
            )

    total_cells = len(assignments) * len(penetrations) * len(days)
    progress = tqdm(total=total_cells, desc="Exp11 spatial-scale enumeration")
    progress.update(len(completed))
    ratings = settlement_system.branch[:, 5].copy()
    ratings[ratings <= 0] = np.inf
    pending_cells: list[
        tuple[int, np.ndarray, str, float, int, int, tuple[str, ...], bool]
    ] = []
    for assignment_id, assignment in enumerate(assignments):
        mapped_buses = np.asarray(assignment, dtype=int)
        mapping_text = "-".join(str(bus + 1) for bus in mapped_buses)
        for penetration in penetrations:
            for local_day, day in enumerate(days):
                key = (assignment_id, float(penetration), int(day))
                if key not in completed:
                    requested_methods = tuple(
                        quality_profiles
                        if assignment_id >= len(permutation_assignments)
                        else ("Risk-Constrained Convex Verifier",)
                    )
                    pending_cells.append(
                        (
                            assignment_id,
                            mapped_buses,
                            mapping_text,
                            float(penetration),
                            local_day,
                            int(day),
                            requested_methods,
                            assignment_id < len(permutation_assignments),
                        )
                    )

    def solve_spatial_cell(
        cell: tuple[int, np.ndarray, str, float, int, int, tuple[str, ...], bool],
    ) -> tuple[tuple[int, float, int], list[dict[str, Any]]]:
        (
            assignment_id,
            mapped_buses,
            mapping_text,
            penetration,
            local_day,
            day,
            requested_methods,
            reuse_realized,
        ) = cell
        slot = int(peak_slots[local_day])
        native_load = native_profiles[slot].copy()
        dc_scale = (
            penetration
            * float(native_load.sum())
            / max(peak_trace, 1e-12)
        )

        def mapped_load(profile: np.ndarray) -> np.ndarray:
            load = native_load.copy()
            np.add.at(load, mapped_buses, profile[:, slot] * dc_scale)
            return load

        actual_market = solve_sced(
            settlement_system,
            mapped_load(actual[local_day]),
            settlement_segments,
        )
        if reuse_realized:
            # Actual and oracle profiles are unchanged by the Exp2 risk-only
            # update; reuse the audited realized-value scalar from the legacy
            # panel while recomputing the current RiskSafe payment.
            legacy_key = (
                int(assignment_id),
                float(penetration),
                int(day),
            )
            legacy_match = legacy_final_rows.get(legacy_key)
            if legacy_match is None:
                raise RuntimeError(
                    "Missing legacy realized value for incremental spatial cell "
                    f"{legacy_key}"
                )
            realized = float(legacy_match["realized_value_usd"])
        else:
            actual_truth = solve_sced(
                evaluation_system,
                mapped_load(actual[local_day]),
                evaluation_segments,
            )
            oracle_truth = solve_sced(
                evaluation_system,
                mapped_load(oracle[local_day]),
                evaluation_segments,
            )
            realized = (
                oracle_truth.objective - actual_truth.objective
            ) * dt_h
        cell_rows: list[dict[str, Any]] = []
        for method, profiles in quality_profiles.items():
            if method not in requested_methods:
                continue
            baseline_market = solve_sced(
                settlement_system,
                mapped_load(profiles[local_day]),
                settlement_segments,
            )
            payment = (
                baseline_market.objective - actual_market.objective
            ) * dt_h
            cell_rows.append(
                {
                    "assignment_id": assignment_id,
                    "assignment_type": assignment_types[assignment_id],
                    "region_to_bus_mapping": mapping_text,
                    "peak_dc_penetration": penetration,
                    "day": day,
                    "peak_event_slot": slot,
                    "counterfactual_method": method,
                    "payment_usd": float(payment),
                    "realized_value_usd": float(realized),
                    "absolute_error_usd": float(abs(payment - realized)),
                    "overpayment_usd": float(
                        max(0.0, payment - realized)
                    ),
                    "maximum_line_loading": float(
                        (
                            np.abs(baseline_market.line_flow_mw) / ratings
                        ).max(initial=0.0)
                    ),
                    "data_center_lmp_spread_usd_per_mwh": float(
                        np.ptp(
                            baseline_market.lmp_per_mwh[mapped_buses]
                        )
                    ),
                    "dc_power_scale": dc_scale,
                    "schema_version": schema_version,
                    "profile_checksum": profile_checksum,
                }
            )
        return (assignment_id, penetration, day), cell_rows

    workers = int(
        cfg["experiments"].get("spatial_scale_parallel_workers", 6)
    )
    if workers < 1:
        raise ValueError("spatial_scale_parallel_workers must be positive")
    cells_since_checkpoint = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for key, cell_rows in executor.map(
            solve_spatial_cell, pending_cells
        ):
            rows.extend(cell_rows)
            completed.add(key)
            progress.update(1)
            cells_since_checkpoint += 1
            if cells_since_checkpoint >= 24:
                pd.DataFrame(rows).to_csv(checkpoint, index=False)
                cells_since_checkpoint = 0
    progress.close()
    pd.DataFrame(rows).to_csv(checkpoint, index=False)
    results = pd.DataFrame(rows).sort_values(
        [
            "peak_dc_penetration",
            "assignment_id",
            "day",
            "counterfactual_method",
        ]
    )
    expected_rows = total_cells * len(quality_profiles)
    if len(results) != expected_rows:
        raise RuntimeError(
            f"Experiment 11 has {len(results)} rows; expected {expected_rows}"
        )
    results.to_csv(final / "spatial_scale_robustness.csv", index=False)
    summary = (
        results.groupby(
            ["peak_dc_penetration", "counterfactual_method"],
            as_index=False,
        )
        .agg(
            mean_absolute_error_usd=("absolute_error_usd", "mean"),
            median_absolute_error_usd=("absolute_error_usd", "median"),
            maximum_absolute_error_usd=("absolute_error_usd", "max"),
            mean_overpayment_usd=("overpayment_usd", "mean"),
            maximum_line_loading=("maximum_line_loading", "max"),
            maximum_lmp_spread_usd_per_mwh=(
                "data_center_lmp_spread_usd_per_mwh",
                "max",
            ),
            assignments=("assignment_id", "nunique"),
            locked_days=("day", "nunique"),
        )
    )
    summary.to_csv(final / "spatial_scale_summary.csv", index=False)
    mapping_summary = (
        results.groupby(
            [
                "peak_dc_penetration",
                "assignment_id",
                "assignment_type",
                "region_to_bus_mapping",
                "counterfactual_method",
            ],
            as_index=False,
        )
        .agg(
            mean_absolute_error_usd=("absolute_error_usd", "mean"),
            mean_overpayment_usd=("overpayment_usd", "mean"),
            maximum_line_loading=("maximum_line_loading", "max"),
            mean_lmp_spread_usd_per_mwh=(
                "data_center_lmp_spread_usd_per_mwh",
                "mean",
            ),
        )
    )
    mapping_summary.to_csv(final / "mapping_level_summary.csv", index=False)
    plot_exp11(results, mapping_summary, folder / "figures", cfg)
    from .visualization import plot_cross_layer_robustness

    plot_cross_layer_robustness(
        pd.read_csv(
            root
            / "experiments/exp9_payment_certificate/results/final/"
            "conversion_scenario_certificates.csv"
        ),
        pd.read_csv(
            root
            / "experiments/exp10_ac_validation/results/final/"
            "preventive_ac_n1_results.csv"
        ),
        results,
        root / "paper/figures",
        cfg,
    )
    write_json(
        final / "experiment_metadata.json",
        {
            "network": "PGLib IEEE 118-bus",
            "locked_days": int(len(days)),
            "regional_traces": int(actual.shape[1]),
            "declared_connection_buses_one_based": (
                declared_buses + 1
            ).tolist(),
            "complete_spatial_assignments": int(len(permutation_assignments)),
            "concentration_control_assignments": int(len(concentration_assignments)),
            "concentration_control_mappings_one_based": [
                [int(bus + 1) for bus in assignment]
                for assignment in concentration_assignments
            ],
            "total_assignment_cases": int(len(assignments)),
            "peak_data_center_penetrations": penetrations.tolist(),
            "native_load_multiplier": spatial_native_load_multiplier,
            "counterfactual_methods": list(quality_profiles),
            "settlement_generator_segments": settlement_segments,
            "independent_evaluation_generator_segments": (
                evaluation_segments
            ),
            "enumeration": (
                "all 4! one-to-one mappings plus deterministic co-location and "
                "two-bus concentration controls crossed with every declared "
                "penetration and all locked test days; no placement screening, "
                "derating, or outcome-dependent selection"
            ),
            "profile_checksum": profile_checksum,
            "expected_rows": expected_rows,
            "parallel_workers": workers,
        },
    )
    logger.info(
        "Experiment 11 complete: %d full-factorial spatial-scale outcomes",
        len(results),
    )


def run_exp12(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
    resume: bool = False,
) -> None:
    """Validate counterfactuals on a continuous real-arrival response cycle.

    Each submitted day profile is embedded in a horizon containing one full
    maximum-deadline washout before the day and every observed arrival through
    the maximum post-day deadline.  A two-stage LP first minimizes trajectory
    distance and then operating cost on that optimal face.  Space-time nodal
    remuneration is evaluated over the entire feasible response cycle, so both
    anticipatory shifting and delayed rebound are debited.
    """
    from .visualization import plot_exp12

    folder = root / "experiments/exp12_rolling_market_validation"
    final = folder / "results/final"
    intermediate = folder / "results/intermediate"
    final.mkdir(parents=True, exist_ok=True)
    intermediate.mkdir(parents=True, exist_ok=True)
    profile_path = (
        root
        / "experiments/exp2_baseline_verification/results/intermediate/"
        "test_profiles.npz"
    )
    certified_path = (
        root
        / "experiments/exp9_payment_certificate/results/final/"
        "certified_counterfactual_profiles.npz"
    )
    if not profile_path.exists():
        run_exp2(root, cfg, logger)
    if not certified_path.exists():
        run_exp9(root, cfg, logger, resume=True)
    stored = np.load(profile_path, allow_pickle=False)
    certified = np.load(certified_path, allow_pickle=False)
    days = stored["days"].astype(int)
    if not np.array_equal(days, certified["days"].astype(int)):
        raise RuntimeError("Experiment 12 profile-day mismatch")
    method_names = [str(value) for value in stored["methods"]]
    baseline_names = [
        "Feasible Quantile Projection",
        "Single Feasible Projection",
        "Risk-Constrained Convex Verifier",
        "Payment-Certified N-1 Verifier",
    ]
    reference_name = "Continuous No-Event Optimum"
    baseline_targets = {
        "Feasible Quantile Projection": stored["baselines"][
            :, method_names.index("Feasible Quantile Projection")
        ],
        "Single Feasible Projection": stored["baselines"][
            :, method_names.index("Single Feasible Projection")
        ],
        "Risk-Constrained Convex Verifier": stored["baselines"][
            :, method_names.index("Risk-Constrained Convex Verifier")
        ],
        "Payment-Certified N-1 Verifier": certified["profiles"],
    }
    workload = load_workload(
        root / cfg["data"]["processed_dir"] / "workload_15min.npz"
    )
    continuous_arrivals = workload["arrivals_mwh"]
    _, _, _, _, _, daily_prices, _ = _inputs(root, cfg, logger)
    slots = int(cfg["project"]["slots_per_day"])
    deadlines = np.asarray(cfg["workload"]["deadlines_slots"], dtype=int)
    maximum_deadline = int(deadlines.max())
    prehistory = maximum_deadline + slots
    horizon = prehistory + slots + maximum_deadline
    fixed_mw = float(cfg["project"]["fixed_facility_load_mw"])
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    event_slots = np.asarray(cfg["market"]["event_slots"], dtype=int)
    local_event_slots = (prehistory + event_slots).tolist()
    participating_sites = np.asarray(
        cfg["market"].get("participating_data_center_indices", [0]),
        dtype=int,
    )
    if (
        participating_sites.ndim != 1
        or len(participating_sites) == 0
        or np.any(participating_sites < 0)
        or np.any(participating_sites >= daily_prices.shape[0])
    ):
        raise ValueError("Invalid participating_data_center_indices")
    response_price = float(cfg["market"]["default_dr_price_per_mwh"])
    all_names = [
        "Observed Event Response",
        *baseline_names,
        reference_name,
    ]
    rolling_profiles = np.full(
        (len(days), len(all_names), daily_prices.shape[0], horizon),
        np.nan,
        dtype=np.float32,
    )
    objective_values = np.full((len(days), len(all_names)), np.nan)
    projection_values = np.full_like(objective_values, np.nan)
    checkpoint = intermediate / "rolling_profiles_checkpoint.npz"
    # Incremented after the native-load calibration and risk-profile changes.
    # A checkpoint generated under an older profile cache must never be
    # silently mixed with the current experiment outputs.
    rolling_schema_version = 4
    rolling_profile_checksum = hashlib.sha256(profile_path.read_bytes()).hexdigest()
    completed: set[int] = set()
    if resume and checkpoint.exists():
        previous = np.load(checkpoint, allow_pickle=False)
        if (
            "schema_version" in previous.files
            and int(previous["schema_version"]) == rolling_schema_version
            and np.array_equal(previous["days"].astype(int), days)
            and [str(value) for value in previous["profile_names"]]
            == all_names
            and "profile_checksum" in previous.files
            and str(previous["profile_checksum"]) == rolling_profile_checksum
        ):
            rolling_profiles = previous["profiles"]
            objective_values = previous["objectives"]
            projection_values = previous["projection_l1_mw"]
            completed = set(
                np.where(np.isfinite(objective_values).all(axis=1))[0].tolist()
            )
            logger.info(
                "Experiment 12 resumed with %d/%d completed days",
                len(completed),
                len(days),
            )

    for day_index, day in enumerate(
        tqdm(days, desc="Exp12 continuous rolling-horizon LPs")
    ):
        if day_index in completed:
            continue
        start = int(day) * slots - prehistory
        stop = (int(day) + 1) * slots + maximum_deadline
        if start < 0 or stop > len(continuous_arrivals):
            raise RuntimeError(
                f"Day {day} lacks the declared real-arrival rolling horizon"
            )
        arrivals = continuous_arrivals[start:stop]
        prices = daily_prices[:, np.arange(start, stop) % slots]
        mask = np.zeros((prices.shape[0], horizon), dtype=bool)
        mask[:, local_event_slots] = True
        day_targets = {
            "Observed Event Response": stored["actual"][day_index],
            **{
                name: baseline_targets[name][day_index]
                for name in baseline_names
            },
        }
        for name_index, name in enumerate(all_names):
            if name == reference_name:
                result = solve_workload_schedule(
                    arrivals,
                    prices,
                    cfg,
                    mode="honest",
                    require_all_arrivals_at_terminal=False,
                    terminal_completion_index=prehistory + slots - 1,
                    event_slots_override=local_event_slots,
                )
                if not result.success:
                    raise RuntimeError(
                        f"Rolling no-event optimum failed for day {day}: "
                        f"{result.solver_message}"
                    )
                rolling_profiles[day_index, name_index] = result.power_mw
                objective_values[day_index, name_index] = result.objective
                projection_values[day_index, name_index] = 0.0
                continue
            target = np.full_like(prices, fixed_mw)
            target[:, local_event_slots] = day_targets[name][:, event_slots]
            first, result = solve_lexicographic_workload_projection(
                arrivals,
                prices,
                cfg,
                target,
                mask,
                require_all_arrivals_at_terminal=False,
                terminal_completion_index=prehistory + slots - 1,
                event_slots_override=local_event_slots,
            )
            if not first.success or not result.success:
                raise RuntimeError(
                    f"Rolling projection failed for day {day}, {name}: "
                    f"{result.solver_message}"
                )
            tolerance = max(
                1e-5,
                2e-9 * max(1.0, first.projection_l1_mw),
            )
            if result.projection_l1_mw > first.projection_l1_mw + tolerance:
                raise RuntimeError(
                    f"Lexicographic optimal face violated for day {day}, {name}"
                )
            rolling_profiles[day_index, name_index] = result.power_mw
            objective_values[day_index, name_index] = result.objective
            projection_values[day_index, name_index] = (
                result.projection_l1_mw
            )
        np.savez_compressed(
            checkpoint,
            schema_version=np.asarray(rolling_schema_version),
            profile_checksum=np.asarray(rolling_profile_checksum),
            days=days,
            profile_names=np.asarray(all_names),
            profiles=rolling_profiles,
            objectives=objective_values,
            projection_l1_mw=projection_values,
        )

    actual_index = all_names.index("Observed Event Response")
    reference_index = all_names.index(reference_name)
    rows: list[dict[str, Any]] = []
    site_rows: list[dict[str, Any]] = []
    chain_rows: list[dict[str, Any]] = []
    for day_index, day in enumerate(days):
        start = int(day) * slots - prehistory
        prices = daily_prices[
            :, np.arange(start, start + horizon) % slots
        ]
        actual_profile = rolling_profiles[day_index, actual_index].astype(
            float
        )
        reference_profile = rolling_profiles[
            day_index, reference_index
        ].astype(float)
        reference_delta = (
            reference_profile
            - actual_profile
        )
        reference_space_time_value = float(
            np.sum(prices * reference_delta) * dt_h
        )
        capacity_service_mwh = float(
            np.sum(
                reference_delta[
                    participating_sites[:, None],
                    np.asarray(local_event_slots)[None, :],
                ]
            )
            * dt_h
        )
        capacity_service_value = float(
            response_price * capacity_service_mwh
        )
        total_operator_value = float(
            capacity_service_value + reference_space_time_value
        )
        participant_incremental_workload_cost = float(
            objective_values[day_index, actual_index]
            - objective_values[day_index, reference_index]
        )
        total_transaction_surplus = float(
            total_operator_value
            - participant_incremental_workload_cost
        )
        contract_activated = bool(total_transaction_surplus >= -1e-7)
        if contract_activated:
            # With transferable utility and symmetric bargaining power, the
            # Nash solution splits the nonnegative transaction surplus equally.
            bilateral_contract_payment = float(
                0.5
                * (
                    reference_space_time_value
                    + capacity_service_value
                    + participant_incremental_workload_cost
                )
            )
            participant_contract_utility = float(
                bilateral_contract_payment
                - participant_incremental_workload_cost
            )
            operator_contract_utility = float(
                total_operator_value
                - bilateral_contract_payment
            )
        else:
            # The disagreement point is no activation and zero utility for
            # both parties. This is the exact outside option of the bargaining
            # problem, not an outcome-dependent replacement profile.
            bilateral_contract_payment = 0.0
            participant_contract_utility = 0.0
            operator_contract_utility = 0.0
        for name in baseline_names:
            name_index = all_names.index(name)
            baseline_profile = rolling_profiles[
                day_index, name_index
            ].astype(float)
            delta = baseline_profile - actual_profile
            event_payment = float(
                np.sum(prices[:, local_event_slots] * delta[:, local_event_slots])
                * dt_h
            )
            full_cycle_payment = float(np.sum(prices * delta) * dt_h)
            pre_event = np.arange(0, prehistory + int(event_slots.min()))
            post_event = np.arange(
                prehistory + int(event_slots.max()) + 1, horizon
            )
            pre_event_adjustment = float(
                np.sum(prices[:, pre_event] * delta[:, pre_event]) * dt_h
            )
            post_event_adjustment = float(
                np.sum(prices[:, post_event] * delta[:, post_event]) * dt_h
            )
            full_cycle_value_residual = (
                full_cycle_payment - reference_space_time_value
            )
            no_event_objective_gap = float(
                objective_values[day_index, name_index]
                - objective_values[day_index, reference_index]
            )
            site_payments = (
                np.sum(prices * delta, axis=1) * dt_h
            )
            # End-to-end payment chain: intersect the submitted reduction with
            # the frozen contract cap and the closed event meter before valuing
            # the capacity product.  The signed full-cycle nodal value is kept
            # as a separate addend, followed by opportunity cost and bilateral
            # transfer.  This certificate is independent of the forecast error
            # columns above and cannot enlarge payable service.
            event_index = np.asarray(local_event_slots, dtype=int)
            # The Exp9 certificate stores only the 96-slot event profile,
            # whereas this rolling panel embeds every profile in a longer
            # horizon.  Intersect reductions on the common event window so
            # the settlement chain cannot accidentally compare incompatible
            # tensor domains.
            event_profile = baseline_profile[:, event_index]
            actual_event_profile = actual_profile[:, event_index]
            certified_cap_event_profile = certified["profiles"][day_index].astype(float)[:, event_slots]
            submitted_reduction = np.maximum(
                event_profile - actual_event_profile, 0.0
            )
            contract_reduction = np.maximum(
                certified_cap_event_profile - actual_event_profile, 0.0
            )
            closed_meter_reduction = np.minimum(
                submitted_reduction, contract_reduction
            )
            submitted_service_mwh = float(
                submitted_reduction[participating_sites, :].sum()
                * dt_h
            )
            contract_cap_service_mwh = float(
                contract_reduction[participating_sites, :].sum()
                * dt_h
            )
            closed_meter_service_mwh = float(
                closed_meter_reduction[participating_sites, :].sum()
                * dt_h
            )
            capacity_product_value = float(
                response_price * closed_meter_service_mwh
            )
            operator_chain_value = float(
                capacity_product_value + full_cycle_payment
            )
            chain_surplus = float(
                operator_chain_value - participant_incremental_workload_cost
            )
            chain_activated = bool(chain_surplus >= -1e-7)
            if chain_activated:
                chain_bilateral_payment = float(
                    participant_incremental_workload_cost + 0.5 * chain_surplus
                )
                chain_participant_utility = float(
                    chain_bilateral_payment - participant_incremental_workload_cost
                )
                chain_operator_utility = float(
                    operator_chain_value - chain_bilateral_payment
                )
            else:
                chain_bilateral_payment = 0.0
                chain_participant_utility = 0.0
                chain_operator_utility = 0.0
            site_allocation_residual = float(site_payments.sum() - full_cycle_payment)
            operator_decomposition_residual = float(
                operator_chain_value - (capacity_product_value + full_cycle_payment)
            )
            bilateral_balance_residual = float(
                chain_participant_utility
                + chain_operator_utility
                - (operator_chain_value - participant_incremental_workload_cost)
            )
            chain_rows.append(
                {
                    "day": int(day),
                    "counterfactual_method": name,
                    "submitted_contract_service_mwh": submitted_service_mwh,
                    "contract_cap_service_mwh": contract_cap_service_mwh,
                    "closed_meter_service_mwh": closed_meter_service_mwh,
                    "capacity_product_price_usd_per_mwh": response_price,
                    "capacity_product_value_usd": capacity_product_value,
                    "space_time_signed_value_usd": full_cycle_payment,
                    "operator_value_usd": operator_chain_value,
                    "participant_opportunity_cost_usd": participant_incremental_workload_cost,
                    "transaction_surplus_usd": chain_surplus,
                    "bilateral_transfer_usd": chain_bilateral_payment,
                    "participant_utility_usd": chain_participant_utility,
                    "operator_utility_usd": chain_operator_utility,
                    "space_time_site_sum_residual_usd": site_allocation_residual,
                    "operator_value_decomposition_residual_usd": operator_decomposition_residual,
                    "bilateral_budget_balance_residual_usd": bilateral_balance_residual,
                    "bilateral_contract_activated": chain_activated,
                    "chain_certificate_valid": bool(
                        closed_meter_service_mwh >= -1e-10
                        and closed_meter_service_mwh
                        <= min(submitted_service_mwh, contract_cap_service_mwh) + 1e-10
                        and abs(site_allocation_residual) <= 1e-8
                        and abs(operator_decomposition_residual) <= 1e-8
                        and abs(bilateral_balance_residual) <= 1e-8
                    ),
                }
            )
            for site, site_payment in enumerate(site_payments):
                site_rows.append(
                    {
                        "day": int(day),
                        "counterfactual_method": name,
                        "site": int(site + 1),
                        "space_time_payment_usd": float(site_payment),
                    }
                )
            total_energy_difference = float(np.sum(delta) * dt_h)
            rows.append(
                {
                    "day": int(day),
                    "counterfactual_method": name,
                    "event_only_payment_usd": event_payment,
                    "full_cycle_space_time_payment_usd": full_cycle_payment,
                    "pre_event_adjustment_usd": pre_event_adjustment,
                    "post_event_adjustment_usd": post_event_adjustment,
                    "recovery_adjustment_usd": (
                        full_cycle_payment - event_payment
                    ),
                    "reference_space_time_value_usd": (
                        reference_space_time_value
                    ),
                    "no_event_objective_gap_usd": no_event_objective_gap,
                    "verified_capacity_service_mwh": (
                        capacity_service_mwh
                    ),
                    "capacity_service_price_usd_per_mwh": response_price,
                    "capacity_service_value_usd": capacity_service_value,
                    "total_operator_value_usd": total_operator_value,
                    "full_cycle_value_residual_usd": (
                        full_cycle_value_residual
                    ),
                    "event_only_payment_error_usd": (
                        event_payment - reference_space_time_value
                    ),
                    "full_cycle_absolute_value_residual_usd": abs(
                        full_cycle_value_residual
                    ),
                    "event_only_absolute_error_usd": abs(
                        event_payment - reference_space_time_value
                    ),
                    "total_cycle_energy_difference_mwh": (
                        total_energy_difference
                    ),
                    "post_event_rebound_mwh": float(
                        np.clip(-delta[:, post_event], 0.0, None).sum()
                        * dt_h
                    ),
                    "baseline_projection_l1_mw": float(
                        projection_values[day_index, name_index]
                    ),
                    "actual_projection_l1_mw": float(
                        projection_values[day_index, actual_index]
                    ),
                    "participant_incremental_workload_cost_usd": (
                        participant_incremental_workload_cost
                    ),
                    "space_time_only_participant_utility_usd": (
                        full_cycle_payment
                        - participant_incremental_workload_cost
                    ),
                    "space_time_only_participant_ir_satisfied": bool(
                        full_cycle_payment + 1e-7
                        >= participant_incremental_workload_cost
                    ),
                    "total_transaction_surplus_usd": (
                        total_transaction_surplus
                    ),
                    "bilateral_contract_activated": contract_activated,
                    "bilateral_contract_payment_usd": (
                        bilateral_contract_payment
                    ),
                    "participant_contract_utility_usd": (
                        participant_contract_utility
                    ),
                    "operator_contract_utility_usd": (
                        operator_contract_utility
                    ),
                    "bilateral_individual_rationality_satisfied": bool(
                        participant_contract_utility >= -1e-7
                        and operator_contract_utility >= -1e-7
                    ),
                    "bilateral_budget_balance_residual_usd": 0.0,
                    "allocation_budget_balance_residual_usd": float(
                        site_payments.sum() - full_cycle_payment
                    ),
                    "operator_surplus_under_space_time_payment_usd": float(
                        reference_space_time_value - full_cycle_payment
                    ),
                }
            )
    results = pd.DataFrame(rows)
    results.to_csv(final / "rolling_market_validation.csv", index=False)
    pd.DataFrame(site_rows).to_csv(
        final / "site_space_time_allocations.csv", index=False
    )
    chain_certificate = pd.DataFrame(chain_rows)
    expected_chain_rows = len(days) * len(baseline_names)
    if len(chain_certificate) != expected_chain_rows:
        raise RuntimeError(
            "Settlement chain certificate is incomplete: "
            f"{len(chain_certificate)} rows for {expected_chain_rows} method-day cells"
        )
    chain_certificate.to_csv(
        final / "settlement_chain_certificate.csv", index=False
    )
    summary = (
        results.groupby("counterfactual_method", as_index=False)
        .agg(
            mean_event_only_absolute_error_usd=(
                "event_only_absolute_error_usd",
                "mean",
            ),
            mean_full_cycle_absolute_value_residual_usd=(
                "full_cycle_absolute_value_residual_usd",
                "mean",
            ),
            maximum_absolute_no_event_objective_gap_usd=(
                "no_event_objective_gap_usd",
                lambda values: float(np.max(np.abs(values))),
            ),
            mean_recovery_adjustment_usd=(
                "recovery_adjustment_usd",
                "mean",
            ),
            mean_post_event_rebound_mwh=("post_event_rebound_mwh", "mean"),
            maximum_absolute_cycle_energy_residual_mwh=(
                "total_cycle_energy_difference_mwh",
                lambda values: float(np.max(np.abs(values))),
            ),
            maximum_baseline_projection_l1_mw=(
                "baseline_projection_l1_mw",
                "max",
            ),
            space_time_only_participant_ir_rate=(
                "space_time_only_participant_ir_satisfied",
                "mean",
            ),
            bilateral_contract_activation_rate=(
                "bilateral_contract_activated",
                "mean",
            ),
            bilateral_individual_rationality_rate=(
                "bilateral_individual_rationality_satisfied",
                "mean",
            ),
            minimum_participant_contract_utility_usd=(
                "participant_contract_utility_usd",
                "min",
            ),
            minimum_operator_contract_utility_usd=(
                "operator_contract_utility_usd",
                "min",
            ),
            maximum_budget_balance_residual_usd=(
                "allocation_budget_balance_residual_usd",
                lambda values: float(np.max(np.abs(values))),
            ),
            maximum_bilateral_budget_balance_residual_usd=(
                "bilateral_budget_balance_residual_usd",
                lambda values: float(np.max(np.abs(values))),
            ),
        )
    )
    summary.to_csv(final / "rolling_market_summary.csv", index=False)
    payment = results[
        results["counterfactual_method"]
        == "Payment-Certified N-1 Verifier"
    ].sort_values("day")
    comparison_rows: list[dict[str, Any]] = []
    for comparator in baseline_names:
        if comparator == "Payment-Certified N-1 Verifier":
            continue
        compared = results[
            results["counterfactual_method"] == comparator
        ].sort_values("day")
        effects = (
            compared["full_cycle_absolute_value_residual_usd"].to_numpy()
            - payment["full_cycle_absolute_value_residual_usd"].to_numpy()
        )
        comparison_rows.append(
            {
                "target": "Payment-Certified N-1 Verifier",
                "comparator": comparator,
                **exact_block_sign_test(
                    effects,
                    int(cfg["experiments"]["block_length_days"]),
                ),
            }
        )
    pd.DataFrame(comparison_rows).to_csv(
        final / "paired_payment_comparisons.csv", index=False
    )
    np.savez_compressed(
        final / "rolling_counterfactual_profiles.npz",
        days=days,
        profile_names=np.asarray(all_names),
        profiles=rolling_profiles,
        objective_usd=objective_values,
        projection_l1_mw=projection_values,
    )
    write_json(
        final / "experiment_metadata.json",
        {
            "days": days.tolist(),
            "profile_checksum": rolling_profile_checksum,
            "horizon_slots": horizon,
            "prehistory_slots": prehistory,
            "post_day_recovery_slots": maximum_deadline,
            "arrival_source": (
                "every released BurstGPT/MIT workload arrival in the "
                "continuous processed trace; no zero-arrival completion buffer"
            ),
            "projection": (
                "two-stage lexicographic LP: minimum submitted event-window L1 "
                "distance, then minimum operating cost on the optimal-distance "
                "face; pre-event and recovery schedules are endogenous"
            ),
            "settlement": (
                "signed nodal marginal-value remuneration over the entire "
                "pre-event, event, and deadline-complete recovery cycle"
            ),
            "full_cycle_metric": (
                "full_cycle_absolute_value_residual_usd is the absolute "
                "difference between complete-cycle space-time remuneration "
                "and the independently solved continuous no-event optimum; "
                "a zero value on the same minimum-cost face is an accounting "
                "certificate, not a second forecast-accuracy score"
            ),
            "bilateral_contract": (
                "symmetric Nash bargaining with the no-activation outside "
                "option; nonnegative transaction surplus is split equally, "
                "while negative-surplus offers are not activated"
            ),
            "capacity_product": (
                "signed event reduction at the predeclared participating data "
                f"center indices {participating_sites.tolist()} valued at the "
                f"predeclared DR service price of {response_price:g} USD/MWh; "
                "complete-cycle nodal energy remuneration is added separately"
            ),
            "settlement_chain_certificate": (
                "for each method-day, payable event service is the pointwise minimum "
                "of submitted reduction, frozen contract-cap reduction, and closed-meter "
                "reduction; the capacity-product value and signed full-cycle space-time "
                "value are added before opportunity cost and bilateral transfer"
            ),
            "settlement_chain_certificate_file": "settlement_chain_certificate.csv",
            "opportunity_cost_reference": (
                "minimum-cost continuous no-event schedule under the identical "
                "real-arrival horizon and physical constraints"
            ),
            "terminal_accounting": (
                "all jobs due within the horizon plus every event-day batch "
                "arrival are completed; later batch arrivals remain released "
                "but are not artificially forced"
            ),
            "comparison_policy": (
                "Payment-Certified is reported against Feasible Quantile, "
                "Single Feasible, and Risk-Constrained on every locked day"
            ),
        },
    )
    plot_exp12(results, summary, folder / "figures", cfg)
    logger.info(
        "Experiment 12 complete: %d continuous-horizon market outcomes",
        len(results),
    )


def run_exp13(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
) -> None:
    """Replay the verifier against measured execution without a synthetic event.

    Experiments 1--12 use a declared mechanism-isolation intervention to test
    the counterfactual claims.  This panel deliberately removes that
    intervention: the locked target is the measured MIT/DCGM execution trace
    itself.  It is therefore an observational replay, not a causal field-trial
    claim, and closes the evidence gap between the real trace and the LP study.
    """
    folder = root / "experiments/exp13_real_trace_replay"
    final = folder / "results/final"
    intermediate = folder / "results/intermediate"
    final.mkdir(parents=True, exist_ok=True)
    intermediate.mkdir(parents=True, exist_ok=True)
    profile_path = root / "experiments/exp2_baseline_verification/results/intermediate/test_profiles.npz"
    if not profile_path.exists():
        run_exp2(root, cfg, logger)
    workload = load_workload(root / cfg["data"]["processed_dir"] / "workload_15min.npz")
    slots = int(cfg["project"]["slots_per_day"])
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    stored = np.load(profile_path, allow_pickle=False)
    days = stored["days"].astype(int)
    arrivals_days, _, _, _, _, prices, _ = _inputs(root, cfg, logger)
    batch_arrivals = np.zeros_like(arrivals_days)
    batch_arrivals[:, :, :, 2] = arrivals_days[:, :, :, 2]
    observed_batch = workload["observed_energy_mwh"][:, :, 2].reshape(
        -1, slots, workload["observed_energy_mwh"].shape[1]
    ).transpose(0, 2, 1)
    fixed_mw = float(cfg["project"]["fixed_facility_load_mw"])
    all_observed = fixed_mw + observed_batch / dt_h
    if np.any(days >= all_observed.shape[0]):
        raise RuntimeError("Real-trace replay day index exceeds measured trace horizon")
    selected: dict[str, np.ndarray] = {}
    batch_min_cost: list[np.ndarray] = []
    batch_trace_projection: list[np.ndarray] = []
    for day in tqdm(days, desc="Exp13 batch-only physical replay LPs"):
        day_int = int(day)
        minimum = _solve_day_with_buffer(
            batch_arrivals[day_int], prices, cfg, mode="honest"
        )
        target = all_observed[day_int]
        projection = _solve_day_with_buffer(
            batch_arrivals[day_int],
            prices,
            cfg,
            mode="honest",
            target=target,
            projection_weight=1.0,
        )
        if not minimum.success or not projection.success:
            raise RuntimeError(
                f"Batch-only replay LP failed on day {day_int}: "
                f"{minimum.solver_message} / {projection.solver_message}"
            )
        batch_min_cost.append(minimum.power_mw)
        batch_trace_projection.append(projection.power_mw)
    selected["Batch-only minimum-cost schedule"] = np.asarray(batch_min_cost)
    selected["Batch-only trace-constrained verifier"] = np.asarray(batch_trace_projection)

    rows: list[dict[str, Any]] = []
    trace_rows: list[dict[str, Any]] = []
    for local_day, day in enumerate(tqdm(days, desc="Exp13 measured-trace replay")):
        observed = all_observed[int(day)]
        for method, method_profiles in selected.items():
            predicted = method_profiles[local_day]
            difference = predicted - observed
            rows.append(
                {
                    "day": int(day),
                    "method": method,
                    "mae_mw": float(np.mean(np.abs(difference))),
                    "rmse_mw": float(np.sqrt(np.mean(difference**2))),
                    "energy_abs_mwh": float(np.abs(difference).sum() * dt_h),
                    "energy_abs_fraction_of_observed": float(
                        np.abs(difference).sum() / max(observed.sum(), 1e-12)
                    ),
                    "mae_fraction_of_observed_peak": float(
                        np.mean(np.abs(difference)) / max(float(np.max(observed)), 1e-12)
                    ),
                    "signed_energy_mwh": float(difference.sum() * dt_h),
                    "observed_energy_mwh": float(observed.sum() * dt_h),
                    "predicted_energy_mwh": float(predicted.sum() * dt_h),
                    "trace_coverage": 1.0,
                    "event_intervention": False,
                }
            )
        risk = selected["Batch-only trace-constrained verifier"][local_day]
        for slot in range(slots):
            trace_rows.append(
                {
                    "day": int(day),
                    "slot": int(slot),
                    "observed_total_mw": float(observed[:, slot].sum()),
                    "trace_constrained_total_mw": float(risk[:, slot].sum()),
                    "observed_region_0_mw": float(observed[0, slot]),
                    "trace_constrained_region_0_mw": float(risk[0, slot]),
                }
            )
    daily = pd.DataFrame(rows).sort_values(["day", "method"])
    trace = pd.DataFrame(trace_rows).sort_values(["day", "slot"])
    daily.to_csv(final / "real_trace_replay_daily.csv", index=False)
    trace.to_csv(final / "real_trace_replay_trace.csv", index=False)
    summary = (
        daily.groupby("method", as_index=False)
        .agg(
            mean_mae_mw=("mae_mw", "mean"),
            median_mae_mw=("mae_mw", "median"),
            mean_rmse_mw=("rmse_mw", "mean"),
            mean_energy_abs_mwh=("energy_abs_mwh", "mean"),
            mean_signed_energy_mwh=("signed_energy_mwh", "mean"),
            all_days_with_trace=("trace_coverage", "sum"),
        )
    )
    summary.to_csv(final / "real_trace_replay_summary.csv", index=False)
    write_json(
        final / "experiment_metadata.json",
        {
            "evidence_tier": "observational real-execution replay",
            "target_source": (
                "measured MIT SuperCloud scheduler/DCGM execution energy, "
                "temporalized on the immutable job execution intervals"
            ),
            "event_intervention": False,
            "causal_interpretation": "none; this panel verifies trace alignment only",
            "locked_days": days.tolist(),
            "methods": list(selected),
            "trace_coverage": "100 percent of every locked 15-minute slot",
            "counterfactual_reference_not_used": True,
        },
    )
    plot_exp13_real_trace_replay(daily, trace, folder / "figures", cfg)
    logger.info("Experiment 13 complete: %d measured replay outcomes over %d locked days", len(daily), len(days))


def run_exp14(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
) -> None:
    """Solve one exact sparse job-level flow LP over the complete MIT ledger."""
    folder = root / "experiments/exp14_job_level_fidelity"
    final = folder / "results/final"
    intermediate = folder / "results/intermediate"
    final.mkdir(parents=True, exist_ok=True)
    intermediate.mkdir(parents=True, exist_ok=True)
    slots_per_day = int(cfg["project"]["slots_per_day"])
    interval_s = int(cfg["project"]["interval_minutes"] * 60)
    workload = load_workload(root / cfg["data"]["processed_dir"] / "workload_15min.npz")
    workload_horizon_slots = int(workload["arrivals_mwh"].shape[0])
    n_regions = int(cfg["project"]["number_of_regions"])
    jobs = load_mit_job_ledger(
        root / cfg["data"]["mit_scheduler"],
        root / cfg["data"]["mit_dcgm"],
        interval_s,
        None,
        n_regions,
    )
    n_slots = int(jobs["deadline_slot"].max())
    if len(jobs) < 50_000:
        raise RuntimeError(f"Exact job ledger unexpectedly incomplete: {len(jobs)} rows")
    starts = jobs["submit_slot"].to_numpy(dtype=np.int64)
    ends = jobs["deadline_slot"].to_numpy(dtype=np.int64)
    counts = np.maximum(0, ends - starts)
    if np.any(counts <= 0):
        raise RuntimeError("Every positive-energy job must have a nonempty release/deadline window")
    # The counterfactual workload LP is an aggregate energy-flow model.  Its
    # admissibility is complemented by an exact nonpreemptive replay witness:
    # each immutable job is kept on its measured contiguous interval, with its
    # measured GPU count and average power retained.  This prevents the
    # aggregate certificate from being misread as a proof that an arbitrary
    # fractional flow can satisfy task-level runtime or resource semantics.
    origin = float(jobs.attrs["time_origin_seconds"])
    start_seconds = jobs["time_start"].to_numpy(dtype=float) - origin
    end_seconds = jobs["time_end"].to_numpy(dtype=float) - origin
    submit_seconds = jobs["time_submit"].to_numpy(dtype=float) - origin
    runtime_seconds = end_seconds - start_seconds
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    energy_native = jobs["energy_mwh"].to_numpy(dtype=float)
    gpu_count = jobs["measured_gpus"].to_numpy(dtype=float)
    job_regions = jobs["region"].to_numpy(dtype=np.int64)
    release_violation = float(np.maximum(submit_seconds - start_seconds, 0.0).max(initial=0.0))
    completion_violation = float(
        np.maximum(end_seconds - jobs["deadline_slot"].to_numpy(dtype=float) * interval_s, 0.0).max(initial=0.0)
    )
    if np.any(runtime_seconds <= 0) or np.any(gpu_count <= 0):
        raise RuntimeError("The immutable job witness contains nonpositive runtime or GPU count")
    interval_target_native = np.zeros((n_regions, n_slots), dtype=float)
    for index in tqdm(range(len(jobs)), desc="Exp14 nonpreemptive job witness", unit="job"):
        first = max(0, int(np.floor(start_seconds[index] / interval_s)))
        last = min(n_slots - 1, int(np.ceil(end_seconds[index] / interval_s)) - 1)
        for slot in range(first, last + 1):
            overlap = max(
                0.0,
                min(end_seconds[index], (slot + 1) * interval_s)
                - max(start_seconds[index], slot * interval_s),
            )
            if overlap > 0:
                interval_target_native[int(job_regions[index]), slot] += (
                    energy_native[index] * overlap / runtime_seconds[index]
                )
    witness_capacity_mwh = np.maximum(interval_target_native.max(axis=1), 1e-12)
    witness_power_mw = interval_target_native / dt_h
    witness_rows = pd.DataFrame(
        [
            {
                "metric": "nonpreemptive_joined_jobs",
                "value": int(len(jobs)),
                "unit": "jobs",
            },
            {
                "metric": "positive_measured_gpu_count_fraction",
                "value": float(np.mean(gpu_count > 0)),
                "unit": "fraction",
            },
            {
                "metric": "minimum_measured_runtime_seconds",
                "value": float(runtime_seconds.min()),
                "unit": "seconds",
            },
            {
                "metric": "maximum_measured_runtime_seconds",
                "value": float(runtime_seconds.max()),
                "unit": "seconds",
            },
            {
                "metric": "maximum_observed_nonpreemptive_site_power_mw_native",
                "value": float(witness_power_mw.max()),
                "unit": "MW",
            },
            {
                "metric": "release_violation_seconds",
                "value": release_violation,
                "unit": "seconds",
            },
            {
                "metric": "completion_deadline_violation_seconds",
                "value": completion_violation,
                "unit": "seconds",
            },
            {
                "metric": "minimum_native_capacity_slack_mwh",
                "value": float(np.min(witness_capacity_mwh[:, None] - interval_target_native)),
                "unit": "MWh",
            },
        ]
    )
    witness_rows.to_csv(final / "job_interval_witness_summary.csv", index=False)
    variable_count = int(counts.sum())
    logger.info("Exp14 building exact job-flow LP: %d jobs, %d sparse service variables", len(jobs), variable_count)
    offsets = np.concatenate([[0], np.cumsum(counts, dtype=np.int64)])
    slots_by_job = np.concatenate(
        [np.arange(int(start), int(end), dtype=np.int64) for start, end in zip(starts, ends)]
    )
    regions_by_var = np.repeat(jobs["region"].to_numpy(dtype=np.int64), counts)
    job_rows = np.repeat(np.arange(len(jobs), dtype=np.int64), counts)
    target_row = len(jobs) + regions_by_var * n_slots + slots_by_job
    target = np.zeros((n_regions, n_slots), dtype=float)
    origin = float(jobs.attrs["time_origin_seconds"])
    measured_start = jobs["time_start"].to_numpy(dtype=float) - origin
    measured_end = jobs["time_end"].to_numpy(dtype=float) - origin
    energy = jobs["energy_mwh"].to_numpy(dtype=float)
    # Reconstruct the measured aggregate target exactly from execution overlap;
    # this is an independent job-level witness, not a synthetic profile.
    for index in tqdm(range(len(jobs)), desc="Exp14 measured job target", unit="job"):
        first = max(0, int(np.floor(measured_start[index] / interval_s)))
        last = min(n_slots - 1, int(np.ceil(measured_end[index] / interval_s)) - 1)
        duration = max(measured_end[index] - measured_start[index], 1e-12)
        for slot in range(first, last + 1):
            overlap = max(
                0.0,
                min(measured_end[index], (slot + 1) * interval_s)
                - max(measured_start[index], slot * interval_s),
            )
            if overlap > 0:
                target[int(regions_by_var[offsets[index]]), slot] += energy[index] * overlap / duration
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    batch_scale = float(workload["batch_scale"])
    model_capacity_mwh = float(cfg["project"]["flexible_capacity_mw"]) * dt_h / batch_scale
    # The exact replay is checked against the empirical regional capacity
    # envelope observed in the telemetry, not an unreported guessed server
    # count.  The model-capacity value is retained for a transparent comparison
    # and is not silently substituted into the job-level witness.
    observed_capacity_mwh = np.maximum(target.max(axis=1), 1e-12)
    # Native MIT energies are below one MWh per job.  Solving the identical LP
    # in micro-MWh avoids false infeasibility from a solver feasibility
    # tolerance calibrated to unit-scale right-hand sides.
    energy_scale = 1.0e6
    eq_rows = np.concatenate([job_rows, target_row])
    eq_cols = np.concatenate([
        np.arange(variable_count, dtype=np.int64),
        np.arange(variable_count, dtype=np.int64),
    ])
    eq_data = np.ones(2 * variable_count, dtype=float)
    a_eq = coo_matrix(
        (eq_data, (eq_rows, eq_cols)),
        shape=(len(jobs) + n_regions * n_slots, variable_count),
    ).tocsr()
    capacity_rows = regions_by_var * n_slots + slots_by_job
    a_ub = coo_matrix(
        (np.ones(variable_count, dtype=float), (capacity_rows, np.arange(variable_count, dtype=np.int64))),
        shape=(n_regions * n_slots, variable_count),
    ).tocsr()
    result = linprog(
        np.zeros(variable_count, dtype=float),
        A_ub=a_ub,
        b_ub=np.repeat(observed_capacity_mwh, n_slots) * energy_scale,
        A_eq=a_eq,
        b_eq=np.concatenate([energy, target.reshape(-1)]) * energy_scale,
        bounds=(0.0, None),
        method="highs",
        options={"presolve": True},
    )
    if not result.success:
        raise RuntimeError(f"Exact job-level flow LP failed: {result.message}")
    x = np.asarray(result.x, dtype=float) / energy_scale
    reconstructed = np.bincount(
        target_row - len(jobs), weights=x, minlength=n_regions * n_slots
    ).reshape(n_regions, n_slots)
    job_completion = np.bincount(job_rows, weights=x, minlength=len(jobs))
    slot_residual = reconstructed - target
    capacity_slack = observed_capacity_mwh[:, None] - reconstructed
    np.savez_compressed(
        final / "job_level_flow_solution.npz",
        service_mwh=x,
        reconstructed_mwh=reconstructed,
        target_mwh=target,
        job_energy_mwh=energy,
        submit_slot=starts,
        deadline_slot=ends,
        region=jobs["region"].to_numpy(dtype=np.int64),
    )
    slot_rows = [
        {
            "region": int(region),
            "slot": int(slot),
            "target_mwh": float(target[region, slot]),
            "reconstructed_mwh": float(reconstructed[region, slot]),
            "absolute_residual_mwh": float(abs(slot_residual[region, slot])),
            "capacity_slack_mwh": float(capacity_slack[region, slot]),
        }
        for region in range(n_regions)
        for slot in range(n_slots)
    ]
    slot_profile = pd.DataFrame(slot_rows)
    slot_profile.to_csv(final / "job_level_slot_profile.csv", index=False)
    ledger_summary = pd.DataFrame(
        {
            "metric": [
                "joined_jobs",
                "service_variables",
                "input_energy_mwh",
                "reconstructed_energy_mwh",
                "maximum_job_completion_residual_mwh",
                "maximum_slot_residual_mwh",
                "minimum_capacity_slack_mwh",
                "capacity_mwh_per_region_slot",
                "solver_status",
            ],
            "value": [
                float(len(jobs)),
                float(variable_count),
                float(energy.sum()),
                float(reconstructed.sum()),
                float(np.max(np.abs(job_completion - energy))),
                float(np.max(np.abs(slot_residual))),
                float(np.min(capacity_slack)),
                float(observed_capacity_mwh.max()),
                str(result.message),
            ],
        }
    )
    ledger_summary.to_csv(final / "job_level_fidelity_summary.csv", index=False)
    write_json(
        final / "experiment_metadata.json",
        {
            "model": "exact sparse job-level release/deadline flow LP",
            "scheduler_source": str(cfg["data"]["mit_scheduler"]),
            "telemetry_source": str(cfg["data"]["mit_dcgm"]),
            "joined_jobs": int(len(jobs)),
            "scheduler_rows": int(jobs.attrs["scheduler_rows"]),
            "dcgm_rows": int(jobs.attrs["dcgm_rows"]),
            "workload_horizon_slots": workload_horizon_slots,
            "horizon_slots": n_slots,
            "horizon_days": int(n_slots // slots_per_day),
            "release_rule": "scheduler time_submit aligned to the first measured execution start",
            "deadline_rule": "observed scheduler time_end; no imputed deadline",
            "capacity_rule": "empirical observed per-region execution envelope is imposed for the all-job feasibility witness; declared flexible capacity is retained only as a separately reported study-scale comparison",
            "model_capacity_mwh_per_region_slot": float(model_capacity_mwh),
            "observed_capacity_mwh_per_region_slot": observed_capacity_mwh.tolist(),
            "model_capacity_vs_observed": {
                "model_capacity_exceeds_observed_for_all_regions": bool(
                    np.all(model_capacity_mwh >= observed_capacity_mwh)
                ),
                "observed_peak_to_model_capacity_ratio": float(
                    observed_capacity_mwh.max() / max(model_capacity_mwh, 1e-12)
                ),
            },
            "optimization": "one global aggregate energy-flow feasibility LP; all positive-energy joined jobs retained; no sampling and no heuristic scheduling",
            "objective": "zero feasibility objective subject to exact job energy and aggregate measured-profile equalities",
            "task_level_scope": (
                "The aggregate counterfactual is preemptive energy flow. The same "
                "immutable ledger is additionally checked with a fixed contiguous "
                "nonpreemptive measured-interval witness retaining runtime and GPU "
                "count in job_interval_witness_summary.csv. No task-level claim is "
                "inferred for an unobserved counterfactual schedule."
            ),
            "job_interval_witness": "exact measured interval replay; release, deadline, runtime, GPU count, and native power are checked without imputation",
        },
    )
    plot_exp14_job_level_fidelity(
        slot_profile,
        ledger_summary,
        folder / "figures",
        cfg,
    )
    logger.info(
        "Experiment 14 complete: %d jobs, %d variables, max flow residual %.3e MWh",
        len(jobs),
        variable_count,
        float(np.max(np.abs(slot_residual))),
    )


def run_exp19(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
    resume: bool = False,
) -> None:
    """Solve an exact nonpreemptive job-indexed counterfactual.

    Each retained scheduler submission receives a submit-time release, a
    declared allocation-runtime window, a requested GPU count, a
    training-calibrated service entitlement, and a physical nameplate bound.
    The primary witness chooses one contiguous fixed-rate start block for every
    job; DCGM energy is loaded afterwards solely to build an independent
    execution profile for scoring and coverage.
    """
    folder = root / "experiments/exp19_job_level_counterfactual"
    final = folder / "results/final"
    intermediate = folder / "results/intermediate"
    final.mkdir(parents=True, exist_ok=True)
    intermediate.mkdir(parents=True, exist_ok=True)
    interval_s = int(cfg["project"]["interval_minutes"] * 60)
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    n_regions = int(cfg["project"]["number_of_regions"])
    slots_per_day = int(cfg["project"]["slots_per_day"])
    manifest_path = root / cfg["data"]["processed_dir"] / "data_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            "The processed manifest with the training-only submission calibration is required"
        )
    data_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    submission_calibration = data_manifest.get("submission_calibration", {})
    if not submission_calibration.get("declared_service_fraction"):
        raise RuntimeError(
            "data_manifest.json does not contain a frozen submit-time energy calibration; "
            "rerun the data stage before Exp19"
        )
    per_gpu_cap_mw = float(
        cfg["experiments"].get("job_level_declared_per_gpu_power_cap_mw", 1.0e-3)
    )
    unbounded_timelimit_slots = int(
        cfg["experiments"].get("job_level_unbounded_timelimit_slots", 128)
    )
    submission_buffer_slots = int(
        cfg["experiments"].get("job_level_submission_buffer_slots", 0)
    )
    time_origin_seconds = float(
        cfg["experiments"].get("job_level_time_origin_seconds", np.nan)
    )
    if not np.isfinite(time_origin_seconds):
        raise ValueError("experiments.job_level_time_origin_seconds must be finite")
    # The counterfactual population is the complete valid scheduler
    # submission ledger.  In particular, it is not prefiltered by positive
    # DCGM energy or by whether a job later appears in the execution join.
    # Those quantities are opened only after the submit-time decision has been
    # solved and are used for independent scoring.
    # The job-level horizon is a predeclared calendar support, not the maximum
    # completion time of the observed execution join.  It covers the complete
    # locked trace plus the declared future-deadline support while preventing
    # unrelated scheduler records many months later from inflating the exact
    # witness dimension.
    horizon_days = int(
        cfg["experiments"].get(
            "job_level_horizon_days",
            int(cfg["data"].get("scaling_fit_days", 40))
            + int(cfg["experiments"].get("test_days", 54))
            + int(np.ceil(cfg["experiments"].get("lookahead_slots", 512) / slots_per_day)),
        )
    )
    if horizon_days <= 0:
        raise ValueError("job_level_horizon_days must be positive")
    n_slots = horizon_days * slots_per_day
    jobs = load_mit_submission_ledger(
        root / cfg["data"]["mit_scheduler"],
        interval_s,
        n_slots,
        n_regions,
        declared_service_fraction=float(
            submission_calibration["declared_service_fraction"]
        ),
        declared_per_gpu_power_cap_mw=per_gpu_cap_mw,
        declared_fraction_model=submission_calibration.get("per_job_fraction_model"),
        unbounded_timelimit_slots=unbounded_timelimit_slots,
        submission_buffer_slots=submission_buffer_slots,
        time_origin_seconds=time_origin_seconds,
    )
    if len(jobs) < 50_000:
        raise RuntimeError(
            "Job-level counterfactual ledger unexpectedly incomplete after the "
            f"complete-submission load: {len(jobs)} rows"
        )
    # The admissible window is fixed by the submit-time declaration.  Fail
    # closed if the precommitted nameplate cannot serve a declared job inside
    # that declaration; observed energy is not allowed to widen the window.
    infeasible_window_jobs = int(jobs.attrs.get("declared_window_infeasible_jobs", 0))
    if infeasible_window_jobs:
        raise RuntimeError(
            "The declared job-level timelimit is infeasible under the "
            f"precommitted GPU nameplate for {infeasible_window_jobs} jobs; "
            "adjust the nameplate before the data split rather than extending "
            "a submit-time deadline from observed energy."
        )
    starts = jobs["submit_slot"].to_numpy(dtype=np.int64)
    ends = jobs["deadline_slot"].to_numpy(dtype=np.int64)
    counts = np.maximum(0, ends - starts)
    if np.any(counts <= 0):
        raise RuntimeError("Every counterfactual job must have a nonempty release/deadline window")
    n_jobs = int(len(jobs))
    n_slots = int(max(n_slots, int(ends.max())))
    offsets = np.concatenate([[0], np.cumsum(counts, dtype=np.int64)])
    slots_by_job = np.concatenate(
        [np.arange(int(start), int(end), dtype=np.int64) for start, end in zip(starts, ends)]
    )
    job_index = np.repeat(np.arange(n_jobs, dtype=np.int64), counts)
    regions_by_var = np.repeat(jobs["region"].to_numpy(dtype=np.int64), counts)
    variable_count = int(len(slots_by_job))
    energy = jobs["declared_energy_mwh"].to_numpy(dtype=float)
    declared_energy_upper = jobs["declared_energy_upper_mwh"].to_numpy(dtype=float)
    gpu_count = jobs["requested_gpus"].to_numpy(dtype=float)
    if np.any(gpu_count <= 0):
        raise RuntimeError("Counterfactual ledger contains nonpositive GPU count")

    # Reconstruct the measured contiguous execution only after the submit-time
    # start-time inputs have been frozen.  It is an independent scoring profile and
    # cannot contribute to releases, deadlines, energy equalities, GPU bounds,
    # or objective coefficients.
    execution_jobs = load_mit_job_ledger(
        root / cfg["data"]["mit_scheduler"],
        root / cfg["data"]["mit_dcgm"],
        interval_s,
        None,
        n_regions,
        deadline_mode="observed",
        time_origin_seconds=time_origin_seconds,
    )
    origin = float(jobs.attrs["time_origin_seconds"])
    native_profile = np.zeros((n_regions, n_slots), dtype=float)
    observed_job_energy = np.zeros(n_jobs, dtype=float)
    execution_match = np.zeros(n_jobs, dtype=bool)
    submission_index = {
        int(job_id): int(index)
        for index, job_id in enumerate(jobs["id_job"].to_numpy(dtype=np.int64))
    }
    for row in tqdm(
        execution_jobs.itertuples(index=False),
        total=len(execution_jobs),
        desc="Exp19 independent execution audit",
        unit="job",
    ):
        index = submission_index.get(int(row.id_job))
        if index is None:
            continue
        measured_start = float(row.time_start) - origin
        measured_end = float(row.time_end) - origin
        if measured_end <= 0.0 or measured_start >= n_slots * interval_s:
            continue
        execution_match[index] = True
        observed_job_energy[index] = float(row.energy_mwh)
        first = max(0, int(np.floor(measured_start / interval_s)))
        last = min(n_slots - 1, int(np.ceil(measured_end / interval_s)) - 1)
        duration = max(measured_end - measured_start, 1e-12)
        for slot in range(first, last + 1):
            overlap = max(
                0.0,
                min(measured_end, (slot + 1) * interval_s)
                - max(measured_start, slot * interval_s),
            )
            if overlap > 0:
                native_profile[int(jobs["region"].iloc[index]), slot] += (
                    float(row.energy_mwh) * overlap / duration
                )
    if not execution_match.any():
        raise RuntimeError("No submitted jobs could be matched to the independent execution ledger")

    event_slots = set(map(int, cfg["market"]["event_slots"]))
    event_mask = np.asarray([int(slot % int(cfg["project"]["slots_per_day"]) in event_slots) for slot in slots_by_job], dtype=float)
    waiting_cost = float(cfg["workload"]["waiting_cost_per_mwh_slot"][-1])
    event_price = float(cfg["market"]["default_dr_price_per_mwh"])
    waiting = waiting_cost * (slots_by_job - np.repeat(starts, counts))
    objective = waiting + event_price * event_mask
    # Each job may be paused, but no interval can consume more than the
    # precommitted per-GPU nameplate cap.  This cap and the declared energy
    # entitlement are independent of observed runtime and average power.
    interval_gpu_cap = np.repeat(gpu_count * per_gpu_cap_mw * dt_h, counts)
    variable_upper = interval_gpu_cap
    if np.any(variable_upper <= 0):
        raise RuntimeError("Job-level service upper bounds must be positive")

    job_rows = job_index
    site_slot_rows = regions_by_var * n_slots + slots_by_job
    site_capacity_mwh = float(cfg["project"]["flexible_capacity_mw"]) * dt_h
    # A nonpreemptive start-time witness replaces the former fractional-flow
    # shortcut.  Every job selects exactly one integer start and occupies one
    # contiguous fixed-rate block.  All admissible starts are enumerated
    # exactly; if a regional capacity row binds, the run fails closed and the
    # predeclared binding MILP in Exp25 is used instead of silently reverting to
    # a preemptive schedule.
    nonpreemptive = solve_exact_nonpreemptive_blocks(
        starts=starts,
        ends=ends,
        energy_mwh=energy,
        variable_upper_mwh=variable_upper,
        objective_per_mwh=objective,
        site_slot_rows=site_slot_rows,
        n_regions=n_regions,
        n_slots=n_slots,
        site_capacity_mwh=site_capacity_mwh,
        offsets=offsets,
    )
    if not nonpreemptive.success:
        raise RuntimeError(
            "The exact nonpreemptive start-time witness activates a regional "
            "capacity row; solve the predeclared binding start-time MILP panel "
            "before publishing this horizon."
        )
    service = nonpreemptive.service_mwh
    selected_start_slots = nonpreemptive.selected_start_slot
    selected_service_slot_counts = nonpreemptive.service_slot_count
    solver_message = nonpreemptive.solver_message
    expected_service_slot_counts = jobs["required_service_slots"].to_numpy(dtype=np.int64)
    if not np.array_equal(selected_service_slot_counts, expected_service_slot_counts):
        raise RuntimeError("Nonpreemptive block lengths disagree with declared service slots")
    counterfactual = np.bincount(
        site_slot_rows,
        weights=service,
        minlength=n_regions * n_slots,
    ).reshape(n_regions, n_slots)
    job_residual = np.bincount(job_rows, weights=service, minlength=n_jobs) - energy
    capacity_slack = site_capacity_mwh - counterfactual
    slots_per_day = int(cfg["project"]["slots_per_day"])
    event_indices = np.asarray(
        [slot for slot in range(n_slots) if slot % slots_per_day in event_slots],
        dtype=np.int64,
    )
    event_net_reduction = float(
        native_profile[:, event_indices].sum()
        - counterfactual[:, event_indices].sum()
    )
    event_gross_reduction = float(
        np.clip(
            native_profile[:, event_indices] - counterfactual[:, event_indices],
            0.0,
            None,
        ).sum()
    )
    event_rebound = float(
        np.clip(counterfactual[:, event_indices] - native_profile[:, event_indices], 0.0, None).sum()
    )
    declared_total_residual = float(abs(counterfactual.sum() - energy.sum()))
    observed_total_energy = float(observed_job_energy.sum())
    observed_upper_coverage = float(
        np.mean(
            observed_job_energy[execution_match]
            <= declared_energy_upper[execution_match] + 1e-12
        )
    ) if execution_match.any() else 0.0
    observed_central_ratio = float(
        np.median(
            observed_job_energy[execution_match]
            / np.maximum(energy[execution_match], 1e-12)
        )
    ) if execution_match.any() else float("nan")

    # A pre-registered binding-capacity panel uses the same declaration ledger and
    # same submitted ledger under a lower, explicitly stress-tested nameplate.
    # It is a second certificate, not a clipped version of the primary plan;
    # the primal is re-solved with regional capacity rows active whenever the
    # declared stress capacity requires them.
    stress_capacity_mw = float(
        cfg["experiments"].get("job_level_stress_capacity_mw", 0.0)
    )
    stress_summary_rows: list[dict[str, Any]] = []
    stress_daily_rows: list[dict[str, Any]] = []
    if stress_capacity_mw > 0.0:
        if stress_capacity_mw >= float(cfg["project"]["flexible_capacity_mw"]):
            raise ValueError("job_level_stress_capacity_mw must be below the primary capacity")
        a_eq_stress = coo_matrix(
            (np.ones(variable_count, dtype=float),
             (job_rows, np.arange(variable_count, dtype=np.int64))),
            shape=(n_jobs, variable_count),
        ).tocsr()
        a_ub_stress = coo_matrix(
            (np.ones(variable_count, dtype=float),
             (site_slot_rows, np.arange(variable_count, dtype=np.int64))),
            shape=(n_regions * n_slots, variable_count),
        ).tocsr()
        stress_scale = 1.0e6
        stress_result = linprog(
            objective / stress_scale,
            A_ub=a_ub_stress,
            b_ub=np.full(
                n_regions * n_slots,
                stress_capacity_mw * dt_h * stress_scale,
                dtype=float,
            ),
            A_eq=a_eq_stress,
            b_eq=energy * stress_scale,
            bounds=np.column_stack((
                np.zeros(variable_count, dtype=float),
                variable_upper * stress_scale,
            )),
            method="highs",
            options={"presolve": True},
        )
        if not stress_result.success:
            raise RuntimeError(
                "Binding-capacity job-level LP failed: " + str(stress_result.message)
            )
        stress_service = np.asarray(stress_result.x, dtype=float) / stress_scale
        stress_counterfactual = np.bincount(
            site_slot_rows,
            weights=stress_service,
            minlength=n_regions * n_slots,
        ).reshape(n_regions, n_slots)
        stress_residual = np.bincount(
            job_rows, weights=stress_service, minlength=n_jobs
        ) - energy
        stress_slack = stress_capacity_mw * dt_h - stress_counterfactual
        stress_event_reduction = float(
            native_profile[:, event_indices].sum()
            - stress_counterfactual[:, event_indices].sum()
        )
        stress_summary_rows = [
            {"metric": "capacity_mw_per_region", "value": stress_capacity_mw, "unit": "MW"},
            {"metric": "service_variables", "value": variable_count, "unit": "variables"},
            {"metric": "maximum_job_energy_residual_mwh", "value": float(np.max(np.abs(stress_residual))), "unit": "MWh"},
            {"metric": "minimum_site_slot_capacity_slack_mwh", "value": float(np.min(stress_slack)), "unit": "MWh"},
            {"metric": "active_capacity_slot_fraction", "value": float(np.mean(stress_slack <= 1e-10)), "unit": "fraction"},
            {"metric": "event_net_reduction_mwh", "value": stress_event_reduction, "unit": "MWh"},
            {"metric": "event_counterfactual_mwh", "value": float(stress_counterfactual[:, event_indices].sum()), "unit": "MWh"},
            {"metric": "solver_success", "value": 1, "unit": "boolean"},
        ]
        for day in range(int(np.ceil(n_slots / slots_per_day))):
            sl = slice(day * slots_per_day, min((day + 1) * slots_per_day, n_slots))
            if sl.start >= sl.stop:
                continue
            stress_daily_rows.append(
                {
                    "day": day,
                    "capacity_mw_per_region": stress_capacity_mw,
                    "maximum_slot_loading_mw": float(stress_counterfactual[:, sl].max() / dt_h),
                    "minimum_capacity_slack_mwh": float(stress_slack[:, sl].min()),
                    "event_counterfactual_mwh": float(
                        stress_counterfactual[:, sl][:, [
                            i for i in range(sl.stop - sl.start)
                            if (sl.start + i) % slots_per_day in event_slots
                        ]].sum()
                    ) if any((sl.start + i) % slots_per_day in event_slots for i in range(sl.stop - sl.start)) else 0.0,
                }
            )
        np.savez_compressed(
            final / "job_level_capacity_stress_solution.npz",
            service_mwh=stress_service,
            counterfactual_mwh=stress_counterfactual,
            declared_job_energy_mwh=energy,
            submit_slot=starts,
            deadline_slot=ends,
            region=jobs["region"].to_numpy(dtype=np.int64),
            requested_gpus=gpu_count,
        )
    else:
        stress_summary_rows = [
            {"metric": "solver_success", "value": 0, "unit": "boolean"},
            {"metric": "capacity_stress_configured", "value": 0, "unit": "boolean"},
        ]
    pd.DataFrame(stress_summary_rows).to_csv(
        final / "job_level_capacity_stress_summary.csv", index=False
    )
    pd.DataFrame(stress_daily_rows).to_csv(
        final / "job_level_capacity_stress_daily.csv", index=False
    )
    rows = pd.DataFrame(
        [
            {"metric": "submitted_jobs", "value": n_jobs, "unit": "jobs"},
            {"metric": "execution_matched_jobs", "value": int(execution_match.sum()), "unit": "jobs"},
            {"metric": "service_variables", "value": variable_count, "unit": "variables"},
            {"metric": "solver_status", "value": solver_message, "unit": "text"},
            {"metric": "event_energy_native_mwh", "value": float(native_profile[:, event_indices].sum()), "unit": "MWh"},
            {"metric": "event_energy_counterfactual_mwh", "value": float(counterfactual[:, event_indices].sum()), "unit": "MWh"},
            {"metric": "event_reduction_mwh", "value": event_gross_reduction, "unit": "MWh"},
            {"metric": "event_gross_reduction_mwh", "value": event_gross_reduction, "unit": "MWh"},
            {"metric": "event_net_reduction_mwh", "value": event_net_reduction, "unit": "MWh"},
            {"metric": "event_rebound_mwh", "value": event_rebound, "unit": "MWh"},
            {"metric": "declared_energy_conservation_residual_mwh", "value": declared_total_residual, "unit": "MWh"},
            {"metric": "observed_execution_energy_mwh", "value": observed_total_energy, "unit": "MWh"},
            {"metric": "declared_service_energy_mwh", "value": float(energy.sum()), "unit": "MWh"},
            {"metric": "execution_match_fraction", "value": float(execution_match.mean()), "unit": "fraction"},
            {"metric": "observed_within_physical_nameplate_fraction", "value": observed_upper_coverage, "unit": "fraction"},
            {"metric": "median_observed_to_declared_energy_ratio", "value": observed_central_ratio, "unit": "ratio"},
            {"metric": "maximum_job_energy_residual_mwh", "value": float(np.max(np.abs(job_residual))), "unit": "MWh"},
            {"metric": "minimum_site_slot_capacity_slack_mwh", "value": float(np.min(capacity_slack)), "unit": "MWh"},
            {"metric": "maximum_gpu_count", "value": float(np.max(gpu_count)), "unit": "GPUs"},
            {"metric": "per_gpu_power_cap_mw", "value": per_gpu_cap_mw, "unit": "MW/GPU"},
        ]
    )
    rows.to_csv(final / "job_level_counterfactual_summary.csv", index=False)
    # The full service vector is written atomically.  A previous interrupted
    # run left a syntactically valid ZIP prefix without a central directory;
    # downstream coupling now fails closed on such a file instead of silently
    # consuming a partial witness.
    solution_tmp = final / "job_level_counterfactual_solution.tmp.npz"
    np.savez_compressed(
        solution_tmp,
        service_mwh=service,
        counterfactual_mwh=counterfactual,
        native_mwh=native_profile,
        declared_job_energy_mwh=energy,
        declared_job_energy_upper_mwh=declared_energy_upper,
        observed_job_energy_mwh=observed_job_energy,
        execution_match=execution_match.astype(np.int8),
        submit_slot=starts,
        deadline_slot=ends,
        selected_start_slot=selected_start_slots,
        service_slot_count=selected_service_slot_counts,
        region=jobs["region"].to_numpy(dtype=np.int64),
        requested_gpus=gpu_count,
        per_gpu_power_cap_mw=np.asarray([per_gpu_cap_mw], dtype=float),
        source_scale_factor=np.asarray([1.0], dtype=float),
        submission_digest=np.asarray([str(jobs.attrs["canonical_submission_ledger_sha256"])]),
    )
    solution_tmp.replace(final / "job_level_counterfactual_solution.npz")
    profile_rows = []
    for region in range(n_regions):
        for slot in range(n_slots):
            profile_rows.append(
                {
                    "region": region,
                    "slot": slot,
                    "native_mwh": float(native_profile[region, slot]),
                    "counterfactual_mwh": float(counterfactual[region, slot]),
                    "difference_mwh": float(counterfactual[region, slot] - native_profile[region, slot]),
                    "capacity_slack_mwh": float(capacity_slack[region, slot]),
                }
            )
    pd.DataFrame(profile_rows).to_csv(final / "job_level_counterfactual_profile.csv", index=False)
    write_json(
        final / "experiment_metadata.json",
        {
            "experiment": "exact submit-time job-indexed temporal counterfactual",
            "submission_jobs": n_jobs,
            "submitted_jobs": n_jobs,
            "job_level_horizon_days": int(horizon_days),
            "job_level_horizon_slots": int(n_slots),
            "time_origin_seconds": time_origin_seconds,
            "execution_matched_jobs": int(execution_match.sum()),
            "service_variables": variable_count,
            "release_deadline_constraints": "one binary start choice per submitted job, one contiguous fixed-rate service block, and exact declared-energy equality",
            "deadline_source": (
                "submit-time scheduler allocation runtime plus a precommitted queue "
                "allowance; Slurm timelimit is not a submission-to-completion "
                "deadline and no measured-energy extension is permitted"
            ),
            "deadline_mode": "submit_time_declaration",
            "deadline_mode_description": (
                "Slurm allocation runtime plus the precommitted queue allowance; "
                "the allocation runtime is not a submission-to-completion deadline"
            ),
            "declared_window_slots_min": int(
                np.min(jobs["declared_window_slots"].to_numpy(dtype=np.int64))
            ),
            "declared_window_slots_max": int(
                np.max(jobs["declared_window_slots"].to_numpy(dtype=np.int64))
            ),
            "unlimited_timelimit_jobs": int(
                np.sum(
                    jobs["timelimit"].to_numpy(dtype=np.int64)
                    >= np.iinfo(np.uint32).max - 1
                )
            ),
            "observed_time_end_used_as_deadline": False,
            "observed_energy_used_in_decision": False,
            "unbounded_timelimit_slots": unbounded_timelimit_slots,
            "submission_buffer_slots": submission_buffer_slots,
            "declared_per_gpu_power_cap_mw": per_gpu_cap_mw,
            "declared_window_infeasible_jobs": infeasible_window_jobs,
            "declared_service_fraction": float(
                submission_calibration["declared_service_fraction"]
            ),
            "declared_service_fraction_source": (
                "training-only scheduler/DCGM conditional q10/q50/q90 calibration in data_manifest.json"
            ),
            "declared_fraction_source": jobs.attrs.get(
                "declared_fraction_source", "unknown"
            ),
            "declared_fraction_model_version": jobs.attrs.get(
                "declared_fraction_model_version", "unknown"
            ),
            "submission_ledger_digest": str(
                jobs.attrs["canonical_submission_ledger_sha256"]
            ),
            "execution_ledger_digest": "post-event telemetry digest stored by Exp16",
            "deadline_window_rule": (
                "exact submit-time allocation runtime plus a precommitted queue "
                "allowance; required service slots are an audit-only precheck"
            ),
            "site_assignment": "submit-time scenario region; no outcome-dependent migration",
            "gpu_constraint": "each contiguous service block uses the precommitted per-GPU nameplate cap times requested GPU count; only its terminal slot may be fractional to meet the exact entitlement",
            "counterfactual_objective": "waiting cost plus declared event DR tariff; exact finite start-time enumeration when regional rows are inactive",
            "event_slots": sorted(event_slots),
            "event_tariff_per_mwh": event_price,
            "event_reduction_definition": "net equals native event energy minus counterfactual event energy; gross positive-part reduction and rebound are reported separately",
            "capacity_mw_per_region": float(cfg["project"]["flexible_capacity_mw"]),
            "preemptive_scope": "aggregate workload equations remain an envelope, but the indexed Exp19 witness is nonpreemptive",
            "nonpreemptive_witness": "exact submitted-job contiguous start-time schedule; one start per job and no arbitrary pausing",
            "solver": (
                "exact enumeration of every admissible contiguous start for each "
                "job; a binding regional row fails closed and is certified by the "
                "separate Exp25 binary start-time MILP panel"
            ),
            "maximum_job_energy_residual_mwh": float(np.max(np.abs(job_residual))),
            "minimum_site_slot_capacity_slack_mwh": float(np.min(capacity_slack)),
            "observed_execution_energy_mwh": observed_total_energy,
            "declared_service_energy_mwh": float(energy.sum()),
            "execution_match_fraction": float(execution_match.mean()),
            "observed_within_physical_nameplate_fraction": observed_upper_coverage,
            "central_declaration_is_scoring_independent": True,
            "capacity_stress": {
                "planned": bool(
                    float(cfg["experiments"].get("job_level_stress_capacity_mw", 0.0)) > 0.0
                ),
                "capacity_mw": float(
                    cfg["experiments"].get("job_level_stress_capacity_mw", 0.0)
                ),
                "result_file": "job_level_capacity_stress_summary.csv",
                "delegated_binding_panel": "exp25_exante_job_validation",
            },
            "population_rule": (
                "all valid scheduler submissions in the predeclared job-level "
                "horizon; positive-energy execution matching is a post-event scoring join"
            ),
            "selected_start_slot_count": int(np.sum(selected_start_slots >= 0)),
            "contiguity_certificate": {
                "jobs_with_one_start": int(np.sum(selected_start_slots >= 0)),
                "jobs_with_positive_block_length": int(np.sum(selected_service_slot_counts > 0)),
                "maximum_gap_inside_service_block": 0,
            },
        },
    )
    logger.info(
        "Experiment 19 complete: %d jobs, %d variables, net event reduction %.6f MWh, max residual %.3e MWh",
        n_jobs,
        variable_count,
        event_net_reduction,
        float(np.max(np.abs(job_residual))),
    )


def run_exp15(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
    resume: bool = False,
) -> None:
    """Audit the payment interval on a calibration-validation conversion-factor segment.

    The two endpoint profiles are frozen before the locked test period.  For
    each endpoint conversion factor, the independent N-1 evaluator computes
    both endpoint values and an exact joint LP minimum over the continuous
    affine segment joining the reference and certified profiles.  Convexity of
    the secure SCED value supplies the endpoint maximum, so the reported
    payment interval covers the full declared segment without gridding or a
    heuristic interior search.
    """
    from pypower.case24_ieee_rts import case24_ieee_rts

    folder = root / "experiments/exp15_interval_certificate"
    final = folder / "results/final"
    intermediate = folder / "results/intermediate"
    final.mkdir(parents=True, exist_ok=True)
    intermediate.mkdir(parents=True, exist_ok=True)
    profile_path = root / "experiments/exp2_baseline_verification/results/intermediate/test_profiles.npz"
    certified_path = root / "experiments/exp9_payment_certificate/results/final/certified_counterfactual_profiles.npz"
    metadata_path = root / "experiments/exp9_payment_certificate/results/final/experiment_metadata.json"
    if not profile_path.exists():
        run_exp2(root, cfg, logger)
    # Experiment 15 is downstream of the q99-inclusive Experiment 9
    # certificate.  A file can exist while still belonging to an older
    # five-scenario schema, so validate the upstream contract before loading
    # any profile.  This makes a resumed run fail closed instead of mixing
    # endpoint costs from incompatible certificates.
    exp9_refresh_required = not certified_path.exists()
    try:
        exp9_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        scenario_keys = set(
            exp9_metadata.get("power_conversion_scenarios", {}).keys()
        )
        exp9_refresh_required = exp9_refresh_required or not (
            exp9_metadata.get("certificate_schema_version") == 10
            and scenario_keys == {"q01", "q10", "q50", "q90", "q99"}
            and exp9_metadata.get("network_conversion_decomposition", {}).get(
                "network_scale_calibrated_on_q99"
            )
            is True
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        exp9_refresh_required = True
    if exp9_refresh_required:
        run_exp9(root, cfg, logger, resume=True)
    stored = np.load(profile_path, allow_pickle=False)
    certified = np.load(certified_path, allow_pickle=False)
    days = stored["days"].astype(int)
    if not np.array_equal(days, certified["days"].astype(int)):
        raise RuntimeError("Interval audit profile-day mismatch")
    actual_profiles = stored["actual"].astype(float)
    oracle_profiles = stored["oracle"].astype(float)
    methods = [str(value) for value in stored["methods"]]
    single_index = int(stored["selected_single_projection_index"])
    reference_profiles = stored["projection_candidates"][:, single_index].astype(float)
    certified_profiles = certified["profiles"].astype(float)
    # The interval audit intentionally uses the contractual segment joining
    # the validation-selected reference and the payment-certified profile.
    # The larger seven-vertex hull remains the finite-scenario certificate in
    # Experiment 9; this two-endpoint segment is evaluated independently and
    # gives a compact, exactly auditable uncertainty interval.
    candidate_profiles = np.stack(
        [reference_profiles, certified_profiles], axis=0
    )
    exp9_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    dc_scale = float(exp9_metadata["dc_power_scale"])
    fixed_facility_load_mw = float(cfg["project"]["fixed_facility_load_mw"])
    manifest = json.loads((root / cfg["data"]["processed_dir"] / "data_manifest.json").read_text(encoding="utf-8"))
    conversion = manifest["power_calibration"].get(
        "calibration_validation_job_energy_measured_to_predicted_quantiles",
        manifest["power_calibration"][
            "heldout_job_energy_measured_to_predicted_quantiles"
        ],
    )
    raw_endpoint_scales = np.asarray(
        [conversion["0.01"], conversion["0.99"]], dtype=float
    )
    capacity_sensitivity_path = (
        root
        / "experiments/exp16_ledger_capacity_provenance/results/final/"
        "workload_power_calibration_sensitivity.csv"
    )
    if not capacity_sensitivity_path.exists():
        run_exp16(root, cfg, logger)
    capacity_sensitivity = pd.read_csv(capacity_sensitivity_path)
    q99_row = capacity_sensitivity[
        capacity_sensitivity["calibration_ratio_quantile"].astype(str) == "q99"
    ]
    if len(q99_row) != 1:
        raise RuntimeError(
            "Experiment 16 must provide one predeclared q99 capacity audit row"
        )
    capacity_safe_upper = float(q99_row.iloc[0]["capacity_safe_scale_factor"])
    # Keep the complete calibration-validation q99 endpoint in the interval audit.  The
    # network scale was calibrated on q99 while fixed facility demand is held
    # separate, so this endpoint is solved and can be activated without
    # clipping the declared conversion factor.  The flexible-only capacity
    # diagnostic from Experiment 16 remains a separate reconciliation.
    endpoint_labels = ["q01", "q99"]
    endpoint_scales = np.asarray(
        [raw_endpoint_scales[0], raw_endpoint_scales[1]],
        dtype=float,
    )
    q99_capacity_eligible = True
    if not (endpoint_scales[0] < 1.0 < endpoint_scales[1]):
        raise RuntimeError("Calibration-validation q01/q99 interval must bracket unity")
    # Every endpoint cache is tied to the exact frozen profiles and endpoint
    # factors.  This prevents stale costs from an earlier Experiment 9
    # certificate from entering the continuous-segment audit.
    endpoint_profile_checksum = hashlib.sha256(
        np.ascontiguousarray(candidate_profiles, dtype=np.float64).tobytes()
        + np.ascontiguousarray(endpoint_scales, dtype=np.float64).tobytes()
        + np.asarray(
            [dc_scale, fixed_facility_load_mw], dtype=np.float64
        ).tobytes()
    ).hexdigest()
    system = power_system_from_ppc(case24_ieee_rts())
    security = build_n1_security_factors(system)
    native = system.bus[:, 2] * float(cfg["experiments"].get("n1_load_multiplier", 0.9))
    dc_buses = np.asarray([2, 7, 14, 20], dtype=int)
    event_slots = list(map(int, cfg["market"]["event_slots"]))
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    segments = int(
        cfg["experiments"].get(
            "interval_certificate_generator_segments",
            cfg["experiments"].get("payment_certificate_generator_segments", 4),
        )
    )
    workers = int(cfg["experiments"].get("interval_certificate_parallel_workers", 1))
    if workers <= 0:
        raise ValueError("interval_certificate_parallel_workers must be positive")
    checkpoint = intermediate / "interval_endpoint_audit_checkpoint.csv"
    # The endpoint audit is tied to the current N-1 load calibration and the
    # Experiment 9 certificate.  Bump the schema whenever either upstream
    # contract changes so resume cannot reuse an older certificate audit.
    # Schema 12 records the fixed/flexible load map in both endpoint and
    # continuous-segment solves. Earlier checkpoints used a direct
    # ``scale * total-profile`` segment path and are therefore not eligible
    # for resume.
    schema = 12
    rows: list[dict[str, Any]] = []
    interval_rows: list[dict[str, Any]] = []
    existing_endpoint_path = final / "interval_endpoint_certificates.csv"
    known_endpoint_costs: dict[tuple[int, str, str], float] = {}
    if existing_endpoint_path.exists():
        try:
            existing = pd.read_csv(existing_endpoint_path)
            if (
                {"day", "endpoint", "method", "certified_cost_usd"}.issubset(
                    existing.columns
                )
                and "schema_version" in existing.columns
                and set(existing["schema_version"].astype(int).unique()) == {schema}
                and "endpoint_profile_checksum" in existing.columns
                and set(existing["endpoint_profile_checksum"].astype(str).unique())
                == {endpoint_profile_checksum}
            ):
                for row in existing.itertuples(index=False):
                    known_endpoint_costs[
                        (int(row.day), str(row.endpoint), str(row.method))
                    ] = float(row.certified_cost_usd)
        except (OSError, ValueError, KeyError):
            known_endpoint_costs = {}
    completed: set[int] = set()
    if resume and checkpoint.exists():
        previous = pd.read_csv(checkpoint)
        expected_per_day = len(endpoint_labels) * 2
        interval_path = intermediate / "payment_interval_hull_checkpoint.csv"
        interval_previous = (
            pd.read_csv(interval_path) if interval_path.exists() else pd.DataFrame()
        )
        counts = previous.groupby("day").size() if "day" in previous else pd.Series(dtype=int)
        interval_counts = (
            interval_previous.groupby("day").size()
            if "day" in interval_previous
            else pd.Series(dtype=int)
        )
        if (
            "schema_version" in previous
            and set(previous["schema_version"].astype(int).unique()) == {schema}
            and "method" in previous
            and set(previous["method"].astype(str).unique())
            == {
                "Selected Single Feasible Projection",
                "Payment-Certified N-1 Verifier",
            }
            and "endpoint_profile_checksum" in previous
            and set(previous["endpoint_profile_checksum"].astype(str).unique())
            == {endpoint_profile_checksum}
        ):
            completed = set(
                int(day)
                for day in counts[counts == expected_per_day].index
                if int(day) in set(interval_counts[interval_counts == len(endpoint_labels)].index)
            )
            rows = previous[previous["day"].isin(completed)].to_dict("records")
            if "day" in interval_previous:
                interval_rows = interval_previous[
                    interval_previous["day"].isin(completed)
                ].to_dict("records")

    def evaluate_day(
        item: tuple[int, int],
    ) -> tuple[int, list[dict[str, Any]], list[dict[str, Any]]]:
        local_day, day = item
        result_rows: list[dict[str, Any]] = []
        interval_rows: list[dict[str, Any]] = []
        profiles = {
            "Selected Single Feasible Projection": reference_profiles[local_day],
            "Payment-Certified N-1 Verifier": certified_profiles[local_day],
        }
        cost_cache: dict[tuple[bytes, float], float] = {}

        def network_cost(profile: np.ndarray, scale: float) -> float:
            key = (
                np.ascontiguousarray(profile, dtype=np.float64).tobytes(),
                float(scale),
            )
            if key in cost_cache:
                return cost_cache[key]
            total = 0.0
            for slot in event_slots:
                load = _network_load_from_facility_profile(
                    native,
                    dc_buses,
                    profile[:, slot],
                    dc_scale=dc_scale,
                    conversion_scale=float(scale),
                    fixed_facility_load_mw=fixed_facility_load_mw,
                )
                solved = solve_n1_sced(
                    system,
                    load,
                    segments,
                    security_factors=security,
                )
                if not solved.success:
                    raise RuntimeError(
                        f"Interval value solve failed on day {day}, slot {slot}"
                    )
                total += solved.objective * dt_h
            cost_cache[key] = float(total)
            return float(total)

        for endpoint, scale in zip(endpoint_labels, endpoint_scales):
            costs: dict[str, float] = {}
            for method, profile in profiles.items():
                known = known_endpoint_costs.get((int(day), endpoint, method))
                costs[method] = (
                    float(known)
                    if known is not None
                    else network_cost(profile, float(scale))
                )
            reference_cost = costs["Selected Single Feasible Projection"]
            for method, cost in costs.items():
                result_rows.append(
                    {
                        "day": int(day),
                        "endpoint": endpoint,
                        "conversion_scale_factor": float(scale),
                        "unclipped_conversion_scale_factor": float(
                            raw_endpoint_scales[endpoint_labels.index(endpoint)]
                        ),
                        "solver_status": "optimal",
                        "capacity_activation_eligible": True,
                        "method": method,
                        "certified_cost_usd": float(cost),
                        "reference_cost_usd": float(reference_cost),
                        "margin_usd": float(reference_cost - cost),
                        "payment_cap_violation_usd": float(max(0.0, cost - reference_cost)),
                        "independent_segments": segments,
                        "schema_version": schema,
                        "endpoint_profile_checksum": endpoint_profile_checksum,
                    }
                )
            hull_costs = np.asarray(
                [
                    (
                        float(
                            known_endpoint_costs[
                                (
                                    int(day),
                                    endpoint,
                                    (
                                        "Selected Single Feasible Projection"
                                        if index == 0
                                        else "Payment-Certified N-1 Verifier"
                                    ),
                                )
                            ]
                        )
                        if (
                            int(day),
                            endpoint,
                            (
                                "Selected Single Feasible Projection"
                                if index == 0
                                else "Payment-Certified N-1 Verifier"
                            ),
                        )
                        in known_endpoint_costs
                        else network_cost(
                            candidate_profiles[index, local_day], float(scale)
                        )
                    )
                    for index in range(candidate_profiles.shape[0])
                ],
                dtype=float,
            )
            # The interval is a payment interval, so its common subtraction
            # must be the independently replayed realized counterfactual cost,
            # not one of the candidate baseline costs.  This load is observed
            # only for scoring and is never used to select either endpoint.
            counterfactual_cost = network_cost(
                actual_profiles[local_day], float(scale)
            )
            # Independent locked coverage audit. This value is computed only
            # after the contract hull and endpoint profiles are frozen; it is
            # never used to choose an endpoint or a certificate profile.
            oracle_cost = network_cost(oracle_profiles[local_day], float(scale))
            segment_load_profiles = np.empty(
                (2, len(event_slots), len(native)), dtype=float
            )
            for profile_index in range(2):
                for local_slot, slot in enumerate(event_slots):
                    # Use the same fixed/flexible decomposition as the
                    # endpoint certificates.  The segment LP is a coverage
                    # certificate over the physical load path; constructing
                    # it from ``scale * total_profile`` would rescale the
                    # invariant fixed facility demand and invalidate the
                    # endpoint comparison.
                    load = _network_load_from_facility_profile(
                        native,
                        dc_buses,
                        candidate_profiles[profile_index, local_day, :, slot],
                        dc_scale=dc_scale,
                        conversion_scale=float(scale),
                        fixed_facility_load_mw=fixed_facility_load_mw,
                    )
                    segment_load_profiles[profile_index, local_slot] = load
            segment_minimum = solve_n1_sced_segment_minimum(
                system,
                segment_load_profiles,
                segments=segments,
                security_factors=security,
                dt_h=dt_h,
            )
            interval = payment_value_interval(
                hull_costs,
                counterfactual_cost,
                reference_cost,
                oracle_baseline_cost_usd=oracle_cost,
                segment_minimum_baseline_cost_usd=segment_minimum,
            )
            interval_rows.append(
                {
                    "day": int(day),
                    "endpoint": endpoint,
                    "conversion_scale_factor": float(scale),
                    "unclipped_conversion_scale_factor": float(
                        raw_endpoint_scales[endpoint_labels.index(endpoint)]
                    ),
                    "solver_status": "optimal",
                    "capacity_activation_eligible": True,
                    "hull_baseline_cost_min_usd": float(hull_costs.min()),
                    "hull_baseline_cost_max_usd": float(hull_costs.max()),
                    "continuous_segment_minimum_baseline_cost_usd": float(
                        segment_minimum
                    ),
                    "counterfactual_cost_usd": float(
                        counterfactual_cost
                    ),
                    "payment_interval_lower_usd": interval.lower_usd,
                    "payment_interval_upper_usd": interval.upper_usd,
                    "payment_interval_width_usd": interval.width_usd,
                    "selected_reference_payment_usd": interval.selected_payment_usd,
                    "oracle_payment_usd": interval.oracle_payment_usd,
                    "oracle_inside_interval": float(interval.oracle_inside),
                    "candidate_hull_vertices": int(hull_costs.size),
                    "candidate_hull_definition": (
                        "continuous affine segment between selected reference and payment-certified profile; exact joint LP minimum and convex endpoint maximum"
                    ),
                    "schema_version": schema,
                    "endpoint_profile_checksum": endpoint_profile_checksum,
                }
            )
        return int(day), result_rows, interval_rows

    pending = [(index, int(day)) for index, day in enumerate(days) if int(day) not in completed]
    progress = tqdm(total=len(days), initial=len(completed), desc="Exp15 continuous-segment payment audit")
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for day, result_rows, day_interval_rows in executor.map(evaluate_day, pending):
            rows.extend(result_rows)
            interval_rows.extend(day_interval_rows)
            completed.add(day)
            pd.DataFrame(rows).to_csv(checkpoint, index=False)
            pd.DataFrame(interval_rows).to_csv(
                intermediate / "payment_interval_hull_checkpoint.csv",
                index=False,
            )
            progress.update(1)
    progress.close()
    endpoints = pd.DataFrame(rows).sort_values(["day", "endpoint", "method"])
    endpoints.to_csv(final / "interval_endpoint_certificates.csv", index=False)
    summary = (
        endpoints.groupby(["endpoint", "method"], as_index=False)
        .agg(
            conversion_scale_factor=("conversion_scale_factor", "first"),
            mean_margin_usd=("margin_usd", "mean"),
            minimum_margin_usd=("margin_usd", "min"),
            maximum_payment_cap_violation_usd=("payment_cap_violation_usd", "max"),
            locked_day_count=("day", "nunique"),
        )
    )
    summary.to_csv(final / "interval_certificate_summary.csv", index=False)
    intervals = pd.DataFrame(interval_rows).sort_values(["day", "endpoint"])
    intervals.to_csv(final / "payment_value_interval_certificates.csv", index=False)
    interval_summary = (
        intervals.groupby("endpoint", as_index=False)
        .agg(
            conversion_scale_factor=("conversion_scale_factor", "first"),
            mean_interval_width_usd=("payment_interval_width_usd", "mean"),
            maximum_interval_width_usd=("payment_interval_width_usd", "max"),
            oracle_coverage=("oracle_inside_interval", "mean"),
            locked_day_count=("day", "nunique"),
        )
    )
    interval_summary.to_csv(
        final / "payment_value_interval_summary.csv", index=False
    )
    payment_rows = endpoints[endpoints["method"] == "Payment-Certified N-1 Verifier"]
    np.savez_compressed(
        final / "interval_certified_counterfactual_profiles.npz",
        days=days,
        profiles=certified_profiles,
        endpoint_scales=endpoint_scales,
        dc_scale=np.asarray(dc_scale),
    )
    max_violation = float(payment_rows["payment_cap_violation_usd"].max())
    write_json(
        final / "experiment_metadata.json",
        {
            "audit_type": "independent continuous-segment audit of the locked payment-certified profile",
            "interval": {
                "lower_endpoint": float(endpoint_scales[0]),
                "upper_endpoint": float(endpoint_scales[1]),
                "unclipped_upper_endpoint": float(raw_endpoint_scales[1]),
                "source": "complete calibration-validation per-job measured-to-predicted energy-ratio q01 and q99 endpoints",
                "upper_endpoint_policy": (
                    "retain raw q99 and apply it only to the flexible workload "
                    "component; fixed facility demand is carried separately and "
                    "the benchmark scale is calibrated on the q99 envelope"
                ),
                "q99_capacity_safe_upper": capacity_safe_upper,
                "q99_capacity_activation_eligible": q99_capacity_eligible,
                "fixed_load_separated": True,
            },
            "continuous_segment_theorem": (
                "For the affine segment joining the two frozen workload profiles, the joint N-1 SCED LP computes the exact minimum over the shared segment parameter. The optimal linear N-1 SCED value is convex in the conversion factor, so the maximum over the closed interval is attained at an endpoint. The interval therefore uses the joint-LP minimum and convex endpoint maximum, without a grid or endpoint-only lower bound."
            ),
            "profile_source": "Experiment 9 global payment certificate; selected single feasible projection is the contractual reference; no endpoint-specific refit or post-hoc profile selection",
            "external_transfer_comparator": "Feasible Quantile Projection",
            "certificate_generator_segments": segments,
            "locked_days": int(len(days)),
            "event_slots": event_slots,
            "parallel_workers": workers,
            "interval_certificate_valid": bool(max_violation <= 1e-6),
            "certificate_scope": "continuous-segment interval from raw q01 to raw q99 with fixed/flexible load separation, exact joint-LP lower bound, and convex endpoint upper bound; both endpoints are activation-eligible under the q99-calibrated benchmark scale",
            "maximum_payment_cap_violation_usd": max_violation,
            "payment_value_interval": {
                "endpoint_file": "payment_value_interval_certificates.csv",
                "candidate_hull": "continuous affine segment between validation-frozen reference and payment-certified profiles",
                "unclipped_upper_endpoint": float(raw_endpoint_scales[1]),
                "capacity_safe_upper_endpoint": capacity_safe_upper,
                "raw_upper_endpoint": float(raw_endpoint_scales[1]),
                "q99_capacity_activation_eligible": q99_capacity_eligible,
                "counterfactual_source": "trace-observed event load, used only for independent settlement scoring",
                "oracle_used_only_for_coverage_audit": True,
                "mean_oracle_coverage": float(interval_summary["oracle_coverage"].mean()),
                "intervals_are_contractual": True,
                "capacity_eligible_endpoints_only": True,
                "raw_q99_is_stress_only": False,
                "fixed_load_separated": True,
            },
        },
    )
    plot_exp15_interval_certificate(
        endpoints,
        folder / "figures",
        cfg,
        intervals=intervals,
    )
    logger.info(
        "Experiment 15 complete: %d endpoint rows over %d locked days; max payment-cap violation %.3e USD",
        len(endpoints),
        len(days),
        max_violation,
    )


def run_exp16(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
) -> None:
    """Audit the immutable real ledger and reconcile its measured capacity.

    This experiment adds a provenance certificate to the workload feasibility
    claim.  It uses the complete public scheduler/DCGM releases directly,
    computes a canonical digest of the exact joined rows, checks raw-to-join
    energy conservation, and reports the observed per-region execution
    envelope against the declared study capacity.  No synthetic jobs,
    imputed deadlines, or outcome-based row filtering are introduced.
    """
    folder = root / "experiments/exp16_ledger_capacity_provenance"
    final = folder / "results/final"
    intermediate = folder / "results/intermediate"
    final.mkdir(parents=True, exist_ok=True)
    intermediate.mkdir(parents=True, exist_ok=True)
    processed = load_workload(root / cfg["data"]["processed_dir"] / "workload_15min.npz")
    scheduler_path = root / cfg["data"]["mit_scheduler"]
    dcgm_path = root / cfg["data"]["mit_dcgm"]
    commitment_path = root / cfg["project"].get(
        "capacity_commitment_file", "configs/capacity_commitment.json"
    )
    commitment = json.loads(commitment_path.read_text(encoding="utf-8"))
    configured_capacity = float(cfg["project"]["flexible_capacity_mw"])
    if float(commitment["flexible_capacity_mw"]) != configured_capacity:
        raise RuntimeError("Capacity commitment and configured capacity disagree")
    if commitment.get("locked_test_observations_used_for_selection") is not False:
        raise RuntimeError("Capacity commitment does not exclude locked-test observations")
    summary, capacity = audit_mit_ledger_provenance(
        scheduler_path=scheduler_path,
        dcgm_path=dcgm_path,
        processed_workload=processed,
        interval_minutes=float(cfg["project"]["interval_minutes"]),
        configured_capacity_mw=float(cfg["project"]["flexible_capacity_mw"]),
        n_regions=int(cfg["project"]["number_of_regions"]),
    )
    # Certificates must be portable across machines. Do not persist the
    # absolute scratch-workspace path used by the current run.
    summary["source_files"] = {
        "scheduler": str(scheduler_path.relative_to(root)),
        "dcgm": str(dcgm_path.relative_to(root)),
    }
    if not summary["integrity_conditions"]["raw_to_join_energy_conservation"]:
        raise RuntimeError("Raw DCGM energy is not conserved by the joined ledger")
    if not summary["integrity_conditions"]["release_before_execution"]:
        raise RuntimeError("Joined ledger contains an invalid release/execution order")
    flat_rows = []
    for key, value in summary.items():
        if isinstance(value, (dict, list)):
            continue
        flat_rows.append({"metric": key, "value": value})
    for key, value in summary["integrity_conditions"].items():
        flat_rows.append({"metric": f"integrity_{key}", "value": value})
    pd.DataFrame(flat_rows).to_csv(final / "ledger_provenance_summary.csv", index=False)
    capacity.to_csv(final / "capacity_reconciliation.csv", index=False)
    processed = load_workload(root / cfg["data"]["processed_dir"] / "workload_15min.npz")
    manifest = json.loads(
        (root / cfg["data"]["processed_dir"] / "data_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    conversion = manifest["power_calibration"].get(
        "calibration_validation_job_energy_measured_to_predicted_quantiles",
        manifest["power_calibration"][
            "heldout_job_energy_measured_to_predicted_quantiles"
        ],
    )
    # The calibration-validation measured-to-predicted ratios describe MIT GPU batch energy,
    # not the fixed facility load or the independent BurstGPT inference trace.
    # Reconcile the conversion against the same flexible batch envelope used by
    # the provenance certificate; otherwise fixed/inference demand would be
    # double-counted as a workload-to-power calibration error.
    scaled_benchmark_batch_power = (
        np.asarray(processed["observed_energy_mwh"][:, :, 2], dtype=float)
        / float(cfg["project"]["interval_minutes"] / 60.0)
    )
    batch_scale = float(np.asarray(processed["batch_scale"]).reshape(-1)[0])
    raw_execution_batch_power = scaled_benchmark_batch_power / max(batch_scale, 1e-12)
    raw_execution_peak_by_region = np.max(raw_execution_batch_power, axis=0)
    scaled_benchmark_peak_by_region = np.max(scaled_benchmark_batch_power, axis=0)
    calibration_rows = []
    calibration_quantiles = (
        ("q01", "0.01"),
        ("q10", "0.1"),
        ("q50", "0.5"),
        ("q90", "0.9"),
        ("q99", "0.99"),
    )
    for label, conversion_key in calibration_quantiles:
        factor = float(conversion[conversion_key])
        scaled_peak = scaled_benchmark_peak_by_region * factor
        raw_peak = raw_execution_peak_by_region * factor
        capacity_safe_factor = min(
            factor,
            configured_capacity / max(float(scaled_benchmark_peak_by_region.max()), 1e-12),
        )
        capacity_safe_peak = scaled_benchmark_peak_by_region * capacity_safe_factor
        calibration_rows.append(
            {
                "calibration_ratio_quantile": label,
                "calibration_split": "calibration-validation",
                "measured_to_predicted_energy_ratio": factor,
                "maximum_raw_execution_peak_mw": float(raw_peak.max()),
                "maximum_scaled_benchmark_region_peak_mw": float(scaled_peak.max()),
                "capacity_safe_scale_factor": float(capacity_safe_factor),
                "capacity_safe_region_peak_mw": float(capacity_safe_peak.max()),
                "capacity_clip_applied": float(capacity_safe_factor < factor - 1e-12),
                "minimum_regional_headroom_to_118mw": float(
                    configured_capacity - scaled_peak.max()
                ),
                "regions_over_nameplate": int(
                    np.sum(scaled_peak > configured_capacity + 1e-9)
                ),
                "calibration_source": "calibration-validation MIT job energy ratios; no locked-test fitting",
                "batch_scale_to_benchmark_envelope": batch_scale,
                "scaled_benchmark_is_not_raw_utility_measurement": True,
                "spatial_mapping": "four declared DC buses with fixed region order",
            }
        )
    pd.DataFrame(calibration_rows).to_csv(
        final / "workload_power_calibration_sensitivity.csv", index=False
    )
    calibration_summary = manifest["power_calibration"]
    submission_calibration = manifest.get("submission_calibration", {})
    if not submission_calibration:
        raise RuntimeError(
            "The data manifest lacks the training-only submission energy calibration"
        )
    pd.DataFrame(
        [
            {
                "training_jobs": int(submission_calibration["training_jobs"]),
                "test_jobs": int(submission_calibration["test_jobs"]),
                "declared_service_fraction": float(
                    submission_calibration["declared_service_fraction"]
                ),
                "physical_upper_service_fraction": float(
                    submission_calibration["physical_upper_service_fraction"]
                ),
                "q01": float(submission_calibration["fraction_quantiles"]["0.01"]),
                "q10": float(submission_calibration["fraction_quantiles"]["0.1"]),
                "q50": float(submission_calibration["fraction_quantiles"]["0.5"]),
                "q90": float(submission_calibration["fraction_quantiles"]["0.9"]),
                "q99": float(submission_calibration["fraction_quantiles"]["0.99"]),
                "conditional_model_type": submission_calibration.get(
                    "per_job_fraction_model", {}
                ).get("model_type", "scalar")
                if submission_calibration.get("per_job_fraction_model")
                else "scalar",
                "validation_model_diagnostics": json.dumps(
                    submission_calibration.get("per_job_fraction_model", {}).get(
                        "validation_diagnostics", {}
                    ),
                    sort_keys=True,
                ),
                "locked_model_diagnostics": json.dumps(
                    submission_calibration.get("per_job_fraction_model", {}).get(
                        "locked_diagnostics", {}
                    ),
                    sort_keys=True,
                ),
                "telemetry_role": submission_calibration["telemetry_role"],
            }
        ]
    ).to_csv(final / "submission_calibration_summary.csv", index=False)
    pd.DataFrame(
        [
            {
                "calibration_scope": "three-way MIT DCGM job-power model",
                "train_observations": int(calibration_summary["train_observations"]),
                "calibration_validation_observations": int(
                    calibration_summary["validation_observations"]
                ),
                "locked_observations": int(calibration_summary["locked_observations"]),
                "test_observations": int(calibration_summary["test_observations"]),
                "test_mae_watts": float(calibration_summary["test_mae_watts"]),
                "test_rmse_watts": float(calibration_summary["test_rmse_watts"]),
                "test_r2": float(calibration_summary["test_r2"]),
                "calibration_validation_mae_watts": float(
                    calibration_summary["validation_metrics"]["mae_watts"]
                ),
                "calibration_validation_rmse_watts": float(
                    calibration_summary["validation_metrics"]["rmse_watts"]
                ),
                "calibration_validation_r2": float(
                    calibration_summary["validation_metrics"]["r2"]
                ),
                "locked_mae_watts": float(
                    calibration_summary["locked_metrics"]["mae_watts"]
                ),
                "locked_rmse_watts": float(
                    calibration_summary["locked_metrics"]["rmse_watts"]
                ),
                "locked_r2": float(calibration_summary["locked_metrics"]["r2"]),
                "calibration_validation_aggregate_energy_ratio": float(
                    calibration_summary[
                        "calibration_validation_aggregate_measured_to_predicted_energy_ratio"
                    ]
                ),
                "locked_aggregate_energy_ratio": float(
                    calibration_summary[
                        "locked_aggregate_measured_to_predicted_energy_ratio"
                    ]
                ),
                "raw_execution_peak_mw": float(raw_execution_peak_by_region.max()),
                "scaled_benchmark_peak_mw": float(scaled_benchmark_peak_by_region.max()),
                "configured_nameplate_mw": configured_capacity,
                "raw_measurement_is_not_scaled_utility_power": True,
                "spatial_mapping_is_declared_scenario": True,
            }
        ]
    ).to_csv(final / "physical_calibration_summary.csv", index=False)
    write_json(final / "ledger_provenance_certificate.json", summary)
    write_json(
        final / "source_hashes.json",
        {
            "scheduler": {
                "path": str(scheduler_path.relative_to(root)),
                "sha256": sha256(scheduler_path),
                "bytes": int(scheduler_path.stat().st_size),
            },
            "dcgm": {
                "path": str(dcgm_path.relative_to(root)),
                "sha256": sha256(dcgm_path),
                "bytes": int(dcgm_path.stat().st_size),
            },
            "processed_workload": {
                "path": str((root / cfg["data"]["processed_dir"] / "workload_15min.npz").relative_to(root)),
                "sha256": sha256(root / cfg["data"]["processed_dir"] / "workload_15min.npz"),
            },
        },
    )
    metadata = {
        "experiment": "immutable ledger provenance and real execution capacity reconciliation",
        "evidence_tier": "same-source MIT scheduler/DCGM observational evidence",
        "source_rows_are_unchanged": True,
        "synthetic_rows": 0,
        "imputed_deadlines": 0,
        "canonical_joined_ledger_sha256": summary["canonical_joined_ledger_sha256"],
        "canonical_submission_ledger_sha256": summary[
            "canonical_submission_ledger_sha256"
        ],
        "submission_ledger_row_count": int(summary["submission_row_count"]),
        "submission_digest_excludes_execution_telemetry": True,
        "integrity_passed": bool(all(summary["integrity_conditions"].values())),
        "capacity_commitment": {
            "path": str(commitment_path.relative_to(root)),
            "source": str(cfg["project"].get("flexible_capacity_source", "")),
            "configured_capacity_mw": configured_capacity,
            "locked_test_observations_used_for_selection": False,
            "measured_envelope_is_reconciliation_only": True,
        },
        "capacity_interpretation": (
            "The 118-MW nameplate is committed before validation/test selection. "
            "The raw MIT execution peak is reported separately from the scaled "
            "benchmark envelope used for the declared study scale; neither is "
            "used to tune a locked-day schedule."
        ),
        "configured_capacity_mw": float(cfg["project"]["flexible_capacity_mw"]),
        "maximum_raw_execution_peak_mw": summary["capacity_measurement"][
            "maximum_raw_execution_peak_mw"
        ],
        "maximum_scaled_benchmark_peak_mw": summary["capacity_measurement"][
            "maximum_scaled_benchmark_peak_mw"
        ],
        "maximum_scaled_benchmark_peak_to_configured_capacity_ratio": summary[
            "capacity_measurement"
        ]["maximum_scaled_benchmark_peak_to_configured_capacity_ratio"],
        "physical_calibration_summary": {
            "file": "physical_calibration_summary.csv",
            "train_observations": int(calibration_summary["train_observations"]),
            "calibration_validation_observations": int(
                calibration_summary["validation_observations"]
            ),
            "locked_observations": int(calibration_summary["locked_observations"]),
            "calibration_validation_mae_watts": float(
                calibration_summary["validation_metrics"]["mae_watts"]
            ),
            "calibration_validation_rmse_watts": float(
                calibration_summary["validation_metrics"]["rmse_watts"]
            ),
            "calibration_validation_r2": float(
                calibration_summary["validation_metrics"]["r2"]
            ),
            "locked_mae_watts": float(
                calibration_summary["locked_metrics"]["mae_watts"]
            ),
            "locked_rmse_watts": float(
                calibration_summary["locked_metrics"]["rmse_watts"]
            ),
            "locked_r2": float(calibration_summary["locked_metrics"]["r2"]),
            "test_mae_watts": float(calibration_summary["test_mae_watts"]),
            "test_rmse_watts": float(calibration_summary["test_rmse_watts"]),
            "test_r2": float(calibration_summary["test_r2"]),
            "aggregate_measured_to_predicted_energy_ratio": float(
                calibration_summary[
                    "calibration_validation_aggregate_measured_to_predicted_energy_ratio"
                ]
            ),
            "locked_aggregate_measured_to_predicted_energy_ratio": float(
                calibration_summary[
                    "locked_aggregate_measured_to_predicted_energy_ratio"
                ]
            ),
            "interpretation": (
                "The job-level model calibrates GPU energy only. Conversion "
                "scenarios use the calibration-validation partition; the locked "
                "partition is reported solely as a generalization audit. The "
                "network profile remains a declared four-region scenario and is "
                "not a co-located utility measurement."
            ),
        },
        "power_calibration_sensitivity": {
            "file": "workload_power_calibration_sensitivity.csv",
            "ratios": ["0.01", "0.1", "0.5", "0.9", "0.99"],
            "calibration_split": "calibration-validation",
            "locked_test_observations_used_for_scaling": False,
            "capacity_sensitivity_scope": (
                "flexible workload batch only; this diagnostic does not gate "
                "network activation"
            ),
            "capacity_clip_is_batch_only_diagnostic": True,
            "network_activation_scale_source": (
                "Experiment 9 q99-calibrated fixed/flexible conversion with "
                "the fixed facility component carried separately"
            ),
            "interpretation": (
                "The power conversion is a declared calibration-validation uncertainty interval. "
                "The q99 capacity-safe factor is a flexible-batch diagnostic; "
                "network activation uses the separate fixed/flexible conversion "
                "certificate in Experiment 9. These results are not treated as "
                "geography-free evidence."
            ),
        },
        "submission_energy_calibration": {
            "file": "submission_calibration_summary.csv",
            "training_rule": submission_calibration["training_rule"],
            "declared_service_fraction": float(
                submission_calibration["declared_service_fraction"]
            ),
            "declared_fraction_model_type": submission_calibration.get(
                "per_job_fraction_model", {}
            ).get("model_type", "scalar"),
            "conditional_q10_q50_q90_at_submit_time": bool(
                submission_calibration.get("per_job_fraction_model")
            ),
            "physical_upper_service_fraction": float(
                submission_calibration["physical_upper_service_fraction"]
            ),
            "telemetry_used_in_exp19_decision": False,
        },
    }
    write_json(final / "experiment_metadata.json", metadata)
    plot_exp16_ledger_capacity(summary, capacity, folder / "figures", cfg)
    logger.info(
        "Experiment 16 complete: %d joined jobs, digest=%s, committed capacity=%.3f MW",
        summary["joined_positive_energy_jobs"],
        summary["canonical_joined_ledger_sha256"][:12],
        configured_capacity,
    )


def run_exp17(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
    resume: bool = False,
) -> None:
    """Evaluate the verifier with only event-gate information available.

    The main counterfactual panel is an ex-post ledger audit.  This separate
    panel freezes the information boundary at a pre-event commitment
    checkpoint, removes every post-gate arrival from the optimization input,
    and retains the deadline-indexed cumulative state for work already
    committed at the gate.
    A
    gate-causal no-event profile is frozen as the contract baseline; a second
    committed-ledger response LP uses the declared DR price to move eligible
    service away from the event window.  Both LPs use the same masked ledger,
    so the response is not created by future arrivals or a post-processing
    clip.  The response rows are an explicitly simulated operating replay;
    the independent locked execution tensor is reported in a separate
    observational trace panel and is never silently treated as an event label.
    """
    from .visualization import plot_exp17_decision_time

    folder = root / "experiments/exp17_decision_time_information"
    final = folder / "results/final"
    intermediate = folder / "results/intermediate"
    final.mkdir(parents=True, exist_ok=True)
    intermediate.mkdir(parents=True, exist_ok=True)
    profile_path = (
        root
        / "experiments/exp2_baseline_verification/results/intermediate/test_profiles.npz"
    )
    validation_path = (
        root
        / "experiments/exp2_baseline_verification/results/intermediate/validation_profiles.npz"
    )
    if not profile_path.exists() or not validation_path.exists():
        run_exp2(root, cfg, logger, resume=True)
    stored = np.load(profile_path, allow_pickle=False)
    validation = np.load(validation_path, allow_pickle=False)
    days = stored["days"].astype(int)
    methods = [str(value) for value in stored["methods"]]
    risk_index = methods.index("Risk-Constrained Convex Verifier")
    complete_profiles = stored["baselines"][:, risk_index]
    actual = stored["actual"]
    oracle = stored["oracle"]
    arrivals_days, observed, valid_days, _, _, prices, _ = _inputs(root, cfg, logger)
    # Reconstruct the exact locked strategic reference used by Exp2.  The
    # event-gate target is then refit below with the current day's post-gate
    # arrivals masked before feature construction; the complete-day cache is
    # intentionally not used as a decision-time target.
    model_honest, model_strategic, _, _ = precompute_reference_schedules(
        root, cfg, arrivals_days, valid_days, prices, logger
    )
    strategic = observed + (model_strategic - model_honest)
    observed_meter = observed[days].copy()
    observed_trace_rows: list[dict[str, Any]] = []
    event_slots = list(map(int, cfg["market"]["event_slots"]))
    gate = int(cfg["experiments"].get("decision_time_event_gate_slot", min(event_slots)))
    if gate < 0 or gate >= min(event_slots):
        raise ValueError(
            "decision_time_event_gate_slot must be nonnegative and strictly before the first event slot"
        )
    terminal = int(
        cfg["experiments"].get("decision_time_terminal_completion_index", gate - 1)
    )
    projection_weight = float(
        cfg["experiments"].get("decision_time_projection_weight", 1.0)
    )
    response_dr_prices = np.asarray(
        cfg["experiments"].get(
            "decision_time_response_dr_prices",
            [150.0, 300.0, 450.0, 600.0],
        ),
        dtype=float,
    )
    response_projection_weights = np.asarray(
        cfg["experiments"].get(
            "decision_time_response_projection_weights",
            [0.0, 0.25, 0.5, 1.0],
        ),
        dtype=float,
    )
    response_false_budget = float(
        cfg["experiments"].get(
            "decision_time_response_validation_false_budget_mwh", 0.25
        )
    )
    committed_event_service_mwh = float(
        cfg["experiments"].get(
            "decision_time_committed_event_service_mwh", 0.0
        )
    )
    if (
        response_dr_prices.size == 0
        or np.any(response_dr_prices < 0.0)
        or response_projection_weights.size == 0
        or np.any(response_projection_weights < 0.0)
        or response_false_budget < 0.0
        or committed_event_service_mwh < 0.0
    ):
        raise ValueError("Invalid causal response candidate grid")
    # Exp17 is a deployment-time rolling checkpoint, not the full-horizon
    # settlement replay.  Keep only the 96 event-day slots in each gate LP;
    # unexpired batch state is carried to the next checkpoint through the
    # terminal cumulative state.  This avoids expanding four gate LPs per day
    # over 512 zero-arrival look-ahead slots while preserving the same release,
    # deadline, and capacity constraints on the committed information set.
    gate_cfg = copy.deepcopy(cfg)
    gate_cfg["experiments"]["lookahead_slots"] = 0
    # The committed ledger, causal target, and no-DR reference are identical
    # for every point in the response price/regularization grid.  Cache them
    # once per validation day; only the response LP itself is re-solved for a
    # changed economic parameter.
    response_day_cache: dict[int, tuple[np.ndarray, float, np.ndarray, Any]] = {}

    def solve_committed_response(
        day: int,
        dr_price: float,
        response_projection_weight: float,
    ) -> tuple[Any, Any, Any, Any, float]:
        """Solve causal baseline and response LPs on a masked ledger.

        The baseline LP is solved with the causal target and no event tariff;
        it is the profile submitted before the event.  The second LP applies
        the declared DR tariff to the same committed ledger and is retained as
        a post-event operating trace.  Separating the two avoids scoring a
        post-response trajectory as if it were a baseline certificate.
        """
        day = int(day)
        cached = response_day_cache.get(day)
        if cached is None:
            truncated = arrivals_days[day].copy()
            future_arrivals_mwh = float(truncated[gate:].sum())
            truncated[gate:] = 0.0
            gate_arrivals = arrivals_days[day].copy()
            gate_arrivals[gate:] = 0.0
            target = predict_causal_metadata_gradient_boosting(
                strategic,
                valid_days,
                day,
                int(cfg["project"]["seed"]),
                arrivals_days,
                arrivals_day_override=gate_arrivals,
            )
            committed_reference_result = _solve_day_with_buffer(
                truncated,
                prices,
                gate_cfg,
                mode="honest",
                target=None,
                projection_weight=0.0,
                require_all_arrivals_at_terminal=False,
                terminal_completion_index=terminal,
                event_slots_override=event_slots,
            )
            if not committed_reference_result.success:
                raise RuntimeError(
                    f"Committed-ledger reference LP failed on day {day}: "
                    f"{committed_reference_result.solver_message}"
                )
            response_day_cache[day] = (
                truncated,
                future_arrivals_mwh,
                target,
                committed_reference_result,
            )
        truncated, future_arrivals_mwh, target, committed_reference_result = response_day_cache[day]
        fixed_load = float(cfg["project"]["fixed_facility_load_mw"])
        flexible_capacity = float(cfg["project"]["flexible_capacity_mw"])
        committed_event_upper = np.full(
            (prices.shape[0], truncated.shape[0]),
            fixed_load + flexible_capacity,
            dtype=float,
        )
        committed_baseline_result = _solve_day_with_buffer(
            truncated,
            prices,
            gate_cfg,
            mode="honest",
            target=target,
            # The submitted contract is independent of the post-event
            # tariff/response candidate.  Keeping the gate-causal baseline
            # penalty fixed prevents the response calibration grid from
            # silently changing the contract being scored.
            projection_weight=projection_weight,
            power_upper_mw=committed_event_upper,
            minimum_participant_event_mwh=committed_event_service_mwh,
            require_all_arrivals_at_terminal=False,
            terminal_completion_index=terminal,
            event_slots_override=event_slots,
        )
        if not committed_baseline_result.success:
            raise RuntimeError(
                f"Committed-ledger baseline LP failed on day {day}: "
                f"{committed_baseline_result.solver_message}"
            )
        # The response trajectory is allowed to reduce the committed service
        # at event slots, but it cannot create a larger submitted baseline.
        # This is a linear contractual upper bound, not a post-solve clip.
        response_upper = committed_event_upper.copy()
        response_upper[:, event_slots] = np.minimum(
            response_upper[:, event_slots],
            committed_baseline_result.power_mw[:, event_slots],
        )
        committed_result = _solve_day_with_buffer(
            truncated,
            prices,
            gate_cfg,
            mode="event_response",
            dr_price=float(dr_price),
            target=target,
            projection_weight=float(response_projection_weight),
            power_upper_mw=response_upper,
            require_all_arrivals_at_terminal=False,
            terminal_completion_index=terminal,
            event_slots_override=event_slots,
        )
        if not committed_result.success:
            raise RuntimeError(
                f"Committed-ledger response LP failed on day {day}: "
                f"{committed_result.solver_message}"
            )
        return (
            committed_result,
            committed_baseline_result,
            committed_reference_result,
            target,
            future_arrivals_mwh,
        )

    # A causal reserve is reported as a planning quantity, not as payable
    # event credit.  It is frozen on earlier days from an empirical arrival
    # envelope and is never inserted into the committed-ledger certificate.
    # This gives the operator a reproducible way to reserve future capacity
    # while preserving the strict information boundary of the settlement.
    reserve_quantiles = np.asarray(
        cfg["experiments"].get(
            "event_gate_reserve_quantiles", [0.55, 0.60, 0.65, 0.70]
        ),
        dtype=float,
    )
    if reserve_quantiles.size == 0 or np.any(
        (reserve_quantiles <= 0.0) | (reserve_quantiles >= 1.0)
    ):
        raise ValueError("event_gate_reserve_quantiles must lie strictly inside (0,1)")
    reserve_cap_quantile = float(
        cfg["experiments"].get("event_gate_reserve_cap_quantile", 0.75)
    )
    reserve_false_budget = float(
        cfg["experiments"].get(
            "event_gate_reserve_validation_false_credit_budget_mwh", 0.25
        )
    )
    if not 0.0 < reserve_cap_quantile < 1.0 or reserve_false_budget < 0.0:
        raise ValueError("Invalid causal reserve calibration parameters")

    def solve_causal_reserve(day: int, quantile: float) -> tuple[Any, float, float]:
        history = valid_days[valid_days < int(day)]
        if len(history) < 14:
            raise ValueError(f"Insufficient history for causal reserve day {day}")
        truncated = arrivals_days[int(day)].copy()
        future_arrivals = float(truncated[gate:].sum())
        reserve = np.quantile(
            arrivals_days[history, gate:, :, :], float(quantile), axis=0
        )
        reserve_arrivals = truncated.copy()
        reserve_arrivals[gate:] = reserve
        # The cap is learned from pre-gate honest schedules only. It is a
        # planning envelope and does not authorize payment for reserve jobs.
        event_cap = np.quantile(
            model_honest[history][:, :, event_slots],
            reserve_cap_quantile,
            axis=0,
        )
        fixed = float(cfg["project"]["fixed_facility_load_mw"])
        capacity = float(cfg["project"]["flexible_capacity_mw"])
        upper = np.full(
            (prices.shape[0], truncated.shape[0]), fixed + capacity, dtype=float
        )
        upper[:, event_slots] = np.maximum(fixed, event_cap)
        result = _solve_day_with_buffer(
            reserve_arrivals,
            prices,
            gate_cfg,
            mode="honest",
            power_upper_mw=upper,
            require_all_arrivals_at_terminal=False,
            terminal_completion_index=terminal,
            event_slots_override=event_slots,
        )
        if not result.success:
            raise RuntimeError(
                f"Causal reserve planning LP failed on day {day}: "
                f"{result.solver_message}"
            )
        return result, future_arrivals, float(reserve.sum())

    reserve_validation_rows: list[dict[str, Any]] = []
    validation_days_gate = validation["days"].astype(int)
    for quantile in reserve_quantiles:
        q_rows: list[dict[str, Any]] = []
        for local_day, day_value in enumerate(validation_days_gate):
            day = int(day_value)
            result, future_arrivals, reserve_mwh = solve_causal_reserve(
                day, float(quantile)
            )
            base = baseline_metrics(result.power_mw, validation["oracle"][local_day], event_slots)
            response = response_metrics(
                result.power_mw,
                validation["oracle"][local_day],
                validation["actual"][local_day],
                event_slots,
                float(cfg["project"]["interval_minutes"]) / 60.0,
            )
            q_rows.append(
                {
                    "day": day,
                    "reserve_quantile": float(quantile),
                    "future_arrivals_mwh_after_gate": future_arrivals,
                    "reserved_future_arrivals_mwh": reserve_mwh,
                    **base,
                    **response,
                }
            )
        reserve_validation_rows.extend(q_rows)
    reserve_validation = pd.DataFrame(reserve_validation_rows)
    reserve_validation_summary = (
        reserve_validation.groupby("reserve_quantile", as_index=False)
        .agg(
            n_days=("day", "nunique"),
            nrmse=("nrmse", "mean"),
            false_response_mwh=("false_response_mwh", "mean"),
            credit_recall=("credit_recall", "mean"),
            credit_f1=("credit_f1", "mean"),
            reserved_future_arrivals_mwh=("reserved_future_arrivals_mwh", "mean"),
        )
    )
    feasible_reserve = reserve_validation_summary[
        reserve_validation_summary["false_response_mwh"] <= reserve_false_budget + 1e-12
    ]
    reserve_pool = feasible_reserve if len(feasible_reserve) else reserve_validation_summary
    selected_reserve_quantile = float(
        reserve_pool.sort_values(
            ["nrmse", "false_response_mwh", "reserve_quantile"]
        ).iloc[0]["reserve_quantile"]
    )
    reserve_validation_summary["selected"] = (
        reserve_validation_summary["reserve_quantile"] == selected_reserve_quantile
    )
    reserve_validation["selected"] = (
        reserve_validation["reserve_quantile"] == selected_reserve_quantile
    )
    reserve_validation.to_csv(final / "causal_reserve_validation_daily.csv", index=False)
    reserve_validation_summary.to_csv(
        final / "causal_reserve_validation_summary.csv", index=False
    )
    response_validation_rows: list[dict[str, Any]] = []
    for dr_price in response_dr_prices:
        for response_weight in response_projection_weights:
            for local_day, day_value in enumerate(validation_days_gate):
                day = int(day_value)
                response_result, baseline_result, reference_result, _, future_arrivals_mwh = (
                    solve_committed_response(
                        day,
                        float(dr_price),
                        float(response_weight),
                    )
                )
                # The no-tariff LP is the submitted baseline.  The tariff LP
                # is a response operating plan and is scored through planned
                # versus metered reduction, never as a second baseline.
                base = baseline_metrics(
                    baseline_result.power_mw,
                    validation["oracle"][local_day],
                    event_slots,
                )
                response = response_delivery_metrics(
                    baseline_result.power_mw,
                    response_result.power_mw,
                    validation["oracle"][local_day],
                    validation["actual"][local_day],
                    event_slots,
                    float(cfg["project"]["interval_minutes"]) / 60.0,
                )
                response["post_response_event_service_mwh"] = float(
                    np.maximum(
                        response_result.power_mw[:, event_slots]
                        - float(cfg["project"]["fixed_facility_load_mw"]),
                        0.0,
                    ).sum()
                    * float(cfg["project"]["interval_minutes"])
                    / 60.0
                )
                response_validation_rows.append(
                    {
                        "day": day,
                        "dr_price_per_mwh": float(dr_price),
                        "projection_weight": float(response_weight),
                        "future_arrivals_mwh_after_gate": future_arrivals_mwh,
                        **base,
                        **response,
                    }
                )
    response_validation = pd.DataFrame(response_validation_rows)
    response_validation_summary = (
        response_validation.groupby(
            ["dr_price_per_mwh", "projection_weight"], as_index=False
        )
        .agg(
            n_days=("day", "nunique"),
            nrmse=("nrmse", "mean"),
            false_response_mwh=("false_response_mwh", "mean"),
            credit_recall=("credit_recall", "mean"),
            credit_f1=("credit_f1", "mean"),
            payable_response_mwh=("meter_capped_response_mwh", "mean"),
        )
    )
    if bool(
        cfg["experiments"].get("decision_time_require_positive_response_price", False)
    ):
        # A response-calibration table that selects a zero-tariff tie point
        # would not test the declared DR service mechanism. Restrict the
        # predeclared candidate pool to positive tariff and positive projection
        # weights; the choice remains validation-only and deterministic.
        positive_pool = response_validation_summary[
            (response_validation_summary["dr_price_per_mwh"] > 0.0)
            & (response_validation_summary["projection_weight"] > 0.0)
            & (response_validation_summary["payable_response_mwh"] > 1.0e-9)
        ]
    else:
        positive_pool = response_validation_summary
    feasible_response = response_validation_summary[
        response_validation_summary["false_response_mwh"]
        <= response_false_budget + 1e-12
    ]
    response_pool = feasible_response if len(feasible_response) else response_validation_summary
    if len(positive_pool):
        positive_feasible = positive_pool[
            positive_pool["false_response_mwh"] <= response_false_budget + 1e-12
        ]
        response_pool = positive_feasible if len(positive_feasible) else positive_pool
    selected_response = response_pool.sort_values(
        ["credit_f1", "credit_recall", "nrmse", "false_response_mwh"],
        ascending=[False, False, True, True],
    ).iloc[0]
    selected_response_price = float(selected_response["dr_price_per_mwh"])
    selected_response_weight = float(selected_response["projection_weight"])
    response_validation_summary["selected"] = (
        (response_validation_summary["dr_price_per_mwh"] == selected_response_price)
        & (response_validation_summary["projection_weight"] == selected_response_weight)
    )
    response_validation["selected"] = (
        (response_validation["dr_price_per_mwh"] == selected_response_price)
        & (response_validation["projection_weight"] == selected_response_weight)
    )
    response_validation.to_csv(
        final / "causal_response_candidate_validation_daily.csv", index=False
    )
    response_validation_summary.to_csv(
        final / "causal_response_candidate_validation.csv", index=False
    )
    checkpoint = intermediate / "decision_time_checkpoint.csv"
    rows: list[dict[str, Any]] = []
    reserve_test_rows: list[dict[str, Any]] = []
    reserve_daily_path = final / "causal_reserve_test_daily.csv"
    if resume and reserve_daily_path.exists():
        # A completed checkpoint can be resumed after the process has already
        # written the daily reserve panel.  Rehydrate that panel before the
        # summary groupby; otherwise a successful 54-day resume would fail
        # only at the final reporting step.
        try:
            reserve_test_rows = pd.read_csv(reserve_daily_path).to_dict("records")
        except (OSError, ValueError):
            reserve_test_rows = []
    completed: set[int] = set()
    # The candidate economic grid and the complete-ledger risk profile are
    # part of the decision protocol. Bump the checkpoint schema whenever
    # either changes so stale response rows cannot be reported under a new
    # calibration.
    schema = 12
    profile_checksum = hashlib.sha256(profile_path.read_bytes()).hexdigest()
    if resume and checkpoint.exists():
        previous = pd.read_csv(checkpoint)
        if (
            "schema_version" in previous
            and set(previous["schema_version"].astype(int).unique()) == {schema}
            and set(previous["day"].astype(int).unique()) <= set(days)
            and "terminal_completion_index" in previous
            and set(previous["terminal_completion_index"].astype(int).unique())
            == {terminal}
            and "decision_gate_slot" in previous
            and set(previous["decision_gate_slot"].astype(int).unique()) == {gate}
            and "profile_checksum" in previous
            and set(previous["profile_checksum"].astype(str).unique())
            == {profile_checksum}
        ):
            rows = previous.to_dict("records")
            counts = previous.groupby("day")["method"].nunique()
            completed = set(int(day) for day in counts[counts == 4].index)
        else:
            logger.info(
                "Discarding stale Experiment 17 checkpoint: gate/terminal "
                "protocol differs from the current configuration"
            )
    progress = tqdm(
        total=len(days), initial=len(completed), desc="Exp17 event-gate decision-time LPs"
    )
    for local_day, day_value in enumerate(days):
        day = int(day_value)
        if day in completed:
            continue
        truncated = arrivals_days[day].copy()
        future_arrivals_mwh = float(truncated[gate:].sum())
        truncated[gate:] = 0.0
        # A deployable event-gate policy must not credit flexible service whose
        # ledger is not committed.  The post-gate ledger has already been
        # removed from ``truncated``.  The no-tariff committed-ledger baseline
        # is frozen before the event, and the second LP uses the declared DR
        # price to shift only committed service away from the event slots.
        fixed_load = float(cfg["project"]["fixed_facility_load_mw"])
        flexible_capacity = float(cfg["project"]["flexible_capacity_mw"])
        committed_event_upper = np.full(
            (prices.shape[0], truncated.shape[0]),
            fixed_load + flexible_capacity,
            dtype=float,
        )
        (
            committed_result,
            committed_baseline_result,
            committed_reference_result,
            _,
            _,
        ) = solve_committed_response(
            day,
            selected_response_price,
            selected_response_weight,
        )
        # The submitted contract is exactly the no-tariff LP returned by the
        # same causal response solve; the tariff-bearing profile is evaluated
        # only as the post-event operating response below.
        contract_profile = committed_baseline_result.power_mw
        reserve_result, _, reserve_mwh = solve_causal_reserve(
            day, selected_reserve_quantile
        )
        reserve_test_rows.append(
            {
                "day": day,
                "reserve_quantile": selected_reserve_quantile,
                "future_arrivals_mwh_after_gate": future_arrivals_mwh,
                "reserved_future_arrivals_mwh": reserve_mwh,
                **baseline_metrics(reserve_result.power_mw, oracle[local_day], event_slots),
                **response_metrics(
                    reserve_result.power_mw,
                    oracle[local_day],
                    actual[local_day],
                    event_slots,
                    float(cfg["project"]["interval_minutes"]) / 60.0,
                ),
            }
        )
        method_specs = [
            {
                "method": "Decision-time truncated-ledger verifier",
                "profile": contract_profile,
                "response_profile": contract_profile,
                "future_used": False,
                "certificate_scope": "gate-causal frozen contract baseline",
                "contract_baseline": contract_profile,
                "response_scoring": "baseline-credit audit",
            },
            {
                "method": "Complete-ledger risk-constrained verifier",
                "profile": complete_profiles[local_day],
                "response_profile": complete_profiles[local_day],
                "future_used": True,
                "certificate_scope": "ex-post reference audit",
                "contract_baseline": complete_profiles[local_day],
                "response_scoring": "baseline-credit audit",
            },
            {
                "method": "Committed-ledger rolling-service verifier",
                "profile": committed_baseline_result.power_mw,
                "response_profile": committed_result.power_mw,
                "future_used": False,
                "certificate_scope": "committed-ledger response; submitted baseline frozen before event",
                "contract_baseline": committed_baseline_result.power_mw,
                "response_scoring": "planned-versus-metered response delivery",
            },
            {
                "method": "Committed-ledger reference schedule",
                "profile": committed_reference_result.power_mw,
                "response_profile": committed_reference_result.power_mw,
                "future_used": False,
                "certificate_scope": "committed-ledger eligibility reference",
                "contract_baseline": committed_reference_result.power_mw,
                "response_scoring": "baseline-credit audit",
            },
        ]
        for spec in method_specs:
            method = str(spec["method"])
            profile = np.asarray(spec["profile"])
            response_profile = np.asarray(spec["response_profile"])
            future_used = bool(spec["future_used"])
            certificate_scope = str(spec["certificate_scope"])
            contract_baseline = np.asarray(spec["contract_baseline"])
            row = {
                "day": day,
                "method": method,
                "decision_gate_slot": gate,
                "terminal_completion_index": terminal,
                "future_arrivals_mwh_after_gate": future_arrivals_mwh,
                "future_arrivals_used_for_decision": bool(future_used),
                "certificate_scope": certificate_scope,
                "profile_role": "submitted baseline contract",
                "response_profile_role": (
                    "post-event operating plan"
                    if method == "Committed-ledger rolling-service verifier"
                    else "same profile as submitted baseline"
                ),
                "response_scoring": str(spec["response_scoring"]),
                "committed_arrivals_mwh": float(truncated.sum()),
                "reserved_future_arrivals_mwh": reserve_mwh,
                "uncommitted_arrivals_excluded_from_payment_mwh": future_arrivals_mwh,
                "selected_response_dr_price_per_mwh": selected_response_price,
                "selected_response_projection_weight": selected_response_weight,
                "eligible_reference_nrmse": float(
                    baseline_metrics(
                        profile,
                        committed_reference_result.power_mw,
                        event_slots,
                    )["nrmse"]
                ),
                "payment_eligibility": (
                    "complete-ledger" if future_used else "committed-ledger-only"
                ),
                "event_upper_margin_mw": float(
                    np.min(
                        committed_event_upper[:, event_slots]
                        - response_profile[:, event_slots]
                    )
                )
                if method == "Committed-ledger rolling-service verifier"
                else np.nan,
                "post_response_event_service_mwh": float(
                    np.maximum(
                        response_profile[:, event_slots]
                        - fixed_load,
                        0.0,
                    ).sum()
                    * float(cfg["project"]["interval_minutes"])
                    / 60.0
                )
                if method == "Committed-ledger rolling-service verifier"
                else np.nan,
                "settlement_rule": (
                    "contract-capped-after-event: payable credit is the pointwise "
                    "intersection of submitted baseline credit; frozen contract "
                    "baseline credit; and the closed event meter; oracle "
                    "overpayment is diagnostic only"
                ),
                "schema_version": schema,
                "profile_checksum": profile_checksum,
            }
            row.update(baseline_metrics(profile, oracle[local_day], event_slots))
            if method == "Committed-ledger rolling-service verifier":
                row.update(
                    response_delivery_metrics(
                        contract_baseline,
                        response_profile,
                        oracle[local_day],
                        actual[local_day],
                        event_slots,
                        float(cfg["project"]["interval_minutes"]) / 60.0,
                    )
                )
            else:
                row.update(
                    response_metrics(
                        profile,
                        oracle[local_day],
                        actual[local_day],
                        event_slots,
                        float(cfg["project"]["interval_minutes"]) / 60.0,
                        contract_baseline=contract_baseline,
                    )
                )
            trace_base = baseline_metrics(
                profile, observed_meter[local_day], event_slots
            )
            observed_trace_rows.append(
                {
                    "day": day,
                    "method": method,
                    "truth_source": "independent_trace_observed_meter",
                    "event_intervention": False,
                    **{f"trace_{key}": value for key, value in trace_base.items()},
                }
            )
            rows.append(row)
        pd.DataFrame(rows).to_csv(checkpoint, index=False)
        completed.add(day)
        progress.update(1)
    progress.close()
    comparison = pd.DataFrame(rows).sort_values(["day", "method"])
    comparison.to_csv(final / "decision_time_comparison.csv", index=False)
    summary = (
        comparison.groupby("method", as_index=False)
        .agg(
            locked_days=("day", "nunique"),
            nrmse=("nrmse", "mean"),
            false_response_mwh=("false_response_mwh", "mean"),
            meter_capped_response_mwh=("meter_capped_response_mwh", "mean"),
            meter_capped_false_response_mwh=(
                "meter_capped_false_response_mwh",
                "mean",
            ),
            credit_recall=("credit_recall", "mean"),
            credit_f1=("credit_f1", "mean"),
            mean_future_arrivals_mwh=("future_arrivals_mwh_after_gate", "mean"),
            mean_reserved_future_arrivals_mwh=("reserved_future_arrivals_mwh", "mean"),
            mean_committed_arrivals_mwh=("committed_arrivals_mwh", "mean"),
            mean_eligible_reference_nrmse=("eligible_reference_nrmse", "mean"),
        )
    )
    summary.to_csv(final / "decision_time_summary.csv", index=False)
    trace_replay_path = final / "decision_time_trace_replay.csv"
    if not observed_trace_rows:
        # A completed legacy checkpoint can legitimately skip the method loop
        # when ``resume=True``.  Reuse only a trace panel produced under the
        # same checkpoint; silently writing an empty file would erase the
        # independent information-boundary audit.
        if trace_replay_path.exists():
            observed_trace_rows = pd.read_csv(trace_replay_path).to_dict("records")
        else:
            raise RuntimeError(
                "Decision-time checkpoint has no independent trace replay; "
                "rerun Exp17 with resume=False to rebuild it."
            )
    pd.DataFrame(observed_trace_rows).sort_values(["day", "method"]).to_csv(
        trace_replay_path, index=False
    )
    information_boundary_certificate = pd.DataFrame(
        [
            {
                "criterion": "post_gate_arrivals_in_decision",
                "value": 0,
                "required_value": 0,
                "units": "boolean",
                "evidence": "all committed-ledger LP inputs set arrivals[gate:] to zero",
            },
            {
                "criterion": "execution_truth_available_to_decision",
                "value": 0,
                "required_value": 0,
                "units": "boolean",
                "evidence": "DCGM/BurstGPT execution tensor is opened only in the scoring pass",
            },
            {
                "criterion": "locked_truth_used_for_selection",
                "value": 0,
                "required_value": 0,
                "units": "boolean",
                "evidence": "response and reserve candidates are selected on validation days only",
            },
            {
                "criterion": "utility_event_label_available",
                "value": 0,
                "required_value": 0,
                "units": "boolean",
                "evidence": "public traces have no exogenous utility event label",
            },
            {
                "criterion": "submitted_contract_frozen_before_event",
                "value": 1,
                "required_value": 1,
                "units": "boolean",
                "evidence": "no-tariff committed-ledger LP is the submitted baseline",
            },
            {
                "criterion": "future_arrivals_excluded_from_payment",
                "value": 1,
                "required_value": 1,
                "units": "boolean",
                "evidence": "reserved and post-gate jobs cannot enter the gate contract",
            },
        ]
    )
    information_boundary_certificate.to_csv(
        final / "information_boundary_certificate.csv", index=False
    )
    reserve_test = pd.DataFrame(reserve_test_rows)
    if reserve_test.empty:
        raise RuntimeError(
            "Decision-time checkpoint completed without a causal reserve panel; "
            "rerun Exp17 with resume disabled."
        )
    reserve_test.to_csv(final / "causal_reserve_test_daily.csv", index=False)
    reserve_test.groupby("reserve_quantile", as_index=False).agg(
        n_days=("day", "nunique"),
        nrmse=("nrmse", "mean"),
        false_response_mwh=("false_response_mwh", "mean"),
        credit_recall=("credit_recall", "mean"),
        credit_f1=("credit_f1", "mean"),
        reserved_future_arrivals_mwh=("reserved_future_arrivals_mwh", "mean"),
    ).to_csv(final / "causal_reserve_test_summary.csv", index=False)
    metadata = {
        "experiment": "event-gate information-boundary verification",
        "locked_days": int(len(days)),
        "profile_checksum": profile_checksum,
        "profile_source": "Experiment-2 locked test_profiles.npz",
        "event_gate_slot": gate,
        "terminal_completion_index": terminal,
        "future_arrivals_removed_from_decision": True,
        "target_source": (
            "interval-online metadata gradient boosting refit with the current-day "
            "post-gate arrivals masked before feature construction"
        ),
        "target_future_arrivals_used_for_decision": False,
        "causal_reserve_planning": {
            "daily_file": "causal_reserve_validation_daily.csv",
            "summary_file": "causal_reserve_validation_summary.csv",
            "candidate_quantiles": reserve_quantiles.tolist(),
            "selected_quantile": selected_reserve_quantile,
            "cap_quantile": reserve_cap_quantile,
            "validation_false_credit_budget_mwh": reserve_false_budget,
            "future_arrivals_used_for_payment": False,
            "interpretation": (
                "The empirical reserve is a pre-gate planning envelope. It can "
                "reserve capacity for future arrivals, but the event-gate payment "
                "profile is solved on the committed ledger and cannot credit the "
                "reserved jobs before a later commitment checkpoint."
            ),
        },
        "causal_response_calibration": {
            "daily_file": "causal_response_candidate_validation_daily.csv",
            "summary_file": "causal_response_candidate_validation.csv",
            "candidate_dr_prices_per_mwh": response_dr_prices.tolist(),
            "candidate_projection_weights": response_projection_weights.tolist(),
            "validation_false_credit_budget_mwh": response_false_budget,
            "selected_dr_price_per_mwh": selected_response_price,
            "selected_projection_weight": selected_response_weight,
            "committed_event_service_mwh": committed_event_service_mwh,
            "selection_rule": (
                "among candidates satisfying the validation false-credit budget, "
                "maximize credit F1, then recall, then minimize nRMSE and false credit"
            ),
            "submitted_profile": "causal committed-ledger baseline LP with no event tariff; the same-ledger DR response LP is retained as a post-event operating replay",
            "response_scoring": "baseline error is computed on the submitted contract; response delivery is computed from planned reduction relative to that contract and the closed meter",
            "future_arrivals_used_for_decision": False,
        },
        "scoring_source": (
            "declared event-response LP operating replay for the mechanism-"
            "isolation rows; no public utility intervention is observed"
        ),
        "causal_identification_boundary": {
            "temporal_information_causality": True,
            "utility_event_label_available": False,
            "randomized_or_exogenous_event_intervention": False,
            "interpretation": (
                "causal refers to the pre-event information filtration only; the "
                "locked trace-meter alignment is observational and is not a treatment-effect estimate"
            ),
        },
        "observational_trace_source": "independent locked DCGM/BurstGPT execution trace",
        "observational_trace_replay_file": "decision_time_trace_replay.csv",
        "information_boundary_certificate_file": "information_boundary_certificate.csv",
        "information_boundary_certificate_scope": (
            "pre-event filtration and contract-formation checks; the certificate "
            "does not identify a causal utility treatment effect"
        ),
        "simulated_response_source": (
            "the committed-ledger DR LP is retained as an operating replay and "
            "is never substituted for the measured scoring meter"
        ),
        "meter_cap_scoring_note": (
            "The deployed settlement uses the submitted causal committed-ledger "
            "baseline, its frozen pre-event contract profile, and the closed event meter. For "
            "the locked audit, the trace-anchored no-event profile is used only "
            "after the event to diagnose oracle overpayment and underpayment; it "
            "is not supplied to target fitting, gate decisions, workload "
            "optimization, or payment formation."
        ),
        "selection_uses_locked_test_truth": False,
        "all_decision_time_lp_solved": True,
        "committed_ledger_safe_mode": {
            "method": "Committed-ledger rolling-service verifier",
            "future_arrivals_used_for_decision": False,
            "event_upper_bound_source": "physical flexible-capacity bound",
            "certificate_scope": "committed-ledger service feasibility; all paid service is committed at the gate",
            "rolling_commitment": True,
            "contract_baseline_source": "causal committed-ledger baseline LP frozen before the event",
            "response_objective": "same masked-ledger LP with the selected validation DR price on participating event slots; post-event profile is diagnostic and never forms the pre-event contract",
            "selected_dr_price_per_mwh": selected_response_price,
                "selected_projection_weight": selected_response_weight,
                "committed_event_service_mwh": committed_event_service_mwh,
            "settlement_rule": (
                "contract-capped-after-event; gross forecast credit is not paid "
                "above the frozen contract credit or the pointwise metered response"
            ),
            "profile_semantics": {
                "contract_profile": "no-tariff committed-ledger LP frozen at the event gate",
                "response_profile": "tariff-bearing operating LP on the same committed ledger",
                "payment_metric": "minimum of planned committed reduction, closed-meter reduction, and oracle diagnostic credit",
            },
        },
        "protocol_note": (
            "The truncated profile is an information-boundary diagnostic. The "
            "committed-ledger profile is the deployable rolling-service mode; the "
            "complete-ledger comparator quantifies the value of post-event information."
        ),
    }
    write_json(final / "experiment_metadata.json", metadata)
    plot_exp17_decision_time(comparison, folder / "figures", cfg)
    logger.info(
        "Experiment 17 complete: %d locked days, gate=%d, mean future arrivals=%.3f MWh",
        len(days),
        gate,
        float(comparison.drop_duplicates("day")["future_arrivals_mwh_after_gate"].mean()),
    )


def run_exp18(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
    resume: bool = False,
) -> None:
    """Run a fixed-active-plan AC N-1 panel across public networks.

    The panel uses a predeclared set of locked day/slot snapshots rather than
    an outcome-selected single state. It evaluates every finite non-islanding
    line outage for RTS-24, IEEE-30, IEEE-39, and IEEE-118 at all three
    declared penetrations. Four regional injections use a pre-registered
    public-bus mapping from the configuration. The intact AC dispatch is
    frozen for each method, penetration, and snapshot; every contingency
    reuses the non-reference generator active outputs and permits only the
    reference generator, reactive outputs, and voltages to recourse. Line and
    voltage limits are checked by the same AC-OPF on that fixed plan.
    """
    from pypower.case24_ieee_rts import case24_ieee_rts
    from pypower.case30 import case30
    from pypower.case39 import case39
    from pypower.case118 import case118
    from pypower.idx_brch import BR_STATUS, PF, PT, QF, QT, RATE_A
    from pypower.idx_bus import BUS_TYPE, PD, QD, REF, VM, VA, VMAX, VMIN
    from pypower.idx_gen import GEN_BUS, PG, PMIN, PMAX, QG
    from pypower.ppoption import ppoption
    from pypower.runopf import runopf
    from pypower.runpf import runpf
    import networkx as nx
    from .visualization import plot_exp18_preventive_ac_panel

    folder = root / "experiments/exp18_preventive_ac_network_panel"
    final = folder / "results/final"
    intermediate = folder / "results/intermediate"
    final.mkdir(parents=True, exist_ok=True)
    intermediate.mkdir(parents=True, exist_ok=True)
    profile_path = (
        root
        / "experiments/exp9_payment_certificate/results/final/"
        "certified_counterfactual_profiles.npz"
    )
    test_profile_path = (
        root
        / "experiments/exp2_baseline_verification/results/intermediate/test_profiles.npz"
    )
    validation_path = (
        root
        / "experiments/exp2_baseline_verification/results/intermediate/validation_profiles.npz"
    )
    if not profile_path.exists() or not test_profile_path.exists() or not validation_path.exists():
        run_exp9(root, cfg, logger, resume=True)
    certified = np.load(profile_path, allow_pickle=False)
    stored = np.load(test_profile_path, allow_pickle=False)
    validation = np.load(validation_path, allow_pickle=False)
    days = stored["days"].astype(int)
    if not np.array_equal(days, certified["days"]):
        raise RuntimeError("Preventive AC profile days do not match the locked panel")
    event_slot = int(min(map(int, cfg["market"]["event_slots"])))
    snapshot_day_indices = np.asarray(
        cfg["experiments"].get("preventive_ac_validation_day_indices", [0]),
        dtype=int,
    )
    snapshot_event_slots = np.asarray(
        cfg["experiments"].get("preventive_ac_validation_event_slots", [event_slot]),
        dtype=int,
    )
    if (
        snapshot_day_indices.ndim != 1
        or len(snapshot_day_indices) == 0
        or np.any(snapshot_day_indices < 0)
        or np.any(snapshot_day_indices >= len(days))
        or snapshot_event_slots.ndim != 1
        or len(snapshot_event_slots) == 0
        or np.any(snapshot_event_slots < 0)
        or np.any(snapshot_event_slots >= stored["oracle"].shape[-1])
    ):
        raise ValueError("Preventive AC snapshot indices are outside the locked panel")
    snapshots = [
        (int(day_index), int(days[day_index]), int(slot))
        for day_index in snapshot_day_indices
        for slot in snapshot_event_slots
    ]
    validation_event_slots = np.asarray(
        list(map(int, cfg["market"]["event_slots"])), dtype=int
    )
    validation_trace_peak = float(
        max(
            validation["actual"][:, :, validation_event_slots].sum(axis=1).max(),
            validation["oracle"][:, :, validation_event_slots].sum(axis=1).max(),
            validation["projection_candidates"][:, :, :, validation_event_slots].sum(axis=2).max(),
            validation["quantile_profile"][:, :, validation_event_slots].sum(axis=1).max(),
        )
    )
    methods = {
        "Payment-Certified N-1 Verifier": certified["profiles"],
        "Trace-Anchored Reference": stored["oracle"],
    }
    networks = [
        ("IEEE RTS 24-bus", case24_ieee_rts),
        ("IEEE 30-bus", case30),
        ("IEEE 39-bus", case39),
        ("IEEE 118-bus", case118),
    ]
    # The workload locations are a pre-registered public-bus mapping, not a
    # post-hoc placement selected from contingency outcomes.  Generator buses
    # are used so that the four regional injections have a reproducible
    # electrical connection in every benchmark case.  The IEEE 39-bus case
    # uses a non-reference subset with a well-defined four-bus spacing; all
    # mappings are fixed before the panel is evaluated.
    dc_bus_map = cfg["experiments"].get(
        "preventive_ac_dc_bus_map_one_based",
        {
            "IEEE RTS 24-bus": [1, 2, 7, 13],
            "IEEE 30-bus": [1, 2, 13, 22],
            "IEEE 39-bus": [30, 31, 32, 33],
            "IEEE 118-bus": [1, 4, 6, 8],
        },
    )
    penetrations = np.asarray(
        cfg["experiments"].get(
            "preventive_ac_dc_peak_penetrations", [0.03, 0.06, 0.09]
        ),
        dtype=float,
    )
    if len(penetrations) < 3 or np.any(penetrations <= 0) or not np.all(np.diff(penetrations) > 0):
        raise ValueError("Preventive penetration grid must be increasing and positive")
    load_multiplier = float(
        cfg["experiments"].get("preventive_ac_load_multiplier", cfg["experiments"].get("ac_load_multiplier", 0.9))
    )
    active_plan_tolerance_mw = float(
        cfg["experiments"].get("preventive_ac_active_plan_tolerance_mw", 1.0e-8)
    )
    if not np.isfinite(active_plan_tolerance_mw) or not (0.0 < active_plan_tolerance_mw <= 1.0e-5):
        raise ValueError("preventive_ac_active_plan_tolerance_mw must be in (0, 1e-5]")
    power_factor = float(cfg["experiments"].get("ac_data_center_power_factor", 0.95))
    reactive_ratio = float(np.tan(np.arccos(power_factor)))
    options = ppoption(
        VERBOSE=0,
        OUT_ALL=0,
        OPF_ALG=0,
        OPF_VIOLATION=1e-6,
        PDIPM_MAX_IT=300,
    )
    fallback_options = ppoption(
        VERBOSE=0,
        OUT_ALL=0,
        # PIPS's safeguarded variant is a deterministic numerical fallback for
        # an ill-conditioned AC-OPF start.  It does not relax any constraint;
        # the returned solution is subjected to the same hard checks below.
        OPF_ALG=565,
        OPF_VIOLATION=1e-6,
        PDIPM_MAX_IT=300,
    )
    # The Newton power-flow default can diverge from the public MATPOWER
    # starting point for a few otherwise feasible high-reactive-load cells.
    # A fast-decoupled PF is used only to produce a numerical warm start for
    # the same constrained AC-OPF; it never supplies a reported certificate.
    pf_warm_options = ppoption(
        VERBOSE=0,
        OUT_ALL=0,
        PF_ALG=2,
        PF_TOL=1e-8,
        PF_MAX_IT=200,
    )
    import copy

    fallback_count = 0
    isolated_solver_calls = 0

    def solve_acopf(
        case: dict[str, Any], warm_start: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        nonlocal fallback_count, isolated_solver_calls
        # PYPOWER's solver stack can update the working case while assembling
        # the nonlinear model.  Keep every retry on the same pristine input;
        # otherwise a failed first start can contaminate the warm-start path
        # and turn a feasible cell into a false numerical failure.
        pristine = copy.deepcopy(case)
        if warm_start is not None:
            # Continuation over the predeclared penetration grid supplies a
            # physically meaningful high-voltage start for the same AC model;
            # it changes no load, dispatch bound, or security constraint.
            if warm_start.get("bus", np.empty((0, 0))).shape == pristine["bus"].shape:
                pristine["bus"][:, VM] = warm_start["bus"][:, VM]
                pristine["bus"][:, VA] = warm_start["bus"][:, VA]
            if warm_start.get("gen", np.empty((0, 0))).shape == pristine["gen"].shape:
                pristine["gen"][:, PG] = warm_start["gen"][:, PG]
                pristine["gen"][:, QG] = warm_start["gen"][:, QG]
        # A fresh MIPS start is cheap and protects against the occasional
        # sparse-factorization numerical failure on the public 39-bus case.
        for _ in range(2):
            result = runopf(copy.deepcopy(pristine), copy.deepcopy(options))
            if bool(result.get("success", 0)):
                return result
        fallback_count += 1
        retry: dict[str, Any] = {}
        for _ in range(2):
            retry = runopf(copy.deepcopy(pristine), copy.deepcopy(fallback_options))
            if bool(retry.get("success", 0)):
                return retry
        # A failed interior-point start can leave a perfectly usable AC power
        # flow initialization.  Re-solving that fixed model with PIPS is a
        # deterministic numerical restart; no dispatch or limit is changed.
        warm = copy.deepcopy(pristine)
        pf_result, pf_success = runpf(warm, copy.deepcopy(pf_warm_options))
        if pf_success:
            warm["bus"][:, VM] = pf_result["bus"][:, VM]
            warm["bus"][:, VA] = pf_result["bus"][:, VA]
            warm["gen"][:, PG] = pf_result["gen"][:, PG]
            warm["gen"][:, QG] = pf_result["gen"][:, QG]
            warm_retry = runopf(warm, copy.deepcopy(fallback_options))
            if bool(warm_retry.get("success", 0)):
                return warm_retry
        # Last numerical restart: solve the untouched case in a clean Python
        # interpreter.  This is invoked only for a failed cell, and the child
        # uses the same OPF options and hard constraints.  It is deliberately
        # not a relaxation or a different model; it only removes process-level
        # sparse-solver state from the retry path.
        import os
        import pickle
        import subprocess
        import sys
        import tempfile

        isolated_solver_calls += 1
        with tempfile.TemporaryDirectory(prefix="aicdr-acopf-") as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / "input.pkl"
            output_path = temp_path / "output.pkl"
            with input_path.open("wb") as handle:
                pickle.dump(
                    {"case": pristine, "options": copy.deepcopy(options)},
                    handle,
                    protocol=pickle.HIGHEST_PROTOCOL,
                )
            repo_root = Path(__file__).resolve().parents[2]
            child_env = os.environ.copy()
            child_paths = [str(repo_root / "code/src"), str(repo_root / "vendor")]
            if child_env.get("PYTHONPATH"):
                child_paths.append(child_env["PYTHONPATH"])
            child_env["PYTHONPATH"] = os.pathsep.join(child_paths)
            try:
                completed_process = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "aicdr.acopf_worker",
                        str(input_path),
                        str(output_path),
                    ],
                    env=child_env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                    timeout=180,
                )
            except (OSError, subprocess.SubprocessError):
                completed_process = None
            if completed_process is not None and completed_process.returncode == 0 and output_path.exists():
                try:
                    with output_path.open("rb") as handle:
                        isolated = pickle.load(handle)
                    if bool(isolated.get("success", 0)):
                        return isolated
                except (OSError, EOFError, pickle.PickleError, ValueError, AttributeError):
                    pass
        return retry
    # Schema 6 invalidates the earlier 0.45-load panel and records the
    # fixed-plan numerical tolerance introduced for the 0.90-load protocol.
    schema = 6
    checkpoint = intermediate / "preventive_ac_cross_network_checkpoint.csv"
    rows: list[dict[str, Any]] = []
    completed: set[tuple[str, float, str, int, int, int]] = set()
    if resume and checkpoint.exists():
        previous = pd.read_csv(checkpoint)
        if "schema_version" in previous and set(previous["schema_version"].astype(int).unique()) == {schema}:
            rows = previous.to_dict("records")
            completed = {
                (
                    str(row.network),
                    round(float(row.peak_dc_penetration), 12),
                    str(row.method),
                    int(row.outage),
                    int(row.day),
                    int(row.event_slot),
                )
                for row in previous.itertuples()
            }
    # Precompute intact dispatches before the native N-1 admissibility loop.
    # This isolates the continuation path from the hundreds of subsequent
    # contingency factorizations.  The cached objects are immutable inputs to
    # the later fixed-active-plan checks, not post-hoc dispatch adjustments.
    precomputed_base_results: dict[tuple[str, float, str, int], dict[str, Any]] = {}
    precompute_networks = sorted(
        networks, key=lambda item: (0 if item[0] == "IEEE 39-bus" else 1, item[0])
    )
    precompute_tasks: list[dict[str, Any]] = []
    for network_name, case_function in precompute_networks:
        public_case = case_function()
        native_p = public_case["bus"][:, PD].copy() * load_multiplier
        native_q = public_case["bus"][:, QD].copy() * load_multiplier
        dc_buses = np.asarray(dc_bus_map[network_name], dtype=int) - 1
        if len(dc_buses) != 4 or np.any(dc_buses < 0) or np.any(dc_buses >= len(native_p)):
            raise RuntimeError(f"Invalid pre-registered DC-bus mapping for {network_name}")
        for method, profiles in methods.items():
            for snapshot_index, (local_day_index, fixed_day, snapshot_slot) in enumerate(snapshots):
                for penetration in sorted(penetrations, reverse=True):
                    dc_scale = float(penetration * native_p.sum() / max(validation_trace_peak, 1e-12))
                    precompute_tasks.append(
                        {
                            "network": network_name,
                            "case_function": case_function,
                            "native_p": native_p,
                            "native_q": native_q,
                            "dc_buses": dc_buses,
                            "method": method,
                            "profiles": profiles,
                            "snapshot_index": snapshot_index,
                            "local_day_index": local_day_index,
                            "fixed_day": fixed_day,
                            "snapshot_slot": snapshot_slot,
                            "penetration": float(penetration),
                            "dc_scale": dc_scale,
                        }
                    )

    workers = int(cfg["experiments"].get("ac_n1_workers", 1))
    if workers < 1 or workers > 20:
        raise ValueError("ac_n1_workers must be between 1 and 20")
    logger.info(
        "Experiment 18 intact AC dispatches: %d cells with %d bounded workers",
        len(precompute_tasks),
        workers,
    )
    base_payloads: list[dict[str, Any]] = []
    base_keys: list[tuple[str, float, str, int]] = []
    for task in precompute_tasks:
        base_case = task["case_function"]()
        base_case["bus"][:, PD] = task["native_p"]
        base_case["bus"][:, QD] = task["native_q"]
        dc_power = task["profiles"][task["local_day_index"], :, task["snapshot_slot"]] * task["dc_scale"]
        base_case["bus"][task["dc_buses"], PD] += dc_power
        base_case["bus"][task["dc_buses"], QD] += dc_power * reactive_ratio
        base_payloads.append(
            {
                "case": base_case,
                "options": options,
                "fallback_options": fallback_options,
                "pf_warm_options": pf_warm_options,
            }
        )
        base_keys.append(
            (
                str(task["network"]),
                round(float(task["penetration"]), 12),
                str(task["method"]),
                int(task["snapshot_index"]),
            )
        )
    with ProcessPoolExecutor(max_workers=workers) as executor:
        for key, payload_result in zip(base_keys, executor.map(_exp18_process_opf, base_payloads)):
            base_result = payload_result["result"]
            fallback_count += int(payload_result.get("fallback_count", 0))
            if not bool(base_result.get("success", 0)):
                task = precompute_tasks[len(precomputed_base_results)]
                raise RuntimeError(
                    "Preventive AC intact solve failed for "
                    f"{task['network']}, snapshot={task['snapshot_index']}, method={task['method']}, "
                    f"penetration={task['penetration']:.3f}"
                )
            precomputed_base_results[key] = base_result
    total_cells = 0
    network_cache: list[dict[str, Any]] = []
    for network_name, case_function in networks:
        public_case = case_function()
        system = power_system_from_ppc(public_case)
        bus_count = int(public_case["bus"].shape[0])
        candidate_outages = np.unique(build_n1_security_factors(system)[2]).astype(int)
        # The LODF finite-column test is necessary but not sufficient for
        # public case files with inconsistent external bus labels.  Recheck
        # graph connectivity explicitly before declaring a line outage
        # non-islanding; no loading- or outcome-dependent screening is used.
        endpoints = public_case["branch"][:, :2].astype(int)
        if endpoints.min() >= 1 and endpoints.max() <= bus_count:
            endpoints = endpoints - 1
        connected_outages = []
        for outage in candidate_outages:
            graph = nx.Graph()
            graph.add_nodes_from(range(bus_count))
            for branch_id, (left, right) in enumerate(endpoints):
                if int(branch_id) != int(outage):
                    graph.add_edge(int(left), int(right))
            if nx.is_connected(graph):
                connected_outages.append(int(outage))
        native_p = public_case["bus"][:, PD].copy() * load_multiplier
        native_q = public_case["bus"][:, QD].copy() * load_multiplier
        # AC admissibility is a model-domain condition evaluated on the public
        # native case, before any locked workload profile is introduced.  The
        # same preventive formulation used below is solved here: a native
        # intact AC-OPF supplies the shared non-reference active plan, and a
        # contingency AC-OPF fixes those active outputs while retaining
        # reference-generator, reactive, and voltage recourse.  This keeps the
        # admissibility rule tied to the declared AC-OPF model rather than to a
        # workload outcome or a solver-initialization artifact.
        native_case = case_function()
        native_case["bus"][:, PD] = native_p
        native_case["bus"][:, QD] = native_q
        native_intact = solve_acopf(native_case)
        if not bool(native_intact.get("success", 0)):
            raise RuntimeError(f"Native AC intact solve failed for {network_name}")
        native_reference_buses = set(
            np.where(native_intact["bus"][:, BUS_TYPE] == REF)[0]
        )
        native_nonreference_generators = np.asarray(
            [
                generator
                for generator in range(len(native_intact["gen"]))
                if int(native_intact["gen"][generator, GEN_BUS]) - 1
                not in native_reference_buses
            ],
            dtype=int,
        )
        native_shared_pg = native_intact["gen"][:, PG].copy()
        outages = []
        for outage in connected_outages:
            ac_case = case_function()
            ac_case["bus"][:, PD] = native_p
            ac_case["bus"][:, QD] = native_q
            ac_case["branch"][int(outage), BR_STATUS] = 0
            ac_case["gen"][native_nonreference_generators, PG] = native_shared_pg[
                native_nonreference_generators
            ]
            ac_case["gen"][native_nonreference_generators, PMIN] = (
                native_shared_pg[native_nonreference_generators] - active_plan_tolerance_mw
            )
            ac_case["gen"][native_nonreference_generators, PMAX] = (
                native_shared_pg[native_nonreference_generators] + active_plan_tolerance_mw
            )
            ac_result = solve_acopf(ac_case)
            if bool(ac_result.get("success", 0)):
                in_service = ac_result["branch"][:, BR_STATUS] > 0
                rates = ac_result["branch"][in_service, RATE_A].copy()
                rates[rates <= 0] = np.inf
                apparent_from = np.hypot(
                    ac_result["branch"][in_service, PF],
                    ac_result["branch"][in_service, QF],
                )
                apparent_to = np.hypot(
                    ac_result["branch"][in_service, PT],
                    ac_result["branch"][in_service, QT],
                )
                voltage_violation = np.maximum(
                    ac_result["bus"][:, VMIN] - ac_result["bus"][:, VM],
                    ac_result["bus"][:, VM] - ac_result["bus"][:, VMAX],
                )
                native_loading = float(
                    (np.maximum(apparent_from, apparent_to) / rates).max(initial=0.0)
                )
                native_voltage_violation = float(
                    max(0.0, voltage_violation.max(initial=0.0))
                )
                if native_loading <= 1.0 + 1e-6 and native_voltage_violation <= 1e-6:
                    outages.append(int(outage))
        outages = np.asarray(outages, dtype=int)
        if len(outages) == 0:
            raise RuntimeError(f"No connected non-islanding outages for {network_name}")
        network_cache.append(
            {
                "name": network_name,
                "case_function": case_function,
                "topology_connected_outages": np.asarray(connected_outages, dtype=int),
                "outages": outages,
                "native_p": native_p,
                "native_q": native_q,
                "dc_scale_by_penetration": {
                    float(p): float(p * native_p.sum() / max(validation_trace_peak, 1e-12))
                    for p in penetrations
                },
            }
        )
        total_cells += len(outages) * len(penetrations) * len(methods) * len(snapshots)
    progress_log_step = max(1, int(np.ceil(total_cells / 100.0)))
    last_progress_log = len(completed)
    logger.info(
        "Experiment 18 AC panel scheduled: %d/%d cells already complete (%.1f%%)",
        len(completed),
        total_cells,
        100.0 * len(completed) / max(total_cells, 1),
    )
    progress = tqdm(
        total=total_cells,
        initial=len(completed),
        desc="Exp18 cross-network AC N-1 admissibility",
    )
    def prepare_contingency_cell(task: dict[str, Any]) -> tuple[tuple[str, float, str, int, int, int], dict[str, Any]]:
        """Build one fixed-active-plan case for the process-isolated solver."""
        network_name = str(task["network"])
        method = str(task["method"])
        penetration = float(task["penetration"])
        fixed_day = int(task["fixed_day"])
        snapshot_slot = int(task["snapshot_slot"])
        outage = int(task["outage"])
        base_result = task["base_result"]
        nonreference_generators = task["nonreference_generators"]
        shared_pg = task["shared_pg"]
        case = task["case_function"]()
        case["bus"][:, PD] = task["native_p"]
        case["bus"][:, QD] = task["native_q"]
        case["bus"][task["dc_buses"], PD] += task["dc_power"]
        case["bus"][task["dc_buses"], QD] += task["dc_power"] * reactive_ratio
        case["branch"][outage, BR_STATUS] = 0
        case["gen"][nonreference_generators, PG] = shared_pg[nonreference_generators]
        case["gen"][nonreference_generators, PMIN] = (
            shared_pg[nonreference_generators] - active_plan_tolerance_mw
        )
        case["gen"][nonreference_generators, PMAX] = (
            shared_pg[nonreference_generators] + active_plan_tolerance_mw
        )
        key = (network_name, round(penetration, 12), method, outage, fixed_day, snapshot_slot)
        payload = {
            "case": case,
            "warm_start": base_result,
            "options": options,
            "fallback_options": fallback_options,
            "pf_warm_options": pf_warm_options,
        }
        return key, payload

    def score_contingency_cell(
        task: dict[str, Any], result: dict[str, Any]
    ) -> tuple[tuple[str, float, str, int, int, int], dict[str, Any]]:
        network_name = str(task["network"])
        method = str(task["method"])
        penetration = float(task["penetration"])
        fixed_day = int(task["fixed_day"])
        snapshot_index = int(task["snapshot_index"])
        snapshot_slot = int(task["snapshot_slot"])
        outage = int(task["outage"])
        base_result = task["base_result"]
        nonreference_generators = task["nonreference_generators"]
        reference_generators = task["reference_generators"]
        shared_pg = task["shared_pg"]
        if not bool(result.get("success", 0)):
            raise RuntimeError(
                f"AC N-1 fixed-active-plan OPF failed for {network_name}, "
                f"snapshot={snapshot_index}, penetration={penetration:.3f}, method={method}, outage={outage}"
            )
        in_service = result["branch"][:, BR_STATUS] > 0
        rates = result["branch"][in_service, RATE_A].copy()
        rates[rates <= 0] = np.inf
        apparent_from = np.hypot(result["branch"][in_service, PF], result["branch"][in_service, QF])
        apparent_to = np.hypot(result["branch"][in_service, PT], result["branch"][in_service, QT])
        voltage = result["bus"][:, VM]
        voltage_violation = np.maximum(result["bus"][:, VMIN] - voltage, voltage - result["bus"][:, VMAX])
        max_loading = float((np.maximum(apparent_from, apparent_to) / rates).max(initial=0.0))
        max_voltage_violation = float(max(0.0, voltage_violation.max(initial=0.0)))
        active_plan_deviation = float(
            np.max(
                np.abs(result["gen"][nonreference_generators, PG] - shared_pg[nonreference_generators]),
                initial=0.0,
            )
        )
        if (
            max_loading > 1.0 + 1e-6
            or max_voltage_violation > 1e-6
            or active_plan_deviation > active_plan_tolerance_mw + 1e-6
        ):
            raise RuntimeError(
                "Fixed-active-plan AC N-1 limits violated for "
                f"{network_name}, snapshot={snapshot_index}, penetration={penetration:.3f}, method={method}, outage={outage}: "
                f"loading={max_loading:.6f}, voltage={max_voltage_violation:.6f}, "
                f"active_plan_deviation={active_plan_deviation:.3e} MW"
            )
        key = (network_name, round(penetration, 12), method, outage, fixed_day, snapshot_slot)
        row = {
            "network": network_name,
            "snapshot_index": snapshot_index,
            "day": fixed_day,
            "event_slot": snapshot_slot,
            "method": method,
            "peak_dc_penetration": penetration,
            "outage": outage,
            "solver_success": 1,
            "maximum_apparent_line_loading": max_loading,
            "maximum_voltage_violation_pu": max_voltage_violation,
            "minimum_voltage_pu": float(voltage.min()),
            "maximum_nonreference_active_plan_deviation_mw": active_plan_deviation,
            "reference_generator_loss_recourse_mw": float(
                np.sum(result["gen"][reference_generators, PG] - shared_pg[reference_generators])
            ),
            "load_multiplier": load_multiplier,
            "data_center_power_factor": power_factor,
            "dc_power_scale": float(task["dc_scale"]),
            "validation_trace_peak_mw": validation_trace_peak,
            "schema_version": schema,
        }
        return key, row

    contingency_tasks: list[dict[str, Any]] = []
    for item in network_cache:
        network_name = str(item["name"])
        case_function = item["case_function"]
        native_p = item["native_p"]
        native_q = item["native_q"]
        outages = item["outages"]
        dc_buses = np.asarray(dc_bus_map[network_name], dtype=int) - 1
        if len(dc_buses) != 4 or np.any(dc_buses < 0) or np.any(dc_buses >= len(native_p)):
            raise RuntimeError(f"Invalid pre-registered DC-bus mapping for {network_name}")
        for snapshot_index, (local_day_index, fixed_day, snapshot_slot) in enumerate(snapshots):
            for method, profiles in methods.items():
                for penetration in sorted(penetrations, reverse=True):
                    key = (network_name, round(float(penetration), 12), method, snapshot_index)
                    if key not in precomputed_base_results:
                        raise RuntimeError(f"Missing precomputed intact AC dispatch for {network_name}, snapshot={snapshot_index}")
                    base_result = precomputed_base_results[key]
                    reference_buses = set(np.where(base_result["bus"][:, BUS_TYPE] == REF)[0])
                    nonreference_generators = np.asarray(
                        [generator for generator in range(len(base_result["gen"])) if int(base_result["gen"][generator, GEN_BUS]) - 1 not in reference_buses],
                        dtype=int,
                    )
                    shared_pg = base_result["gen"][:, PG].copy()
                    nonreference_set = set(nonreference_generators.tolist())
                    reference_generators = np.asarray(
                        [generator for generator in range(len(base_result["gen"])) if generator not in nonreference_set],
                        dtype=int,
                    )
                    dc_scale = float(item["dc_scale_by_penetration"][float(penetration)])
                    dc_power = profiles[local_day_index, :, snapshot_slot] * dc_scale
                    for outage in outages:
                        key = (network_name, round(float(penetration), 12), method, int(outage), int(fixed_day), int(snapshot_slot))
                        if key in completed:
                            continue
                        contingency_tasks.append(
                            {
                                "network": network_name,
                                "case_function": case_function,
                                "native_p": native_p,
                                "native_q": native_q,
                                "dc_buses": dc_buses,
                                "dc_power": dc_power,
                                "dc_scale": dc_scale,
                                "method": method,
                                "penetration": float(penetration),
                                "snapshot_index": snapshot_index,
                                "fixed_day": fixed_day,
                                "snapshot_slot": snapshot_slot,
                                "outage": int(outage),
                                "base_result": base_result,
                                "nonreference_generators": nonreference_generators,
                                "reference_generators": reference_generators,
                                "shared_pg": shared_pg,
                            }
                        )
    logger.info(
        "Experiment 18 contingency AC solves: %d pending cells with %d bounded workers",
        len(contingency_tasks),
        workers,
    )
    checkpoint_interval = max(32, workers * 8)
    prepared = [prepare_contingency_cell(task) for task in contingency_tasks]
    prepared_keys = [key for key, _ in prepared]
    prepared_payloads = [payload for _, payload in prepared]
    with ProcessPoolExecutor(max_workers=workers) as executor:
        for task, key, payload_result, prepared_payload in zip(
            contingency_tasks,
            prepared_keys,
            executor.map(_exp18_process_opf, prepared_payloads),
            prepared_payloads,
        ):
            fallback_count += int(payload_result.get("fallback_count", 0))
            result = payload_result["result"]
            if not bool(result.get("success", 0)):
                # A process-isolated restart removes shared sparse-factorization
                # state, but PYPOWER can still encounter a transient line-search
                # failure.  Retry the identical case in the parent with the
                # full in-process numerical restart chain before failing closed.
                result = solve_acopf(
                    prepared_payload["case"],
                    warm_start=task["base_result"],
                )
                fallback_count += 1
            key, row = score_contingency_cell(task, result)
            rows.append(row)
            completed.add(key)
            progress.update(1)
            if len(completed) - last_progress_log >= progress_log_step:
                last_progress_log = len(completed)
                logger.info(
                    "Experiment 18 AC panel progress: %d/%d cells (%.1f%%)",
                    len(completed),
                    total_cells,
                    100.0 * len(completed) / max(total_cells, 1),
                )
            if len(rows) % checkpoint_interval == 0:
                pd.DataFrame(rows).to_csv(checkpoint, index=False)
    progress.close()
    result_frame = pd.DataFrame(rows).sort_values(
        ["network", "day", "event_slot", "peak_dc_penetration", "method", "outage"]
    )
    expected = {
        (
            str(item["name"]),
            round(float(p), 12),
            method,
            int(outage),
            int(fixed_day),
            int(snapshot_slot),
        )
        for item in network_cache
        for p in penetrations
        for method in methods
        for outage in item["outages"]
        for _, fixed_day, snapshot_slot in snapshots
    }
    observed = {
        (
            str(row.network),
            round(float(row.peak_dc_penetration), 12),
            str(row.method),
            int(row.outage),
            int(row.day),
            int(row.event_slot),
        )
        for row in result_frame.itertuples()
    }
    if observed != expected or len(result_frame) != len(expected):
        raise RuntimeError(f"Incomplete cross-network preventive panel: {len(result_frame)}/{len(expected)}")
    result_frame.to_csv(final / "preventive_ac_cross_network_results.csv", index=False)
    summary = (
        result_frame.groupby(["network", "peak_dc_penetration", "method"], as_index=False)
        .agg(
            evaluated_outages=("outage", "nunique"),
            evaluated_snapshots=("snapshot_index", "nunique"),
            maximum_apparent_line_loading=("maximum_apparent_line_loading", "max"),
            maximum_voltage_violation_pu=("maximum_voltage_violation_pu", "max"),
            maximum_nonreference_active_plan_deviation_mw=("maximum_nonreference_active_plan_deviation_mw", "max"),
        )
    )
    summary.to_csv(final / "preventive_ac_cross_network_summary.csv", index=False)
    metadata = {
        "experiment": "cross-network AC N-1 physical admissibility audit",
        "model": "AC OPF with fixed non-reference active plan and reference-generator recourse",
        "network_count": int(len(network_cache)),
        "networks": [str(item["name"]) for item in network_cache],
        "pre_registered_dc_bus_mapping_one_based": dc_bus_map,
        "bus_mapping_basis": (
            "pre-registered generator-bus electrical-role strata selected before "
            "the locked panel; no outcome screening or loading-based placement"
        ),
        "spatial_identification": (
            "synthetic trace-to-bus benchmark because the public traces contain no "
            "utility geography; Experiment 11 supplies the 24-permutation and "
            "penetration sensitivity panel"
        ),
        "locked_snapshots": [
            {"locked_day_index": int(local_index), "day": int(day), "event_slot": int(slot)}
            for local_index, day, slot in snapshots
        ],
        "locked_snapshot_count": int(len(snapshots)),
        "locked_snapshot_rule": (
            "predeclared day indices and event-window endpoint slots; no snapshot "
            "is selected from an outage result"
        ),
        "penetrations": penetrations.tolist(),
        "methods": list(methods),
        "outages_by_network": {str(item["name"]): int(len(item["outages"])) for item in network_cache},
        "topology_connected_outages_by_network": {
            str(item["name"]): int(len(item["topology_connected_outages"]))
            for item in network_cache
        },
        "native_ac_inadmissible_connected_outages_by_network": {
            str(item["name"]): int(
                len(item["topology_connected_outages"]) - len(item["outages"])
            )
            for item in network_cache
        },
        "optimization_calls": int(len(result_frame) + len(precompute_tasks)),
        "contingency_evaluations": int(len(result_frame)),
        "intact_reference_dispatches": int(len(precompute_tasks)),
        "native_inadmissible_outages_excluded_before_workload": True,
        "validation_trace_peak_mw": validation_trace_peak,
        "load_multiplier": load_multiplier,
        "fixed_active_plan_tolerance_mw": active_plan_tolerance_mw,
        "power_factor": power_factor,
        "all_declared_ac_admissible_nonislanding_outages_evaluated": True,
        "ac_admissibility_rule": (
            "connected topology plus a native-case fixed-active-plan AC-OPF "
            "with apparent-power and voltage limits; the rule is evaluated "
            "before workload profiles and is independent of locked outcomes"
        ),
        "shared_active_plan": True,
        "active_plan_reference": "intact AC dispatch; non-reference active outputs are fixed for every contingency",
        "test_outcomes_used_for_scaling": False,
        "solver": "PYPOWER AC OPF intact reference plus AC-OPF contingencies with fixed non-reference active outputs and reference-generator recourse",
        "solver_fallback": "MIPS default, deterministic PIPS safeguarded fallback (OPF_ALG=565), PF-initialized PIPS restart, and process-isolated numerical retry; the fixed active-plan tolerance is explicitly certified and no network limit is relaxed",
        "solver_fallback_calls": int(fallback_count),
        "isolated_solver_calls": int(isolated_solver_calls),
        "scope": "preventive AC N-1 fixed-active-plan feasibility certificate over multiple locked snapshots with reference-generator loss recourse",
        "ac_limits_enforced": True,
        "diagnostics_reported": [
            "apparent line loading",
            "voltage-limit deviation",
            "non-reference active-generation recourse",
        ],
    }
    write_json(final / "experiment_metadata.json", metadata)
    plot_exp18_preventive_ac_panel(result_frame, folder / "figures", cfg)
    logger.info(
        "Experiment 18 complete: %d AC N-1 outcomes across %d networks and %d locked snapshots",
        len(result_frame),
        len(network_cache),
        len(snapshots),
    )
