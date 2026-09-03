from __future__ import annotations

import hashlib
import json
import logging
import re
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from .progress import progress as tqdm

from .utils import sha256, write_json


CLASS_NAMES = ("realtime_inference", "elastic_inference", "batch_gpu")


_GPU_REQUEST_PATTERN = re.compile(r"(?:gpu|gres/gpu)([^,;\s]*)", re.IGNORECASE)


def _parse_requested_gpu_count(value: object) -> int | None:
    """Parse a Slurm GPU request without consulting allocation telemetry.

    The MIT scheduler release uses forms such as ``gpu:1`` and
    ``gpu:volta:8``.  A missing request is treated as unknown and is rejected
    by the submission-ledger loader; silently replacing it with one GPU would
    be an outcome-dependent capacity heuristic.
    """
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return None
    match = _GPU_REQUEST_PATTERN.search(str(value))
    if match is None:
        return None
    # Vendor/type identifiers can contain digits (e.g., ``gpu:a100:8``); the
    # final numeric token is the requested count.
    tokens = re.findall(r"[0-9]+", match.group(1))
    if not tokens:
        return None
    count = int(tokens[-1])
    return count if count > 0 else None


def _declared_runtime_slots(
    timelimit: np.ndarray,
    interval_s: int,
    unbounded_timelimit_slots: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Convert the submitted allocation runtime to finite interval slots."""
    values = np.asarray(timelimit, dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("timelimit contains non-finite values")
    if int(unbounded_timelimit_slots) <= 0:
        raise ValueError("unbounded_timelimit_slots must be positive")
    unlimited = values >= np.iinfo(np.uint32).max - 1
    runtime = np.where(
        unlimited,
        int(unbounded_timelimit_slots),
        np.maximum(1, np.ceil(values / float(interval_s)).astype(np.int64)),
    ).astype(np.int64)
    return runtime, unlimited


def _balanced_submission_region_labels(frame: pd.DataFrame, n_regions: int) -> np.ndarray:
    """Assign deterministic scenario regions from submit-time fields only."""
    if n_regions <= 0:
        raise ValueError("n_regions must be positive")
    required = {
        "id_job",
        "time_submit",
        "requested_gpus",
        "declared_runtime_slots",
        "job_type",
        "gres_req",
    }
    if not required.issubset(frame.columns):
        missing = sorted(required.difference(frame.columns))
        raise ValueError(f"missing columns for submission region scenario: {missing}")
    work = frame.copy()
    job_codes = pd.Categorical(work["job_type"].fillna("").astype(str)).codes
    gres_codes = pd.Categorical(work["gres_req"].fillna("").astype(str)).codes
    order = np.lexsort(
        (
            work["id_job"].to_numpy(dtype=np.int64),
            work["time_submit"].to_numpy(dtype=float),
            work["declared_runtime_slots"].to_numpy(dtype=np.int64),
            work["requested_gpus"].to_numpy(dtype=np.int64),
            gres_codes,
            job_codes,
        )
    )
    labels = np.empty(len(work), dtype=np.int64)
    labels[order] = np.arange(len(work), dtype=np.int64) % int(n_regions)
    return labels


def _balanced_trace_region_labels(frame: pd.DataFrame, n_regions: int) -> np.ndarray:
    """Assign a reproducible region *scenario* without hashing identifiers.

    The public BurstGPT and MIT releases do not expose utility locations.  A
    row-identifier hash would therefore create a visually convenient but
    irreproducible pseudo-geography.  This rule first sorts immutable records
    by observed workload signature and then distributes each stratum in a
    round-robin cycle.  It preserves the marginal mix of workload classes,
    runtimes, GPU counts, and energy across the declared regions while making
    clear that the labels are contractual scenario factors, not measured
    locations.  All location-to-bus permutations are evaluated downstream.
    """
    if n_regions <= 0:
        raise ValueError("n_regions must be positive")
    required = {"id_job", "energy_j", "time_submit_aligned", "time_end_aligned", "time_start_aligned"}
    if not required.issubset(frame.columns):
        missing = sorted(required.difference(frame.columns))
        raise ValueError(f"missing columns for deterministic region scenario: {missing}")
    work = frame.copy()
    job_type = work.get("job_type", pd.Series("", index=work.index)).fillna("").astype(str)
    gres = work.get("gres_req", pd.Series("", index=work.index)).fillna("").astype(str)
    job_type_codes = pd.Categorical(job_type).codes
    gres_codes = pd.Categorical(gres).codes
    runtime = np.maximum(
        work["time_end_aligned"].to_numpy(dtype=float)
        - work["time_start_aligned"].to_numpy(dtype=float),
        0.0,
    )
    gpu_count = work.get("measured_gpus", pd.Series(0, index=work.index)).to_numpy(dtype=float)
    energy = work["energy_j"].to_numpy(dtype=float)
    submit = work["time_submit_aligned"].to_numpy(dtype=float)
    ids = work["id_job"].to_numpy(dtype=np.int64)
    order = np.lexsort((ids, energy, runtime, submit, gpu_count, gres_codes, job_type_codes))
    labels = np.empty(len(work), dtype=np.int64)
    labels[order] = np.arange(len(work), dtype=np.int64) % int(n_regions)
    return labels


def _balanced_request_region_labels(
    timestamp: np.ndarray,
    model: pd.Series,
    log_type: pd.Series,
    row_ids: np.ndarray,
    n_regions: int,
) -> np.ndarray:
    """Deterministic feature-stratified regions for request traces."""
    if n_regions <= 0:
        raise ValueError("n_regions must be positive")
    model_codes = pd.Categorical(model.fillna("").astype(str)).codes
    log_codes = pd.Categorical(log_type.fillna("").astype(str)).codes
    order = np.lexsort((row_ids, timestamp, log_codes, model_codes))
    labels = np.empty(len(row_ids), dtype=np.int64)
    labels[order] = np.arange(len(row_ids), dtype=np.int64) % int(n_regions)
    return labels


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
    calibration = _fit_dcgm_power_calibration(
        dcgm_path,
        int(cfg["project"]["seed"]),
        logger,
        scheduler_path=scheduler_path,
        training_days=int(cfg["data"].get("submission_calibration_training_days", 40)),
    )
    submission_calibration = _fit_submission_energy_calibration(
        scheduler_path=scheduler_path,
        dcgm_path=dcgm_path,
        interval_s=interval_s,
        declared_per_gpu_power_cap_mw=float(
            cfg["experiments"].get("job_level_declared_per_gpu_power_cap_mw", 1.0e-3)
        ),
        unbounded_timelimit_slots=int(
            cfg["experiments"].get("job_level_unbounded_timelimit_slots", 128)
        ),
        training_days=int(cfg["data"].get("submission_calibration_training_days", 40)),
        logger=logger,
    )

    dt_h = cfg["project"]["interval_minutes"] / 60.0
    q = float(cfg["data"]["percentile_for_scaling"])
    inf_raw_power = inference.sum(axis=(1, 2)) / dt_h
    batch_raw_power = batch_observed.sum(axis=1) / dt_h
    day_index = np.arange(n_slots) // slots_per_day
    slot_index = np.arange(n_slots) % slots_per_day
    n_days = n_slots // slots_per_day
    day_coverage = np.bincount(
        day_index, weights=valid_slots.astype(float), minlength=int(day_index.max()) + 1
    )
    valid_days = np.where(day_coverage >= 0.95 * slots_per_day)[0]
    scaling_fit_days = int(cfg["data"].get("scaling_fit_days", 40))
    if scaling_fit_days <= 0:
        raise ValueError("data.scaling_fit_days must be positive")
    fit_days = valid_days[:scaling_fit_days]
    fit_mask = np.isin(day_index, fit_days)
    positive_inf = inf_raw_power[fit_mask & (inf_raw_power > 0)]
    positive_batch = batch_raw_power[fit_mask & (batch_raw_power > 0)]
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
    batch_balance = np.cumsum(batch_arrivals - batch_observed, axis=0)
    batch_balance = np.maximum(batch_balance, 0.0)
    initial_batch_backlog = np.zeros((n_days, n_regions), dtype=np.float64)
    for day in range(1, n_days):
        initial_batch_backlog[day] = batch_balance[day * slots_per_day - 1]

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
        "submission_calibration": submission_calibration,
        "processing": {
            "interval_seconds": interval_s,
            "regions": n_regions,
            "spatial_mapping": (
                "feature-stratified round-robin workload scenario over immutable "
                "request/job records; no physical geography is inferred"
            ),
            "inference_scale_mwh_per_token": inf_scale,
            "batch_hyperscale_multiplier": batch_scale,
            "scaling_quantile": q,
            "scaling_fit_days": scaling_fit_days,
            "scaling_fit_day_ids": fit_days.tolist(),
            "scaling_scope": "first complete days before validation/test split; frozen before all downstream experiments",
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
            "submission_energy_fraction": float(
                submission_calibration["declared_service_fraction"]
            ),
            "submission_energy_fraction_source": (
                "chronological scheduler/DCGM calibration using only jobs submitted "
                "and completed inside the declared historical information set"
            ),
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
                "stage": "MIT immutable scheduler-DCGM join",
                "input_records": int(batch_stats["scheduler_rows"]),
                "retained_records": int(batch_stats["full_positive_energy_joined_jobs"]),
                "split_or_join_rule": "last scheduler record per immutable job ID with positive measured energy",
                "downstream_role": "full-horizon job-level witness in Experiments 14 and 16",
            },
            {
                "stage": "MIT common trace horizon filter",
                "input_records": int(batch_stats["full_positive_energy_joined_jobs"]),
                "retained_records": int(batch_stats["valid_joined_jobs"]),
                "split_or_join_rule": "aligned execution start before the common 121-day tensor horizon",
                "downstream_role": "batch arrivals and independent execution for Experiments 1--13",
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
                "stage": "Submit-time energy-envelope calibration",
                "input_records": int(submission_calibration["joined_positive_jobs"]),
                "retained_records": int(submission_calibration["training_jobs"]),
                "split_or_join_rule": (
                "chronological scheduler/DCGM job join inside the declared historical "
                "information set; telemetry is used only to fit the frozen envelope"
                ),
                "downstream_role": (
                    "ex-ante declared service quantity and physical upper bound for Exp19"
                ),
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
    downstream experiment while keeping the locked release artifacts
    internally consistent.
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
            mismatches.append(f"{relative}: not declared in locked manifest")
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
            # Public request traces have no utility geography.  Use the
            # declared feature-stratified scenario rule and evaluate every
            # downstream region-to-bus permutation instead of hashing IDs.
            regions = _balanced_request_region_labels(
                timestamp,
                chunk["Model"],
                chunk["Log Type"],
                row_ids,
                n_regions,
            )
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
    full_positive_energy_joined_jobs = int(len(jobs))
    # The MIT and BurstGPT releases each use their own relative clock. Preserve every
    # observed inter-arrival time while aligning the first eligible measured MIT job
    # with the beginning of the common counterfactual horizon.
    time_origin_s = float(jobs["time_start"].min())
    jobs["time_submit_aligned"] = jobs["time_submit"] - time_origin_s
    jobs["time_start_aligned"] = jobs["time_start"] - time_origin_s
    jobs["time_end_aligned"] = jobs["time_end"] - time_origin_s
    jobs = jobs[jobs["time_start_aligned"] < n_slots * interval_s].copy()
    jobs["region"] = _balanced_trace_region_labels(jobs, n_regions)
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
        region = int(row.region)
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
        "full_positive_energy_joined_jobs": full_positive_energy_joined_jobs,
        "valid_joined_jobs": int(len(jobs)),
        "jobs_excluded_by_common_trace_horizon": int(
            full_positive_energy_joined_jobs - len(jobs)
        ),
        "common_trace_horizon_definition": (
            "jobs whose aligned execution start is before the common BurstGPT/MIT "
            "tensor horizon; the full immutable join is retained separately by "
            "Experiments 14 and 16"
        ),
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


def _fit_dcgm_power_calibration(
    path: Path,
    seed: int,
    logger: logging.Logger,
    *,
    scheduler_path: Path | None = None,
    training_days: int = 40,
) -> dict[str, Any]:
    """Fit the GPU-power model on a chronological, observable information set.

    The previous implementation used ``id_job mod 10`` as a pseudo-random
    split.  That split is reproducible, but it is not an ex-ante information
    boundary: jobs from the future can enter the training fit.  When the
    scheduler release is available, this routine joins only the scheduler
    timestamps needed to define a historical cutoff and fits on jobs submitted
    and completed before that cutoff.  The DCGM fields remain labels, never
    membership selectors for the submitted ledger.
    """
    if int(training_days) <= 0:
        raise ValueError("training_days must be positive")
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
    if scheduler_path is not None:
        scheduler = pd.read_csv(
            scheduler_path,
            usecols=["id_job", "time_submit", "time_end"],
        ).replace([np.inf, -np.inf], np.nan)
        scheduler["id_job"] = pd.to_numeric(scheduler["id_job"], errors="coerce")
        scheduler["time_submit"] = pd.to_numeric(scheduler["time_submit"], errors="coerce")
        scheduler["time_end"] = pd.to_numeric(scheduler["time_end"], errors="coerce")
        scheduler = scheduler.dropna(subset=["id_job", "time_submit", "time_end"])
        scheduler = scheduler[scheduler["time_end"] >= scheduler["time_submit"]].copy()
        scheduler = scheduler.sort_values(
            ["id_job", "time_end"], kind="mergesort"
        ).drop_duplicates("id_job", keep="last")
        df = df.merge(scheduler, on="id_job", how="inner", validate="many_to_one")
        if df.empty:
            raise RuntimeError("No DCGM rows match scheduler timestamps for chronological calibration")
        origin = float(df["time_submit"].min())
        cutoff = origin + float(training_days) * 86400.0
        mask = (df["time_submit"] >= origin) & (df["time_submit"] < cutoff) & (df["time_end"] <= cutoff)
        training_rule = (
            "chronological scheduler information set: time_submit and time_end "
            f"< {int(training_days)} days after the earliest matched submission"
        )
    else:
        # This fallback is intentionally chronological in file order and is
        # retained only for unit-level callers that do not have the scheduler
        # release.  Production preprocessing always supplies scheduler_path.
        ordered = np.arange(len(df), dtype=np.int64)
        cutoff_rows = max(1, int(np.ceil(len(df) * min(1.0, training_days / 100.0))))
        mask = ordered < cutoff_rows
        origin = float("nan")
        cutoff = float("nan")
        training_rule = "chronological DCGM row prefix fallback (scheduler unavailable)"
    df["log_gpu_memory"] = np.log1p(df["maxgpumemoryused_bytes"].clip(lower=0))
    df["log_runtime"] = np.log1p(df["totalexecutiontime_sec"].clip(lower=0))
    features = ["smutilization_pct_avg", "memoryutilization_pct_avg", "log_gpu_memory", "log_runtime"]
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
        "training_rule": training_rule,
        "calibration_origin_submit_seconds": origin,
        "calibration_cutoff_seconds": cutoff,
        "calibration_cutoff_days": int(training_days),
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


def _fit_submission_energy_calibration(
    *,
    scheduler_path: Path,
    dcgm_path: Path,
    interval_s: int,
    declared_per_gpu_power_cap_mw: float,
    unbounded_timelimit_slots: int,
    training_days: int,
    logger: logging.Logger,
) -> dict[str, Any]:
    """Fit the ex-ante service fraction on the immutable training partition.

    Slurm exposes a requested GPU count and an allocation runtime, but no
    energy entitlement.  The submitted ledger therefore commits an energy
    *quantity* equal to a training-only utilization fraction times the
    requested nameplate and declared runtime.  DCGM appears here only to fit
    that fraction before the validation/test split; it is never joined into
    the submission digest and never enters the Exp19 feasibility constraints.
    The physical upper bound remains the full requested nameplate, so the
    conversion audit can report coverage instead of silently widening a
    deadline when an observed job exceeds its central estimate.  Calibration
    is chronological: a job is in the information set only when its submit
    and scheduler completion timestamps both precede the precommitted cutoff.
    A positive DCGM energy value is required only to supply a calibration label;
    it is not used to define the Exp19 submission population or any locked-day
    eligibility set.  Within the matched calibration labels, membership in the
    training split is determined solely by the chronological submit/end-time
    cutoff; no immutable-ID modulo rule or locked-day outcome is used.
    """
    if float(declared_per_gpu_power_cap_mw) <= 0.0:
        raise ValueError("declared_per_gpu_power_cap_mw must be positive")
    if int(training_days) <= 0:
        raise ValueError("training_days must be positive")
    scheduler_columns = [
        "id_job",
        "time_submit",
        "time_end",
        "timelimit",
        "gres_req",
        "job_type",
        "state",
    ]
    scheduler = pd.read_csv(scheduler_path, usecols=scheduler_columns)
    scheduler["id_job"] = pd.to_numeric(scheduler["id_job"], errors="coerce")
    scheduler["time_submit"] = pd.to_numeric(scheduler["time_submit"], errors="coerce")
    scheduler["time_end"] = pd.to_numeric(scheduler["time_end"], errors="coerce")
    scheduler["timelimit"] = pd.to_numeric(scheduler["timelimit"], errors="coerce")
    scheduler["requested_gpus"] = scheduler["gres_req"].map(_parse_requested_gpu_count)
    scheduler = scheduler.sort_values(
        ["id_job", "time_submit", "timelimit", "gres_req"],
        kind="mergesort",
        na_position="first",
    ).drop_duplicates("id_job", keep="last")
    scheduler = scheduler[
        scheduler["id_job"].notna()
        & scheduler["time_submit"].notna()
        & scheduler["time_end"].notna()
        & scheduler["timelimit"].notna()
        & scheduler["requested_gpus"].notna()
        & (scheduler["requested_gpus"] > 0)
        & (scheduler["timelimit"] > 0)
    ].copy()
    runtime_slots, unlimited = _declared_runtime_slots(
        scheduler["timelimit"].to_numpy(dtype=float), interval_s, unbounded_timelimit_slots
    )
    scheduler["declared_runtime_slots"] = runtime_slots
    scheduler["unlimited_timelimit"] = unlimited
    dcgm = pd.read_csv(
        dcgm_path,
        usecols=["id_job", "energyconsumed_joules"],
    )
    dcgm = dcgm.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["id_job", "energyconsumed_joules"]
    )
    measured = dcgm.groupby("id_job", as_index=False).agg(
        measured_energy_joules=("energyconsumed_joules", "sum")
    )
    joined = scheduler.merge(measured, on="id_job", how="inner", validate="one_to_one")
    joined = joined[
        (joined["measured_energy_joules"] > 0)
        & (joined["time_end"] >= joined["time_submit"])
    ].copy()
    if joined.empty:
        raise RuntimeError("No positive-energy jobs are available for submit-time calibration")
    dt_h = float(interval_s) / 3600.0
    nameplate_mwh = (
        joined["requested_gpus"].to_numpy(dtype=float)
        * float(declared_per_gpu_power_cap_mw)
        * joined["declared_runtime_slots"].to_numpy(dtype=float)
        * dt_h
    )
    joined["nameplate_energy_mwh"] = nameplate_mwh
    joined["measured_energy_mwh"] = joined["measured_energy_joules"] / 3.6e9
    joined["measured_to_nameplate_fraction"] = (
        joined["measured_energy_mwh"] / joined["nameplate_energy_mwh"]
    )
    calibration_origin = float(joined["time_submit"].min())
    calibration_cutoff = calibration_origin + float(training_days) * 86400.0
    training = joined[
        (joined["time_submit"] >= calibration_origin)
        & (joined["time_submit"] < calibration_cutoff)
        & (joined["time_end"] <= calibration_cutoff)
    ].copy()
    training = training[np.isfinite(training["measured_to_nameplate_fraction"])].copy()
    training = training[training["measured_to_nameplate_fraction"] > 0]
    if training.empty:
        raise RuntimeError("Submit-time calibration training split is empty")
    fractions = training["measured_to_nameplate_fraction"].to_numpy(dtype=float)
    quantiles = {str(q): float(np.quantile(fractions, q)) for q in [0.01, 0.10, 0.50, 0.90, 0.99]}
    payload = {
        "joined_positive_jobs": int(len(joined)),
        "training_jobs": int(len(training)),
        "test_jobs": int(len(joined) - len(training)),
        "training_rule": (
            "chronological historical information set: time_submit and time_end "
            f"< {int(training_days)} days after the earliest joined submission"
        ),
        "calibration_origin_submit_seconds": calibration_origin,
        "calibration_cutoff_seconds": calibration_cutoff,
        "calibration_cutoff_days": int(training_days),
        "declared_per_gpu_power_cap_mw": float(declared_per_gpu_power_cap_mw),
        "interval_seconds": int(interval_s),
        "unbounded_timelimit_slots": int(unbounded_timelimit_slots),
        "fraction_quantiles": quantiles,
        "declared_service_fraction_lower": float(quantiles["0.1"]),
        "declared_service_fraction": float(quantiles["0.5"]),
        "physical_upper_service_fraction": 1.0,
        "training_fraction_above_physical_upper": int(np.sum(fractions > 1.0 + 1e-12)),
        "all_joined_fraction_quantiles": {
            str(q): float(np.quantile(joined["measured_to_nameplate_fraction"], q))
            for q in [0.01, 0.10, 0.50, 0.90, 0.99]
        },
        "central_estimate_is_not_observed_energy": True,
        "entitlement_interval_semantics": (
            "the central q50 fraction is the committed ex-ante entitlement; "
            "q10 is a predeclared empirical lower envelope and the full "
            "requested nameplate is the physical upper bound"
        ),
        "telemetry_role": "training-only calibration; excluded from submit ledger digest and Exp19 constraints",
        "calibration_label_rule": (
            "matched positive DCGM energy is a label requirement for the "
            "training-only calibration sample; it never filters Exp19 submissions"
        ),
        "membership_rule_excludes_outcome_filtered_job_ids": True,
    }
    logger.info(
        "Submit-time energy calibration: %d/%d training jobs, central utilization %.6g",
        len(training),
        len(joined),
        payload["declared_service_fraction"],
    )
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
    deadline_mode: str = "observed",
    unbounded_timelimit_slots: int = 128,
    submission_buffer_slots: int = 0,
    declared_per_gpu_power_cap_mw: float = 1.0e-3,
    time_origin_seconds: float | None = None,
) -> pd.DataFrame:
    """Return the complete measured-job ledger used by exact replay checks.

    The join is the same immutable ``id_job``/positive-energy join used by
    :func:`_aggregate_mit_jobs`, but it retains release, execution, deadline,
    measured energy, GPU count and a deterministic spatial label.  ``observed``
    mode retains the scheduler completion time as a retrospective replay
    witness.  ``declared_timelimit`` mode constructs a service window from the
    submitter-declared Slurm allocation runtime, a precommitted queue
    allowance, and a finite fallback for Slurm's unlimited sentinel. Slurm
    ``--time`` limits runtime after allocation starts; it is not a
    submission-to-completion deadline. The observed ``time_end`` and measured
    energy never define the decision window.
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
            "timelimit",
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
    if time_origin_seconds is None:
        origin = float(jobs["time_start"].min())
    else:
        origin = float(time_origin_seconds)
        if not np.isfinite(origin):
            raise ValueError("time_origin_seconds must be finite when supplied")
    if deadline_mode not in {"observed", "declared_timelimit"}:
        raise ValueError(
            "deadline_mode must be 'observed' or 'declared_timelimit'"
        )
    if int(unbounded_timelimit_slots) <= 0:
        raise ValueError("unbounded_timelimit_slots must be positive")
    if int(submission_buffer_slots) < 0:
        raise ValueError("submission_buffer_slots must be nonnegative")
    if float(declared_per_gpu_power_cap_mw) <= 0.0:
        raise ValueError("declared_per_gpu_power_cap_mw must be positive")
    requested_n_slots = n_slots
    jobs["submit_slot"] = np.floor(
        np.maximum(0.0, jobs["time_submit"].to_numpy(dtype=float) - origin)
        / float(interval_s)
    ).astype(np.int64)
    jobs["start_slot"] = np.floor(
        np.maximum(0.0, jobs["time_start"].to_numpy(dtype=float) - origin)
        / float(interval_s)
    ).astype(np.int64)
    jobs["deadline_slot_observed"] = np.ceil(
        (jobs["time_end"].to_numpy(dtype=float) - origin) / float(interval_s)
    ).astype(np.int64)
    # ``timelimit`` is an allocation run-time declaration, not a deadline from
    # submission. The service window therefore consists of the submit time,
    # a precommitted queue allowance, and the declared allocation duration.
    # Slurm's UINT_MAX sentinel denotes an unlimited request; it is mapped to
    # a finite declared runtime so the counterfactual remains a bounded LP.
    # A measured energy value is never allowed to enlarge either component of
    # the submitted window.
    timelimit_seconds = jobs["timelimit"].to_numpy(dtype=np.int64)
    unlimited = timelimit_seconds >= np.iinfo(np.uint32).max - 1
    declared_runtime_slots = np.where(
        unlimited,
        int(unbounded_timelimit_slots),
        np.maximum(
            1,
            np.ceil(timelimit_seconds / float(interval_s)).astype(np.int64),
        ),
    ).astype(np.int64)
    declared_window_slots = declared_runtime_slots + int(submission_buffer_slots)
    required_service_slots = np.ceil(
        (jobs["energy_j"].to_numpy(dtype=float) / 3.6e9)
        / (
            np.maximum(jobs["measured_gpus"].to_numpy(dtype=float), 1.0)
            * float(declared_per_gpu_power_cap_mw)
            * (float(interval_s) / 3600.0)
        )
    ).astype(np.int64)
    required_service_slots = np.maximum(required_service_slots, 1)
    jobs["required_service_slots"] = required_service_slots.astype(np.int64)
    jobs["declared_runtime_slots"] = declared_runtime_slots
    jobs["declared_window_slots"] = declared_window_slots
    jobs["deadline_slot_declared_runtime"] = (
        jobs["submit_slot"].to_numpy(dtype=np.int64) + declared_window_slots
    ).astype(np.int64)
    # Historical consumers use this alias; all new metadata reports the
    # runtime and queue components separately so the column cannot be read as
    # a native Slurm deadline.
    jobs["deadline_slot_declared_timelimit"] = jobs[
        "deadline_slot_declared_runtime"
    ]
    jobs["deadline_slot"] = (
        jobs["deadline_slot_observed"]
        if deadline_mode == "observed"
        else jobs["deadline_slot_declared_timelimit"]
    ).astype(np.int64)
    if requested_n_slots is None:
        if deadline_mode == "declared_timelimit":
            n_slots = int(jobs["deadline_slot"].max())
        else:
            n_slots = int(jobs["deadline_slot_observed"].max())
    if n_slots is None or n_slots <= 0:
        raise ValueError("n_slots must be positive or None")
    jobs["submit_slot_raw"] = jobs["submit_slot"]
    jobs["start_slot_raw"] = jobs["start_slot"]
    jobs["deadline_slot_raw"] = jobs["deadline_slot"]
    jobs["submit_slot"] = jobs["submit_slot"].clip(lower=0, upper=n_slots - 1)
    jobs["start_slot"] = jobs["start_slot"].clip(lower=0, upper=n_slots - 1)
    jobs["deadline_slot"] = jobs["deadline_slot"].clip(lower=1, upper=n_slots)
    jobs["energy_mwh"] = jobs["energy_j"].to_numpy(dtype=float) / 3.6e9
    jobs["time_submit_aligned"] = jobs["time_submit"].to_numpy(dtype=float) - origin
    jobs["time_start_aligned"] = jobs["time_start"].to_numpy(dtype=float) - origin
    jobs["time_end_aligned"] = jobs["time_end"].to_numpy(dtype=float) - origin
    jobs["region"] = _balanced_trace_region_labels(jobs, n_regions)
    jobs["within_horizon"] = (
        (jobs["submit_slot_raw"] < int(n_slots))
        & (jobs["start_slot_raw"] < int(n_slots))
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
    jobs.attrs["deadline_mode"] = deadline_mode
    jobs.attrs["unbounded_timelimit_slots"] = int(unbounded_timelimit_slots)
    jobs.attrs["submission_buffer_slots"] = int(submission_buffer_slots)
    jobs.attrs["declared_per_gpu_power_cap_mw"] = float(declared_per_gpu_power_cap_mw)
    jobs.attrs["declared_window_infeasible_jobs"] = int(
        np.sum(
            jobs["required_service_slots"].to_numpy(dtype=np.int64)
            > jobs["declared_window_slots"].to_numpy(dtype=np.int64)
        )
    )
    jobs.attrs["deadline_window_rule"] = (
        "submit-time allocation runtime plus a precommitted queue allowance; "
        "Slurm timelimit is not a submission-to-completion deadline and measured "
        "energy is a feasibility check, never a deadline extension or window extension"
    )
    return jobs.reset_index(drop=True)


def load_mit_submission_ledger(
    scheduler_path: Path,
    interval_s: int,
    n_slots: int | None,
    n_regions: int,
    declared_service_fraction: float,
    declared_per_gpu_power_cap_mw: float,
    declared_service_fraction_lower: float | None = None,
    unbounded_timelimit_slots: int = 128,
    submission_buffer_slots: int = 0,
    eligible_job_ids: set[int] | None = None,
    time_origin_seconds: float | None = None,
) -> pd.DataFrame:
    """Return a submit-time-only job ledger for ex-ante scheduling.

    This function deliberately does not read the DCGM file.  Every decision
    field is available when a job is submitted: immutable job ID, submit time,
    requested GPUs, job class, and Slurm allocation runtime.  The central
    energy entitlement is the training-fitted utilization fraction times the
    requested GPU nameplate and declared runtime.  The optional q10-derived
    lower fraction creates an explicit ex-ante interval: the central field is
    the committed q50 entitlement, the lower field is an empirical lower
    envelope, and the upper field is the physical nameplate bound. These
    fields are fixed before any execution join.
    ``eligible_job_ids`` is retained as a compatibility argument but is
    deliberately rejected.  An outcome-derived job-ID set is a post-event
    population filter and would make the apparent submit-time contract
    non-deployable.  Retrospective scoring must join the complete submitted
    ledger after the decision has been frozen.
    """
    if int(interval_s) <= 0:
        raise ValueError("interval_s must be positive")
    if int(submission_buffer_slots) < 0:
        raise ValueError("submission_buffer_slots must be nonnegative")
    if float(declared_service_fraction) <= 0.0 or float(declared_service_fraction) > 1.0:
        raise ValueError("declared_service_fraction must lie in (0, 1]")
    lower_fraction = (
        float(declared_service_fraction)
        if declared_service_fraction_lower is None
        else float(declared_service_fraction_lower)
    )
    if not 0.0 < lower_fraction <= float(declared_service_fraction):
        raise ValueError(
            "declared_service_fraction_lower must lie in (0, declared_service_fraction]"
        )
    if float(declared_per_gpu_power_cap_mw) <= 0.0:
        raise ValueError("declared_per_gpu_power_cap_mw must be positive")
    scheduler_columns = ["id_job", "time_submit", "timelimit", "gres_req", "job_type", "state"]
    scheduler = pd.read_csv(scheduler_path, usecols=scheduler_columns)
    scheduler["id_job"] = pd.to_numeric(scheduler["id_job"], errors="coerce")
    scheduler["time_submit"] = pd.to_numeric(scheduler["time_submit"], errors="coerce")
    scheduler["timelimit"] = pd.to_numeric(scheduler["timelimit"], errors="coerce")
    scheduler["requested_gpus"] = scheduler["gres_req"].map(_parse_requested_gpu_count)
    scheduler = scheduler.sort_values(
        ["id_job", "time_submit", "timelimit", "gres_req"],
        kind="mergesort",
        na_position="first",
    ).drop_duplicates("id_job", keep="last")
    if eligible_job_ids is not None:
        raise ValueError(
            "eligible_job_ids is forbidden for submit-time ledgers; use the "
            "complete scheduler population and join execution telemetry only "
            "after the decision is frozen"
        )
    before_filter = len(scheduler)
    scheduler = scheduler[
        scheduler["id_job"].notna()
        & scheduler["time_submit"].notna()
        & scheduler["timelimit"].notna()
        & scheduler["requested_gpus"].notna()
        & (scheduler["requested_gpus"] > 0)
        & (scheduler["timelimit"] > 0)
    ].copy()
    if scheduler.empty:
        raise RuntimeError("No GPU jobs with valid submit-time declarations were retained")
    runtime_slots, unlimited = _declared_runtime_slots(
        scheduler["timelimit"].to_numpy(dtype=float), interval_s, unbounded_timelimit_slots
    )
    scheduler["declared_runtime_slots"] = runtime_slots
    scheduler["unlimited_timelimit"] = unlimited
    if time_origin_seconds is None:
        origin = float(scheduler["time_submit"].min())
    else:
        origin = float(time_origin_seconds)
        if not np.isfinite(origin):
            raise ValueError("time_origin_seconds must be finite when supplied")
    scheduler["submit_slot_raw"] = np.floor(
        (scheduler["time_submit"].to_numpy(dtype=float) - origin) / float(interval_s)
    ).astype(np.int64)
    scheduler["submit_slot"] = np.maximum(scheduler["submit_slot_raw"].to_numpy(dtype=np.int64), 0)
    scheduler["declared_window_slots"] = (
        scheduler["declared_runtime_slots"].to_numpy(dtype=np.int64)
        + int(submission_buffer_slots)
    )
    scheduler["deadline_slot_raw"] = (
        scheduler["submit_slot"].to_numpy(dtype=np.int64)
        + scheduler["declared_window_slots"].to_numpy(dtype=np.int64)
    )
    dt_h = float(interval_s) / 3600.0
    requested_gpu = scheduler["requested_gpus"].to_numpy(dtype=float)
    runtime = scheduler["declared_runtime_slots"].to_numpy(dtype=float)
    nameplate = requested_gpu * float(declared_per_gpu_power_cap_mw) * runtime * dt_h
    scheduler["declared_energy_mwh"] = nameplate * float(declared_service_fraction)
    scheduler["declared_energy_lower_mwh"] = nameplate * lower_fraction
    scheduler["declared_energy_upper_mwh"] = nameplate
    scheduler["required_service_slots"] = np.maximum(
        1,
        np.ceil(
            scheduler["declared_energy_mwh"].to_numpy(dtype=float)
            / (requested_gpu * float(declared_per_gpu_power_cap_mw) * dt_h)
        ).astype(np.int64),
    )
    scheduler["region"] = _balanced_submission_region_labels(scheduler, n_regions)
    if n_slots is None:
        horizon = int(scheduler["deadline_slot_raw"].max())
    else:
        horizon = int(n_slots)
        scheduler = scheduler[scheduler["submit_slot_raw"] < horizon].copy()
        if scheduler.empty:
            raise RuntimeError("No submit-time jobs fall within the requested horizon")
    scheduler["deadline_slot"] = np.clip(
        scheduler["deadline_slot_raw"].to_numpy(dtype=np.int64), 1, horizon
    )
    scheduler["within_horizon"] = (
        (scheduler["submit_slot_raw"].to_numpy(dtype=np.int64) >= 0)
        &
        (scheduler["submit_slot_raw"].to_numpy(dtype=np.int64) < horizon)
        & (scheduler["deadline_slot"].to_numpy(dtype=np.int64) > scheduler["submit_slot"].to_numpy(dtype=np.int64))
        & (scheduler["declared_energy_mwh"].to_numpy(dtype=float) > 0.0)
    )
    scheduler = scheduler[scheduler["within_horizon"]].copy()
    if scheduler.empty:
        raise RuntimeError("No feasible submit-time windows remain in the horizon")
    scheduler["deadline_slot"] = np.maximum(
        scheduler["deadline_slot"].to_numpy(dtype=np.int64),
        scheduler["submit_slot"].to_numpy(dtype=np.int64) + 1,
    )
    scheduler["deadline_slot"] = np.minimum(
        scheduler["deadline_slot"].to_numpy(dtype=np.int64), horizon
    )
    scheduler["declared_window_infeasible"] = (
        scheduler["required_service_slots"].to_numpy(dtype=np.int64)
        > scheduler["declared_window_slots"].to_numpy(dtype=np.int64)
    )
    canonical_columns = [
        "id_job",
        "time_submit",
        "timelimit",
        "gres_req",
        "job_type",
        "state",
        "requested_gpus",
        "declared_runtime_slots",
        "declared_window_slots",
        "declared_energy_mwh",
        "declared_energy_upper_mwh",
        "submit_slot",
        "deadline_slot",
        "region",
    ]
    canonical = scheduler[canonical_columns].sort_values("id_job", kind="mergesort")
    canonical_text = canonical.to_csv(
        index=False, lineterminator="\n", float_format="%.17g"
    ).encode("utf-8")
    scheduler.attrs["canonical_submission_ledger_sha256"] = hashlib.sha256(canonical_text).hexdigest()
    scheduler.attrs["time_origin_seconds"] = origin
    scheduler.attrs["scheduler_rows"] = int(before_filter)
    scheduler.attrs["retained_submission_jobs"] = int(len(scheduler))
    scheduler.attrs["dropped_invalid_submission_rows"] = int(before_filter - len(scheduler))
    scheduler.attrs["population_rule"] = (
        "all scheduler rows with valid submit-time GPU requests and allocation "
        "runtimes; execution telemetry is joined only after the decision"
    )
    scheduler.attrs["deadline_mode"] = "submit_time_declaration"
    scheduler.attrs["declared_service_fraction"] = float(declared_service_fraction)
    scheduler.attrs["declared_service_fraction_lower"] = float(lower_fraction)
    scheduler.attrs["declared_per_gpu_power_cap_mw"] = float(declared_per_gpu_power_cap_mw)
    scheduler.attrs["unbounded_timelimit_slots"] = int(unbounded_timelimit_slots)
    scheduler.attrs["submission_buffer_slots"] = int(submission_buffer_slots)
    scheduler.attrs["declared_window_infeasible_jobs"] = int(
        scheduler["declared_window_infeasible"].sum()
    )
    scheduler.attrs["digest_fields_exclude_execution_telemetry"] = True
    scheduler.attrs["execution_telemetry_is_post_event_only"] = True
    return scheduler.reset_index(drop=True)


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
        "id_job", "time_start", "time_end", "time_submit", "timelimit",
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
    # The submit ledger is committed before an event and therefore receives a
    # separate digest over scheduler declarations only.  In particular,
    # time_start/time_end and every DCGM-derived quantity are absent from this
    # tuple.  The joined execution digest below remains available for the
    # retrospective telemetry reconciliation.
    submission_last = scheduler_raw.copy()
    submission_last["requested_gpus"] = submission_last["gres_req"].map(
        _parse_requested_gpu_count
    )
    submission_last = submission_last.sort_values(
        ["id_job", "time_submit", "timelimit", "gres_req"],
        kind="mergesort",
        na_position="first",
    ).drop_duplicates("id_job", keep="last")
    submission_canonical = submission_last[
        [
            "id_job",
            "time_submit",
            "timelimit",
            "gres_req",
            "job_type",
            "state",
            "requested_gpus",
        ]
    ].copy()
    submission_canonical = submission_canonical[
        submission_canonical["id_job"].notna()
        & submission_canonical["time_submit"].notna()
        & submission_canonical["timelimit"].notna()
        & (submission_canonical["timelimit"] > 0)
        & submission_canonical["requested_gpus"].notna()
    ].sort_values("id_job", kind="mergesort")
    submission_text = submission_canonical[
        ["id_job", "time_submit", "timelimit", "gres_req", "job_type", "state"]
    ].to_csv(index=False, lineterminator="\n", float_format="%.17g").encode("utf-8")
    submission_digest = hashlib.sha256(submission_text).hexdigest()
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
    batch_scale = float(np.asarray(processed_workload.get("batch_scale", 1.0)).reshape(-1)[0])
    if not np.isfinite(batch_scale) or batch_scale <= 0:
        raise ValueError("Processed batch_scale must be positive and finite")
    slots_per_day = int(processed_workload["observed_energy_mwh"].shape[0] // max(1, len(processed_workload.get("valid_days", []))))
    if slots_per_day <= 0:
        slots_per_day = 96
    # The processed trace is deliberately scaled to the declared benchmark
    # envelope.  Preserve the raw execution scale for provenance so the
    # post-hoc reconciliation cannot be misread as a measured 118-MW utility
    # peak.
    scaled_benchmark_power = observed_batch / dt_h
    raw_execution_power = scaled_benchmark_power / batch_scale
    capacity_rows: list[dict[str, Any]] = []
    for region in range(int(n_regions)):
        scaled_values = scaled_benchmark_power[:, region]
        raw_values = raw_execution_power[:, region]
        capacity_rows.append(
            {
                "region": int(region),
                "configured_flexible_capacity_mw": float(configured_capacity_mw),
                "raw_execution_p50_mw": float(np.quantile(raw_values, 0.50)),
                "raw_execution_p95_mw": float(np.quantile(raw_values, 0.95)),
                "raw_execution_p99_mw": float(np.quantile(raw_values, 0.99)),
                "raw_execution_peak_mw": float(np.max(raw_values)),
                "scaled_benchmark_p50_mw": float(np.quantile(scaled_values, 0.50)),
                "scaled_benchmark_p95_mw": float(np.quantile(scaled_values, 0.95)),
                "scaled_benchmark_p99_mw": float(np.quantile(scaled_values, 0.99)),
                "scaled_benchmark_peak_mw": float(np.max(scaled_values)),
                "capacity_excess_peak_mw": float(max(0.0, np.max(scaled_values) - configured_capacity_mw)),
                "slots_above_configured_capacity": int(np.sum(scaled_values > configured_capacity_mw + 1e-9)),
                "observed_slots": int(scaled_values.size),
            }
        )
    capacity = pd.DataFrame(capacity_rows)
    all_slots = int(scaled_benchmark_power.shape[0])
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
        "canonical_submission_ledger_sha256": submission_digest,
        "submission_row_count": int(len(submission_canonical)),
        "submission_gpu_parseable_fraction": float(
            submission_canonical["requested_gpus"].notna().mean()
        )
        if len(submission_canonical)
        else 0.0,
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
            "submission_digest_excludes_execution_telemetry": True,
        },
        "capacity_measurement": {
            "interval_hours": dt_h,
            "observed_profile_slots": all_slots,
            "configured_capacity_mw": float(configured_capacity_mw),
            "batch_scale_to_benchmark_envelope": batch_scale,
            "maximum_raw_execution_peak_mw": float(capacity["raw_execution_peak_mw"].max()),
            "maximum_scaled_benchmark_peak_mw": float(capacity["scaled_benchmark_peak_mw"].max()),
            "maximum_scaled_benchmark_peak_to_configured_capacity_ratio": float(
                capacity["scaled_benchmark_peak_mw"].max() / max(float(configured_capacity_mw), 1e-12)
            ),
            "capacity_rows_are_scaled_benchmark_envelope": True,
            "raw_execution_is_unscaled_source_measurement": True,
        },
    }
    return summary, capacity
