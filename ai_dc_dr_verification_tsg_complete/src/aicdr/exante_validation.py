"""Independent validation of the submit-time job contract."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import linprog
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
    dcgm_ids = pd.read_csv(
        root / cfg["data"]["mit_dcgm"],
        usecols=["id_job", "energyconsumed_joules"],
    )
    eligible_job_ids = set(
        dcgm_ids.loc[
            pd.to_numeric(dcgm_ids["energyconsumed_joules"], errors="coerce") > 0,
            "id_job",
        ].astype(np.int64)
    )
    submission = load_mit_submission_ledger(
        root / cfg["data"]["mit_scheduler"],
        interval_s,
        None,
        n_regions,
        declared_service_fraction=float(calibration["declared_service_fraction"]),
        declared_per_gpu_power_cap_mw=cap_mw,
        unbounded_timelimit_slots=runtime_fallback,
        submission_buffer_slots=queue_buffer,
        eligible_job_ids=eligible_job_ids,
    )
    execution = load_mit_job_ledger(
        root / cfg["data"]["mit_scheduler"],
        root / cfg["data"]["mit_dcgm"],
        interval_s,
        None,
        n_regions,
        deadline_mode="observed",
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
    # declared window intersects that day's event is retained.  Capacity rows
    # are imposed only on the eight event slots, and a precommitted event
    # service floor makes the rows operationally binding.  This is a compact
    # sparse LP certificate, not a sampled or clipped trajectory.
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
    stress_upper = np.repeat(
        stress_gpus
        * cap_mw
        * dt_h,
        stress_counts,
    )
    stress_event_mask = (
        (stress_slots >= event_start)
        & (stress_slots < event_end)
        & np.isin(stress_slots % slots_per_day, event_slots)
    )
    event_slot_values = np.asarray(
        [stress_day * slots_per_day + slot for slot in event_slots], dtype=np.int64
    )
    event_position = {
        int(slot): index for index, slot in enumerate(event_slot_values.tolist())
    }
    event_var_indices = np.flatnonzero(stress_event_mask)
    if len(event_var_indices) == 0:
        raise RuntimeError("The predeclared Exp25 stress cohort has no event variables")
    capacity_rows = (
        stress_regions[event_var_indices] * len(event_slot_values)
        + np.asarray(
            [event_position[int(slot)] for slot in stress_slots[event_var_indices]],
            dtype=np.int64,
        )
    )
    capacity_row_count = n_regions * len(event_slot_values)
    floor_row = capacity_row_count
    ub_rows = np.concatenate([capacity_rows, np.full(len(event_var_indices), floor_row)])
    ub_cols = np.concatenate([event_var_indices, event_var_indices])
    ub_values = np.concatenate(
        [
            np.ones(len(event_var_indices), dtype=float),
            -np.ones(len(event_var_indices), dtype=float),
        ]
    )
    a_ub = coo_matrix(
        (ub_values, (ub_rows, ub_cols)),
        shape=(capacity_row_count + 1, len(stress_slots)),
    ).tocsr()
    a_eq = coo_matrix(
        (
            np.ones(len(stress_slots), dtype=float),
            (stress_jobs, np.arange(len(stress_slots), dtype=np.int64)),
        ),
        shape=(len(cohort), len(stress_slots)),
    ).tocsr()
    waiting = float(cfg["workload"]["waiting_cost_per_mwh_slot"][-1]) * (
        stress_slots - np.repeat(stress_starts, stress_counts)
    )
    stress_objective = waiting + float(cfg["market"]["default_dr_price_per_mwh"]) * stress_event_mask
    stress_scale = 1.0e6
    stress_result = linprog(
        stress_objective / stress_scale,
        A_ub=a_ub,
        b_ub=np.concatenate(
            [
                np.full(capacity_row_count, stress_capacity_mw * dt_h * stress_scale),
                np.asarray([-stress_floor_mwh * stress_scale]),
            ]
        ),
        A_eq=a_eq,
        b_eq=stress_energy * stress_scale,
        bounds=np.column_stack(
            [np.zeros(len(stress_slots)), stress_upper * stress_scale]
        ),
        method="highs",
        options={"presolve": True},
    )
    if not stress_result.success:
        raise RuntimeError("Exp25 binding-capacity LP failed: " + str(stress_result.message))
    stress_service = np.asarray(stress_result.x, dtype=float) / stress_scale
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
        "submitted_jobs": int(len(submission)),
        "execution_matched_jobs": int(len(joined)),
        "declared_service_fraction": float(calibration["declared_service_fraction"]),
        "physical_upper_service_fraction": float(calibration["physical_upper_service_fraction"]),
        "declared_per_gpu_power_cap_mw": cap_mw,
        "unbounded_timelimit_slots": runtime_fallback,
        "submission_buffer_slots": queue_buffer,
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
            "capacity_mw_per_region": stress_capacity_mw,
            "event_service_floor_mwh": stress_floor_mwh,
            "event_service_delivered_mwh": float(stress_profile[:, event_slot_values].sum()),
            "active_event_capacity_slot_fraction": float(np.mean(stress_capacity_slack <= 1e-10)),
            "minimum_event_capacity_slack_mwh": float(stress_capacity_slack.min()),
            "maximum_job_energy_residual_mwh": float(np.max(np.abs(stress_job_residual))),
            "solver_success": True,
            "solution_file": "job_level_capacity_stress_solution.npz",
        },
        "interpretation": (
            "The central declaration is a training-only ex-ante entitlement; the "
            "full requested nameplate is the physical upper bound. Observed DCGM "
            "energy is reported for coverage and cannot alter a release, deadline, "
            "or service equality."
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
