from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .audit import run_audit
from .data import preprocess_all
from .experiments import (
    run_exp1,
    run_exp2,
    run_exp3,
    run_exp4,
    run_exp5,
    run_exp6,
    run_exp7,
    run_exp8,
    run_exp9,
    run_exp10,
    run_exp11,
    run_exp12,
    run_exp13,
    run_exp14,
    run_exp15,
    run_exp16,
    run_exp17,
    run_exp18,
    run_exp19,
)
from .trace_replay import run_trace_meter_replay
from .scale_audit import run_exp21_scale_consistency
from .utils import ensure_dirs, environment_manifest, set_reproducible_seed, write_json


def manifest_path_for_stage(root: Path, stage: str) -> Path:
    """Preserve the canonical all-stage record when running a diagnostic stage."""
    if stage == "all":
        return root / "artifacts" / "run_manifest.json"
    return root / "artifacts" / "stage_runs" / f"{stage}_latest.json"


def run_pipeline(
    root: Path,
    cfg: dict[str, Any],
    stage: str,
    force_preprocess: bool,
    resume: bool,
    logger: logging.Logger,
) -> None:
    """Run the paper's complete data-to-audit workflow from one entry point."""
    ensure_dirs(root)
    commitment = root / cfg["project"].get(
        "capacity_commitment_file", "configs/capacity_commitment.json"
    )
    if not commitment.exists():
        raise FileNotFoundError(f"Missing pre-split capacity commitment: {commitment}")
    committed = json.loads(commitment.read_text(encoding="utf-8"))
    configured_capacity = float(cfg["project"]["flexible_capacity_mw"])
    if not bool(committed.get("locked_test_observations_used_for_selection") is False):
        raise ValueError("Capacity commitment must explicitly exclude locked-test observations")
    if not abs(float(committed["flexible_capacity_mw"]) - configured_capacity) <= 1e-12:
        raise ValueError("Configured flexible capacity differs from immutable commitment")
    set_reproducible_seed(int(cfg["project"]["seed"]))
    manifest_path = manifest_path_for_stage(root, stage)
    now = datetime.now(timezone.utc)
    resume_all_run = False
    if stage == "all" and resume and manifest_path.exists():
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        resume_all_run = previous.get("stage_requested") == "all"
    if resume_all_run:
        manifest = previous
        manifest.setdefault("resume_events_utc", []).append(now.isoformat())
        manifest["resume"] = True
        for record in manifest.get("stages", {}).values():
            if record.get("status") == "running":
                record["status"] = "interrupted"
                record["interrupted_utc"] = now.isoformat()
        logger.info(
            "Resuming unified run from %s; completed stages will be reused",
            manifest.get("started_utc"),
        )
    else:
        manifest = {
            "started_utc": now.isoformat(),
            "stage_requested": stage,
            "resume": bool(resume),
            "environment": environment_manifest(),
            "stages": {},
        }

    functions: list[tuple[str, Callable[[], None]]] = [
        ("data", lambda: preprocess_all(root, cfg, force_preprocess, logger)),
        ("exp1", lambda: run_exp1(root, cfg, logger)),
        ("exp2", lambda: run_exp2(root, cfg, logger)),
        ("exp3", lambda: run_exp3(root, cfg, logger)),
        ("exp4", lambda: run_exp4(root, cfg, logger)),
        ("exp5", lambda: run_exp5(root, cfg, logger, resume=resume)),
        ("exp6", lambda: run_exp6(root, cfg, logger, resume=resume)),
        ("exp7", lambda: run_exp7(root, cfg, logger, resume=resume)),
        ("exp8", lambda: run_exp8(root, cfg, logger, resume=resume)),
        ("exp9", lambda: run_exp9(root, cfg, logger, resume=resume)),
        ("exp10", lambda: run_exp10(root, cfg, logger, resume=resume)),
        ("exp11", lambda: run_exp11(root, cfg, logger, resume=resume)),
        ("exp12", lambda: run_exp12(root, cfg, logger, resume=resume)),
        ("exp13", lambda: run_exp13(root, cfg, logger)),
        ("exp14", lambda: run_exp14(root, cfg, logger)),
        ("exp15", lambda: run_exp15(root, cfg, logger, resume=resume)),
        ("exp16", lambda: run_exp16(root, cfg, logger)),
        ("exp17", lambda: run_exp17(root, cfg, logger, resume=resume)),
        ("exp18", lambda: run_exp18(root, cfg, logger, resume=resume)),
        ("exp19", lambda: run_exp19(root, cfg, logger, resume=resume)),
        ("exp20", lambda: run_trace_meter_replay(root, cfg, logger)),
        ("exp21", lambda: run_exp21_scale_consistency(root, cfg, logger)),
        (
            "audit",
            lambda: run_audit(
                root,
                cfg,
                logger,
                # A resumed unified run can finish from the compact locked
                # artifact package after raw inputs have been archived.  The
                # explicit data/full stages still fail closed on missing or
                # mismatched sources; audit-only execution records the missing
                # raw files as an identification boundary.
                allow_missing_raw=(stage in {"audit", "all"}),
            ),
        ),
    ]
    if resume_all_run:
        # The canonical manifest predates the two new information-boundary and
        # AC panels. Migrate it in place so a final --stage all --resume
        # reuses immutable completed stages while executing every artifact
        # whose upstream payment certificate or implementation changed.
        known_names = {name for name, _ in functions}
        for name in sorted(known_names.difference(manifest.get("stages", {}))):
            manifest["stages"][name] = {
                "status": "pending",
                "migration_note": "stage added after the previous unified run",
            }
        for name in {"exp2", "exp10", "exp11", "exp12", "exp15", "exp17", "exp18", "exp19", "exp20", "audit"}:
            if name not in manifest.get("stages", {}):
                continue
            # A long stage may have been rerun and independently checked after
            # the previous unified manifest was created.  Reuse that immutable
            # stage record when it is complete; otherwise mark it pending so
            # the unified entry point still executes the missing work.
            standalone = root / "artifacts" / "stage_runs" / f"{name}_latest.json"
            standalone_record = None
            if standalone.exists():
                try:
                    standalone_record = json.loads(standalone.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    standalone_record = None
            if standalone_record and standalone_record.get("status") == "completed":
                manifest["stages"][name] = {
                    **standalone_record,
                    "status": "completed",
                    "migration_note": "reused independently completed stage artifact",
                }
            else:
                manifest["stages"][name]["status"] = "pending"
                manifest["stages"][name]["migration_note"] = (
                    "rerun after the validation-frozen payment certificate and "
                    "new audit panels"
                )
    selected = [name for name, _ in functions] if stage == "all" else [stage]
    # A later standalone stage still requires its data dependency.
    if stage in {
        "exp1",
        "exp2",
        "exp3",
        "exp4",
        "exp5",
        "exp6",
        "exp7",
        "exp8",
        "exp9",
        "exp10",
        "exp11",
        "exp12",
        "exp13",
        "exp14",
        "exp15",
        "exp16",
        "exp17",
        "exp18",
        "exp19",
        "exp20",
        "exp21",
        "audit",
    } and stage not in {"audit", "exp20", "exp21"}:
        preprocess_all(root, cfg, False, logger)
    elif stage in {"audit", "exp20", "exp21"}:
        # The audit is intentionally runnable from the compact source/artifact
        # package after raw inputs have been moved to the verified archive.  It
        # consumes the locked processed tensor and checks its manifest-bound
        # outputs; the independent trace-meter replay has the same boundary
        # because it scores the locked tensor and Exp2 profiles only. Explicit
        # data/full runs still call ``preprocess_all`` and fail closed when a
        # declared raw file is absent or mismatched.
        processed = root / cfg["data"]["processed_dir"] / "workload_15min.npz"
        if not processed.exists():
            raise FileNotFoundError(
                "Locked processed workload is missing; restore the verified "
                "raw archive before running the audit."
            )
        logger.info(
            "%s stage uses the locked processed workload; raw-source validation "
            "remains enforced by data/full stages.",
            stage.upper(),
        )
    for name, function in functions:
        if name not in selected:
            continue
        if (
            resume_all_run
            and name != "audit"
            and manifest.get("stages", {}).get(name, {}).get("status")
            == "completed"
        ):
            logger.info(
                "===== SKIP COMPLETED STAGE %s ON RESUME =====",
                name.upper(),
            )
            continue
        logger.info("===== START STAGE %s =====", name.upper())
        started = datetime.now(timezone.utc)
        manifest["stages"][name] = {"started_utc": started.isoformat(), "status": "running"}
        write_json(manifest_path, manifest)
        try:
            function()
        except Exception as exc:
            manifest["stages"][name].update(
                {"finished_utc": datetime.now(timezone.utc).isoformat(), "status": "failed", "error": repr(exc)}
            )
            write_json(manifest_path, manifest)
            raise
        finished = datetime.now(timezone.utc)
        manifest["stages"][name].update(
            {
                "finished_utc": finished.isoformat(),
                "elapsed_seconds": (finished - started).total_seconds(),
                "status": "completed",
            }
        )
        write_json(manifest_path, manifest)
        logger.info("===== END STAGE %s (%.1f s) =====", name.upper(), (finished - started).total_seconds())
        completed_count = sum(
            record.get("status") == "completed"
            for record in manifest.get("stages", {}).values()
        )
        logger.info(
            "Unified pipeline progress: %.1f%% (%d/%d stages completed)",
            100.0 * completed_count / len(functions),
            completed_count,
            len(functions),
        )
    manifest["finished_utc"] = datetime.now(timezone.utc).isoformat()
    manifest["status"] = "completed"
    write_json(manifest_path, manifest)
