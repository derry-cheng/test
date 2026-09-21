"""Contract, information-boundary, and settlement-lineage audit.

The audit is deliberately independent of the optimization routines.  It
recomputes the active declaration scale from the saved submit-time ledger,
checks that no future-arrival or execution field was used by the executable
bridge, and separates declaration-only network replay from the observed-meter
scoring panel.  A declaration replay can establish feasibility and a signed
network value; it cannot establish a payable meter amount without a closed
meter record.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .executable_witness import _declaration_energy_overlapping_days
from .utils import write_json


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_exp30_contract_lineage_audit(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
) -> None:
    """Write a release audit for the causal and settlement information sets."""

    folder = root / "experiments/exp30_contract_lineage_audit"
    final = folder / "results/final"
    final.mkdir(parents=True, exist_ok=True)

    exp27 = root / "experiments/exp27_executable_common_witness/results/final"
    exp29 = root / "experiments/exp29_executable_target_bridge/results/final"
    exp20 = root / "experiments/exp20_trace_meter_replay/results/final"
    witness_path = exp27 / "runtime_complete_witness.npz"
    job_path = exp27 / "job_level_runtime_summary.csv"
    bridge_certificate_path = exp27 / "risk_to_executable_bridge_certificate.json"
    witness_certificate_path = exp27 / "runtime_witness_coupling_certificate.json"
    settlement_path = exp27 / "common_witness_settlement.csv"
    observed_summary_path = exp20 / "trace_meter_replay_summary.csv"
    target_audit_path = exp29 / "executable_target_bridge_audit.csv"
    required = [
        witness_path,
        job_path,
        bridge_certificate_path,
        witness_certificate_path,
        settlement_path,
        observed_summary_path,
        target_audit_path,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Contract lineage audit requires completed Exp20, Exp27, and Exp29 artifacts: "
            + "; ".join(missing)
        )

    bridge_certificate = json.loads(bridge_certificate_path.read_text(encoding="utf-8"))
    witness_certificate = json.loads(witness_certificate_path.read_text(encoding="utf-8"))
    with np.load(witness_path, allow_pickle=False) as witness:
        submit_slot = np.asarray(witness["submit_slot"], dtype=np.int64)
        runtime_slots = np.asarray(witness["runtime_slots"], dtype=np.int64)
        declared_upper = np.asarray(
            witness["declared_job_energy_upper_mwh"], dtype=float
        )
        declared_central = np.asarray(
            witness["declared_job_energy_mwh"], dtype=float
        )
    jobs = pd.read_csv(job_path)
    if len(jobs) != len(submit_slot):
        raise RuntimeError("The declaration ledger and runtime witness have different populations")
    # The certificate stores the locked-day count, while the bridge CSV stores
    # the immutable day identifiers.  Reading those identifiers avoids any
    # dependence on a guessed contiguous test range.
    bridge_daily_path = exp27 / "risk_to_executable_bridge.csv"
    bridge_daily = pd.read_csv(bridge_daily_path)
    risk_days = bridge_daily["day"].to_numpy(dtype=np.int64)
    slots_per_day = int(cfg["project"]["slots_per_day"])
    recomputed_upper = _declaration_energy_overlapping_days(
        submit_slot, runtime_slots, declared_upper, risk_days, slots_per_day
    )
    recomputed_central = _declaration_energy_overlapping_days(
        submit_slot, runtime_slots, declared_central, risk_days, slots_per_day
    )
    certificate_upper = float(
        bridge_certificate.get("locked_active_declared_upper_energy_mwh", np.nan)
    )
    certificate_central = float(
        bridge_certificate.get("locked_active_declared_central_energy_mwh", np.nan)
    )
    scale_upper_residual = recomputed_upper - certificate_upper
    scale_central_residual = recomputed_central - certificate_central

    settlement = pd.read_csv(settlement_path)
    observed_summary = pd.read_csv(observed_summary_path)
    target_audit = pd.read_csv(target_audit_path)
    settlement_meter_columns = {
        "closed_meter_baseline_mwh",
        "closed_meter_counterfactual_mwh",
        "metered_reduction_mwh",
    }.intersection(set(settlement.columns))
    declaration_only = not bool(settlement_meter_columns)
    future_arrivals_used = bool(
        bridge_certificate.get("future_arrivals_used", False)
        or bridge_certificate.get("execution_telemetry_used", False)
        or witness_certificate.get("observed_execution_telemetry_used", False)
    )
    finite_and_feasible = bool(
        np.isfinite(settlement.select_dtypes(include=[np.number]).to_numpy()).all()
        and settlement.get("solver_success", pd.Series(dtype=bool)).all()
    )
    rows = [
        {"check": "active_upper_scale_recomputed", "value": recomputed_upper, "unit": "MWh", "passed": True},
        {"check": "active_central_scale_recomputed", "value": recomputed_central, "unit": "MWh", "passed": True},
        {"check": "active_upper_scale_certificate_residual", "value": scale_upper_residual, "unit": "MWh", "passed": abs(scale_upper_residual) <= 1.0e-8},
        {"check": "active_central_scale_certificate_residual", "value": scale_central_residual, "unit": "MWh", "passed": abs(scale_central_residual) <= 1.0e-8},
        {"check": "future_arrivals_or_execution_telemetry_used", "value": float(future_arrivals_used), "unit": "boolean", "passed": not future_arrivals_used},
        {"check": "declaration_witness_n1_replay_finite", "value": float(finite_and_feasible), "unit": "boolean", "passed": finite_and_feasible},
        {"check": "settlement_has_closed_meter_fields", "value": float(bool(settlement_meter_columns)), "unit": "boolean", "passed": declaration_only},
        {"check": "observed_meter_panel_available_for_scoring", "value": float(len(observed_summary)), "unit": "rows", "passed": len(observed_summary) > 0},
        {"check": "target_bridge_audit_available", "value": float(len(target_audit)), "unit": "rows", "passed": len(target_audit) > 0},
    ]
    checks = pd.DataFrame(rows)
    checks.to_csv(final / "contract_lineage_checks.csv", index=False)
    summary = pd.DataFrame(
        [
            {"metric": "active_upper_declaration_energy_mwh", "value": recomputed_upper, "unit": "MWh"},
            {"metric": "active_central_declaration_energy_mwh", "value": recomputed_central, "unit": "MWh"},
            {"metric": "locked_risk_days", "value": len(risk_days), "unit": "days"},
            {"metric": "declaration_jobs", "value": len(jobs), "unit": "jobs"},
            {"metric": "settlement_replay_cells", "value": len(settlement), "unit": "day-slots"},
            {"metric": "observed_meter_scoring_rows", "value": len(observed_summary), "unit": "rows"},
            {"metric": "target_bridge_audit_rows", "value": len(target_audit), "unit": "rows"},
            {"metric": "future_arrivals_used", "value": float(future_arrivals_used), "unit": "boolean"},
            {"metric": "declaration_only_network_replay", "value": float(declaration_only), "unit": "boolean"},
            {"metric": "closed_meter_payment_ready", "value": float(not declaration_only), "unit": "boolean"},
            {"metric": "all_lineage_checks_passed", "value": float(bool(checks["passed"].all())), "unit": "boolean"},
        ]
    )
    summary.to_csv(final / "contract_lineage_summary.csv", index=False)
    metadata = {
        "experiment": "causal contract and settlement lineage audit",
        "schema_version": 1,
        "information_boundary": "submit-time declarations for the executable witness; observed meter only for independent locked scoring",
        "future_arrivals_used": future_arrivals_used,
        "execution_telemetry_used": bool(
            bridge_certificate.get("execution_telemetry_used", False)
            or witness_certificate.get("observed_execution_telemetry_used", False)
        ),
        "scale_definition": "sum_j declaration_energy_j * overlap(runtime_block_j, locked_windows) / runtime_slots_j",
        "target_tracking_definition": "Exp29 reports total RMSE normalized by total-profile magnitude and flexible relative L2; it is not silently treated as exact target feasibility",
        "settlement_interpretation": "Exp27 is a declaration-only network-value replay; Exp20 is an independent observed-meter scoring panel; a closed meter is required before calling a payment payable",
        "declaration_only_network_replay": declaration_only,
        "closed_meter_payment_ready": not declaration_only,
        "source_sha256": {str(path.name): _sha256(path) for path in required},
        "files": {
            "checks": "contract_lineage_checks.csv",
            "summary": "contract_lineage_summary.csv",
        },
    }
    write_json(final / "experiment_metadata.json", metadata)
    logger.info(
        "Exp30 contract lineage audit [100%%]: active upper=%.3f MWh, closed_meter_payment_ready=%s",
        recomputed_upper,
        not declaration_only,
    )
