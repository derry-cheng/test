"""Declaration-only runtime-complete witness and common network settlement.

This module closes the identity gap between the indexed workload model and the
network/payment evidence.  It reads only submit-time fields from the immutable
Exp19 submission witness.  Every submitted job is assigned one fixed
contiguous runtime block.  The primary profile is the declared GPU-nameplate
upper-capacity commitment; a calibrated central-energy profile is materialized
on the identical blocks so the two physical meanings cannot be conflated.  The
baseline and event response are both finite exact start-time enumerations;
neither uses execution telemetry or a fitted aggregate target.
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
from .coupling_invariant import validate_job_network_coupling
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


def _service_window_from_runtime_blocks(
    starts: np.ndarray,
    runtime_slots: np.ndarray,
    submit_slot: np.ndarray,
    deadline_slot: np.ndarray,
    energy_per_slot_mwh: np.ndarray,
) -> np.ndarray:
    """Materialize one indexed service vector for a contiguous runtime witness.

    The vector follows the canonical Exp19 ordering: each job owns the complete
    ``[submit_slot, deadline_slot)`` window, with zero service outside its
    selected runtime block.  Keeping the queue allowance in the window makes
    the declaration-only certificate directly comparable with the indexed
    job/network invariant used by Exp22 and Exp26.
    """
    widths = np.asarray(deadline_slot, dtype=np.int64) - np.asarray(submit_slot, dtype=np.int64)
    offsets = np.concatenate(([0], np.cumsum(widths, dtype=np.int64)))
    service = np.zeros(int(offsets[-1]), dtype=float)
    for index, (start, release, runtime, offset) in enumerate(
        zip(starts, submit_slot, runtime_slots, offsets[:-1])
    ):
        local_start = int(start) - int(release)
        begin = int(offset) + local_start
        end = begin + int(runtime)
        if local_start < 0 or end > int(offset + widths[index]):
            raise ValueError("runtime block falls outside its indexed declaration window")
        service[begin:end] = float(energy_per_slot_mwh[index])
    return service


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
    """Enumerate every declared start and return the exact minimum per job.

    The waiting term is the block integral in Eq. (6), rather than a charge
    on the block start alone.  For a start delay ``d`` and runtime ``r`` the
    number of delayed service slot-units is
    ``sum_{k=0}^{r-1}(d+k) = r*d + r*(r-1)/2``.  The triangular term is
    constant over candidate starts for one job but is retained in the saved
    objective certificate so that the code and the mathematical definition
    have identical units.
    """
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
        runtime_int = int(runtime)
        block_delay_slot_units = (
            float(runtime_int) * delay
            + 0.5 * float(runtime_int) * float(max(runtime_int - 1, 0))
        )
        cost = (
            float(waiting_cost_per_mwh_slot)
            * float(energy_slot)
            * block_delay_slot_units
        )
        if event_price_enabled:
            cost = cost + float(event_price_per_mwh) * float(energy_slot) * event_intervals
        # np.argmin is deterministic and returns the earliest candidate under
        # a tie, which is part of the declared policy and not a post-solve rule.
        choice = int(np.argmin(cost))
        selected[index] = int(candidates[choice])
        selected_cost[index] = float(cost[choice])
    return selected, selected_cost


def _select_risk_aligned_starts(
    submit_slot: np.ndarray,
    runtime_slots: np.ndarray,
    region: np.ndarray,
    queue_buffer_slots: int,
    energy_per_slot_mwh: np.ndarray,
    event_prefix: np.ndarray,
    risk_price_by_region_slot: np.ndarray,
    waiting_cost_per_mwh_slot: float,
    event_price_per_mwh: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Enumerate an executable realization of a frozen aggregate risk profile.

    The risk fit is converted once into a fixed regional slot price
    ``pi_{r,t}`` (the declared event tariff times the normalized flexible
    demand).  Each job then chooses the minimum of a finite contiguous-start
    set under waiting, event, and ``pi`` costs.  This is an exact separable
    realization of the frozen contract; it never optimizes against the locked
    response profile or uses an outcome-dependent rule.
    """
    submit_slot = np.asarray(submit_slot, dtype=np.int64)
    runtime_slots = np.asarray(runtime_slots, dtype=np.int64)
    region = np.asarray(region, dtype=np.int64)
    energy_per_slot_mwh = np.asarray(energy_per_slot_mwh, dtype=float)
    risk_price_by_region_slot = np.asarray(risk_price_by_region_slot, dtype=float)
    selected = np.empty(len(submit_slot), dtype=np.int64)
    selected_cost = np.empty(len(submit_slot), dtype=float)
    if risk_price_by_region_slot.ndim != 2:
        raise ValueError("risk_price_by_region_slot must be region by absolute slot")
    for index, (release, runtime, region_index, energy_slot) in enumerate(
        zip(submit_slot, runtime_slots, region, energy_per_slot_mwh)
    ):
        first = int(release)
        last = int(release + queue_buffer_slots)
        candidates = np.arange(first, last + 1, dtype=np.int64)
        runtime_int = int(runtime)
        if np.any(candidates + runtime_int >= len(event_prefix)):
            raise ValueError("risk-aligned start enumeration exceeds the event horizon")
        delay = candidates - first
        delayed_slot_units = (
            float(runtime_int) * delay
            + 0.5 * float(runtime_int) * float(max(runtime_int - 1, 0))
        )
        event_intervals = event_prefix[candidates + runtime_int] - event_prefix[candidates]
        risk_block_cost = np.asarray(
            [
                float(risk_price_by_region_slot[int(region_index), start : start + runtime_int].sum())
                for start in candidates.tolist()
            ],
            dtype=float,
        )
        cost = (
            float(waiting_cost_per_mwh_slot)
            * float(energy_slot)
            * delayed_slot_units
            + float(event_price_per_mwh)
            * float(energy_slot)
            * event_intervals
            + float(energy_slot) * risk_block_cost
        )
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
    """Build the common declaration-only witness and replay it through N-1 value.

    Settlement is evaluated for every slot of each locked day.  Event-slot
    rows remain flagged in the ledger for the event-specific analysis, while
    the signed full-day replay prevents clipping or window selection from
    changing the payment total.
    """
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
    if "declared_job_energy_mwh" not in stored.files:
        raise ValueError(
            "Exp19 witness must expose the calibrated central declared energy "
            "for the runtime-complete capacity certificate"
        )
    declared_job_energy_mwh = np.asarray(stored["declared_job_energy_mwh"], dtype=float)
    declared_job_energy_upper_mwh = np.asarray(
        stored["declared_job_energy_upper_mwh"]
        if "declared_job_energy_upper_mwh" in stored.files
        else requested_gpus
        * float(np.asarray(stored["per_gpu_power_cap_mw"], dtype=float).reshape(-1)[0])
        * (np.asarray(stored["deadline_slot"], dtype=np.int64) - np.asarray(stored["submit_slot"], dtype=np.int64) - int(cfg["experiments"].get("job_level_submission_buffer_slots", 96)))
        * float(cfg["project"]["interval_minutes"])
        / 60.0,
        dtype=float,
    )
    per_gpu_cap_mw = float(np.asarray(stored["per_gpu_power_cap_mw"], dtype=float).reshape(-1)[0])
    source_submission_digest = str(np.asarray(stored["submission_digest"]).reshape(-1)[0])
    n_regions = int(cfg["project"]["number_of_regions"])
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    slots_per_day = int(cfg["project"]["slots_per_day"])
    queue_buffer_slots = int(cfg["experiments"].get("job_level_submission_buffer_slots", 96))
    if queue_buffer_slots <= 0:
        raise ValueError("A positive declaration-only queue allowance is required")
    if not (
        len(submit_slot)
        == len(deadline_slot)
        == len(region)
        == len(requested_gpus)
        == len(declared_job_energy_mwh)
        == len(declared_job_energy_upper_mwh)
    ):
        raise ValueError("Exp19 declaration arrays have inconsistent lengths")
    if (
        np.any(region < 0)
        or np.any(region >= n_regions)
        or np.any(requested_gpus <= 0)
        or np.any(~np.isfinite(declared_job_energy_mwh))
        or np.any(~np.isfinite(declared_job_energy_upper_mwh))
        or np.any(declared_job_energy_mwh < -1.0e-12)
        or np.any(declared_job_energy_upper_mwh < -1.0e-12)
    ):
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
    nameplate_upper_residual = declared_job_energy_upper_mwh - runtime_energy_mwh
    if np.max(np.abs(nameplate_upper_residual)) > 1.0e-10:
        raise RuntimeError(
            "Exp19 nameplate upper-energy field is inconsistent with the fixed "
            "GPU cap and runtime definition"
        )
    if np.any(declared_job_energy_mwh > declared_job_energy_upper_mwh + 1.0e-10):
        raise RuntimeError("A central declared energy exceeds its nameplate upper bound")
    central_energy_per_slot_mwh = declared_job_energy_mwh / runtime_slots
    central_power_mw = central_energy_per_slot_mwh / dt_h
    event_slots = np.asarray(list(map(int, cfg["market"]["event_slots"])), dtype=int)
    if np.any(event_slots < 0) or np.any(event_slots >= slots_per_day):
        raise ValueError("Event slots must lie inside one declared day")
    event_mask = np.zeros(horizon_slots + 1, dtype=np.int8)
    event_mask[np.asarray([t for t in range(horizon_slots + 1) if t % slots_per_day in set(event_slots)], dtype=int)] = 1
    event_prefix = np.concatenate([[0], np.cumsum(event_mask, dtype=np.int64)])
    waiting_cost = float(cfg["workload"]["waiting_cost_per_mwh_slot"][-1])
    event_price = float(cfg["market"]["default_dr_price_per_mwh"])
    test_profile_path = root / "experiments/exp2_baseline_verification/results/intermediate/test_profiles.npz"
    if not test_profile_path.exists():
        raise FileNotFoundError(f"Locked risk profile is missing: {test_profile_path}")
    with np.load(test_profile_path, allow_pickle=False) as risk_store:
        risk_methods = [str(value) for value in risk_store["methods"].tolist()]
        if "Risk-Constrained Convex Verifier" not in risk_methods:
            raise RuntimeError("Exp2 profile cache does not contain the declared risk verifier")
        risk_index = risk_methods.index("Risk-Constrained Convex Verifier")
        risk_days = np.asarray(risk_store["days"], dtype=np.int64)
        locked_risk_profile = np.asarray(
            risk_store["baselines"][:, risk_index], dtype=float
        )
    if locked_risk_profile.shape[1:] != (n_regions, slots_per_day):
        raise ValueError("Risk profile dimensions do not match the declared regional clock")
    if len(risk_days) != locked_risk_profile.shape[0]:
        raise ValueError("Risk profile day index and profile count disagree")
    # A fixed scale transformation makes the aggregate statistical contract
    # commensurate with the submit-time declaration envelope before it is
    # priced. Exp2 reports a four-region facility profile on its own workload
    # scale, whereas the indexed witness has a deliberately predeclared
    # nameplate. The conversion therefore uses only declarations submitted on
    # the locked days; no selected start, completion, or telemetry value enters
    # the scale. The flexible component is then normalized by its largest
    # locked value for the fixed-price realization below. Both the raw profile
    # and the scaled executable contract are retained and hashed.
    risk_flexible_target = np.maximum(
        locked_risk_profile - float(cfg["project"]["fixed_facility_load_mw"]), 0.0
    )
    locked_submission_mask = np.isin(
        submit_slot // slots_per_day, risk_days.astype(np.int64)
    )
    locked_declared_upper_energy_mwh = float(
        declared_job_energy_upper_mwh[locked_submission_mask].sum()
    )
    locked_declared_central_energy_mwh = float(
        declared_job_energy_mwh[locked_submission_mask].sum()
    )
    risk_flexible_target_energy_mwh = float(risk_flexible_target.sum() * dt_h)
    if risk_flexible_target_energy_mwh <= 0.0:
        raise RuntimeError("The locked risk profile has no positive flexible energy")
    risk_contract_scale_upper = (
        locked_declared_upper_energy_mwh / risk_flexible_target_energy_mwh
    )
    risk_contract_scale_central = (
        locked_declared_central_energy_mwh / risk_flexible_target_energy_mwh
    )
    risk_contract_profile_upper = (
        float(cfg["project"]["fixed_facility_load_mw"])
        + risk_contract_scale_upper * risk_flexible_target
    )
    risk_contract_profile_central = (
        float(cfg["project"]["fixed_facility_load_mw"])
        + risk_contract_scale_central * risk_flexible_target
    )
    risk_contract_flexible_upper = np.maximum(
        risk_contract_profile_upper
        - float(cfg["project"]["fixed_facility_load_mw"]),
        0.0,
    )
    risk_target_scale_mw = max(float(np.max(risk_contract_flexible_upper)), 1.0e-12)
    risk_price_by_region_slot = np.zeros((n_regions, horizon_slots), dtype=float)
    for day, target_day in zip(risk_days.tolist(), risk_contract_flexible_upper):
        start = int(day) * slots_per_day
        stop = start + slots_per_day
        if start < 0 or stop > horizon_slots:
            raise ValueError("A locked risk profile day exceeds the runtime witness horizon")
        risk_price_by_region_slot[:, start:stop] = (
            float(event_price) * target_day / risk_target_scale_mw
        )

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
    risk_aligned_starts, risk_aligned_cost = _select_risk_aligned_starts(
        submit_slot,
        runtime_slots,
        region,
        queue_buffer_slots,
        energy_per_slot_mwh,
        event_prefix,
        risk_price_by_region_slot,
        waiting_cost,
        event_price,
    )
    baseline_profile = _aggregate_blocks(
        baseline_starts, runtime_slots, region, power_mw, n_regions, horizon_slots, dt_h
    )
    response_profile = _aggregate_blocks(
        response_starts, runtime_slots, region, power_mw, n_regions, horizon_slots, dt_h
    )
    risk_aligned_profile = _aggregate_blocks(
        risk_aligned_starts,
        runtime_slots,
        region,
        power_mw,
        n_regions,
        horizon_slots,
        dt_h,
    )
    # The primary witness is a conservative nameplate-capacity commitment.  A
    # second profile uses the calibrated central declaration energy from Exp19
    # on the *same* start blocks.  Keeping both profiles in the artifact makes
    # the physical energy semantics explicit and prevents a nameplate upper
    # bound from being presented as measured consumption.
    central_baseline_profile = _aggregate_blocks(
        baseline_starts,
        runtime_slots,
        region,
        central_power_mw,
        n_regions,
        horizon_slots,
        dt_h,
    )
    central_response_profile = _aggregate_blocks(
        response_starts,
        runtime_slots,
        region,
        central_power_mw,
        n_regions,
        horizon_slots,
        dt_h,
    )
    baseline_service_window = _service_window_from_runtime_blocks(
        baseline_starts,
        runtime_slots,
        submit_slot,
        deadline_slot,
        energy_per_slot_mwh,
    )
    response_service_window = _service_window_from_runtime_blocks(
        response_starts,
        runtime_slots,
        submit_slot,
        deadline_slot,
        energy_per_slot_mwh,
    )
    risk_aligned_service_window = _service_window_from_runtime_blocks(
        risk_aligned_starts,
        runtime_slots,
        submit_slot,
        deadline_slot,
        energy_per_slot_mwh,
    )
    central_risk_aligned_profile = _aggregate_blocks(
        risk_aligned_starts,
        runtime_slots,
        region,
        central_power_mw,
        n_regions,
        horizon_slots,
        dt_h,
    )
    central_risk_aligned_service_window = _service_window_from_runtime_blocks(
        risk_aligned_starts,
        runtime_slots,
        submit_slot,
        deadline_slot,
        central_energy_per_slot_mwh,
    )
    central_baseline_service_window = _service_window_from_runtime_blocks(
        baseline_starts,
        runtime_slots,
        submit_slot,
        deadline_slot,
        central_energy_per_slot_mwh,
    )
    central_response_service_window = _service_window_from_runtime_blocks(
        response_starts,
        runtime_slots,
        submit_slot,
        deadline_slot,
        central_energy_per_slot_mwh,
    )
    baseline_energy_residual = baseline_profile.sum() - runtime_energy_mwh.sum()
    response_energy_residual = response_profile.sum() - runtime_energy_mwh.sum()
    central_baseline_energy_residual = (
        central_baseline_profile.sum() - declared_job_energy_mwh.sum()
    )
    central_response_energy_residual = (
        central_response_profile.sum() - declared_job_energy_mwh.sum()
    )
    central_risk_aligned_energy_residual = (
        central_risk_aligned_profile.sum() - declared_job_energy_mwh.sum()
    )
    site_capacity_mw = float(cfg["project"]["flexible_capacity_mw"])
    baseline_typed_certificate = validate_job_network_coupling(
        service_mwh=baseline_service_window,
        job_energy_mwh=runtime_energy_mwh,
        submit_slot=submit_slot,
        deadline_slot=deadline_slot,
        region=region,
        aggregate_mwh=baseline_profile,
        dt_h=dt_h,
        requested_gpus=requested_gpus,
        per_gpu_power_cap_mw=per_gpu_cap_mw,
        site_capacity_mw=site_capacity_mw,
    )
    response_typed_certificate = validate_job_network_coupling(
        service_mwh=response_service_window,
        job_energy_mwh=runtime_energy_mwh,
        submit_slot=submit_slot,
        deadline_slot=deadline_slot,
        region=region,
        aggregate_mwh=response_profile,
        dt_h=dt_h,
        requested_gpus=requested_gpus,
        per_gpu_power_cap_mw=per_gpu_cap_mw,
        site_capacity_mw=site_capacity_mw,
    )
    central_baseline_typed_certificate = validate_job_network_coupling(
        service_mwh=central_baseline_service_window,
        job_energy_mwh=declared_job_energy_mwh,
        submit_slot=submit_slot,
        deadline_slot=deadline_slot,
        region=region,
        aggregate_mwh=central_baseline_profile,
        dt_h=dt_h,
        requested_gpus=requested_gpus,
        per_gpu_power_cap_mw=per_gpu_cap_mw,
        site_capacity_mw=site_capacity_mw,
    )
    central_response_typed_certificate = validate_job_network_coupling(
        service_mwh=central_response_service_window,
        job_energy_mwh=declared_job_energy_mwh,
        submit_slot=submit_slot,
        deadline_slot=deadline_slot,
        region=region,
        aggregate_mwh=central_response_profile,
        dt_h=dt_h,
        requested_gpus=requested_gpus,
        per_gpu_power_cap_mw=per_gpu_cap_mw,
        site_capacity_mw=site_capacity_mw,
    )
    risk_aligned_typed_certificate = validate_job_network_coupling(
        service_mwh=risk_aligned_service_window,
        job_energy_mwh=runtime_energy_mwh,
        submit_slot=submit_slot,
        deadline_slot=deadline_slot,
        region=region,
        aggregate_mwh=risk_aligned_profile,
        dt_h=dt_h,
        requested_gpus=requested_gpus,
        per_gpu_power_cap_mw=per_gpu_cap_mw,
        site_capacity_mw=site_capacity_mw,
    )
    central_risk_aligned_typed_certificate = validate_job_network_coupling(
        service_mwh=central_risk_aligned_service_window,
        job_energy_mwh=declared_job_energy_mwh,
        submit_slot=submit_slot,
        deadline_slot=deadline_slot,
        region=region,
        aggregate_mwh=central_risk_aligned_profile,
        dt_h=dt_h,
        requested_gpus=requested_gpus,
        per_gpu_power_cap_mw=per_gpu_cap_mw,
        site_capacity_mw=site_capacity_mw,
    )
    if not all(
        certificate.valid
        for certificate in (
            baseline_typed_certificate,
            response_typed_certificate,
            central_baseline_typed_certificate,
            central_response_typed_certificate,
            risk_aligned_typed_certificate,
            central_risk_aligned_typed_certificate,
        )
    ):
        raise RuntimeError("Runtime-complete witness typed coupling certificate failed")
    minimum_baseline_slack_mwh = float(np.min(site_capacity_mw * dt_h - baseline_profile))
    minimum_response_slack_mwh = float(np.min(site_capacity_mw * dt_h - response_profile))
    minimum_risk_aligned_slack_mwh = float(
        np.min(site_capacity_mw * dt_h - risk_aligned_profile)
    )
    if max(
        abs(baseline_energy_residual),
        abs(response_energy_residual),
        abs(central_baseline_energy_residual),
        abs(central_response_energy_residual),
    ) > 1.0e-10:
        raise RuntimeError("Runtime-complete witness does not conserve declared job energy")
    if min(
        minimum_baseline_slack_mwh,
        minimum_response_slack_mwh,
        minimum_risk_aligned_slack_mwh,
    ) < -1.0e-10:
        raise RuntimeError("Runtime-complete witness exceeds a predeclared regional capacity row")
    if np.any(baseline_starts < submit_slot) or np.any(response_starts < submit_slot):
        raise RuntimeError("A witness start precedes its submit-time release")
    if np.any(baseline_starts + runtime_slots > deadline_slot) or np.any(response_starts + runtime_slots > deadline_slot):
        raise RuntimeError("A witness block crosses its declared deadline")
    event_indices = np.asarray(
        [t for t in range(horizon_slots) if t % slots_per_day in set(event_slots)], dtype=np.int64
    )
    event_reduction_mwh = float(baseline_profile[:, event_indices].sum() - response_profile[:, event_indices].sum())
    central_event_reduction_mwh = float(
        central_baseline_profile[:, event_indices].sum()
        - central_response_profile[:, event_indices].sum()
    )
    event_response_delay_mwh = float(np.maximum(response_profile[:, event_indices] - baseline_profile[:, event_indices], 0.0).sum())
    risk_bridge_rows: list[dict[str, Any]] = []
    fixed_load_for_bridge = float(cfg["project"]["fixed_facility_load_mw"])
    for day, target_day in zip(risk_days.tolist(), locked_risk_profile):
        day = int(day)
        day_slice = slice(day * slots_per_day, (day + 1) * slots_per_day)
        raw_target_total = np.asarray(target_day, dtype=float)
        risk_day_index = int(np.flatnonzero(risk_days == day)[0])
        target_total_upper = np.asarray(
            risk_contract_profile_upper[risk_day_index], dtype=float
        )
        target_total_central = np.asarray(
            risk_contract_profile_central[risk_day_index], dtype=float
        )
        upper_realization = (
            risk_aligned_profile[:, day_slice] / dt_h + fixed_load_for_bridge
        )
        central_realization = (
            central_risk_aligned_profile[:, day_slice] / dt_h + fixed_load_for_bridge
        )
        target_flexible_upper = np.maximum(target_total_upper - fixed_load_for_bridge, 0.0)
        target_flexible_central = np.maximum(target_total_central - fixed_load_for_bridge, 0.0)
        upper_error = upper_realization - target_total_upper
        central_error = central_realization - target_total_central
        risk_bridge_rows.append(
            {
                "day": day,
                "risk_profile_source": "Exp2 validation-fitted Risk-Constrained Convex Verifier",
                "raw_risk_profile_total_energy_mwh": float(raw_target_total.sum() * dt_h),
                "upper_contract_profile_total_energy_mwh": float(
                    target_total_upper.sum() * dt_h
                ),
                "central_contract_profile_total_energy_mwh": float(
                    target_total_central.sum() * dt_h
                ),
                "upper_capacity_realization_energy_mwh": float(upper_realization.sum() * dt_h),
                "central_energy_realization_energy_mwh": float(central_realization.sum() * dt_h),
                "upper_capacity_realization_nrmse": float(
                    np.sqrt(np.mean(upper_error**2))
                    / max(float(np.mean(np.abs(target_total_upper))), 1.0e-12)
                ),
                "central_energy_realization_nrmse": float(
                    np.sqrt(np.mean(central_error**2))
                    / max(float(np.mean(np.abs(target_total_central))), 1.0e-12)
                ),
                "upper_capacity_realization_rmse_mw": float(np.sqrt(np.mean(upper_error**2))),
                "central_energy_realization_rmse_mw": float(np.sqrt(np.mean(central_error**2))),
                "upper_capacity_realization_nrmse_flexible_target": float(
                    np.sqrt(np.mean(upper_error**2))
                    / max(float(np.mean(np.abs(target_flexible_upper))), 1.0e-12)
                ),
                "central_energy_realization_nrmse_flexible_target": float(
                    np.sqrt(np.mean(central_error**2))
                    / max(float(np.mean(np.abs(target_flexible_central))), 1.0e-12)
                ),
                "upper_capacity_profile_max_mw": float(np.max(upper_realization)),
                "central_profile_max_mw": float(np.max(central_realization)),
                "risk_price_max_usd_per_mwh": float(
                    np.max(
                        risk_price_by_region_slot[
                            :, day * slots_per_day : (day + 1) * slots_per_day
                        ]
                    )
                ),
                "same_declaration_digest": source_submission_digest,
            }
        )
    risk_bridge = pd.DataFrame(risk_bridge_rows).sort_values("day").reset_index(drop=True)
    risk_bridge.to_csv(final / "risk_to_executable_bridge.csv", index=False)
    risk_profile_digest = _array_digest(risk_days, locked_risk_profile)
    write_json(
        final / "risk_to_executable_bridge_certificate.json",
        {
            "schema_version": 2,
            "risk_profile_source": "experiments/exp2_baseline_verification/results/intermediate/test_profiles.npz::Risk-Constrained Convex Verifier",
            "risk_profile_digest": risk_profile_digest,
            "submission_digest": source_submission_digest,
            "mapping": "p_exec_upper=P_fix+gamma_upper*max(p_risk-P_fix,0), gamma_upper=locked_submit_nameplate_energy/sum(max(p_risk-P_fix,0)*dt); pi_{r,t}=p_DR*max(p_exec_upper_{r,t}-P_fix,0)/max_{r,t}max(p_exec_upper-P_fix,0); each job enumerates every contiguous declaration-feasible start under waiting + event + pi costs",
            "optimization_class": "finite exact start-time enumeration with fixed linear slot prices",
            "locked_days": int(len(risk_bridge)),
            "raw_risk_profile_total_energy_mwh": float(locked_risk_profile.sum() * dt_h),
            "risk_flexible_target_energy_mwh": risk_flexible_target_energy_mwh,
            "locked_submit_declared_upper_energy_mwh": locked_declared_upper_energy_mwh,
            "locked_submit_declared_central_energy_mwh": locked_declared_central_energy_mwh,
            "upper_contract_scale": risk_contract_scale_upper,
            "central_contract_scale": risk_contract_scale_central,
            "upper_contract_profile_digest": _array_digest(risk_days, risk_contract_profile_upper),
            "central_contract_profile_digest": _array_digest(risk_days, risk_contract_profile_central),
            "upper_capacity_realization_mean_nrmse": float(risk_bridge["upper_capacity_realization_nrmse"].mean()),
            "central_energy_realization_mean_nrmse": float(risk_bridge["central_energy_realization_nrmse"].mean()),
            "upper_capacity_realization_mean_nrmse_flexible_target": float(
                risk_bridge["upper_capacity_realization_nrmse_flexible_target"].mean()
            ),
            "central_energy_realization_mean_nrmse_flexible_target": float(
                risk_bridge["central_energy_realization_nrmse_flexible_target"].mean()
            ),
            "same_submission_index": True,
            "future_arrivals_used": False,
            "execution_telemetry_used": False,
            "network_response_profile": "risk_aligned_profile",
            "settlement_definition": (
                "payable response is the minimum of the declaration-witnessed "
                "reduction and the frozen contract-cap reduction on event slots; "
                "the signed N-1 network value is added and a zero floor is applied "
                "only to the reported cash settlement"
            ),
            "files": {"daily": "risk_to_executable_bridge.csv"},
        },
    )
    witness_digest = _array_digest(
        submit_slot,
        deadline_slot,
        runtime_slots,
        region,
        requested_gpus,
        declared_job_energy_mwh,
        declared_job_energy_upper_mwh,
        baseline_starts,
        response_starts,
        baseline_service_window,
        response_service_window,
        baseline_profile,
        response_profile,
        central_baseline_service_window,
        central_response_service_window,
        central_baseline_profile,
        central_response_profile,
        risk_aligned_starts,
        risk_aligned_service_window,
        risk_aligned_profile,
        central_risk_aligned_service_window,
        central_risk_aligned_profile,
        locked_risk_profile,
        risk_contract_profile_upper,
        risk_contract_profile_central,
    )
    typed_certificate = {
        "schema_version": 4,
        "witness_digest": witness_digest,
        "source_submission_digest": source_submission_digest,
        "profile_identity_asserted": True,
        "service_vector_identity_asserted": True,
        "digest_inputs": [
            "submit_slot",
            "deadline_slot",
            "runtime_slots",
            "region",
            "requested_gpus",
            "declared_job_energy_mwh",
            "declared_job_energy_upper_mwh",
            "baseline_start_slot",
            "response_start_slot",
            "baseline_service_mwh",
            "counterfactual_service_mwh",
            "baseline_mwh",
            "counterfactual_mwh",
            "central_baseline_service_mwh",
            "central_counterfactual_service_mwh",
            "central_baseline_mwh",
            "central_counterfactual_mwh",
            "risk_aligned_start_slot",
            "risk_aligned_service_mwh",
            "risk_aligned_mwh",
            "central_risk_aligned_service_mwh",
            "central_risk_aligned_mwh",
            "locked_risk_profile",
            "risk_contract_profile_upper",
            "risk_contract_profile_central",
        ],
        "runtime_definition": (
            "one contiguous block inside each submit-to-deadline declaration "
            "window; the primary profile is the declared GPU-nameplate upper "
            "capacity and the central profile uses the calibrated declared "
            "energy on the same block"
        ),
        "baseline": baseline_typed_certificate.to_dict(),
        "counterfactual": response_typed_certificate.to_dict(),
        "central_baseline": central_baseline_typed_certificate.to_dict(),
        "central_counterfactual": central_response_typed_certificate.to_dict(),
        "risk_aligned": risk_aligned_typed_certificate.to_dict(),
        "central_risk_aligned": central_risk_aligned_typed_certificate.to_dict(),
        "risk_bridge": {
            "risk_profile_digest": risk_profile_digest,
            "upper_contract_profile_digest": _array_digest(risk_days, risk_contract_profile_upper),
            "central_contract_profile_digest": _array_digest(risk_days, risk_contract_profile_central),
            "price_normalization_mw": risk_target_scale_mw,
            "upper_contract_scale": risk_contract_scale_upper,
            "central_contract_scale": risk_contract_scale_central,
            "locked_submit_declared_upper_energy_mwh": locked_declared_upper_energy_mwh,
            "locked_submit_declared_central_energy_mwh": locked_declared_central_energy_mwh,
            "event_tariff_per_mwh": event_price,
            "scale_source": "submit-time declaration energy on the locked risk days",
            "raw_profile_retained": True,
            "locked_days": int(len(risk_days)),
        },
    }
    np.savez_compressed(
        final / "runtime_complete_witness.npz",
        submit_slot=submit_slot,
        deadline_slot=deadline_slot,
        runtime_slots=runtime_slots,
        region=region,
        requested_gpus=requested_gpus,
        per_gpu_power_cap_mw=np.asarray([per_gpu_cap_mw]),
        declared_job_energy_mwh=declared_job_energy_mwh,
        declared_job_energy_upper_mwh=declared_job_energy_upper_mwh,
        runtime_energy_mwh=runtime_energy_mwh,
        central_energy_per_slot_mwh=central_energy_per_slot_mwh,
        baseline_start_slot=baseline_starts,
        response_start_slot=response_starts,
        baseline_service_mwh=baseline_service_window,
        counterfactual_service_mwh=response_service_window,
        baseline_mwh=baseline_profile,
        counterfactual_mwh=response_profile,
        central_baseline_service_mwh=central_baseline_service_window,
        central_counterfactual_service_mwh=central_response_service_window,
        central_baseline_mwh=central_baseline_profile,
        central_counterfactual_mwh=central_response_profile,
        risk_aligned_start_slot=risk_aligned_starts,
        risk_aligned_service_mwh=risk_aligned_service_window,
        risk_aligned_mwh=risk_aligned_profile,
        central_risk_aligned_service_mwh=central_risk_aligned_service_window,
        central_risk_aligned_mwh=central_risk_aligned_profile,
        locked_risk_profile=locked_risk_profile,
        risk_contract_profile_upper=risk_contract_profile_upper,
        risk_contract_profile_central=risk_contract_profile_central,
        source_submission_digest=np.asarray([source_submission_digest]),
        witness_digest=np.asarray([witness_digest]),
    )
    del baseline_service_window, response_service_window
    job_summary = pd.DataFrame(
        {
            "job_index": np.arange(len(submit_slot), dtype=np.int64),
            "region": region,
            "requested_gpus": requested_gpus,
            "submit_slot": submit_slot,
            "deadline_slot": deadline_slot,
            "runtime_slots": runtime_slots,
            "declared_job_energy_mwh": declared_job_energy_mwh,
            "declared_job_energy_upper_mwh": declared_job_energy_upper_mwh,
            "runtime_energy_mwh": runtime_energy_mwh,
            "baseline_start_slot": baseline_starts,
            "counterfactual_start_slot": response_starts,
            "risk_aligned_start_slot": risk_aligned_starts,
            "baseline_event_slots": event_prefix[baseline_starts + runtime_slots] - event_prefix[baseline_starts],
            "counterfactual_event_slots": event_prefix[response_starts + runtime_slots] - event_prefix[response_starts],
            "baseline_objective_usd": baseline_cost,
            "counterfactual_objective_usd": response_cost,
            "risk_aligned_objective_usd": risk_aligned_cost,
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
            {"metric": "nameplate_upper_runtime_energy_mwh", "value": float(runtime_energy_mwh.sum()), "unit": "MWh"},
            {"metric": "central_declared_service_energy_mwh", "value": float(declared_job_energy_mwh.sum()), "unit": "MWh"},
            {"metric": "central_to_nameplate_energy_ratio", "value": float(declared_job_energy_mwh.sum() / max(runtime_energy_mwh.sum(), 1.0e-12)), "unit": "ratio"},
            {"metric": "baseline_energy_residual_mwh", "value": float(baseline_energy_residual), "unit": "MWh"},
            {"metric": "counterfactual_energy_residual_mwh", "value": float(response_energy_residual), "unit": "MWh"},
            {"metric": "central_baseline_energy_residual_mwh", "value": float(central_baseline_energy_residual), "unit": "MWh"},
            {"metric": "central_counterfactual_energy_residual_mwh", "value": float(central_response_energy_residual), "unit": "MWh"},
            {"metric": "baseline_minimum_site_capacity_slack_mwh", "value": minimum_baseline_slack_mwh, "unit": "MWh"},
            {"metric": "counterfactual_minimum_site_capacity_slack_mwh", "value": minimum_response_slack_mwh, "unit": "MWh"},
            {"metric": "risk_aligned_minimum_site_capacity_slack_mwh", "value": minimum_risk_aligned_slack_mwh, "unit": "MWh"},
            {"metric": "baseline_event_energy_mwh", "value": float(baseline_profile[:, event_indices].sum()), "unit": "MWh"},
            {"metric": "counterfactual_event_energy_mwh", "value": float(response_profile[:, event_indices].sum()), "unit": "MWh"},
            {"metric": "event_reduction_mwh", "value": event_reduction_mwh, "unit": "MWh"},
            {"metric": "central_event_reduction_mwh", "value": central_event_reduction_mwh, "unit": "MWh"},
            {"metric": "risk_aligned_event_energy_mwh", "value": float(risk_aligned_profile[:, event_indices].sum()), "unit": "MWh"},
            {"metric": "risk_aligned_event_reduction_mwh", "value": float(baseline_profile[:, event_indices].sum() - risk_aligned_profile[:, event_indices].sum()), "unit": "MWh"},
            {"metric": "central_risk_aligned_energy_residual_mwh", "value": float(central_risk_aligned_energy_residual), "unit": "MWh"},
            {"metric": "risk_flexible_target_energy_mwh", "value": risk_flexible_target_energy_mwh, "unit": "MWh"},
            {"metric": "locked_submit_declared_upper_energy_mwh", "value": locked_declared_upper_energy_mwh, "unit": "MWh"},
            {"metric": "locked_submit_declared_central_energy_mwh", "value": locked_declared_central_energy_mwh, "unit": "MWh"},
            {"metric": "risk_contract_scale_upper", "value": risk_contract_scale_upper, "unit": "ratio"},
            {"metric": "risk_contract_scale_central", "value": risk_contract_scale_central, "unit": "ratio"},
            {"metric": "risk_bridge_upper_mean_nrmse", "value": float(risk_bridge["upper_capacity_realization_nrmse"].mean()), "unit": "ratio"},
            {"metric": "risk_bridge_central_mean_nrmse", "value": float(risk_bridge["central_energy_realization_nrmse"].mean()), "unit": "ratio"},
            {"metric": "risk_bridge_upper_mean_nrmse_flexible_target", "value": float(risk_bridge["upper_capacity_realization_nrmse_flexible_target"].mean()), "unit": "ratio"},
            {"metric": "risk_bridge_central_mean_nrmse_flexible_target", "value": float(risk_bridge["central_energy_realization_nrmse_flexible_target"].mean()), "unit": "ratio"},
            {"metric": "event_response_delay_mwh", "value": event_response_delay_mwh, "unit": "MWh"},
            {"metric": "baseline_jobs_with_one_contiguous_block", "value": len(baseline_starts), "unit": "jobs"},
            {"metric": "counterfactual_jobs_with_one_contiguous_block", "value": len(response_starts), "unit": "jobs"},
            {"metric": "baseline_max_job_energy_residual_mwh", "value": baseline_typed_certificate.max_job_energy_residual_mwh, "unit": "MWh"},
            {"metric": "counterfactual_max_job_energy_residual_mwh", "value": response_typed_certificate.max_job_energy_residual_mwh, "unit": "MWh"},
            {"metric": "baseline_max_aggregation_residual_mwh", "value": baseline_typed_certificate.max_aggregation_residual_mwh, "unit": "MWh"},
            {"metric": "counterfactual_max_aggregation_residual_mwh", "value": response_typed_certificate.max_aggregation_residual_mwh, "unit": "MWh"},
            {"metric": "baseline_max_gpu_bound_violation_mwh", "value": baseline_typed_certificate.maximum_gpu_bound_violation_mwh, "unit": "MWh"},
            {"metric": "counterfactual_max_gpu_bound_violation_mwh", "value": response_typed_certificate.maximum_gpu_bound_violation_mwh, "unit": "MWh"},
            {"metric": "baseline_minimum_typed_capacity_slack_mwh", "value": baseline_typed_certificate.minimum_site_capacity_slack_mwh, "unit": "MWh"},
            {"metric": "counterfactual_minimum_typed_capacity_slack_mwh", "value": response_typed_certificate.minimum_site_capacity_slack_mwh, "unit": "MWh"},
        ]
    )
    summary.to_csv(final / "common_witness_summary.csv", index=False)
    write_json(final / "runtime_witness_coupling_certificate.json", typed_certificate)
    logger.info("Exp27 declaration witness [35%%]: jobs=%d, runtime energy=%.3f MWh", len(submit_slot), runtime_energy_mwh.sum())

    # The network replay is evaluated on the same baseline and risk-aligned
    # response trajectory that was selected by the declaration witness.  The
    # locked-day index is taken from the Exp2 panel so the scope is an
    # identified study cohort.  A separate ordinary event-price response is
    # retained in the archive as an ablation; it cannot be used to claim a
    # network value for the risk-priced trajectory.
    test_profile_path = root / "experiments/exp2_baseline_verification/results/intermediate/test_profiles.npz"
    if not test_profile_path.exists():
        raise FileNotFoundError(f"Locked day index is missing: {test_profile_path}")
    test_days = np.asarray(np.load(test_profile_path, allow_pickle=False)["days"], dtype=int)
    network_days = [
        int(day)
        for day in test_days
        if int(day) * slots_per_day + slots_per_day <= horizon_slots
    ]
    if not network_days:
        raise RuntimeError("No locked days fit inside the runtime-complete witness horizon")
    system, security, buses = _load_common_network_case(cfg)
    base_load = np.asarray(system.bus[:, 2], dtype=float) * float(cfg["experiments"].get("n1_load_multiplier", 0.9))
    fixed_load_mw = float(cfg["project"]["fixed_facility_load_mw"])
    segment_count = int(cfg["experiments"].get("coupled_network_generator_segments", 4))
    settlement_slots = list(range(slots_per_day))
    event_slot_set = set(int(slot) for slot in event_slots.tolist())
    risk_day_to_index = {int(day): int(index) for index, day in enumerate(risk_days.tolist())}
    network_tasks = [
        (int(day), int(slot)) for day in network_days for slot in settlement_slots
    ]

    def solve_network(task: tuple[int, int]) -> dict[str, Any]:
        day, slot = task
        absolute_slot = day * slots_per_day + slot
        baseline_mw = baseline_profile[:, absolute_slot] / dt_h
        response_mw = risk_aligned_profile[:, absolute_slot] / dt_h
        baseline_load = base_load.copy()
        response_load = base_load.copy()
        baseline_load[buses] += fixed_load_mw + baseline_mw
        response_load[buses] += fixed_load_mw + response_mw
        baseline = solve_n1_sced(system, baseline_load, segment_count, security_factors=security)
        response = solve_n1_sced(system, response_load, segment_count, security_factors=security)
        if not baseline.success or not response.success:
            raise RuntimeError(f"Common witness RTS-24 solve failed at day={day}, slot={slot}")
        # The marginal credit is evaluated at the baseline dispatch endpoint,
        # matching the signed linearization in Eq. (27). Response prices would
        # make the payment depend on the counterfactual being credited.
        nodal_credit = float(np.dot(baseline_mw - response_mw, baseline.lmp_per_mwh[buses]) * dt_h)
        value = float((baseline.objective - response.objective) * dt_h)
        risk_index = risk_day_to_index.get(int(day))
        if risk_index is None:
            raise RuntimeError(f"Network day {day} is absent from the locked risk profile")
        contract_target_mw = np.asarray(
            risk_contract_flexible_upper[risk_index, :, slot], dtype=float
        )
        gross_reduction_mw = np.maximum(baseline_mw - response_mw, 0.0)
        contract_cap_mw = np.maximum(baseline_mw - contract_target_mw, 0.0)
        metered_reduction_mwh = float(gross_reduction_mw.sum() * dt_h)
        contract_cap_mwh = float(contract_cap_mw.sum() * dt_h)
        # Apply the contract cap pointwise before summing across regions. A
        # minimum of the two aggregate sums could overpay when one region is
        # above its cap and another is below it.
        payable_response_mwh = float(
            np.minimum(gross_reduction_mw, contract_cap_mw).sum() * dt_h
            if slot in event_slot_set
            else 0.0
        )
        capacity_payment = float(payable_response_mwh * event_price)
        signed_contract_value = float(capacity_payment + value)
        payable_settlement = float(max(0.0, signed_contract_value))
        return {
            "day": day,
            "slot": slot,
            "absolute_slot": absolute_slot,
            "is_event_slot": int(slot in event_slot_set),
            "settlement_window": "full_declared_day",
            "baseline_witness_profile_sha256": witness_digest,
            "counterfactual_witness_profile_sha256": witness_digest,
            "counterfactual_profile_role": "risk_aligned_declaration_witness",
            "baseline_total_flexible_mw": float(baseline_mw.sum()),
            "counterfactual_total_flexible_mw": float(response_mw.sum()),
            "baseline_secure_cost_usd_per_interval": float(baseline.objective * dt_h),
            "counterfactual_secure_cost_usd_per_interval": float(response.objective * dt_h),
            "network_value_usd": value,
            "nodal_meter_credit_usd": nodal_credit,
            "gross_declared_reduction_mwh": metered_reduction_mwh,
            "frozen_contract_cap_mwh": contract_cap_mwh,
            "payable_response_mwh": payable_response_mwh,
            "capacity_payment_usd": capacity_payment,
            "signed_contract_value_usd": signed_contract_value,
            "payable_settlement_usd": payable_settlement,
            "settlement_floor_applied": int(signed_contract_value < 0.0),
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
    if not np.isfinite(network.select_dtypes(include=[np.number]).to_numpy()).all():
        raise RuntimeError("Common witness settlement contains a non-finite signed value")
    signed_value_total = float(network["network_value_usd"].sum())
    signed_meter_credit_total = float(network["nodal_meter_credit_usd"].sum())
    signed_settlement_total = float(network["payable_settlement_usd"].sum())
    negative_value_cells = int((network["network_value_usd"] < -1.0e-12).sum())
    event_network = network.loc[network["is_event_slot"].astype(bool)]
    settlement_summary = pd.DataFrame(
        [
            {"metric": "full_cycle_cells", "value": int(len(network)), "unit": "day-slots"},
            {"metric": "event_cells", "value": int(len(event_network)), "unit": "day-slots"},
            {"metric": "locked_days", "value": int(len(network_days)), "unit": "days"},
            {"metric": "finite_n1_contingencies_per_cell", "value": int(security[3]), "unit": "contingencies"},
            {"metric": "negative_network_value_cells", "value": negative_value_cells, "unit": "cells"},
            {"metric": "signed_network_value_usd", "value": signed_value_total, "unit": "USD"},
            {"metric": "signed_nodal_meter_credit_usd", "value": signed_meter_credit_total, "unit": "USD"},
            {"metric": "capacity_payment_usd", "value": float(network["capacity_payment_usd"].sum()), "unit": "USD"},
            {"metric": "payable_response_mwh", "value": float(network["payable_response_mwh"].sum()), "unit": "MWh"},
            {"metric": "settlement_floor_cells", "value": int(network["settlement_floor_applied"].sum()), "unit": "cells"},
            {"metric": "signed_payable_settlement_usd", "value": signed_settlement_total, "unit": "USD"},
            {"metric": "signed_value_minus_meter_credit_usd", "value": signed_value_total - signed_meter_credit_total, "unit": "USD"},
        ]
    )
    settlement_summary.to_csv(final / "common_witness_settlement_summary.csv", index=False)
    summary_with_settlement = pd.concat(
        [summary, settlement_summary.assign(metric=lambda frame: "settlement_" + frame["metric"])],
        ignore_index=True,
    )
    summary_with_settlement.to_csv(final / "common_witness_summary.csv", index=False)
    logger.info("Exp27 common witness network/settlement [85%%]: %d full-cycle cells, %d event cells, %d N-1 outages/cell", len(network), len(event_network), int(security[3]))

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
        "schema_version": 3,
        "source_exp19": "experiments/exp19_job_level_counterfactual/results/final/job_level_counterfactual_solution.npz",
        "source_submission_digest": source_submission_digest,
        "source_exp19_metadata_digest": hashlib.sha256(source_meta_path.read_bytes()).hexdigest(),
        "submitted_jobs": int(len(submit_slot)),
        "horizon_slots": horizon_slots,
        "queue_buffer_slots": queue_buffer_slots,
        "runtime_definition": "deadline_slot - submit_slot - fixed declaration queue allowance; one contiguous fixed-rate block is used for both the predeclared GPU-nameplate upper-capacity profile and the calibrated central-energy profile",
        "runtime_complete": True,
        "runtime_energy_entitlement_mwh": float(runtime_energy_mwh.sum()),
        "central_declared_service_energy_mwh": float(declared_job_energy_mwh.sum()),
        "nameplate_upper_energy_mwh": float(declared_job_energy_upper_mwh.sum()),
        "central_to_nameplate_energy_ratio": float(
            declared_job_energy_mwh.sum() / max(runtime_energy_mwh.sum(), 1.0e-12)
        ),
        "profile_semantics": {
            "network_profile": "predeclared GPU-nameplate upper-capacity commitment; it is not measured consumption",
            "central_profile": "calibrated q50 declared service energy on the identical contiguous blocks",
            "upper_bound_check": "declared_job_energy_mwh <= declared_job_energy_upper_mwh = requested_gpus * per_gpu_power_cap_mw * runtime_slots * dt_h",
        },
        "observed_execution_telemetry_used": False,
        "telemetry_fields_used_in_decision": [],
        "declaration_fields_used": ["submit_slot", "deadline_slot", "region", "requested_gpus", "per_gpu_power_cap_mw", "declared_job_energy_mwh", "declared_job_energy_upper_mwh", "submission_digest"],
        "baseline_policy": "exact earliest-start member of the declaration-feasible contiguous-block set",
        "response_policy": "exact enumeration of every declaration-feasible contiguous start with predeclared waiting and event-tariff costs; retained as an ordinary-price ablation",
        "risk_aligned_policy": "exact enumeration of every declaration-feasible contiguous start with predeclared waiting, event-tariff, and frozen risk-profile slot prices",
        "risk_bridge": {
            "source": "Exp2 locked Risk-Constrained Convex Verifier profile",
            "profile_digest": risk_profile_digest,
            "upper_contract_profile_digest": _array_digest(risk_days, risk_contract_profile_upper),
            "central_contract_profile_digest": _array_digest(risk_days, risk_contract_profile_central),
            "scale_source": "submit-time declaration energy on the locked risk days",
            "raw_profile_retained": True,
            "price_normalization_mw": risk_target_scale_mw,
            "upper_contract_scale": risk_contract_scale_upper,
            "central_contract_scale": risk_contract_scale_central,
            "locked_submit_declared_upper_energy_mwh": locked_declared_upper_energy_mwh,
            "locked_submit_declared_central_energy_mwh": locked_declared_central_energy_mwh,
            "price_formula": "p_exec_upper=P_fix+gamma_upper*max(p_risk-P_fix,0); pi_{r,t}=p_DR*max(p_exec_upper_{r,t}-P_fix,0)/max_{r,t}max(p_exec_upper-P_fix,0)",
            "finite_exact_realization": True,
            "network_replay_profile": "risk_aligned_profile",
            "settlement_payment_cap": "min(declaration-witnessed event reduction, frozen contract-cap reduction)",
            "daily_audit_file": "risk_to_executable_bridge.csv",
            "certificate_file": "risk_to_executable_bridge_certificate.json",
        },
        "event_slots": event_slots.tolist(),
        "event_tariff_per_mwh": event_price,
        "waiting_cost_per_mwh_slot": waiting_cost,
        "capacity_mw_per_region": site_capacity_mw,
        "baseline_minimum_site_capacity_slack_mwh": minimum_baseline_slack_mwh,
        "counterfactual_minimum_site_capacity_slack_mwh": minimum_response_slack_mwh,
        "event_reduction_mwh": event_reduction_mwh,
        "central_event_reduction_mwh": central_event_reduction_mwh,
        "risk_aligned_event_reduction_mwh": float(
            baseline_profile[:, event_indices].sum()
            - risk_aligned_profile[:, event_indices].sum()
        ),
        "witness_digest": witness_digest,
        "profile_identity_asserted": True,
        "service_vector_identity_asserted": True,
        "digest_inputs": typed_certificate["digest_inputs"],
        "runtime_typed_certificate": {
            "file": "runtime_witness_coupling_certificate.json",
            "baseline_valid": bool(baseline_typed_certificate.valid),
            "counterfactual_valid": bool(response_typed_certificate.valid),
            "maximum_job_energy_residual_mwh": float(
                max(
                    baseline_typed_certificate.max_job_energy_residual_mwh,
                    response_typed_certificate.max_job_energy_residual_mwh,
                )
            ),
            "maximum_aggregation_residual_mwh": float(
                max(
                    baseline_typed_certificate.max_aggregation_residual_mwh,
                    response_typed_certificate.max_aggregation_residual_mwh,
                )
            ),
            "maximum_gpu_bound_violation_mwh": float(
                max(
                    baseline_typed_certificate.maximum_gpu_bound_violation_mwh,
                    response_typed_certificate.maximum_gpu_bound_violation_mwh,
                )
            ),
            "minimum_site_capacity_slack_mwh": float(
                min(
                    baseline_typed_certificate.minimum_site_capacity_slack_mwh,
                    response_typed_certificate.minimum_site_capacity_slack_mwh,
                )
            ),
        },
        "central_energy_typed_certificate": {
            "baseline_valid": bool(central_baseline_typed_certificate.valid),
            "counterfactual_valid": bool(central_response_typed_certificate.valid),
            "maximum_job_energy_residual_mwh": float(
                max(
                    central_baseline_typed_certificate.max_job_energy_residual_mwh,
                    central_response_typed_certificate.max_job_energy_residual_mwh,
                )
            ),
            "maximum_aggregation_residual_mwh": float(
                max(
                    central_baseline_typed_certificate.max_aggregation_residual_mwh,
                    central_response_typed_certificate.max_aggregation_residual_mwh,
                )
            ),
            "maximum_gpu_bound_violation_mwh": float(
                max(
                    central_baseline_typed_certificate.maximum_gpu_bound_violation_mwh,
                    central_response_typed_certificate.maximum_gpu_bound_violation_mwh,
                )
            ),
            "minimum_site_capacity_slack_mwh": float(
                min(
                    central_baseline_typed_certificate.minimum_site_capacity_slack_mwh,
                    central_response_typed_certificate.minimum_site_capacity_slack_mwh,
                )
            ),
        },
        "risk_aligned_typed_certificate": {
            "baseline_valid": bool(risk_aligned_typed_certificate.valid),
            "counterfactual_valid": bool(risk_aligned_typed_certificate.valid),
            "maximum_job_energy_residual_mwh": float(
                risk_aligned_typed_certificate.max_job_energy_residual_mwh
            ),
            "maximum_aggregation_residual_mwh": float(
                risk_aligned_typed_certificate.max_aggregation_residual_mwh
            ),
            "maximum_gpu_bound_violation_mwh": float(
                risk_aligned_typed_certificate.maximum_gpu_bound_violation_mwh
            ),
            "minimum_site_capacity_slack_mwh": float(
                risk_aligned_typed_certificate.minimum_site_capacity_slack_mwh
            ),
        },
        "central_risk_aligned_typed_certificate": {
            "baseline_valid": bool(central_risk_aligned_typed_certificate.valid),
            "counterfactual_valid": bool(central_risk_aligned_typed_certificate.valid),
            "maximum_job_energy_residual_mwh": float(
                central_risk_aligned_typed_certificate.max_job_energy_residual_mwh
            ),
            "maximum_aggregation_residual_mwh": float(
                central_risk_aligned_typed_certificate.max_aggregation_residual_mwh
            ),
            "maximum_gpu_bound_violation_mwh": float(
                central_risk_aligned_typed_certificate.maximum_gpu_bound_violation_mwh
            ),
            "minimum_site_capacity_slack_mwh": float(
                central_risk_aligned_typed_certificate.minimum_site_capacity_slack_mwh
            ),
        },
        "network_settlement": {
            "network_case": "IEEE RTS-24 (PYPOWER case24_ieee_rts)",
            "network_buses_one_based": (buses + 1).tolist(),
            "locked_days": network_days,
            "replay_cells": int(len(network)),
            "full_cycle_cells": int(len(network)),
            "event_replay_cells": int(len(event_network)),
            "settlement_window_slots": settlement_slots,
            "settlement_window": "full_declared_day",
            "generator_segments": segment_count,
            "finite_nonislanding_n1_contingencies_per_cell": int(security[3]),
            "base_load_multiplier": float(cfg["experiments"].get("n1_load_multiplier", 0.9)),
            "fixed_facility_load_mw_per_bus": fixed_load_mw,
            "profile_source": "runtime_complete_witness.npz baseline_mwh and counterfactual_mwh (nameplate upper-capacity commitment)",
            "settlement_source_digest": witness_digest,
            "signed_settlement": True,
            "negative_network_value_cells": negative_value_cells,
            "signed_network_value_usd": signed_value_total,
            "signed_nodal_meter_credit_usd": signed_meter_credit_total,
            "signed_payable_settlement_usd": signed_settlement_total,
            "all_solver_cells_successful": bool(network["solver_success"].all()),
        },
        "files": {
            "witness": "runtime_complete_witness.npz",
            "job_level": "job_level_runtime_summary.csv",
            "summary": "common_witness_summary.csv",
            "typed_coupling_certificate": "runtime_witness_coupling_certificate.json",
            "settlement": "common_witness_settlement.csv",
            "settlement_summary": "common_witness_settlement_summary.csv",
            "risk_bridge": "risk_to_executable_bridge.csv",
            "risk_bridge_certificate": "risk_to_executable_bridge_certificate.json",
            "figure": "fig28_common_executable_witness.pdf",
        },
    }
    write_json(final / "experiment_metadata.json", metadata)
    (folder / "README.md").write_text(
        """# Experiment 27: executable common workload witness

This experiment reads only submit-time fields from the immutable Exp19
submission ledger. Every job receives one fixed contiguous runtime block.
The primary workload profile is the declared GPU-nameplate upper-capacity
commitment, while a calibrated central-energy profile and an exact risk-priced
realization are materialized on the identical blocks. Baseline, tariff
response, and risk-aligned starts are obtained by finite exact enumeration over
the declaration-feasible queue allowance. The saved primary arrays are then
reused verbatim for a signed full-day RTS-24 DC N-1 settlement replay; event
slots are flagged for the event-specific analysis.

The final directory contains the NPZ witness with both indexed service vectors,
the job-level runtime certificate, the typed job/aggregation/GPU/capacity
certificate, risk-to-executable bridge certificate, common witness summary,
full-day signed settlement replay, metadata, and publication figure. Execution
telemetry never enters a decision.
""",
        encoding="utf-8",
    )
    logger.info("Exp27 executable common witness [100%%]: PASS; digest=%s", witness_digest[:12])
