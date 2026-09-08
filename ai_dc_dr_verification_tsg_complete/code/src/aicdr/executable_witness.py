"""Declaration-only runtime-complete witness and common network settlement.

This module closes the identity gap between the indexed workload model and the
network/payment evidence.  It reads only submit-time fields from the immutable
Exp19 submission witness.  Every submitted job is assigned a fixed contiguous
runtime block at its declared GPU nameplate.  The baseline and event response
are both finite exact start-time enumerations; neither uses execution telemetry
or a fitted aggregate target.
"""

from __future__ import annotations

import hashlib
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .optimization import build_n1_security_factors, power_system_from_ppc, solve_n1_sced
from .progress import progress as tqdm
from .utils import write_json


def _array_digest(*arrays: np.ndarray) -> str:
    digest = hashlib.sha256()
    for array in arrays:
        value = np.ascontiguousarray(array)
        digest.update(str(value.dtype).encode("utf-8"))
        digest.update(str(value.shape).encode("utf-8"))
        digest.update(value.tobytes())
    return digest.hexdigest()


def _aggregate_blocks(
    starts: np.ndarray,
    runtime_slots: np.ndarray,
    region: np.ndarray,
    power_mw: np.ndarray,
    n_regions: int,
    n_slots: int,
    dt_h: float,
) -> np.ndarray:
    """Aggregate fixed-rate contiguous blocks without slot-level heuristics."""
    delta = np.zeros((n_regions, n_slots + 1), dtype=float)
    np.add.at(delta, (region, starts), power_mw)
    np.add.at(delta, (region, starts + runtime_slots), -power_mw)
    # A block ending exactly at the horizon is represented by the sentinel
    # column and therefore does not require a special-case truncation.
    return np.cumsum(delta[:, :-1], axis=1) * float(dt_h)


def _select_exact_starts(
    submit_slot: np.ndarray,
    runtime_slots: np.ndarray,
    queue_buffer_slots: int,
    energy_per_slot_mwh: np.ndarray,
    event_prefix: np.ndarray,
    waiting_cost_per_mwh_slot: float,
    event_price_per_mwh: float,
    *,
    event_price_enabled: bool,
) -> tuple[np.ndarray, np.ndarray]:
    """Enumerate every declared start and return the exact minimum per job."""
    selected = np.empty(len(submit_slot), dtype=np.int64)
    selected_cost = np.empty(len(submit_slot), dtype=float)
    for index, (release, runtime, energy_slot) in enumerate(
        zip(submit_slot, runtime_slots, energy_per_slot_mwh)
    ):
        first = int(release)
        last = int(release + queue_buffer_slots)
        candidates = np.arange(first, last + 1, dtype=np.int64)
        delay = candidates - first
        event_intervals = event_prefix[candidates + int(runtime)] - event_prefix[candidates]
        cost = float(waiting_cost_per_mwh_slot) * float(energy_slot) * delay
        if event_price_enabled:
            cost = cost + float(event_price_per_mwh) * float(energy_slot) * event_intervals
        # np.argmin is deterministic and returns the earliest candidate under
        # a tie, which is part of the declared policy and not a post-solve rule.
        choice = int(np.argmin(cost))
        selected[index] = int(candidates[choice])
        selected_cost[index] = float(cost[choice])
    return selected, selected_cost


def _load_common_network_case(cfg: dict[str, Any]):
    from pypower.case24_ieee_rts import case24_ieee_rts

    system = power_system_from_ppc(case24_ieee_rts())
    security = build_n1_security_factors(system)
    buses = np.asarray(
        cfg["experiments"].get("coupled_network_buses_one_based", [3, 8, 15, 21]),
        dtype=int,
    ) - 1
    if len(buses) != int(cfg["project"]["number_of_regions"]):
        raise ValueError("Common witness bus map must contain one bus per workload region")
    if np.any(buses < 0) or np.any(buses >= len(system.bus)) or len(np.unique(buses)) != len(buses):
        raise ValueError("Common witness bus map contains an invalid or repeated RTS-24 bus")
    return system, security, buses


