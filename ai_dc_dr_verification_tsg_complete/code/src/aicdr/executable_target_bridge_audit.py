"""Independent audit of the risk-to-executable target bridge.

The common witness intentionally solves a finite declaration-feasible start
problem.  This module checks that the saved policy is the exact minimizer of
that finite problem, then reports the residual between the aggregate contract
profile and the executable job witness.  The residual is an auditable quantity;
it is never silently treated as a zero target-tracking constraint.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .executable_witness import _select_risk_aligned_starts
from .utils import write_json


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _metric_rows(values: dict[str, tuple[float, str]]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"metric": key, "value": float(value), "unit": unit}
            for key, (value, unit) in values.items()
        ]
    )


def run_exp29_executable_target_bridge_audit(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
) -> None:
    """Recompute exact start optimality and quantify target-tracking residuals."""

    folder = root / "experiments/exp29_executable_target_bridge"
    final = folder / "results/final"
    figures = folder / "figures"
    final.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    exp27 = root / "experiments/exp27_executable_common_witness/results/final"
    witness_path = exp27 / "runtime_complete_witness.npz"
    job_path = exp27 / "job_level_runtime_summary.csv"
    bridge_path = exp27 / "risk_to_executable_bridge.csv"
    if not all(path.exists() for path in (witness_path, job_path, bridge_path)):
        raise FileNotFoundError("Exp27 witness artifacts are required before Exp29")

    with np.load(witness_path, allow_pickle=False) as witness:
        submit_slot = np.asarray(witness["submit_slot"], dtype=np.int64)
        deadline_slot = np.asarray(witness["deadline_slot"], dtype=np.int64)
        runtime_slots = np.asarray(witness["runtime_slots"], dtype=np.int64)
        region = np.asarray(witness["region"], dtype=np.int64)
        energy_per_slot_mwh = np.asarray(
            witness["declared_job_energy_upper_mwh"], dtype=float
        ) / np.maximum(runtime_slots, 1)
        risk_aligned_profile = np.asarray(witness["risk_aligned_mwh"], dtype=float)
        risk_contract_profile = np.asarray(
            witness["risk_contract_profile_upper"], dtype=float
        )

    job_summary = pd.read_csv(job_path)
    bridge = pd.read_csv(bridge_path).sort_values("day").reset_index(drop=True)
    if len(job_summary) != len(submit_slot):
        raise RuntimeError("The saved job summary and witness have different populations")

    n_regions, horizon_slots = risk_aligned_profile.shape
    slots_per_day = int(cfg["project"]["slots_per_day"])
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    queue_buffer_slots = int(
        cfg["experiments"].get("job_level_submission_buffer_slots", 96)
    )
    fixed_load_mw = float(cfg["project"]["fixed_facility_load_mw"])
    capacity_mw = float(cfg["project"]["flexible_capacity_mw"])
    event_price = float(cfg["market"]["default_dr_price_per_mwh"])
    waiting_cost = float(cfg["workload"]["waiting_cost_per_mwh_slot"][-1])
    event_slots = set(int(value) for value in cfg["market"]["event_slots"])
    event_mask = np.zeros(horizon_slots + 1, dtype=np.int8)
    event_mask[
        np.asarray(
            [t for t in range(horizon_slots + 1) if t % slots_per_day in event_slots],
            dtype=np.int64,
        )
    ] = 1
    event_prefix = np.concatenate([[0], np.cumsum(event_mask, dtype=np.int64)])

    risk_days = bridge["day"].to_numpy(dtype=np.int64)
    risk_price_by_region_slot = np.zeros((n_regions, horizon_slots), dtype=float)
    flexible_contract = np.maximum(risk_contract_profile - fixed_load_mw, 0.0)
    price_scale_mw = max(float(np.max(flexible_contract)), 1.0e-12)
    for index, day in enumerate(risk_days.tolist()):
        start = int(day) * slots_per_day
        stop = start + slots_per_day
        if stop > horizon_slots:
            raise RuntimeError("A bridge day exceeds the saved witness horizon")
        risk_price_by_region_slot[:, start:stop] = (
            event_price * flexible_contract[index] / price_scale_mw
        )

    recomputed_starts, recomputed_cost = _select_risk_aligned_starts(
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
    saved_starts = job_summary["risk_aligned_start_slot"].to_numpy(dtype=np.int64)
    saved_cost = job_summary["risk_aligned_objective_usd"].to_numpy(dtype=float)
    start_mismatch = int(np.count_nonzero(recomputed_starts != saved_starts))
    max_cost_residual = float(np.max(np.abs(recomputed_cost - saved_cost)))

    daily_rows: list[dict[str, Any]] = []
    for index, day in enumerate(risk_days.tolist()):
        day_slice = slice(int(day) * slots_per_day, (int(day) + 1) * slots_per_day)
        target = risk_contract_profile[index]
        realization = risk_aligned_profile[:, day_slice] / dt_h + fixed_load_mw
        error = realization - target
        flexible_target = np.maximum(target - fixed_load_mw, 0.0)
        rmse = float(np.sqrt(np.mean(error**2)))
        flex_rmse = float(np.sqrt(np.mean(error**2)))
        # The flexible-target score is a relative L2 error.  Its denominator
        # must use the same RMS norm as the numerator; a mean-absolute
        # denominator artificially inflates the score when the fixed facility
        # load dominates the total profile.
        flexible_target_rms = max(
            float(np.sqrt(np.mean(flexible_target**2))), 1.0e-12
        )
        daily_rows.append(
            {
                "day": int(day),
                "target_total_energy_mwh": float(target.sum() * dt_h),
                "realized_total_energy_mwh": float(realization.sum() * dt_h),
                "signed_energy_residual_mwh": float(error.sum() * dt_h),
                "target_tracking_rmse_mw": rmse,
                "target_tracking_nrmse_total": rmse
                / max(float(np.mean(np.abs(target))), 1.0e-12),
                "target_tracking_nrmse_flexible": flex_rmse / flexible_target_rms,
                "target_tracking_relative_l2_flexible": float(np.linalg.norm(error))
                / max(float(np.linalg.norm(flexible_target)), 1.0e-12),
                "maximum_absolute_residual_mw": float(np.max(np.abs(error))),
                "realized_flexible_peak_mw": float(np.max(realization - fixed_load_mw)),
                "capacity_utilization_peak": float(
                    np.max(realization - fixed_load_mw) / max(capacity_mw, 1.0e-12)
                ),
            }
        )
    daily = pd.DataFrame(daily_rows)
    daily.to_csv(final / "executable_target_bridge_daily.csv", index=False)

    service_variables = int(np.sum(deadline_slot - submit_slot))
    candidate_count = int(len(submit_slot) * (queue_buffer_slots + 1))
    summary = _metric_rows(
        {
            "submitted_jobs": (float(len(submit_slot)), "jobs"),
            "service_variables": (float(service_variables), "job-slot variables"),
            "candidate_starts_per_job": (float(queue_buffer_slots + 1), "starts/job"),
            "enumerated_start_candidates": (float(candidate_count), "candidates"),
            "exact_start_mismatch_jobs": (float(start_mismatch), "jobs"),
            "maximum_objective_recomputation_residual_usd": (
                max_cost_residual,
                "USD",
            ),
            "mean_target_tracking_nrmse_total": (
                float(daily["target_tracking_nrmse_total"].mean()),
                "ratio",
            ),
            "mean_target_tracking_nrmse_flexible": (
                float(daily["target_tracking_nrmse_flexible"].mean()),
                "ratio",
            ),
            "mean_target_tracking_relative_l2_flexible": (
                float(daily["target_tracking_relative_l2_flexible"].mean()),
                "ratio",
            ),
            "maximum_absolute_target_residual_mw": (
                float(daily["maximum_absolute_residual_mw"].max()),
                "MW",
            ),
            "mean_signed_energy_residual_mwh": (
                float(daily["signed_energy_residual_mwh"].mean()),
                "MWh/day",
            ),
            "maximum_peak_capacity_utilization": (
                float(daily["capacity_utilization_peak"].max()),
                "ratio",
            ),
            "minimum_site_capacity_slack_mw": (
                capacity_mw - float(daily["realized_flexible_peak_mw"].max()),
                "MW",
            ),
            "risk_days": (float(len(risk_days)), "days"),
            "fixed_load_mw": (fixed_load_mw, "MW"),
            "flexible_capacity_mw": (capacity_mw, "MW"),
        }
    )
    summary.to_csv(final / "executable_target_bridge_audit.csv", index=False)

    metadata = {
        "experiment": "independent exact audit of the risk-to-executable bridge",
        "schema_version": 1,
        "optimization_class": "finite exact enumeration of every declaration-feasible contiguous start under a fixed linear dual-price surrogate",
        "heuristic_target_tracking": False,
        "target_tracking_definition": "daily total-profile RMSE divided by the flexible-target RMS; relative L2 is also reported",
        "future_arrivals_used": False,
        "execution_telemetry_used": False,
        "candidate_count_definition": "submitted jobs multiplied by queue allowance plus one",
        "submitted_jobs": int(len(submit_slot)),
        "service_variables": service_variables,
        "enumerated_start_candidates": candidate_count,
        "exact_start_mismatch_jobs": start_mismatch,
        "maximum_objective_recomputation_residual_usd": max_cost_residual,
        "mean_target_tracking_nrmse_total": float(daily["target_tracking_nrmse_total"].mean()),
        "mean_target_tracking_nrmse_flexible": float(daily["target_tracking_nrmse_flexible"].mean()),
        "mean_target_tracking_relative_l2_flexible": float(
            daily["target_tracking_relative_l2_flexible"].mean()
        ),
        "source_sha256": {
            "runtime_complete_witness.npz": _sha256(witness_path),
            "job_level_runtime_summary.csv": _sha256(job_path),
            "risk_to_executable_bridge.csv": _sha256(bridge_path),
        },
        "files": {
            "summary": "executable_target_bridge_audit.csv",
            "daily": "executable_target_bridge_daily.csv",
            "figure": "fig29_target_tracking.pdf",
        },
    }
    write_json(final / "experiment_metadata.json", metadata)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    representative = int(risk_days[0])
    representative_index = 0
    day_slice = slice(representative * slots_per_day, (representative + 1) * slots_per_day)
    target_day = risk_contract_profile[representative_index].sum(axis=0)
    realization_day = risk_aligned_profile[:, day_slice].sum(axis=0) / dt_h + fixed_load_mw * n_regions
    residual_day = realization_day - target_day
    x = np.arange(slots_per_day)
    # Keep the two-panel audit legible at IEEE two-column width without
    # displacing the reference list beyond the ten-page manuscript limit.
    fig, axes = plt.subplots(2, 1, figsize=(7.1, 3.25), sharex=True, constrained_layout=True)
    axes[0].plot(x, target_day, color="#0072B2", linewidth=1.8, label="Contract target")
    axes[0].plot(x, realization_day, color="#D55E00", linewidth=1.8, label="Executable witness")
    axes[0].set_ylabel("Total load (MW)")
    axes[0].set_title("Target-to-executable bridge on a locked day")
    axes[0].legend(frameon=False, fontsize=8, ncol=2)
    axes[0].grid(axis="y", alpha=0.25)
    axes[1].axhline(0.0, color="#333333", linewidth=0.8)
    axes[1].plot(x, residual_day, color="#009E73", linewidth=1.4)
    axes[1].set_ylabel("Residual (MW)")
    axes[1].set_xlabel("15-minute interval")
    axes[1].grid(axis="y", alpha=0.25)
    for axis in axes:
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
    for suffix in ("png", "pdf"):
        fig.savefig(figures / f"fig29_target_tracking.{suffix}", dpi=320, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    logger.info(
        "Exp29 target bridge audit [100%%]: %d candidates, start mismatches=%d, mean flexible nRMSE=%.4f",
        candidate_count,
        start_mismatch,
        float(daily["target_tracking_nrmse_flexible"].mean()),
    )
