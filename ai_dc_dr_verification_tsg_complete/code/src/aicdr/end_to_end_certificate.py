"""End-to-end evidence-chain certificate for the released experiment package.

The certificate is deliberately cached-only.  It does not refit a model,
select a parameter, or alter a profile.  Instead, it recomputes the indexed
job-to-network residuals and checks that the risk, payment, and all-outage
artifacts retain their declared source roles.  This closes the provenance gap
between the independent evidence panels without pretending that aggregate and
job-indexed trajectories are numerically identical.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .coupling_invariant import validate_job_network_coupling
from .executable_witness import _array_digest, _service_window_from_runtime_blocks
from .optimization import power_system_from_ppc
from .utils import sha256, write_json


def _relative(root: Path, path: Path) -> str:
    return str(path.relative_to(root))


def _source_record(root: Path, path: Path, role: str, scope: str) -> dict[str, Any]:
    return {
        "source_file": _relative(root, path),
        "source_sha256": sha256(path),
        "profile_role": role,
        "shape_or_scope": scope,
    }


def _bool_series(values: pd.Series) -> np.ndarray:
    """Parse boolean CSV columns without treating the string ``False`` as true."""
    if pd.api.types.is_bool_dtype(values):
        return values.to_numpy(dtype=bool)
    normalized = values.astype(str).str.strip().str.lower()
    if not normalized.isin({"true", "false", "1", "0"}).all():
        raise ValueError("boolean certificate column contains an unknown value")
    return normalized.isin({"true", "1"}).to_numpy(dtype=bool)


def run_exp26_end_to_end_certificate(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
) -> None:
    """Recompute and record the final declaration-to-settlement lineage."""
    folder = root / "experiments/exp26_end_to_end_certificate"
    final = folder / "results/final"
    final.mkdir(parents=True, exist_ok=True)
    logger.info("Exp26 end-to-end lineage certificate [0%]")

    job_path = root / "experiments/exp19_job_level_counterfactual/results/final/job_level_counterfactual_solution.npz"
    job_meta_path = root / "experiments/exp19_job_level_counterfactual/results/final/experiment_metadata.json"
    coupling_path = root / "experiments/exp22_coupled_job_network_certificate/results/final/coupled_network_summary.csv"
    coupling_meta_path = root / "experiments/exp22_coupled_job_network_certificate/results/final/experiment_metadata.json"
    risk_path = root / "experiments/exp2_baseline_verification/results/intermediate/test_profiles.npz"
    risk_meta_path = root / "experiments/exp2_baseline_verification/results/final/experiment_metadata.json"
    payment_path = root / "experiments/exp9_payment_certificate/results/final/conversion_scenario_certificates.csv"
    payment_eval_path = root / "experiments/exp9_payment_certificate/results/final/payment_evaluation_intervals.csv"
    payment_meta_path = root / "experiments/exp9_payment_certificate/results/final/experiment_metadata.json"
    payment_profile_path = root / "experiments/exp9_payment_certificate/results/final/certified_counterfactual_profiles.npz"
    outage_path = root / "experiments/exp24_all_outage_security_panel/results/final/all_outage_security_replay.csv"
    outage_meta_path = root / "experiments/exp24_all_outage_security_panel/results/final/experiment_metadata.json"
    common_witness_path = root / "experiments/exp27_executable_common_witness/results/final/runtime_complete_witness.npz"
    common_summary_path = root / "experiments/exp27_executable_common_witness/results/final/common_witness_summary.csv"
    common_typed_certificate_path = root / "experiments/exp27_executable_common_witness/results/final/runtime_witness_coupling_certificate.json"
    common_settlement_path = root / "experiments/exp27_executable_common_witness/results/final/common_witness_settlement.csv"
    common_settlement_summary_path = root / "experiments/exp27_executable_common_witness/results/final/common_witness_settlement_summary.csv"
    risk_bridge_path = root / "experiments/exp27_executable_common_witness/results/final/risk_to_executable_bridge.csv"
    risk_bridge_certificate_path = root / "experiments/exp27_executable_common_witness/results/final/risk_to_executable_bridge_certificate.json"
    common_meta_path = root / "experiments/exp27_executable_common_witness/results/final/experiment_metadata.json"
    required = [
        job_path,
        job_meta_path,
        coupling_path,
        coupling_meta_path,
        risk_path,
        risk_meta_path,
        payment_path,
        payment_eval_path,
        payment_meta_path,
        payment_profile_path,
        outage_path,
        outage_meta_path,
        common_witness_path,
        common_summary_path,
        common_typed_certificate_path,
        common_settlement_path,
        common_settlement_summary_path,
        risk_bridge_path,
        risk_bridge_certificate_path,
        common_meta_path,
    ]
    missing = [str(path) for path in required if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise FileNotFoundError("Exp26 requires completed upstream artifacts: " + "; ".join(missing))

    job_meta = json.loads(job_meta_path.read_text(encoding="utf-8"))
    coupling_meta = json.loads(coupling_meta_path.read_text(encoding="utf-8"))
    risk_meta = json.loads(risk_meta_path.read_text(encoding="utf-8"))
    payment_meta = json.loads(payment_meta_path.read_text(encoding="utf-8"))
    outage_meta = json.loads(outage_meta_path.read_text(encoding="utf-8"))
    common_meta = json.loads(common_meta_path.read_text(encoding="utf-8"))
    common_typed_certificate = json.loads(
        common_typed_certificate_path.read_text(encoding="utf-8")
    )
    risk_bridge_certificate = json.loads(
        risk_bridge_certificate_path.read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (root / cfg["data"]["processed_dir"] / "data_manifest.json").read_text(encoding="utf-8")
    )
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0

    job = np.load(job_path, allow_pickle=False)
    service = np.asarray(job["service_mwh"], dtype=float)
    starts = np.asarray(job["submit_slot"], dtype=np.int64)
    ends = np.asarray(job["deadline_slot"], dtype=np.int64)
    regions = np.asarray(job["region"], dtype=np.int64)
    aggregate = np.asarray(job["counterfactual_mwh"], dtype=float)
    energy = np.asarray(job["declared_job_energy_mwh"], dtype=float)
    requested_gpus = np.asarray(job["requested_gpus"], dtype=float)
    per_gpu_cap = float(np.asarray(job["per_gpu_power_cap_mw"], dtype=float).reshape(-1)[0])
    if not (len(starts) == len(ends) == len(regions) == len(energy) == len(requested_gpus)):
        raise ValueError("Exp19 witness arrays have inconsistent job dimensions")
    if aggregate.ndim != 2 or not np.isfinite(service).all() or not np.isfinite(aggregate).all():
        raise ValueError("Exp19 witness has an invalid service or aggregate array")

    # Exp27 is the declaration-only runtime-complete witness used by the new
    # common physical chain. It must be indexed by the same immutable
    # submission digest as Exp19, and its settlement rows must reference the
    # exact saved profile digest rather than a separately fitted trajectory.
    common = np.load(common_witness_path, allow_pickle=False)
    common_runtime = np.asarray(common["runtime_slots"], dtype=np.int64)
    common_runtime_energy = np.asarray(common["runtime_energy_mwh"], dtype=float)
    common_region = np.asarray(common["region"], dtype=np.int64)
    common_baseline_service = np.asarray(common["baseline_service_mwh"], dtype=float)
    common_counterfactual_service = np.asarray(common["counterfactual_service_mwh"], dtype=float)
    common_baseline = np.asarray(common["baseline_mwh"], dtype=float)
    common_counterfactual = np.asarray(common["counterfactual_mwh"], dtype=float)
    common_central_baseline = np.asarray(common["central_baseline_mwh"], dtype=float)
    common_central_counterfactual = np.asarray(common["central_counterfactual_mwh"], dtype=float)
    common_risk_aligned = np.asarray(common["risk_aligned_mwh"], dtype=float)
    common_central_risk_aligned = np.asarray(
        common["central_risk_aligned_mwh"], dtype=float
    )
    common_locked_risk_profile = np.asarray(common["locked_risk_profile"], dtype=float)
    common_risk_contract_upper = np.asarray(
        common["risk_contract_profile_upper"], dtype=float
    )
    common_risk_contract_central = np.asarray(
        common["risk_contract_profile_central"], dtype=float
    )
    common_declared_energy = np.asarray(common["declared_job_energy_mwh"], dtype=float)
    common_declared_upper = np.asarray(common["declared_job_energy_upper_mwh"], dtype=float)
    common_submit = np.asarray(common["submit_slot"], dtype=np.int64)
    common_deadline = np.asarray(common["deadline_slot"], dtype=np.int64)
    common_baseline_start = np.asarray(common["baseline_start_slot"], dtype=np.int64)
    common_counterfactual_start = np.asarray(common["response_start_slot"], dtype=np.int64)
    common_gpus = np.asarray(common["requested_gpus"], dtype=float)
    common_cap = float(np.asarray(common["per_gpu_power_cap_mw"], dtype=float).reshape(-1)[0])
    common_digest = str(np.asarray(common["witness_digest"]).reshape(-1)[0])
    source_digest = str(np.asarray(job["submission_digest"]).reshape(-1)[0])
    if common_meta.get("profile_identity_asserted") is not True:
        raise RuntimeError("Exp27 does not assert identity of its saved workload profiles")
    if common_meta.get("service_vector_identity_asserted") is not True:
        raise RuntimeError("Exp27 does not assert identity of its saved indexed service vectors")
    if common_meta.get("source_submission_digest") != source_digest:
        raise RuntimeError("Exp27 and Exp19 do not share the same submission-ledger digest")
    if (
        common_typed_certificate.get("witness_digest") != common_digest
        or common_typed_certificate.get("source_submission_digest") != source_digest
        or common_typed_certificate.get("profile_identity_asserted") is not True
        or common_typed_certificate.get("service_vector_identity_asserted") is not True
        or common_typed_certificate.get("baseline", {}).get("valid") is not True
        or common_typed_certificate.get("counterfactual", {}).get("valid") is not True
        or common_typed_certificate.get("central_baseline", {}).get("valid") is not True
        or common_typed_certificate.get("central_counterfactual", {}).get("valid") is not True
        or common_typed_certificate.get("risk_aligned", {}).get("valid") is not True
        or common_typed_certificate.get("central_risk_aligned", {}).get("valid") is not True
    ):
        raise RuntimeError("Exp27 typed runtime coupling certificate is invalid or detached")
    if not (
        len(common_submit) == len(common_deadline) == len(common_runtime)
        == len(common_runtime_energy) == len(starts)
    ):
        raise RuntimeError("Exp27 runtime-complete witness is not indexed by the Exp19 submission ledger")
    expected_runtime = common_gpus * common_cap * dt_h * common_runtime
    if np.max(np.abs(expected_runtime - common_runtime_energy)) > 1e-12:
        raise RuntimeError("Exp27 runtime energy is not implied by the declared GPU/runtime fields")
    if len(common_declared_energy) != len(common_runtime) or len(common_declared_upper) != len(common_runtime):
        raise RuntimeError("Exp27 central and upper declared energies are not job-indexed")
    if np.any(common_declared_energy < -1.0e-12) or np.any(common_declared_energy > common_declared_upper + 1.0e-10):
        raise RuntimeError("Exp27 central declared energy violates its nameplate upper bound")
    if np.max(np.abs(common_declared_upper - expected_runtime)) > 1.0e-12:
        raise RuntimeError("Exp27 declared nameplate upper energy is inconsistent with runtime fields")
    queue_buffer = int(common_meta["queue_buffer_slots"])
    if np.max(np.abs(common_deadline - (common_submit + common_runtime + queue_buffer))) > 0:
        raise RuntimeError("Exp27 runtime/deadline identity check failed")
    if common_baseline.shape != common_counterfactual.shape or common_baseline.ndim != 2:
        raise RuntimeError("Exp27 saved workload profiles have incompatible shapes")
    energy_per_slot = common_gpus * common_cap * dt_h
    expected_baseline_service = _service_window_from_runtime_blocks(
        common_baseline_start,
        common_runtime,
        common_submit,
        common_deadline,
        energy_per_slot,
    )
    expected_counterfactual_service = _service_window_from_runtime_blocks(
        common_counterfactual_start,
        common_runtime,
        common_submit,
        common_deadline,
        energy_per_slot,
    )
    if not np.array_equal(common_baseline_service, expected_baseline_service):
        raise RuntimeError("Exp27 baseline indexed service vector is not implied by its saved starts")
    if not np.array_equal(common_counterfactual_service, expected_counterfactual_service):
        raise RuntimeError("Exp27 counterfactual indexed service vector is not implied by its saved starts")
    recomputed_common_digest = _array_digest(
        common_submit,
        common_deadline,
        common_runtime,
        common_region,
        common_gpus,
        common_declared_energy,
        common_declared_upper,
        common_baseline_start,
        common_counterfactual_start,
        common_baseline_service,
        common_counterfactual_service,
        common_baseline,
        common_counterfactual,
        common["central_baseline_service_mwh"],
        common["central_counterfactual_service_mwh"],
        common_central_baseline,
        common_central_counterfactual,
        common["risk_aligned_start_slot"],
        common["risk_aligned_service_mwh"],
        common_risk_aligned,
        common["central_risk_aligned_service_mwh"],
        common["central_risk_aligned_mwh"],
        common["locked_risk_profile"],
        common_risk_contract_upper,
        common_risk_contract_central,
    )
    if recomputed_common_digest != common_digest:
        raise RuntimeError("Exp27 witness digest does not bind every saved service/profile array")
    common_baseline_typed_recheck = validate_job_network_coupling(
        service_mwh=common_baseline_service,
        job_energy_mwh=common_runtime_energy,
        submit_slot=common_submit,
        deadline_slot=common_deadline,
        region=common_region,
        aggregate_mwh=common_baseline,
        dt_h=dt_h,
        requested_gpus=common_gpus,
        per_gpu_power_cap_mw=common_cap,
        site_capacity_mw=float(cfg["project"]["flexible_capacity_mw"]),
    )
    common_counterfactual_typed_recheck = validate_job_network_coupling(
        service_mwh=common_counterfactual_service,
        job_energy_mwh=common_runtime_energy,
        submit_slot=common_submit,
        deadline_slot=common_deadline,
        region=common_region,
        aggregate_mwh=common_counterfactual,
        dt_h=dt_h,
        requested_gpus=common_gpus,
        per_gpu_power_cap_mw=common_cap,
        site_capacity_mw=float(cfg["project"]["flexible_capacity_mw"]),
    )
    central_baseline_service = np.asarray(common["central_baseline_service_mwh"], dtype=float)
    central_counterfactual_service = np.asarray(common["central_counterfactual_service_mwh"], dtype=float)
    risk_aligned_service = np.asarray(common["risk_aligned_service_mwh"], dtype=float)
    central_risk_aligned_service = np.asarray(
        common["central_risk_aligned_service_mwh"], dtype=float
    )
    central_energy_per_slot = common_declared_energy / common_runtime
    expected_central_baseline_service = _service_window_from_runtime_blocks(
        common_baseline_start,
        common_runtime,
        common_submit,
        common_deadline,
        central_energy_per_slot,
    )
    expected_central_counterfactual_service = _service_window_from_runtime_blocks(
        common_counterfactual_start,
        common_runtime,
        common_submit,
        common_deadline,
        central_energy_per_slot,
    )
    if not np.array_equal(central_baseline_service, expected_central_baseline_service) or not np.array_equal(central_counterfactual_service, expected_central_counterfactual_service):
        raise RuntimeError("Exp27 central service vectors are not implied by the same starts")
    expected_central_risk_aligned_service = _service_window_from_runtime_blocks(
        np.asarray(common["risk_aligned_start_slot"], dtype=np.int64),
        common_runtime,
        common_submit,
        common_deadline,
        central_energy_per_slot,
    )
    if not np.array_equal(
        central_risk_aligned_service, expected_central_risk_aligned_service
    ):
        raise RuntimeError("Exp27 central risk-aligned service is not implied by the same starts")
    central_baseline_typed_recheck = validate_job_network_coupling(
        service_mwh=central_baseline_service,
        job_energy_mwh=common_declared_energy,
        submit_slot=common_submit,
        deadline_slot=common_deadline,
        region=common_region,
        aggregate_mwh=common_central_baseline,
        dt_h=dt_h,
        requested_gpus=common_gpus,
        per_gpu_power_cap_mw=common_cap,
        site_capacity_mw=float(cfg["project"]["flexible_capacity_mw"]),
    )
    central_counterfactual_typed_recheck = validate_job_network_coupling(
        service_mwh=central_counterfactual_service,
        job_energy_mwh=common_declared_energy,
        submit_slot=common_submit,
        deadline_slot=common_deadline,
        region=common_region,
        aggregate_mwh=common_central_counterfactual,
        dt_h=dt_h,
        requested_gpus=common_gpus,
        per_gpu_power_cap_mw=common_cap,
        site_capacity_mw=float(cfg["project"]["flexible_capacity_mw"]),
    )
    risk_aligned_typed_recheck = validate_job_network_coupling(
        service_mwh=risk_aligned_service,
        job_energy_mwh=common_runtime_energy,
        submit_slot=common_submit,
        deadline_slot=common_deadline,
        region=common_region,
        aggregate_mwh=common_risk_aligned,
        dt_h=dt_h,
        requested_gpus=common_gpus,
        per_gpu_power_cap_mw=common_cap,
        site_capacity_mw=float(cfg["project"]["flexible_capacity_mw"]),
    )
    central_risk_aligned_typed_recheck = validate_job_network_coupling(
        service_mwh=central_risk_aligned_service,
        job_energy_mwh=common_declared_energy,
        submit_slot=common_submit,
        deadline_slot=common_deadline,
        region=common_region,
        aggregate_mwh=common_central_risk_aligned,
        dt_h=dt_h,
        requested_gpus=common_gpus,
        per_gpu_power_cap_mw=common_cap,
        site_capacity_mw=float(cfg["project"]["flexible_capacity_mw"]),
    )
    if not all(
        certificate.valid
        for certificate in (
            common_baseline_typed_recheck,
            common_counterfactual_typed_recheck,
            central_baseline_typed_recheck,
            central_counterfactual_typed_recheck,
            risk_aligned_typed_recheck,
            central_risk_aligned_typed_recheck,
        )
    ):
        raise RuntimeError("Exp27 stored service vectors fail the typed coupling recheck")
    common_settlement = pd.read_csv(common_settlement_path)
    if common_settlement.empty:
        raise RuntimeError("Exp27 settlement replay is empty")
    if not common_settlement["baseline_witness_profile_sha256"].eq(common_digest).all() or not common_settlement["counterfactual_witness_profile_sha256"].eq(common_digest).all():
        raise RuntimeError("Exp27 settlement rows do not reference the common witness digest")
    with np.load(risk_path, allow_pickle=False) as early_risk_store:
        risk_days = np.asarray(early_risk_store["days"], dtype=np.int64)
        risk_methods = [str(value) for value in early_risk_store["methods"].tolist()]
        if "Risk-Constrained Convex Verifier" not in risk_methods:
            raise RuntimeError("Exp2 archive lacks the locked risk verifier profile")
        risk_profile = np.asarray(
            early_risk_store["baselines"][:, risk_methods.index("Risk-Constrained Convex Verifier")],
            dtype=float,
        )
        risk_day_count = int(len(risk_days))
    expected_full_cycle_rows = risk_day_count * int(cfg["project"]["slots_per_day"])
    if len(common_settlement) != expected_full_cycle_rows or not common_settlement["settlement_window"].eq("full_declared_day").all():
        raise RuntimeError("Exp27 settlement replay does not cover every slot of every locked day")
    required_settlement_columns = {
        "gross_declared_reduction_mwh",
        "frozen_contract_cap_mwh",
        "payable_response_mwh",
        "capacity_payment_usd",
        "signed_contract_value_usd",
        "settlement_floor_applied",
    }
    if not required_settlement_columns.issubset(common_settlement.columns):
        raise RuntimeError("Exp27 settlement ledger lacks the explicit payment-cap fields")
    if not np.allclose(
        common_settlement["payable_settlement_usd"],
        np.maximum(common_settlement["signed_contract_value_usd"], 0.0),
        atol=1e-12,
        rtol=0.0,
    ):
        raise RuntimeError("Exp27 payable settlement is inconsistent with its declared floor")
    payable_cap = np.minimum(
        common_settlement["gross_declared_reduction_mwh"].to_numpy(dtype=float),
        common_settlement["frozen_contract_cap_mwh"].to_numpy(dtype=float),
    )
    if np.any(common_settlement["payable_response_mwh"].to_numpy(dtype=float) > payable_cap + 1e-10):
        raise RuntimeError("Exp27 payable response exceeds the frozen contract cap")
    # Recompute the pointwise reduction intersection from the saved regional
    # witness arrays. Checking only the minimum of two aggregate totals would
    # allow cross-region overpayment to cancel underpayment elsewhere.
    event_slots = set(int(value) for value in cfg["market"]["event_slots"])
    risk_contract_flexible = np.maximum(
        common_risk_contract_upper - float(cfg["project"]["fixed_facility_load_mw"]),
        0.0,
    )
    risk_day_to_index = {int(day): index for index, day in enumerate(risk_days.tolist())}
    expected_pointwise_payable = []
    for row in common_settlement.itertuples(index=False):
        day = int(row.day)
        slot = int(row.slot)
        day_index = risk_day_to_index.get(day)
        if day_index is None:
            raise RuntimeError(f"Exp27 settlement row day {day} is absent from the risk profile")
        absolute_slot = day * int(cfg["project"]["slots_per_day"]) + slot
        baseline_flexible = common_baseline[:, absolute_slot] / dt_h
        response_flexible = common_risk_aligned[:, absolute_slot] / dt_h
        gross = np.maximum(baseline_flexible - response_flexible, 0.0)
        cap = np.maximum(baseline_flexible - risk_contract_flexible[day_index, :, slot], 0.0)
        expected_pointwise_payable.append(
            float(np.minimum(gross, cap).sum() * dt_h) if slot in event_slots else 0.0
        )
    if not np.allclose(
        common_settlement["payable_response_mwh"].to_numpy(dtype=float),
        np.asarray(expected_pointwise_payable),
        atol=1e-10,
        rtol=0.0,
    ):
        raise RuntimeError("Exp27 pointwise contract-cap intersection is inconsistent with the witness")
    common_settlement_summary = pd.read_csv(common_settlement_summary_path)
    settlement_values = dict(zip(common_settlement_summary["metric"].astype(str), common_settlement_summary["value"].astype(float)))
    if int(settlement_values.get("full_cycle_cells", -1)) != expected_full_cycle_rows or not np.isclose(settlement_values.get("signed_payable_settlement_usd", np.nan), common_settlement["payable_settlement_usd"].sum(), atol=1e-9, rtol=0.0):
        raise RuntimeError("Exp27 signed settlement summary is inconsistent with its ledger")
    bridge = pd.read_csv(risk_bridge_path)
    required_bridge_columns = {
        "day",
        "raw_risk_profile_total_energy_mwh",
        "upper_contract_profile_total_energy_mwh",
        "central_contract_profile_total_energy_mwh",
        "upper_capacity_realization_energy_mwh",
        "central_energy_realization_energy_mwh",
        "upper_capacity_realization_nrmse",
        "central_energy_realization_nrmse",
        "upper_capacity_realization_nrmse_flexible_target",
        "central_energy_realization_nrmse_flexible_target",
        "same_declaration_digest",
    }
    if (
        len(bridge) != risk_day_count
        or not required_bridge_columns.issubset(bridge.columns)
        or not bridge["same_declaration_digest"].eq(source_digest).all()
    ):
        raise RuntimeError("Exp27 risk-to-executable bridge is not aligned with the submission digest")
    if risk_bridge_certificate.get("submission_digest") != source_digest or not risk_bridge_certificate.get("same_submission_index"):
        raise RuntimeError("Exp27 risk-to-executable bridge certificate is detached")
    if common_locked_risk_profile.shape != risk_profile.shape or not np.allclose(
        common_locked_risk_profile, risk_profile, atol=1e-12, rtol=0.0
    ):
        raise RuntimeError("Exp27 does not retain the locked Exp2 risk profile exactly")
    fixed_load = float(cfg["project"]["fixed_facility_load_mw"])
    risk_flexible = np.maximum(risk_profile - fixed_load, 0.0)
    risk_flexible_energy = float(risk_flexible.sum() * dt_h)
    locked_submit_mask = np.isin(
        common_submit // int(cfg["project"]["slots_per_day"]), risk_days
    )
    expected_upper_scale = (
        float(common_declared_upper[locked_submit_mask].sum()) / risk_flexible_energy
    )
    expected_central_scale = (
        float(common_declared_energy[locked_submit_mask].sum()) / risk_flexible_energy
    )
    expected_upper_contract = fixed_load + expected_upper_scale * risk_flexible
    expected_central_contract = fixed_load + expected_central_scale * risk_flexible
    if not np.allclose(
        common_risk_contract_upper, expected_upper_contract, atol=1e-12, rtol=0.0
    ):
        raise RuntimeError("Exp27 upper risk contract is not implied by locked submit-time declarations")
    if not np.allclose(
        common_risk_contract_central, expected_central_contract, atol=1e-12, rtol=0.0
    ):
        raise RuntimeError("Exp27 central risk contract is not implied by locked submit-time declarations")
    if not np.isclose(
        float(risk_bridge_certificate.get("upper_contract_scale", np.nan)),
        expected_upper_scale,
        atol=1e-12,
        rtol=0.0,
    ) or not np.isclose(
        float(risk_bridge_certificate.get("central_contract_scale", np.nan)),
        expected_central_scale,
        atol=1e-12,
        rtol=0.0,
    ):
        raise RuntimeError("Exp27 risk contract scales are not reproducible from declarations")
    bridge_days = bridge["day"].to_numpy(dtype=np.int64)
    if not np.array_equal(bridge_days, risk_days):
        raise RuntimeError("Exp27 bridge rows are not in the locked chronological day order")
    for index, day in enumerate(risk_days.tolist()):
        day_slice = slice(
            int(day) * int(cfg["project"]["slots_per_day"]),
            (int(day) + 1) * int(cfg["project"]["slots_per_day"]),
        )
        upper_realization = common_risk_aligned[:, day_slice] / dt_h + fixed_load
        central_realization = common_central_risk_aligned[:, day_slice] / dt_h + fixed_load
        upper_target = common_risk_contract_upper[index]
        central_target = common_risk_contract_central[index]
        expected_upper_nrmse = float(
            np.sqrt(np.mean((upper_realization - upper_target) ** 2))
            / max(np.mean(np.abs(upper_target)), 1e-12)
        )
        expected_central_nrmse = float(
            np.sqrt(np.mean((central_realization - central_target) ** 2))
            / max(np.mean(np.abs(central_target)), 1e-12)
        )
        row = bridge.iloc[index]
        if not np.isclose(
            float(row["upper_capacity_realization_nrmse"]),
            expected_upper_nrmse,
            atol=1e-12,
            rtol=0.0,
        ) or not np.isclose(
            float(row["central_energy_realization_nrmse"]),
            expected_central_nrmse,
            atol=1e-12,
            rtol=0.0,
        ):
            raise RuntimeError("Exp27 bridge residuals do not match the saved contract and executable profiles")
    common_summary = pd.read_csv(common_summary_path)
    common_metrics = dict(zip(common_summary["metric"].astype(str), common_summary["value"].astype(float)))
    if abs(common_metrics.get("baseline_energy_residual_mwh", np.inf)) > 1e-9 or abs(common_metrics.get("counterfactual_energy_residual_mwh", np.inf)) > 1e-9:
        raise RuntimeError("Exp27 runtime-complete energy certificate exceeds tolerance")
    for prefix in ("baseline", "counterfactual"):
        if (
            float(common_typed_certificate[prefix]["max_job_energy_residual_mwh"]) > 1e-12
            or float(common_typed_certificate[prefix]["max_aggregation_residual_mwh"]) > 1e-12
            or float(common_typed_certificate[prefix]["maximum_gpu_bound_violation_mwh"]) > 1e-12
            or float(common_typed_certificate[prefix]["minimum_site_capacity_slack_mwh"]) < -1e-12
        ):
            raise RuntimeError(f"Exp27 {prefix} typed runtime coupling residual exceeds tolerance")

    # Exp19 uses zero-based regional labels.  The first certificate checks the
    # indexed witness and regional aggregation before any network valuation.
    coupling = validate_job_network_coupling(
        service_mwh=service,
        job_energy_mwh=energy,
        submit_slot=starts,
        deadline_slot=ends,
        region=regions,
        aggregate_mwh=aggregate,
        dt_h=dt_h,
        requested_gpus=requested_gpus,
        per_gpu_power_cap_mw=per_gpu_cap,
        site_capacity_mw=float(cfg["project"]["flexible_capacity_mw"]),
    )
    if not coupling.valid:
        raise RuntimeError("Exp26 indexed job/network coupling certificate failed")
    logger.info(
        "Exp26 indexed witness recheck [25%%]: jobs=%d, variables=%d, max residual=%.3e MWh",
        len(starts),
        len(service),
        coupling.max_aggregation_residual_mwh,
    )

    coupling_summary = pd.read_csv(coupling_path)
    coupling_values = dict(
        zip(coupling_summary["metric"].astype(str), coupling_summary["value"].astype(float))
    )
    summary_fields = {
        "maximum_job_to_aggregate_residual_mwh": coupling.max_aggregation_residual_mwh,
        "maximum_job_energy_recheck_residual_mwh": coupling.max_job_energy_residual_mwh,
        "maximum_gpu_bound_violation_mwh": coupling.maximum_gpu_bound_violation_mwh,
        "minimum_site_capacity_slack_mwh": coupling.minimum_site_capacity_slack_mwh,
    }
    for name, value in summary_fields.items():
        if name not in coupling_values or not np.isclose(coupling_values[name], value, atol=1e-10, rtol=0.0):
            raise RuntimeError(f"Exp22 summary does not match recomputed {name}")
    if not np.isclose(coupling_values.get("submitted_jobs", np.nan), len(starts), atol=0.0, rtol=0.0):
        raise RuntimeError("Exp22 submitted-job count is inconsistent with the indexed witness")
    if coupling_meta.get("network_profile_is_same_job_witness") is not True:
        raise RuntimeError("Exp22 does not mark the network profile as the indexed witness")

    # Recompute the declared region-to-bus incidence rather than accepting the
    # Exp22 metadata flag as the mapping certificate.  This is a matrix-only
    # check (no SCED is re-solved): the bus profile is the image of the same
    # reconstructed regional witness, with the physical MWh-to-MW conversion
    # applied once and only once.
    from pypower.case24_ieee_rts import case24_ieee_rts

    network_system = power_system_from_ppc(case24_ieee_rts())
    configured_buses = np.asarray(
        cfg["experiments"].get("coupled_network_buses_one_based", [3, 8, 15, 21]),
        dtype=int,
    )
    metadata_buses = np.asarray(
        coupling_meta.get("data_center_buses_one_based", []), dtype=int
    )
    if (
        configured_buses.shape != (aggregate.shape[0],)
        or not np.array_equal(configured_buses, metadata_buses)
        or np.any(configured_buses < 1)
        or np.any(configured_buses > len(network_system.bus))
        or len(np.unique(configured_buses)) != len(configured_buses)
    ):
        raise RuntimeError("Exp22 bus mapping is not the declared one-hot RTS-24 map")
    bus_mapping = np.zeros((len(network_system.bus), aggregate.shape[0]), dtype=float)
    bus_mapping[configured_buses - 1, np.arange(aggregate.shape[0])] = 1.0
    network_profile = bus_mapping @ (aggregate / dt_h)
    mapped_coupling = validate_job_network_coupling(
        service_mwh=service,
        job_energy_mwh=energy,
        submit_slot=starts,
        deadline_slot=ends,
        region=regions,
        aggregate_mwh=aggregate,
        dt_h=dt_h,
        requested_gpus=requested_gpus,
        per_gpu_power_cap_mw=per_gpu_cap,
        site_capacity_mw=float(cfg["project"]["flexible_capacity_mw"]),
        network_profile_mw=network_profile,
        network_mapping=bus_mapping,
    )
    if not mapped_coupling.valid:
        raise RuntimeError("Exp26 RTS-24 region-to-bus mapping certificate failed")

    risk = np.load(risk_path, allow_pickle=False)
    risk_days = np.asarray(risk["days"], dtype=int)
    risk_profiles = np.asarray(risk["baselines"], dtype=float)
    method_names = [str(value) for value in risk["methods"].tolist()]
    if risk_profiles.ndim != 4 or len(risk_days) != risk_profiles.shape[0]:
        raise ValueError("Exp2 test-profile archive has an invalid shape")
    if "Risk-Constrained Convex Verifier" not in method_names:
        raise ValueError("Exp2 test-profile archive has no risk-constrained profile")
    risk_profile = risk_profiles[:, method_names.index("Risk-Constrained Convex Verifier")]
    payment_profiles = np.load(payment_profile_path, allow_pickle=False)
    payment_days = np.asarray(payment_profiles["days"], dtype=int)
    payment_profile = np.asarray(payment_profiles["profiles"], dtype=float)
    if not np.array_equal(risk_days, payment_days) or risk_profile.shape != payment_profile.shape:
        raise RuntimeError("Risk and payment profiles do not share the locked index and dimensions")
    risk_certificate = risk_meta.get("risk_fit_certificate", {})
    if not bool(risk_certificate.get("risk_constraints_satisfied", 0.0)):
        raise RuntimeError("Exp2 risk certificate is not marked as satisfied")
    if payment_meta.get("test_peak_used_for_scaling") is not False:
        raise RuntimeError("Exp9 payment scale was not frozen independently of locked test peaks")

    source_records = [
        _source_record(root, job_path, "executable submitted-job witness", str(service.shape)),
        _source_record(root, common_witness_path, "runtime-complete common witness used by network settlement", str(common_counterfactual.shape)),
        _source_record(root, common_settlement_path, "N-1 settlement replay of the runtime-complete common witness", str(common_settlement.shape)),
        _source_record(root, risk_bridge_path, "exact risk-profile to executable-start bridge", str(bridge.shape)),
        _source_record(root, risk_path, "validation-fitted aggregate risk target", str(risk_profile.shape)),
        _source_record(root, payment_profile_path, "payment-certified feasible profile hull", str(payment_profile.shape)),
        _source_record(root, coupling_path, "recomputed job-to-network certificate summary", "metric table"),
        _source_record(root, outage_path, "frozen-profile all-outage N-1 replay", str(pd.read_csv(outage_path).shape)),
    ]
    lineage = pd.DataFrame(source_records)
    lineage["risk_contract_satisfied"] = lineage["profile_role"].eq(
        "validation-fitted aggregate risk target"
    )
    lineage["network_mapping_recomputed_from_job_witness"] = lineage["profile_role"].eq(
        "recomputed job-to-network certificate summary"
    )
    lineage["payment_cap_is_relative_n1_cap"] = lineage["profile_role"].eq(
        "payment-certified feasible profile hull"
    )
    lineage["common_witness_identity_asserted"] = lineage["profile_role"].isin(
        [
            "executable submitted-job witness",
            "runtime-complete common witness used by network settlement",
            "N-1 settlement replay of the runtime-complete common witness",
            "exact risk-profile to executable-start bridge",
        ]
    )
    lineage.to_csv(final / "profile_role_lineage.csv", index=False)

    payment = pd.read_csv(payment_path)
    if payment.empty or not np.isfinite(payment["payment_cap_margin_usd"].to_numpy(dtype=float)).all():
        raise RuntimeError("Exp9 payment certificate contains no finite margins")
    max_violation = float(payment["payment_cap_violation_usd"].max())
    min_margin = float(payment["payment_cap_margin_usd"].min())
    if max_violation > 1e-6:
        raise RuntimeError(f"Payment cap violation exceeds tolerance: {max_violation:.3e} USD")
    payment_audit = payment.groupby("conversion_scenario", as_index=False).agg(
        certified_cells=("day", "size"),
        minimum_relative_cap_margin_usd=("payment_cap_margin_usd", "min"),
        maximum_relative_cap_violation_usd=("payment_cap_violation_usd", "max"),
    )
    payment_eval = pd.read_csv(payment_eval_path)
    realized_audit = payment_eval.groupby("counterfactual_method", as_index=False).agg(
        evaluated_cells=("day", "size"),
        mean_realized_payment_overpayment_usd=("overpayment_usd", "mean"),
        maximum_realized_payment_overpayment_usd=("overpayment_usd", "max"),
    )
    payment_audit.to_csv(final / "payment_relative_cap_audit.csv", index=False)
    realized_audit.to_csv(final / "realized_payment_audit.csv", index=False)

    outage = pd.read_csv(outage_path)
    event_slots = len(cfg["market"]["event_slots"])
    outage_success = _bool_series(outage["solver_success"])
    outage_complete = (
        bool(outage_meta.get("all_finite_nonislanding_outages_evaluated"))
        and len(outage) == len(risk_days) * event_slots * 2
        and outage["credible_contingencies"].astype(int).eq(37).all()
        and outage["evaluated_finite_nonislanding_outages"].astype(int).eq(37).all()
        and bool(outage_success.all())
    )
    if not outage_complete:
        raise RuntimeError("Exp24 all-outage replay is incomplete or contains an unsuccessful solve")
    logger.info("Exp26 risk/payment/outage lineage checks [75%]")

    checks = pd.DataFrame(
        [
            {
                "stage": "job witness",
                "certificate": "exact declared-energy equality, GPU bound, regional capacity, and regional aggregation",
                "maximum_residual_or_violation": coupling.max_job_energy_residual_mwh,
                "passed": coupling.valid,
            },
            {
                "stage": "aggregate risk contract",
                "certificate": "validation-fitted total plus daily-CVaR constraints",
                "maximum_residual_or_violation": float(risk_certificate.get("primal_constraint_residual", np.nan)),
                "passed": bool(risk_certificate.get("risk_constraints_satisfied", 0.0)),
            },
            {
                "stage": "relative payment cap",
                "certificate": "certified N-1 baseline cost no larger than the validation-frozen cap",
                "maximum_residual_or_violation": max_violation,
                "passed": max_violation <= 1e-6,
            },
            {
                "stage": "network valuation",
                "certificate": "Exp22 network profile is reconstructed from the indexed witness",
                "maximum_residual_or_violation": mapped_coupling.max_network_mapping_residual_mw,
                "passed": mapped_coupling.valid and coupling_meta.get("network_profile_is_same_job_witness") is True,
            },
            {
                "stage": "common executable witness",
                "certificate": "the same declaration-indexed runtime-complete witness digest, central-energy certificate, risk bridge, and signed full-day settlement are reused by network valuation",
                "maximum_residual_or_violation": float(
                    max(
                        abs(common_metrics["baseline_energy_residual_mwh"]),
                        abs(common_metrics["counterfactual_energy_residual_mwh"]),
                        common_typed_certificate["baseline"]["max_job_energy_residual_mwh"],
                        common_typed_certificate["counterfactual"]["max_job_energy_residual_mwh"],
                        common_typed_certificate["baseline"]["max_aggregation_residual_mwh"],
                        common_typed_certificate["counterfactual"]["max_aggregation_residual_mwh"],
                        common_typed_certificate["central_baseline"]["max_job_energy_residual_mwh"],
                        common_typed_certificate["central_counterfactual"]["max_job_energy_residual_mwh"],
                        common_typed_certificate["risk_aligned"]["max_job_energy_residual_mwh"],
                        common_typed_certificate["central_risk_aligned"]["max_job_energy_residual_mwh"],
                    )
                ),
                "passed": bool(
                    common_meta.get("profile_identity_asserted") is True
                    and common_typed_certificate.get("baseline", {}).get("valid") is True
                    and common_typed_certificate.get("counterfactual", {}).get("valid") is True
                    and common_typed_certificate.get("central_baseline", {}).get("valid") is True
                    and common_typed_certificate.get("central_counterfactual", {}).get("valid") is True
                    and common_typed_certificate.get("risk_aligned", {}).get("valid") is True
                    and common_typed_certificate.get("central_risk_aligned", {}).get("valid") is True
                    and common_settlement["solver_success"].all()
                    and len(common_settlement) == risk_day_count * int(cfg["project"]["slots_per_day"])
                    and required_settlement_columns.issubset(common_settlement.columns)
                    and np.allclose(
                        common_settlement["payable_settlement_usd"],
                        np.maximum(common_settlement["signed_contract_value_usd"], 0.0),
                        atol=1e-12,
                        rtol=0.0,
                    )
                ),
            },
            {
                "stage": "complete outage replay",
                "certificate": "all 37 finite non-islanding line outages for every frozen profile cell",
                "maximum_residual_or_violation": float(outage["max_postcontingency_loading"].max()),
                "passed": outage_complete,
            },
        ]
    )
    checks.to_csv(final / "end_to_end_lineage.csv", index=False)
    if not bool(checks["passed"].all()):
        raise RuntimeError("Exp26 lineage certificate contains a failed stage")

    calibration = manifest.get("submission_calibration", {})
    metadata = {
        "experiment": "end-to-end evidence-chain lineage certificate",
            "schema_version": 4,
        "locked_days": int(len(risk_days)),
        "upstream_artifact_hashes": {
            record["profile_role"]: record["source_sha256"] for record in source_records
        },
        "chain": [
            "submit-time declarations -> exact indexed job witness",
            "indexed witness -> regional aggregation and nodal mapping",
            "validation-only aggregate risk target -> relative N-1 payment cap",
            "validation-only aggregate risk target -> fixed-price executable start realization",
            "indexed witness -> RTS-24 N-1 network valuation",
            "runtime-complete common witness -> the same RTS-24 N-1 settlement replay",
            "frozen profiles -> all finite non-islanding outage replay",
        ],
        "profile_roles": {
            "risk_profile": "validation-fitted aggregate contract target from Exp2",
            "payment_profile": "Exp9 feasible profile selected under a relative N-1 cost cap",
            "indexed_job_witness": "Exp19 exact submitted-job declaration index",
            "runtime_complete_common_witness": "Exp27 fixed-runtime contiguous-block witness indexed by the same submission digest",
            "network_settlement_witness_digest": common_digest,
            "profile_identity_asserted": True,
            "role_separation_reason": "The common physical chain uses one runtime-complete declaration witness. Aggregate risk and payment profiles remain explicitly labeled calibration and contract-analysis views, so they cannot be silently substituted for that witness.",
        },
        "job_entitlement_semantics": {
            "central_fraction_q50": float(calibration.get("declared_service_fraction", np.nan)),
            "physical_upper_fraction": float(calibration.get("physical_upper_service_fraction", 1.0)),
            "interpretation": "The central training-only entitlement and the requested-GPU nameplate are fixed before Exp19; execution energy is not used to construct the witness.",
        },
        "coupling_certificate": coupling.to_dict(),
        "network_mapping_certificate": mapped_coupling.to_dict(),
        "common_witness_certificate": {
            "witness_digest": common_digest,
            "submitted_jobs": int(len(common_submit)),
            "runtime_energy_mwh": float(common_runtime_energy.sum()),
            "profile_shape": list(common_counterfactual.shape),
            "settlement_rows": int(len(common_settlement)),
            "settlement_full_cycle_rows": int(len(common_settlement)),
            "settlement_signed": bool(np.allclose(common_settlement["signed_contract_value_usd"], common_settlement["capacity_payment_usd"] + common_settlement["network_value_usd"], atol=1e-12, rtol=0.0)),
            "settlement_payment_cap_verified": bool(
                np.allclose(
                    common_settlement["payable_settlement_usd"],
                    np.maximum(common_settlement["signed_contract_value_usd"], 0.0),
                    atol=1e-12,
                    rtol=0.0,
                )
            ),
            "central_declared_service_energy_mwh": float(common_declared_energy.sum()),
            "nameplate_upper_energy_mwh": float(common_declared_upper.sum()),
            "risk_bridge_file": _relative(root, risk_bridge_path),
            "risk_bridge_certificate_file": _relative(root, risk_bridge_certificate_path),
            "all_settlement_solves_successful": bool(common_settlement["solver_success"].all()),
            "typed_certificate_file": _relative(root, common_typed_certificate_path),
            "typed_certificate_valid": bool(
                common_typed_certificate.get("baseline", {}).get("valid") is True
                and common_typed_certificate.get("counterfactual", {}).get("valid") is True
                and common_typed_certificate.get("central_baseline", {}).get("valid") is True
                and common_typed_certificate.get("central_counterfactual", {}).get("valid") is True
                and common_typed_certificate.get("risk_aligned", {}).get("valid") is True
                and common_typed_certificate.get("central_risk_aligned", {}).get("valid") is True
            ),
            "typed_certificate_max_job_energy_residual_mwh": float(
                max(
                    common_typed_certificate["baseline"]["max_job_energy_residual_mwh"],
                    common_typed_certificate["counterfactual"]["max_job_energy_residual_mwh"],
                )
            ),
            "typed_certificate_max_aggregation_residual_mwh": float(
                max(
                    common_typed_certificate["baseline"]["max_aggregation_residual_mwh"],
                    common_typed_certificate["counterfactual"]["max_aggregation_residual_mwh"],
                )
            ),
            "stored_service_vector_lengths": {
                "baseline": int(len(common_baseline_service)),
                "counterfactual": int(len(common_counterfactual_service)),
            },
            "stored_service_vector_recheck_valid": bool(
                common_baseline_typed_recheck.valid
                and common_counterfactual_typed_recheck.valid
            ),
            "stored_service_vector_identity_asserted": True,
            "witness_digest_recomputed_from_saved_arrays": True,
            "finite_n1_contingencies_per_cell": int(common_settlement["finite_n1_contingencies"].iloc[0]),
        },
        "network_mapping_one_hot_bus_indices_zero_based": (configured_buses - 1).tolist(),
        "payment_certificate_scope": "relative N-1 baseline-cost cap; no absolute no-overpayment, revenue-adequacy, or incentive-compatibility theorem is asserted",
        "payment_cap_maximum_violation_usd": max_violation,
        "payment_cap_minimum_margin_usd": min_margin,
        "all_outage_replay": {
            "rows": int(len(outage)),
            "credible_contingencies_per_cell": 37,
            "all_finite_nonislanding_outages_evaluated": True,
            "all_solver_cells_successful": bool(outage_success.all()),
        },
        "reports": {
            "lineage": "end_to_end_lineage.csv",
            "profile_roles": "profile_role_lineage.csv",
            "relative_payment_cap": "payment_relative_cap_audit.csv",
            "realized_payment": "realized_payment_audit.csv",
        },
        "raw_source_requirement": "Exp26 reads locked processed and final artifacts only; raw scheduler/DCGM files remain required to regenerate Exp19 or Exp25.",
    }
    write_json(final / "end_to_end_certificate.json", metadata)
    write_json(final / "experiment_metadata.json", metadata)
    (folder / "README.md").write_text(
        """# Experiment 26: End-to-end evidence-chain certificate

This cached-only certificate recomputes the indexed job-to-network residuals,
checks the runtime-complete common witness, and verifies the frozen risk,
relative payment, and complete RTS-24 outage artifacts. The declaration witness
and its N-1 settlement replay carry one digest and one submission index. The
aggregate risk and payment profiles remain explicitly labeled analysis views.

The certificate does not refit, select, clip, or re-optimize any upstream
profile. Outputs are written to `results/final/`: `end_to_end_lineage.csv`,
`profile_role_lineage.csv`, `payment_relative_cap_audit.csv`,
`realized_payment_audit.csv`, and the JSON certificate. The Exp27 typed
runtime coupling certificate is loaded and checked before this lineage is
written, but remains a derived certificate rather than a separate profile
role.
""",
        encoding="utf-8",
    )
    logger.info("Exp26 end-to-end lineage certificate [100%]: PASS")