def run_exp27_executable_common_witness(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
) -> None:
    """Build the common declaration-only witness and replay it through N-1 value."""
    folder = root / "experiments/exp27_executable_common_witness"
    final = folder / "results/final"
    figures = folder / "figures"
    final.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    logger.info("Exp27 executable common witness [0%%]")

    source_path = root / "experiments/exp19_job_level_counterfactual/results/final/job_level_counterfactual_solution.npz"
    source_meta_path = root / "experiments/exp19_job_level_counterfactual/results/final/experiment_metadata.json"
    if not source_path.exists() or not source_meta_path.exists():
        raise FileNotFoundError(f"Exp19 declaration witness is missing: {source_path}")
    source_meta = json.loads(source_meta_path.read_text(encoding="utf-8"))
    stored = np.load(source_path, allow_pickle=False)
    # Only submit-time declaration fields are read.  In particular, the
    # observed execution arrays present in the archival NPZ are never accessed.
    submit_slot = np.asarray(stored["submit_slot"], dtype=np.int64)
    deadline_slot = np.asarray(stored["deadline_slot"], dtype=np.int64)
    region = np.asarray(stored["region"], dtype=np.int64)
    requested_gpus = np.asarray(stored["requested_gpus"], dtype=float)
    per_gpu_cap_mw = float(np.asarray(stored["per_gpu_power_cap_mw"], dtype=float).reshape(-1)[0])
    source_submission_digest = str(np.asarray(stored["submission_digest"]).reshape(-1)[0])
    n_regions = int(cfg["project"]["number_of_regions"])
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    slots_per_day = int(cfg["project"]["slots_per_day"])
    queue_buffer_slots = int(cfg["experiments"].get("job_level_submission_buffer_slots", 96))
    if queue_buffer_slots <= 0:
        raise ValueError("A positive declaration-only queue allowance is required")
    if not (len(submit_slot) == len(deadline_slot) == len(region) == len(requested_gpus)):
        raise ValueError("Exp19 declaration arrays have inconsistent lengths")
    if np.any(region < 0) or np.any(region >= n_regions) or np.any(requested_gpus <= 0):
        raise ValueError("The declaration witness contains invalid region or GPU fields")
    runtime_slots = deadline_slot - submit_slot - queue_buffer_slots
    if np.any(runtime_slots < 1):
        raise ValueError("A declaration window does not contain one complete runtime block")
    horizon_slots = int(max(deadline_slot.max(), (submit_slot + queue_buffer_slots + runtime_slots).max()))
    if np.any(submit_slot < 0) or np.any(deadline_slot > horizon_slots):
        raise ValueError("Declaration support lies outside the common witness horizon")
    power_mw = requested_gpus * per_gpu_cap_mw
    energy_per_slot_mwh = power_mw * dt_h
    runtime_energy_mwh = energy_per_slot_mwh * runtime_slots
    event_slots = np.asarray(list(map(int, cfg["market"]["event_slots"])), dtype=int)
    if np.any(event_slots < 0) or np.any(event_slots >= slots_per_day):
        raise ValueError("Event slots must lie inside one declared day")
    event_mask = np.zeros(horizon_slots + 1, dtype=np.int8)
    event_mask[np.asarray([t for t in range(horizon_slots + 1) if t % slots_per_day in set(event_slots)], dtype=int)] = 1
    event_prefix = np.concatenate([[0], np.cumsum(event_mask, dtype=np.int64)])
    waiting_cost = float(cfg["workload"]["waiting_cost_per_mwh_slot"][-1])
    event_price = float(cfg["market"]["default_dr_price_per_mwh"])

    baseline_starts, baseline_cost = _select_exact_starts(
        submit_slot,
        runtime_slots,
        queue_buffer_slots,
        energy_per_slot_mwh,
        event_prefix,
        waiting_cost,
        event_price,
        event_price_enabled=False,
    )
    response_starts, response_cost = _select_exact_starts(
        submit_slot,
        runtime_slots,
        queue_buffer_slots,
        energy_per_slot_mwh,
        event_prefix,
        waiting_cost,
        event_price,
        event_price_enabled=True,
    )
    baseline_profile = _aggregate_blocks(
        baseline_starts, runtime_slots, region, power_mw, n_regions, horizon_slots, dt_h
    )
    response_profile = _aggregate_blocks(
        response_starts, runtime_slots, region, power_mw, n_regions, horizon_slots, dt_h
    )
    baseline_energy_residual = baseline_profile.sum() - runtime_energy_mwh.sum()
    response_energy_residual = response_profile.sum() - runtime_energy_mwh.sum()
    site_capacity_mw = float(cfg["project"]["flexible_capacity_mw"])
    minimum_baseline_slack_mwh = float(np.min(site_capacity_mw * dt_h - baseline_profile))
    minimum_response_slack_mwh = float(np.min(site_capacity_mw * dt_h - response_profile))
    if max(abs(baseline_energy_residual), abs(response_energy_residual)) > 1.0e-10:
        raise RuntimeError("Runtime-complete witness does not conserve declared job energy")
    if min(minimum_baseline_slack_mwh, minimum_response_slack_mwh) < -1.0e-10:
        raise RuntimeError("Runtime-complete witness exceeds a predeclared regional capacity row")
    if np.any(baseline_starts < submit_slot) or np.any(response_starts < submit_slot):
        raise RuntimeError("A witness start precedes its submit-time release")
    if np.any(baseline_starts + runtime_slots > deadline_slot) or np.any(response_starts + runtime_slots > deadline_slot):
        raise RuntimeError("A witness block crosses its declared deadline")
    event_indices = np.asarray(
        [t for t in range(horizon_slots) if t % slots_per_day in set(event_slots)], dtype=np.int64
    )
    event_reduction_mwh = float(baseline_profile[:, event_indices].sum() - response_profile[:, event_indices].sum())
    event_response_delay_mwh = float(np.maximum(response_profile[:, event_indices] - baseline_profile[:, event_indices], 0.0).sum())
    witness_digest = _array_digest(
        submit_slot,
        deadline_slot,
        runtime_slots,
        region,
        requested_gpus,
        baseline_starts,
        response_starts,
        baseline_profile,
        response_profile,
    )
    np.savez_compressed(
        final / "runtime_complete_witness.npz",
        submit_slot=submit_slot,
        deadline_slot=deadline_slot,
        runtime_slots=runtime_slots,
        region=region,
        requested_gpus=requested_gpus,
        per_gpu_power_cap_mw=np.asarray([per_gpu_cap_mw]),
        runtime_energy_mwh=runtime_energy_mwh,
        baseline_start_slot=baseline_starts,
        response_start_slot=response_starts,
        baseline_mwh=baseline_profile,
        counterfactual_mwh=response_profile,
        source_submission_digest=np.asarray([source_submission_digest]),
        witness_digest=np.asarray([witness_digest]),
    )
    job_summary = pd.DataFrame(
        {
            "job_index": np.arange(len(submit_slot), dtype=np.int64),
            "region": region,
            "requested_gpus": requested_gpus,
            "submit_slot": submit_slot,
            "deadline_slot": deadline_slot,
            "runtime_slots": runtime_slots,
            "runtime_energy_mwh": runtime_energy_mwh,
            "baseline_start_slot": baseline_starts,
            "counterfactual_start_slot": response_starts,
            "baseline_event_slots": event_prefix[baseline_starts + runtime_slots] - event_prefix[baseline_starts],
            "counterfactual_event_slots": event_prefix[response_starts + runtime_slots] - event_prefix[response_starts],
            "baseline_objective_usd": baseline_cost,
            "counterfactual_objective_usd": response_cost,
        }
    )
    job_summary.to_csv(final / "job_level_runtime_summary.csv", index=False)
    summary = pd.DataFrame(
        [
            {"metric": "submitted_jobs", "value": len(submit_slot), "unit": "jobs"},
            {"metric": "runtime_slots_min", "value": int(runtime_slots.min()), "unit": "slots"},
            {"metric": "runtime_slots_median", "value": float(np.median(runtime_slots)), "unit": "slots"},
            {"metric": "runtime_slots_p90", "value": float(np.quantile(runtime_slots, 0.90)), "unit": "slots"},
            {"metric": "runtime_slots_max", "value": int(runtime_slots.max()), "unit": "slots"},
            {"metric": "declared_runtime_energy_mwh", "value": float(runtime_energy_mwh.sum()), "unit": "MWh"},
            {"metric": "baseline_energy_residual_mwh", "value": float(baseline_energy_residual), "unit": "MWh"},
            {"metric": "counterfactual_energy_residual_mwh", "value": float(response_energy_residual), "unit": "MWh"},
            {"metric": "baseline_minimum_site_capacity_slack_mwh", "value": minimum_baseline_slack_mwh, "unit": "MWh"},
            {"metric": "counterfactual_minimum_site_capacity_slack_mwh", "value": minimum_response_slack_mwh, "unit": "MWh"},
            {"metric": "baseline_event_energy_mwh", "value": float(baseline_profile[:, event_indices].sum()), "unit": "MWh"},
            {"metric": "counterfactual_event_energy_mwh", "value": float(response_profile[:, event_indices].sum()), "unit": "MWh"},
            {"metric": "event_reduction_mwh", "value": event_reduction_mwh, "unit": "MWh"},
            {"metric": "event_response_delay_mwh", "value": event_response_delay_mwh, "unit": "MWh"},
            {"metric": "baseline_jobs_with_one_contiguous_block", "value": len(baseline_starts), "unit": "jobs"},
            {"metric": "counterfactual_jobs_with_one_contiguous_block", "value": len(response_starts), "unit": "jobs"},
        ]
    )
    summary.to_csv(final / "common_witness_summary.csv", index=False)
    logger.info("Exp27 declaration witness [35%%]: jobs=%d, runtime energy=%.3f MWh", len(submit_slot), runtime_energy_mwh.sum())

    # The network replay is evaluated on exactly the same response and baseline
    # arrays saved above.  The locked-day index is taken from the locked Exp2
    # panel so the scope is an identified study cohort rather than an arbitrary
    # screenshot.  No risk-profile or telemetry array enters this computation.
    test_profile_path = root / "experiments/exp2_baseline_verification/results/intermediate/test_profiles.npz"
    if not test_profile_path.exists():
        raise FileNotFoundError(f"Locked day index is missing: {test_profile_path}")
    test_days = np.asarray(np.load(test_profile_path, allow_pickle=False)["days"], dtype=int)
    network_days = [int(day) for day in test_days if int(day) * slots_per_day + int(event_slots.max()) < horizon_slots]
    if not network_days:
        raise RuntimeError("No locked days fit inside the runtime-complete witness horizon")
    system, security, buses = _load_common_network_case(cfg)
    base_load = np.asarray(system.bus[:, 2], dtype=float) * float(cfg["experiments"].get("n1_load_multiplier", 0.9))
    fixed_load_mw = float(cfg["project"]["fixed_facility_load_mw"])
    segment_count = int(cfg["experiments"].get("coupled_network_generator_segments", 4))
    network_tasks = [(int(day), int(slot)) for day in network_days for slot in event_slots]

    def solve_network(task: tuple[int, int]) -> dict[str, Any]:
        day, slot = task
        absolute_slot = day * slots_per_day + slot
        baseline_mw = baseline_profile[:, absolute_slot] / dt_h
        response_mw = response_profile[:, absolute_slot] / dt_h
        baseline_load = base_load.copy()
        response_load = base_load.copy()
        baseline_load[buses] += fixed_load_mw + baseline_mw
        response_load[buses] += fixed_load_mw + response_mw
        baseline = solve_n1_sced(system, baseline_load, segment_count, security_factors=security)
        response = solve_n1_sced(system, response_load, segment_count, security_factors=security)
        if not baseline.success or not response.success:
            raise RuntimeError(f"Common witness RTS-24 solve failed at day={day}, slot={slot}")
        nodal_credit = float(np.dot(baseline_mw - response_mw, response.lmp_per_mwh[buses]) * dt_h)
        value = float((baseline.objective - response.objective) * dt_h)
        return {
            "day": day,
            "slot": slot,
            "absolute_slot": absolute_slot,
            "baseline_witness_profile_sha256": witness_digest,
            "counterfactual_witness_profile_sha256": witness_digest,
            "baseline_total_flexible_mw": float(baseline_mw.sum()),
            "counterfactual_total_flexible_mw": float(response_mw.sum()),
            "baseline_secure_cost_usd_per_interval": float(baseline.objective * dt_h),
            "counterfactual_secure_cost_usd_per_interval": float(response.objective * dt_h),
            "network_value_usd": value,
            "nodal_meter_credit_usd": nodal_credit,
            "payable_settlement_usd": max(0.0, value),
            "baseline_max_loading_pu": float(baseline.max_loading),
            "counterfactual_max_loading_pu": float(response.max_loading),
            "baseline_max_postcontingency_loading_pu": float(baseline.max_post_contingency_loading),
            "counterfactual_max_postcontingency_loading_pu": float(response.max_post_contingency_loading),
            "finite_n1_contingencies": int(security[3]),
            "solver_success": True,
        }

    workers = int(cfg["experiments"].get("common_witness_network_workers", 4))
    if not 1 <= workers <= 20:
        raise ValueError("common_witness_network_workers must be between 1 and 20")
    network_rows: list[dict[str, Any]] = []
    progress = tqdm(total=len(network_tasks), desc="Exp27 common witness RTS-24 settlement")
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for row in executor.map(solve_network, network_tasks):
            network_rows.append(row)
            progress.update(1)
    progress.close()
    network = pd.DataFrame(network_rows).sort_values(["day", "slot"]).reset_index(drop=True)
    network.to_csv(final / "common_witness_settlement.csv", index=False)
    if not network["solver_success"].all() or network["finite_n1_contingencies"].ne(int(security[3])).any():
        raise RuntimeError("Common witness settlement contains an incomplete N-1 replay")
    logger.info("Exp27 common witness network/settlement [85%%]: %d cells, %d N-1 outages/cell", len(network), int(security[3]))

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    representative_day = network_days[0]
    day_slice = slice(representative_day * slots_per_day, (representative_day + 1) * slots_per_day)
    x = np.arange(slots_per_day)
    fig, ax = plt.subplots(figsize=(7.1, 3.45), constrained_layout=True)
    ax.plot(x, baseline_profile[:, day_slice].sum(axis=0) / dt_h, color="#0072B2", linewidth=1.8, label="Declaration baseline")
    ax.plot(x, response_profile[:, day_slice].sum(axis=0) / dt_h, color="#D55E00", linewidth=1.8, label="Event response")
    ax.axvspan(int(event_slots.min()), int(event_slots.max()) + 1, color="#009E73", alpha=0.12, label="Declared event window")
    ax.set_xlabel("15-minute interval within representative locked day")
    ax.set_ylabel("Flexible workload power (MW)")
    ax.set_title("Runtime-complete workload witness used by network settlement")
    ax.set_xlim(0, slots_per_day - 1)
    ax.grid(axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False, fontsize=8)
    for suffix in ("png", "pdf"):
        fig.savefig(figures / f"fig28_common_executable_witness.{suffix}", dpi=320, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    metadata = {
        "experiment": "declaration-only runtime-complete common workload witness",
        "schema_version": 1,
        "source_exp19": "experiments/exp19_job_level_counterfactual/results/final/job_level_counterfactual_solution.npz",
        "source_submission_digest": source_submission_digest,
        "source_exp19_metadata_digest": hashlib.sha256(source_meta_path.read_bytes()).hexdigest(),
        "submitted_jobs": int(len(submit_slot)),
        "horizon_slots": horizon_slots,
        "queue_buffer_slots": queue_buffer_slots,
        "runtime_definition": "deadline_slot - submit_slot - fixed declaration queue allowance; one contiguous block at requested_gpus times the predeclared per-GPU nameplate",
        "runtime_complete": True,
        "runtime_energy_entitlement_mwh": float(runtime_energy_mwh.sum()),
        "observed_execution_telemetry_used": False,
        "telemetry_fields_used_in_decision": [],
        "declaration_fields_used": ["submit_slot", "deadline_slot", "region", "requested_gpus", "per_gpu_power_cap_mw", "submission_digest"],
        "baseline_policy": "exact earliest-start member of the declaration-feasible contiguous-block set",
        "response_policy": "exact enumeration of every declaration-feasible contiguous start with predeclared waiting and event-tariff costs",
        "event_slots": event_slots.tolist(),
        "event_tariff_per_mwh": event_price,
        "waiting_cost_per_mwh_slot": waiting_cost,
        "capacity_mw_per_region": site_capacity_mw,
        "baseline_minimum_site_capacity_slack_mwh": minimum_baseline_slack_mwh,
        "counterfactual_minimum_site_capacity_slack_mwh": minimum_response_slack_mwh,
        "event_reduction_mwh": event_reduction_mwh,
        "witness_digest": witness_digest,
        "profile_identity_asserted": True,
        "network_settlement": {
            "network_case": "IEEE RTS-24 (PYPOWER case24_ieee_rts)",
            "network_buses_one_based": (buses + 1).tolist(),
            "locked_days": network_days,
            "replay_cells": int(len(network)),
            "generator_segments": segment_count,
            "finite_nonislanding_n1_contingencies_per_cell": int(security[3]),
            "base_load_multiplier": float(cfg["experiments"].get("n1_load_multiplier", 0.9)),
            "fixed_facility_load_mw_per_bus": fixed_load_mw,
            "profile_source": "runtime_complete_witness.npz baseline_mwh and counterfactual_mwh",
            "settlement_source_digest": witness_digest,
            "all_solver_cells_successful": bool(network["solver_success"].all()),
        },
        "files": {
            "witness": "runtime_complete_witness.npz",
            "job_level": "job_level_runtime_summary.csv",
            "summary": "common_witness_summary.csv",
            "settlement": "common_witness_settlement.csv",
            "figure": "fig28_common_executable_witness.pdf",
        },
    }
    write_json(final / "experiment_metadata.json", metadata)
    (folder / "README.md").write_text(
        """# Experiment 27: executable common workload witness

This experiment reads only submit-time fields from the immutable Exp19
submission ledger. Every job receives a fixed contiguous runtime block at its
declared GPU nameplate. Baseline and event response starts are obtained by
finite exact enumeration over the declaration-feasible queue allowance. The
saved arrays are then reused verbatim for the RTS-24 DC N-1 network valuation
and settlement replay. Execution telemetry, aggregate risk targets, and
payment-selected profiles are not inputs.

The final directory contains the NPZ witness, job-level runtime certificate,
common witness summary, settlement replay, metadata, and publication figure.
""",
        encoding="utf-8",
    )
    logger.info("Exp27 executable common witness [100%%]: PASS; digest=%s", witness_digest[:12])
