from __future__ import annotations

import hashlib
import json
import logging
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from tqdm.auto import tqdm

from .utils import sha256, write_json


CLASS_NAMES = ("realtime_inference", "elastic_inference", "batch_gpu")


def preprocess_all(root: Path, cfg: dict[str, Any], force: bool, logger: logging.Logger) -> Path:
    out_dir = root / cfg["data"]["processed_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_paths = [root / p for p in cfg["data"]["burstgpt_files"]]
    scheduler_path = root / cfg["data"]["mit_scheduler"]
    dcgm_path = root / cfg["data"]["mit_dcgm"]
    pglib_path = root / cfg["data"]["pglib_case"]
    _validate_declared_raw_sources(
        root,
        out_dir / "data_manifest.json",
        [*raw_paths, scheduler_path, dcgm_path, pglib_path],
    )
    output = out_dir / "workload_15min.npz"
    if output.exists() and not force:
        try:
            with np.load(output, allow_pickle=False) as cached:
                required = {"arrivals_mwh", "observed_counterfactual_mw", "valid_days"}
                if required <= set(cached.files):
                    logger.info("Processed workload exists and passed archive validation: %s", output)
                    return output
        except (OSError, ValueError, zipfile.BadZipFile):
            logger.warning("Discarding incomplete processed workload archive: %s", output)

    for path in [*raw_paths, scheduler_path, dcgm_path, pglib_path]:
        if not path.exists() or path.stat().st_size == 0:
            raise FileNotFoundError(f"Required full dataset is missing: {path}")

    interval_s = int(cfg["project"]["interval_minutes"] * 60)
    slots_per_day = int(cfg["project"]["slots_per_day"])
    n_regions = int(cfg["project"]["number_of_regions"])
    logger.info("Aggregating all BurstGPT rows into %d-minute intervals", cfg["project"]["interval_minutes"])
    inference, request_counts, valid_slots, raw_stats = _aggregate_burstgpt(
        raw_paths, interval_s, slots_per_day, n_regions, logger
    )
    n_slots = inference.shape[0]
    logger.info("Aggregating measured MIT SuperCloud GPU energy for %d slots", n_slots)
    batch_arrivals, batch_observed, batch_stats = _aggregate_mit_jobs(
        scheduler_path, dcgm_path, n_slots, interval_s, n_regions, logger
    )
    calibration = _fit_dcgm_power_calibration(dcgm_path, int(cfg["project"]["seed"]), logger)

    dt_h = cfg["project"]["interval_minutes"] / 60.0
    q = float(cfg["data"]["percentile_for_scaling"])
    inf_raw_power = inference.sum(axis=(1, 2)) / dt_h
    batch_raw_power = batch_observed.sum(axis=1) / dt_h
    positive_inf = inf_raw_power[inf_raw_power > 0]
    positive_batch = batch_raw_power[batch_raw_power > 0]
    if len(positive_inf) == 0 or len(positive_batch) == 0:
        raise RuntimeError("Real workload aggregation produced no positive observations")
    inf_scale = float(cfg["data"]["inference_peak_target_mw"] / np.quantile(positive_inf, q))
    batch_scale = float(cfg["data"]["batch_peak_target_mw"] / np.quantile(positive_batch, q))
    inference *= inf_scale
    batch_arrivals *= batch_scale
    batch_observed *= batch_scale

    arrivals = np.zeros((n_slots, n_regions, len(CLASS_NAMES)), dtype=np.float64)
    arrivals[:, :, :2] = inference
    arrivals[:, :, 2] = batch_arrivals
    observed_energy = np.zeros_like(arrivals)
    observed_energy[:, :, :2] = inference
    observed_energy[:, :, 2] = batch_observed
    observed_power = float(cfg["project"]["fixed_facility_load_mw"]) + observed_energy.sum(axis=2) / dt_h
    day_index = np.arange(n_slots) // slots_per_day
    slot_index = np.arange(n_slots) % slots_per_day
    batch_balance = np.cumsum(batch_arrivals - batch_observed, axis=0)
    batch_balance = np.maximum(batch_balance, 0.0)
    n_days = n_slots // slots_per_day
    initial_batch_backlog = np.zeros((n_days, n_regions), dtype=np.float64)
    for day in range(1, n_days):
        initial_batch_backlog[day] = batch_balance[day * slots_per_day - 1]
    day_coverage = np.bincount(day_index, weights=valid_slots.astype(float), minlength=int(day_index.max()) + 1)
    valid_days = np.where(day_coverage >= 0.95 * slots_per_day)[0]

    # A complete preprocessing pass can take several minutes.  Write the
    # compressed archive through an open file handle and atomically replace the
    # previous artifact so an interrupted process can never leave a partial
    # ``.npz`` that later stages mistake for valid data.
    temporary_output = output.with_name(output.name + ".tmp")
    with temporary_output.open("wb") as handle:
        np.savez_compressed(
            handle,
            arrivals_mwh=arrivals,
            observed_energy_mwh=observed_energy,
            observed_counterfactual_mw=observed_power,
            initial_batch_backlog_mwh=initial_batch_backlog,
            request_counts=request_counts,
            valid_slots=valid_slots,
            valid_days=valid_days,
            day_index=day_index,
            slot_index=slot_index,
            class_names=np.array(CLASS_NAMES),
            inference_scale_mwh_per_token=inf_scale,
            batch_scale=batch_scale,
            interval_hours=dt_h,
        )
    temporary_output.replace(output)

    summary_rows = []
    for day in range(int(day_index.max()) + 1):
        sl = slice(day * slots_per_day, min((day + 1) * slots_per_day, n_slots))
        for region in range(n_regions):
            row = {"day": day, "region": region, "trace_available": int(day in set(valid_days.tolist()))}
            for k, name in enumerate(CLASS_NAMES):
                row[f"{name}_mwh"] = float(arrivals[sl, region, k].sum())
            row["total_mwh"] = sum(row[f"{name}_mwh"] for name in CLASS_NAMES)
            row["observed_execution_mwh"] = float(observed_energy[sl, region].sum())
            row["initial_batch_backlog_mwh"] = float(initial_batch_backlog[day, region])
            summary_rows.append(row)
    pd.DataFrame(summary_rows).to_csv(out_dir / "workload_daily_summary.csv", index=False)

    manifest = {
        "sources": [
            {"path": str(path.relative_to(root)), "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in [*raw_paths, scheduler_path, dcgm_path, pglib_path]
        ],
        "burstgpt": raw_stats,
        "mit_supercloud": batch_stats,
        "power_calibration": calibration,
        "processing": {
            "interval_seconds": interval_s,
            "regions": n_regions,
            "spatial_mapping": "deterministic multiplicative hash of immutable request/job row identifier",
            "inference_scale_mwh_per_token": inf_scale,
            "batch_hyperscale_multiplier": batch_scale,
            "scaling_quantile": q,
            "valid_days": valid_days.tolist(),
            "missing_trace_days": sorted(set(range(int(day_index.max()) + 1)) - set(valid_days.tolist())),
            "total_arrival_mwh": float(arrivals.sum()),
            "total_observed_execution_mwh": float(observed_energy.sum()),
            "counterfactual_reference": (
                "trace-anchored no-event execution reference; the demand-response "
                "intervention is generated separately by the declared event "
                "scheduling optimization"
            ),
            "initial_backlog_state": "cumulative submitted job energy minus cumulative measured execution energy at each day boundary",
            "maximum_initial_batch_backlog_mwh": float(initial_batch_backlog.max()),
        },
    }
    write_json(out_dir / "data_manifest.json", manifest)
    pd.DataFrame(
        [
            {
                "stage": "BurstGPT request ingestion",
                "input_records": int(raw_stats["rows"]),
                "retained_records": int(raw_stats["rows"]),
                "split_or_join_rule": "all rows in both no-failure releases",
                "downstream_role": "inference arrivals and observed service",
            },
            {
                "stage": "MIT scheduler-telemetry join",
                "input_records": int(batch_stats["scheduler_rows"]),
                "retained_records": int(batch_stats["valid_joined_jobs"]),
                "split_or_join_rule": "immutable job ID with positive measured energy",
                "downstream_role": "batch arrivals and independent execution",
            },
            {
                "stage": "DCGM power calibration",
                "input_records": int(calibration["observations"]),
                "retained_records": int(calibration["train_observations"]),
                "split_or_join_rule": "deterministic immutable-job training split",
                "downstream_role": "power-conversion model fitting",
            },
            {
                "stage": "DCGM held-out calibration",
                "input_records": int(calibration["observations"]),
                "retained_records": int(calibration["test_observations"]),
                "split_or_join_rule": "disjoint immutable-job test split",
                "downstream_role": "conversion scenarios and calibration scoring",
            },
            {
                "stage": "15-minute joint trace",
                "input_records": int(n_slots),
                "retained_records": int(len(valid_days) * slots_per_day),
                "split_or_join_rule": "at least 95% observed intervals per day",
                "downstream_role": "validation and locked evaluation",
            },
        ]
    ).to_csv(out_dir / "data_flow_audit.csv", index=False)
    logger.info("Processed workload written: %s; shape=%s; total=%.2f MWh", output, arrivals.shape, arrivals.sum())
    return output


def _validate_declared_raw_sources(
    root: Path, manifest_path: Path, configured_paths: list[Path]
) -> None:
    """Prevent stale processed results or truncation from entering a new run.

    The locked artifacts may be inspected without the raw inputs, but any new
    preprocessing pass must use the exact sources recorded by the previous
    manifest. This check is intentionally fail-closed because silently
    rebuilding the processed arrays from a partial CSV would invalidate every
    downstream experiment while leaving the old manuscript numbers in place.
    """
    if not manifest_path.exists():
        return
    try:
        declared = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Cannot read raw-source manifest: {manifest_path}") from exc
    expected = {str(item["path"]): item for item in declared.get("sources", [])}
    mismatches: list[str] = []
    for path in configured_paths:
        relative = str(path.relative_to(root))
        source = expected.get(relative)
        if source is None:
            continue
        if not path.exists():
            mismatches.append(f"{relative}: missing")
            continue
        actual_size = path.stat().st_size
        actual_hash = sha256(path)
        if actual_size != int(source.get("bytes", -1)) or actual_hash != source.get("sha256"):
            mismatches.append(
                f"{relative}: expected {source.get('bytes')} bytes/{source.get('sha256')}, "
                f"found {actual_size} bytes/{actual_hash}"
            )
    if mismatches:
        joined = "\n".join(f"- {item}" for item in mismatches)
        raise RuntimeError(
            "Raw inputs do not match data/processed/data_manifest.json. "
            "Restore the original files before preprocessing; the locked "
            "processed artifacts will not be rebuilt from truncated inputs.\n"
            + joined
        )


def _aggregate_burstgpt(
    paths: list[Path], interval_s: int, slots_per_day: int, n_regions: int, logger: logging.Logger
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    max_timestamp = 0
    total_rows = 0
    file_rows: dict[str, int] = {}
    file_ranges: dict[str, tuple[int, int]] = {}
    for path in paths:
        local_rows = 0
        local_min: int | None = None
        local_max: int | None = None
        for chunk in pd.read_csv(path, usecols=["Timestamp"], chunksize=500_000):
            numeric = pd.to_numeric(chunk["Timestamp"], errors="coerce").dropna()
            if len(numeric):
                chunk_min = int(numeric.min())
                chunk_max = int(numeric.max())
                local_min = chunk_min if local_min is None else min(local_min, chunk_min)
                local_max = chunk_max if local_max is None else max(local_max, chunk_max)
                max_timestamp = max(max_timestamp, chunk_max)
            local_rows += len(chunk)
        file_rows[path.name] = local_rows
        if local_min is None or local_max is None:
            raise ValueError(f"No valid timestamp in {path}")
        file_ranges[path.name] = (local_min, local_max)
        total_rows += local_rows
    n_slots = max_timestamp // interval_s + 1
    n_days = (n_slots + slots_per_day - 1) // slots_per_day
    n_slots = n_days * slots_per_day
    energy = np.zeros((n_slots, n_regions, 2), dtype=np.float64)
    counts = np.zeros((n_slots, n_regions, 2), dtype=np.int64)
    valid_slots = np.zeros(n_slots, dtype=bool)
    # An interval with zero requests is a measured zero, not missing data. Coverage is
    # therefore derived from each source file's timestamp support rather than occupancy.
    for first_timestamp, last_timestamp in file_ranges.values():
        first_slot = max(0, first_timestamp // interval_s)
        last_slot = min(n_slots - 1, last_timestamp // interval_s)
        valid_slots[first_slot : last_slot + 1] = True
    global_row = 0
    model_counts: dict[str, int] = {}
    log_counts: dict[str, int] = {}

    for path in paths:
        iterator = pd.read_csv(path, chunksize=250_000)
        for chunk in tqdm(iterator, total=(file_rows[path.name] + 249_999) // 250_000, desc=f"BurstGPT {path.stem}"):
            required = {"Timestamp", "Total tokens", "Log Type", "Model"}
            if not required.issubset(chunk.columns):
                raise ValueError(f"Unexpected BurstGPT schema in {path}: {chunk.columns.tolist()}")
            timestamp = pd.to_numeric(chunk["Timestamp"], errors="coerce").to_numpy()
            tokens = pd.to_numeric(chunk["Total tokens"], errors="coerce").fillna(0).to_numpy(dtype=float)
            good = np.isfinite(timestamp) & (timestamp >= 0) & np.isfinite(tokens) & (tokens > 0)
            row_ids = global_row + np.arange(len(chunk), dtype=np.int64)
            # Multiplicative hashing gives a deterministic, balanced experimental region assignment.
            regions = ((row_ids * np.int64(2654435761) + np.int64(1013904223)) % n_regions).astype(int)
            classes = np.where(chunk["Log Type"].astype(str).str.contains("Conversation", case=False), 0, 1)
            slots = (timestamp // interval_s).astype(np.int64, copy=False)
            for k in (0, 1):
                mask_k = good & (classes == k) & (slots < n_slots)
                if not np.any(mask_k):
                    continue
                np.add.at(energy[:, :, k], (slots[mask_k], regions[mask_k]), tokens[mask_k])
                np.add.at(counts[:, :, k], (slots[mask_k], regions[mask_k]), 1)
            for key, value in chunk["Model"].value_counts().items():
                model_counts[str(key)] = model_counts.get(str(key), 0) + int(value)
            for key, value in chunk["Log Type"].value_counts().items():
                log_counts[str(key)] = log_counts.get(str(key), 0) + int(value)
            global_row += len(chunk)
    stats = {
        "rows": total_rows,
        "files": file_rows,
        "file_timestamp_ranges_seconds": {name: list(bounds) for name, bounds in file_ranges.items()},
        "max_timestamp_seconds": max_timestamp,
        "model_counts": model_counts,
        "log_type_counts": log_counts,
        "total_tokens": float(energy.sum()),
        "valid_intervals": int(valid_slots.sum()),
    }
    logger.info("BurstGPT aggregation complete: %s rows, %.0f tokens", f"{total_rows:,}", energy.sum())
    return energy, counts, valid_slots, stats


def _aggregate_mit_jobs(
    scheduler_path: Path,
    dcgm_path: Path,
    n_slots: int,
    interval_s: int,
    n_regions: int,
    logger: logging.Logger,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    dcgm = pd.read_csv(
        dcgm_path,
        usecols=["id_job", "energyconsumed_joules", "powerusage_watts_avg", "totalexecutiontime_sec"],
    )
    dcgm = dcgm.replace([np.inf, -np.inf], np.nan).dropna(subset=["id_job", "energyconsumed_joules"])
    measured = dcgm.groupby("id_job", as_index=False).agg(
        energy_j=("energyconsumed_joules", "sum"),
        gpu_power_w=("powerusage_watts_avg", "sum"),
        measured_runtime_s=("totalexecutiontime_sec", "max"),
        measured_gpus=("id_job", "size"),
    )
    scheduler = pd.read_csv(
        scheduler_path,
        usecols=["id_job", "time_start", "time_end", "time_submit", "gres_req", "job_type", "state"],
    )
    scheduler = scheduler.sort_values(["id_job", "time_end"]).drop_duplicates("id_job", keep="last")
    jobs = scheduler.merge(measured, on="id_job", how="inner", validate="one_to_one")
    jobs = jobs[
        (jobs["time_start"] >= 0)
        & (jobs["time_end"] > jobs["time_start"])
        & (jobs["energy_j"] > 0)
    ].copy()
    # The MIT and BurstGPT releases each use their own relative clock. Preserve every
    # observed inter-arrival time while aligning the first eligible measured MIT job
    # with the beginning of the common counterfactual horizon.
    time_origin_s = float(jobs["time_start"].min())
    jobs["time_submit_aligned"] = jobs["time_submit"] - time_origin_s
    jobs["time_start_aligned"] = jobs["time_start"] - time_origin_s
    jobs["time_end_aligned"] = jobs["time_end"] - time_origin_s
    jobs = jobs[jobs["time_start_aligned"] < n_slots * interval_s].copy()
    arrivals = np.zeros((n_slots, n_regions), dtype=np.float64)
    observed = np.zeros((n_slots, n_regions), dtype=np.float64)
    used_energy = 0.0
    clipped_jobs = 0
    for row in tqdm(jobs.itertuples(index=False), total=len(jobs), desc="MIT measured jobs"):
        start = float(row.time_start_aligned)
        end = min(float(row.time_end_aligned), n_slots * interval_s)
        if end <= start:
            continue
        duration = float(row.time_end_aligned - row.time_start_aligned)
        region = int(int(row.id_job) % n_regions)
        first = int(start // interval_s)
        last = int(np.ceil(end / interval_s)) - 1
        energy_mwh = float(row.energy_j) / 3.6e9
        # Work enters the controllable queue at submission, not when it happened
        # to execute. Jobs already queued at the common origin form initial backlog.
        submit_slot = int(max(0.0, float(row.time_submit_aligned)) // interval_s)
        if submit_slot < n_slots:
            arrivals[submit_slot, region] += energy_mwh
        for slot in range(first, min(last + 1, n_slots)):
            overlap = max(0.0, min(end, (slot + 1) * interval_s) - max(start, slot * interval_s))
            if overlap > 0:
                allocated = energy_mwh * overlap / duration
                observed[slot, region] += allocated
                used_energy += allocated
        if row.time_end_aligned > n_slots * interval_s:
            clipped_jobs += 1
    stats = {
        "scheduler_rows": int(len(scheduler)),
        "dcgm_rows": int(len(dcgm)),
        "measured_unique_jobs": int(measured["id_job"].nunique()),
        "valid_joined_jobs": int(len(jobs)),
        "time_origin_seconds": time_origin_s,
        "clipped_at_trace_horizon": int(clipped_jobs),
        "measured_energy_mwh_within_horizon": used_energy,
        "submitted_energy_mwh": float(arrivals.sum()),
        "jobs_already_queued_at_origin": int((jobs["time_submit_aligned"] < 0).sum()),
        "completion_delay_slots_quantiles": {
            str(q): float(np.quantile((jobs["time_end"] - jobs["time_submit"]) / interval_s, q))
            for q in [0.5, 0.9, 0.95, 0.99]
        },
        "temporalization": "queue arrivals use scheduler submission time; independent counterfactual truth uses DCGM energy allocated over measured execution intervals",
    }
    logger.info("MIT aggregation complete: %s measured jobs, %.4f raw MWh", f"{len(jobs):,}", used_energy)
    return arrivals, observed, stats


def _fit_dcgm_power_calibration(path: Path, seed: int, logger: logging.Logger) -> dict[str, Any]:
    columns = [
        "id_job",
        "powerusage_watts_avg",
        "smutilization_pct_avg",
        "memoryutilization_pct_avg",
        "maxgpumemoryused_bytes",
        "totalexecutiontime_sec",
    ]
    df = pd.read_csv(path, usecols=columns).replace([np.inf, -np.inf], np.nan).dropna()
    df = df[(df["powerusage_watts_avg"] > 0) & (df["totalexecutiontime_sec"] > 0)].copy()
    df["log_gpu_memory"] = np.log1p(df["maxgpumemoryused_bytes"].clip(lower=0))
    df["log_runtime"] = np.log1p(df["totalexecutiontime_sec"].clip(lower=0))
    features = ["smutilization_pct_avg", "memoryutilization_pct_avg", "log_gpu_memory", "log_runtime"]
    mask = (df["id_job"].astype(np.int64) % 10) < 7
    model = Ridge(alpha=10.0)
    model.fit(df.loc[mask, features], df.loc[mask, "powerusage_watts_avg"])
    pred = model.predict(df.loc[~mask, features])
    truth = df.loc[~mask, "powerusage_watts_avg"].to_numpy()
    residual = truth - pred
    heldout = df.loc[
        ~mask, ["id_job", "totalexecutiontime_sec"]
    ].copy()
    heldout["measured_energy_joules"] = (
        truth * heldout["totalexecutiontime_sec"].to_numpy()
    )
    heldout["predicted_energy_joules"] = (
        np.maximum(0.0, pred)
        * heldout["totalexecutiontime_sec"].to_numpy()
    )
    job_energy = heldout.groupby("id_job", as_index=False).agg(
        measured_energy_joules=("measured_energy_joules", "sum"),
        predicted_energy_joules=("predicted_energy_joules", "sum"),
    )
    job_energy = job_energy[
        (job_energy["measured_energy_joules"] > 0)
        & (job_energy["predicted_energy_joules"] > 0)
    ].copy()
    job_energy["measured_to_predicted_ratio"] = (
        job_energy["measured_energy_joules"]
        / job_energy["predicted_energy_joules"]
    )
    conversion_quantiles = [0.01, 0.1, 0.5, 0.9, 0.99]
    payload = {
        "observations": int(len(df)),
        "train_observations": int(mask.sum()),
        "test_observations": int((~mask).sum()),
        "features": features,
        "coefficients": model.coef_.tolist(),
        "intercept_watts": float(model.intercept_),
        "test_mae_watts": float(mean_absolute_error(truth, pred)),
        "test_rmse_watts": float(mean_squared_error(truth, pred) ** 0.5),
        "test_r2": float(r2_score(truth, pred)),
        "measured_power_quantiles_watts": {
            str(q): float(np.quantile(df["powerusage_watts_avg"], q)) for q in [0.01, 0.1, 0.5, 0.9, 0.99]
        },
        "heldout_residual_quantiles_watts": {
            str(q): float(np.quantile(residual, q)) for q in [0.01, 0.1, 0.5, 0.9, 0.99]
        },
        "heldout_jobs_with_positive_prediction": int(len(job_energy)),
        "heldout_job_energy_measured_to_predicted_quantiles": {
            str(q): float(
                np.quantile(
                    job_energy["measured_to_predicted_ratio"], q
                )
            )
            for q in conversion_quantiles
        },
        "heldout_aggregate_measured_to_predicted_energy_ratio": float(
            job_energy["measured_energy_joules"].sum()
            / job_energy["predicted_energy_joules"].sum()
        ),
    }
    logger.info("Held-out DCGM power calibration: R2=%.3f, RMSE=%.2f W", payload["test_r2"], payload["test_rmse_watts"])
    return payload


def load_workload(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as data:
        return {key: data[key] for key in data.files}


def load_mit_job_ledger(
    scheduler_path: Path,
    dcgm_path: Path,
    interval_s: int,
    n_slots: int | None,
    n_regions: int,
) -> pd.DataFrame:
    """Return the complete measured-job ledger used by exact replay checks.

    The join is the same immutable ``id_job``/positive-energy join used by
    :func:`_aggregate_mit_jobs`, but it retains release, execution, deadline,
    measured energy, GPU count and a deterministic spatial label.  No sample,
    synthetic row, or heuristic deadline is introduced.  The observed
    completion time is used only as a retrospective deadline witness in the
    job-level fidelity experiment.
    """
    dcgm = pd.read_csv(
        dcgm_path,
        usecols=[
            "id_job",
            "energyconsumed_joules",
            "powerusage_watts_avg",
            "totalexecutiontime_sec",
        ],
    )
    dcgm = dcgm.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["id_job", "energyconsumed_joules"]
    )
    measured = dcgm.groupby("id_job", as_index=False).agg(
        energy_j=("energyconsumed_joules", "sum"),
        gpu_power_w=("powerusage_watts_avg", "sum"),
        measured_runtime_s=("totalexecutiontime_sec", "max"),
        measured_gpus=("id_job", "size"),
    )
    scheduler = pd.read_csv(
        scheduler_path,
        usecols=[
            "id_job",
            "time_start",
            "time_end",
            "time_submit",
            "gres_req",
            "job_type",
            "state",
        ],
    )
    scheduler = scheduler.sort_values(["id_job", "time_end"]).drop_duplicates(
        "id_job", keep="last"
    )
    jobs = scheduler.merge(measured, on="id_job", how="inner", validate="one_to_one")
    jobs = jobs[
        (jobs["time_start"] >= 0)
        & (jobs["time_end"] > jobs["time_start"])
        & (jobs["energy_j"] > 0)
    ].copy()
    if jobs.empty:
        raise RuntimeError("MIT scheduler/DCGM join returned no positive-energy jobs")
    origin = float(jobs["time_start"].min())
    if n_slots is None:
        n_slots = int(
            np.ceil(
                (float(jobs["time_end"].max()) - origin) / float(interval_s)
            )
        )
    if n_slots <= 0:
        raise ValueError("n_slots must be positive or None")
    jobs["submit_slot"] = np.floor(
        np.maximum(0.0, jobs["time_submit"].to_numpy(dtype=float) - origin)
        / float(interval_s)
    ).astype(np.int64)
    jobs["start_slot"] = np.floor(
        np.maximum(0.0, jobs["time_start"].to_numpy(dtype=float) - origin)
        / float(interval_s)
    ).astype(np.int64)
    jobs["deadline_slot"] = np.ceil(
        (jobs["time_end"].to_numpy(dtype=float) - origin) / float(interval_s)
    ).astype(np.int64)
    jobs["submit_slot_raw"] = jobs["submit_slot"]
    jobs["deadline_slot_raw"] = jobs["deadline_slot"]
    jobs["submit_slot"] = jobs["submit_slot"].clip(lower=0, upper=n_slots - 1)
    jobs["start_slot"] = jobs["start_slot"].clip(lower=0, upper=n_slots - 1)
    jobs["deadline_slot"] = jobs["deadline_slot"].clip(lower=1, upper=n_slots)
    jobs["energy_mwh"] = jobs["energy_j"].to_numpy(dtype=float) / 3.6e9
    jobs["region"] = jobs["id_job"].astype(np.int64) % int(n_regions)
    jobs["within_horizon"] = (
        (jobs["submit_slot_raw"] < int(n_slots))
        & (jobs["start_slot"] < int(n_slots))
        & (jobs["deadline_slot"] > jobs["submit_slot"])
        & (jobs["energy_mwh"] > 0)
    )
    joined_jobs_before_horizon_filter = int(len(jobs))
    jobs = jobs[jobs["within_horizon"]].copy()
    jobs["deadline_slot"] = np.clip(np.maximum(
        jobs["deadline_slot"].to_numpy(dtype=np.int64),
        jobs["submit_slot"].to_numpy(dtype=np.int64) + 1,
    ), 1, n_slots)
    jobs.attrs["time_origin_seconds"] = origin
    jobs.attrs["scheduler_rows"] = int(len(scheduler))
    jobs.attrs["dcgm_rows"] = int(len(dcgm))
    jobs.attrs["joined_jobs_before_horizon_filter"] = joined_jobs_before_horizon_filter
    jobs.attrs["joined_jobs_after_horizon_filter"] = int(len(jobs))
    return jobs.reset_index(drop=True)


def audit_mit_ledger_provenance(
    scheduler_path: Path,
    dcgm_path: Path,
    processed_workload: dict[str, np.ndarray],
    interval_minutes: float,
    configured_capacity_mw: float,
    n_regions: int,
) -> tuple[dict[str, Any], pd.DataFrame]:
    """Build a source-bound, immutable-row provenance certificate.

    The certificate is computed directly from the public scheduler and DCGM
    releases.  It does not synthesize jobs, infer missing deadlines, or alter
    the source rows.  The canonical digest detects changes to the exact joined
    ledger used by the workload-flow experiments; the independent raw-to-join
    energy check verifies that aggregation has not silently dropped positive
    energy.  The capacity table is a measurement reconciliation: it reports
    the configured study capacity alongside the observed per-region envelope.
    """
    scheduler_columns = [
        "id_job", "time_start", "time_end", "time_submit",
        "gres_req", "job_type", "state",
    ]
    dcgm_columns = [
        "id_job", "energyconsumed_joules", "powerusage_watts_avg",
        "totalexecutiontime_sec",
    ]
    scheduler_raw = pd.read_csv(scheduler_path, usecols=scheduler_columns)
    dcgm_raw = pd.read_csv(dcgm_path, usecols=dcgm_columns)
    dcgm_clean = dcgm_raw.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["id_job", "energyconsumed_joules"]
    )
    scheduler_clean = scheduler_raw.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["id_job", "time_start", "time_end", "time_submit"]
    )
    scheduler_last = scheduler_clean.sort_values(["id_job", "time_end"]).drop_duplicates(
        "id_job", keep="last"
    )
    telemetry_by_job = dcgm_clean.groupby("id_job", as_index=False).agg(
        energy_j=("energyconsumed_joules", "sum"),
        telemetry_rows=("id_job", "size"),
    )
    joined = scheduler_last.merge(
        telemetry_by_job, on="id_job", how="inner", validate="one_to_one"
    )
    joined = joined[
        (joined["time_start"] >= 0)
        & (joined["time_end"] > joined["time_start"])
        & (joined["energy_j"] > 0)
    ].copy()
    canonical_columns = [
        "id_job", "time_submit", "time_start", "time_end", "energy_j",
        "telemetry_rows", "gres_req", "job_type", "state",
    ]
    canonical = joined[canonical_columns].sort_values("id_job").copy()
    canonical_text = canonical.to_csv(
        index=False, lineterminator="\n", float_format="%.17g"
    ).encode("utf-8")
    digest = hashlib.sha256(canonical_text).hexdigest()
    joined_energy_j = float(joined["energy_j"].sum())
    positive_dcgm = dcgm_clean[dcgm_clean["energyconsumed_joules"] > 0]
    positive_dcgm_energy_j = float(positive_dcgm["energyconsumed_joules"].sum())
    # The comparison is intentionally restricted to IDs retained by the exact
    # scheduler/telemetry join; rows outside that join are reported, never imputed.
    retained_ids = set(joined["id_job"].tolist())
    retained_dcgm_energy_j = float(
        positive_dcgm[positive_dcgm["id_job"].isin(retained_ids)]["energyconsumed_joules"].sum()
    )
    temporal = (
        (joined["time_submit"] <= joined["time_start"])
        & (joined["time_start"] < joined["time_end"])
    )
    release_execution = joined["time_submit"] <= joined["time_start"]
    execution_order = joined["time_start"] < joined["time_end"]
    dt_h = float(interval_minutes) / 60.0
    observed_batch = np.asarray(processed_workload["observed_energy_mwh"][:, :, 2], dtype=float)
    slots_per_day = int(processed_workload["observed_energy_mwh"].shape[0] // max(1, len(processed_workload.get("valid_days", []))))
    if slots_per_day <= 0:
        slots_per_day = 96
    observed_power = observed_batch / dt_h
    capacity_rows: list[dict[str, Any]] = []
    for region in range(int(n_regions)):
        values = observed_power[:, region]
        capacity_rows.append(
            {
                "region": int(region),
                "configured_flexible_capacity_mw": float(configured_capacity_mw),
                "observed_p50_mw": float(np.quantile(values, 0.50)),
                "observed_p95_mw": float(np.quantile(values, 0.95)),
                "observed_p99_mw": float(np.quantile(values, 0.99)),
                "observed_peak_mw": float(np.max(values)),
                "capacity_excess_peak_mw": float(max(0.0, np.max(values) - configured_capacity_mw)),
                "slots_above_configured_capacity": int(np.sum(values > configured_capacity_mw + 1e-9)),
                "observed_slots": int(values.size),
            }
        )
    capacity = pd.DataFrame(capacity_rows)
    all_slots = int(observed_power.shape[0])
    summary: dict[str, Any] = {
        "certificate_type": "immutable scheduler/DCGM ledger provenance and capacity reconciliation",
        "source_files": {
            "scheduler": str(scheduler_path),
            "dcgm": str(dcgm_path),
        },
        "scheduler_rows": int(len(scheduler_raw)),
        "scheduler_unique_job_ids": int(scheduler_raw["id_job"].nunique()),
        "scheduler_duplicate_rows_after_last_record_rule": int(len(scheduler_raw) - len(scheduler_last)),
        "dcgm_rows": int(len(dcgm_raw)),
        "dcgm_unique_job_ids": int(dcgm_raw["id_job"].nunique()),
        "joined_positive_energy_jobs": int(len(joined)),
        "joined_positive_energy_fraction_of_scheduler_ids": float(
            len(joined) / max(1, scheduler_raw["id_job"].nunique())
        ),
        "temporal_order_fraction": float(temporal.mean()) if len(temporal) else 0.0,
        "release_before_start_fraction": float(release_execution.mean()) if len(release_execution) else 0.0,
        "start_before_end_fraction": float(execution_order.mean()) if len(execution_order) else 0.0,
        "positive_energy_fraction": float((joined["energy_j"] > 0).mean()) if len(joined) else 0.0,
        "positive_dcgm_energy_j": positive_dcgm_energy_j,
        "retained_join_energy_j": retained_dcgm_energy_j,
        "joined_energy_sum_j": joined_energy_j,
        "raw_to_join_energy_residual_j": float(retained_dcgm_energy_j - joined_energy_j),
        "canonical_joined_ledger_sha256": digest,
        "canonical_row_count": int(len(canonical)),
        "integrity_conditions": {
            "one_to_one_scheduler_record_after_declared_last_record_rule": True,
            "positive_energy_join_only": True,
            "release_before_execution": bool(temporal.all()) if len(temporal) else False,
            "release_before_start": bool(release_execution.all()) if len(release_execution) else False,
            "start_before_end": bool(execution_order.all()) if len(execution_order) else False,
            "raw_to_join_energy_conservation": bool(
                np.isclose(retained_dcgm_energy_j, joined_energy_j, rtol=0, atol=1e-6)
            ),
            "no_synthetic_rows": True,
            "no_imputation": True,
        },
        "capacity_measurement": {
            "interval_hours": dt_h,
            "observed_profile_slots": all_slots,
            "configured_capacity_mw": float(configured_capacity_mw),
            "maximum_observed_peak_mw": float(capacity["observed_peak_mw"].max()),
            "maximum_peak_to_configured_capacity_ratio": float(
                capacity["observed_peak_mw"].max() / max(float(configured_capacity_mw), 1e-12)
            ),
            "capacity_rows_are_observed_execution_envelope": True,
        },
    }
    return summary, capacity
