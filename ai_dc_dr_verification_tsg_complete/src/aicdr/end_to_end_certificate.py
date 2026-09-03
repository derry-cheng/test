"""Cross-stage lineage and certificate checks for the final evidence chain.

The paper contains two deliberately different physical paths.  The aggregate
risk fit produces the contractual target, while the indexed submitted-job
witness supplies an executable service state for the network replay.  This
module makes that separation auditable and checks that every downstream
artifact names its source instead of silently mixing trajectories.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .coupling_invariant import validate_job_network_coupling
from .utils import sha256, write_json


def _metric(frame: pd.DataFrame, name: str) -> float:
    rows = frame.loc[frame["metric"].astype(str).eq(str(name)), "value"]
    if rows.empty:
        raise KeyError(f"metric {name!r} is missing")
    return float(rows.iloc[0])


def _relative(root: Path, path: Path) -> str:
    return str(path.relative_to(root))


def _source_record(root: Path, path: Path, role: str, shape: str, days: int | str) -> dict[str, Any]:
    return {
        "source_file": _relative(root, path),
        "source_sha256": sha256(path),
        "profile_role": role,
        "shape_or_scope": shape,
        "locked_days": days,
    }


def run_exp26_end_to_end_certificate(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
) -> None:
    """Verify the complete lineage from declarations to N--1 settlement.

    This is a compact, cached-only certificate.  It does not refit a model or
    select a parameter.  It recomputes the indexed aggregation and mapping
    residuals from the stored job--slot vector, checks the already frozen risk
    and payment certificates, and records the distinct roles of the aggregate
    contract profile and executable job witness.
    """

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
    outage_path = root / "experiments/exp24_all_outage_security_panel/results/final/all_outage_security_replay.csv"
    outage_meta_path = root / "experiments/exp24_all_outage_security_panel/results/final/experiment_metadata.json"
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
        outage_path,
        outage_meta_path,
    ]
    missing = [str(path) for path in required if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise FileNotFoundError("Exp26 requires completed upstream artifacts: " + "; ".join(missing))

    job_meta = json.loads(job_meta_path.read_text(encoding="utf-8"))
    coupling_meta = json.loads(coupling_meta_path.read_text(encoding="utf-8"))
    risk_meta = json.loads(risk_meta_path.read_text(encoding="utf-8"))
    payment_meta = json.loads(payment_meta_path.read_text(encoding="utf-8"))
    outage_meta = json.loads(outage_meta_path.read_text(encoding="utf-8"))
    manifest_path = root / cfg["data"]["processed_dir"] / "data_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    submission_calibration = manifest.get("submission_calibration", {})
    job = np.load(job_path, allow_pickle=False)
    service = np.asarray(job["service_mwh"], dtype=float)
    starts = np.asarray(job["submit_slot"], dtype=np.int64)
    ends = np.asarray(job["deadline_slot"], dtype=np.int64)
    regions = np.asarray(job["region"], dtype=np.int64)
    aggregate = np.asarray(job["counterfactual_mwh"], dtype=float)
    energy = np.asarray(job["declared_job_energy_mwh"], dtype=float)
    requested_gpus = np.asarray(job["requested_gpus"], dtype=float)
    per_gpu_cap = float(np.asarray(job["per_gpu_power_cap_mw"], dtype=float).reshape(-1)[0])
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    n_regions, n_slots = aggregate.shape
    if len(starts) != len(ends) or len(starts) != len(regions) or len(starts) != len(energy):
        raise ValueError("Exp19 witness arrays have inconsistent job dimensions")
    if not np.isfinite(service).all() or not np.isfinite(aggregate).all():
        raise ValueError("Exp19 witness contains non-finite service or aggregate values")
    mapping = np.eye(n_regions, dtype=float)
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
        network_profile_mw=mapping @ (aggregate / dt_h),
        network_mapping=mapping,
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
    coupling_values = dict(zip(coupling_summary["metric"].astype(str), coupling_summary["value"].astype(float)))
    for key, value in {
        "maximum_job_to_aggregate_residual_mwh": coupling.max_aggregation_residual_mwh,
        "maximum_job_energy_recheck_residual_mwh": coupling.max_job_energy_residual_mwh,
        "maximum_gpu_bound_violation_mwh": coupling.maximum_gpu_bound_violation_mwh,
        "minimum_site_capacity_slack_mwh": coupling.minimum_site_capacity_slack_mwh,
    }.items():
        if key not in coupling_values or not np.isclose(coupling_values[key], value, atol=1e-10, rtol=0.0):
            raise RuntimeError(f"Exp22 summary does not match recomputed {key}")
    if coupling_values.get("submitted_jobs") != float(len(starts)):
        raise RuntimeError("Exp22 submitted-job count is inconsistent with the indexed witness")

    risk = np.load(risk_path, allow_pickle=False)
    risk_days = np.asarray(risk["days"], dtype=int)
    risk_profiles = np.asarray(risk["baselines"], dtype=float)
    method_names = [str(value) for value in risk["methods"].tolist()]
    if risk_profiles.ndim != 4 or len(risk_days) != risk_profiles.shape[0]:
        raise ValueError("Exp2 test profile archive has an invalid shape")
    risk_index = method_names.index("Risk-Constrained Convex Verifier")
    risk_profile = risk_profiles[:, risk_index]
    payment_profiles_path = root / "experiments/exp9_payment_certificate/results/final/certified_counterfactual_profiles.npz"
    payment_profiles = np.load(payment_profiles_path, allow_pickle=False)
    payment_days = np.asarray(payment_profiles["days"], dtype=int)
    payment_profile = np.asarray(payment_profiles["profiles"], dtype=float)
    if not np.array_equal(risk_days, payment_days):
        raise RuntimeError("Risk and payment profiles do not share the locked day index")
    if risk_profile.shape != payment_profile.shape:
        raise RuntimeError("Risk and payment profiles do not share the locked spatial/time dimensions")
    if not bool(risk_meta.get("risk_fit_certificate", {}).get("risk_constraints_satisfied", 0.0)):
        raise RuntimeError("Exp2 risk certificate is not marked as satisfied")
    if payment_meta.get("test_peak_used_for_scaling") is not False:
        raise RuntimeError("Exp9 payment scale was not frozen independently of locked test peaks")

    # The indexed witness and aggregate risk profile intentionally have
    # different units of provenance.  Record their source hashes and role
    # separation explicitly instead of testing accidental numerical equality.
    source_records = [
        _source_record(root, job_path, "executable submitted-job witness", str(service.shape), "full declared horizon"),
        _source_record(root, risk_path, "validation-fitted aggregate contract target", str(risk_profile.shape), len(risk_days)),
        _source_record(root, payment_profiles_path, "payment-certified feasible profile hull", str(payment_profile.shape), len(payment_days)),
        _source_record(root, coupling_path, "recomputed job-to-network certificate summary", "metric table", len(risk_days)),
        _source_record(root, outage_path, "frozen-profile all-outage N-1 replay", str(pd.read_csv(outage_path).shape), len(risk_days)),
    ]
    lineage = pd.DataFrame(source_records)
    lineage["risk_contract_satisfied"] = True
    lineage["network_mapping_recomputed_from_job_witness"] = lineage["profile_role"].eq("recomputed job-to-network certificate summary")
    lineage["payment_cap_is_relative_n1_cap"] = lineage["profile_role"].eq("payment-certified feasible profile hull")
    lineage.to_csv(final / "profile_role_lineage.csv", index=False)

    payment = pd.read_csv(payment_path)
    if payment.empty or not np.isfinite(payment["payment_cap_margin_usd"].to_numpy(dtype=float)).all():
        raise RuntimeError("Payment certificate contains no finite margins")
    max_violation = float(payment["payment_cap_violation_usd"].max())
    min_margin = float(payment["payment_cap_margin_usd"].min())
    if max_violation > 1e-6:
        raise RuntimeError(f"Payment cap violation exceeds tolerance: {max_violation:.3e} USD")
    payment_audit = (
        payment.groupby("conversion_scenario", as_index=False)
        .agg(
            certified_cells=("day", "size"),
            minimum_relative_cap_margin_usd=("payment_cap_margin_usd", "min"),
            maximum_relative_cap_violation_usd=("payment_cap_violation_usd", "max"),
        )
    )
    payment_eval = pd.read_csv(payment_eval_path)
    realized_audit = (
        payment_eval.groupby("counterfactual_method", as_index=False)
        .agg(
            evaluated_cells=("day", "size"),
            mean_realized_payment_overpayment_usd=("overpayment_usd", "mean"),
            maximum_realized_payment_overpayment_usd=("overpayment_usd", "max"),
        )
    )
    payment_audit.to_csv(final / "payment_relative_cap_audit.csv", index=False)
    realized_audit.to_csv(final / "realized_payment_audit.csv", index=False)

    outage = pd.read_csv(outage_path)
    if not bool(outage_meta.get("all_finite_nonislanding_outages_evaluated")):
        raise RuntimeError("Exp24 does not certify the complete finite non-islanding outage set")
    outage_ok = bool(
        len(outage) == int(risk_days.size) * len(cfg["market"]["event_slots"]) * 2
        and outage["credible_contingencies"].astype(int).eq(37).all()
        and outage["evaluated_finite_nonislanding_outages"].astype(int).eq(37).all()
        and outage["solver_success"].astype(bool).all()
    )
    if not outage_ok:
        raise RuntimeError("Exp24 all-outage replay is incomplete or contains an unsuccessful solve")
    logger.info("Exp26 risk/payment/outage lineage checks [75%]")

    checks = [
        {
            "stage": "job witness",
            "certificate": "exact declared-energy equality, GPU bound, and regional capacity",
            "maximum_residual_or_violation": coupling.max_job_energy_residual_mwh,
            "passed": coupling.valid,
        },
        {
            "stage": "aggregate risk contract",
            "certificate": "validation-fitted total plus daily-CVaR constraints",
            "maximum_residual_or_violation": float(risk_meta["risk_fit_certificate"].get("primal_constraint_residual", np.nan)),
            "passed": bool(risk_meta["risk_fit_certificate"].get("risk_constraints_satisfied", 0.0)),
        },
        {
            "stage": "relative payment cap",
            "certificate": "certified N-1 baseline cost no larger than the validation-frozen cap",
            "maximum_residual_or_violation": max_violation,
            "passed": max_violation <= 1e-6,
        },
        {
            "stage": "network valuation",
            "certificate": "RTS-24 N-1 value evaluated from the indexed job witness",
            "maximum_residual_or_violation": coupling.max_network_mapping_residual_mw,
            "passed": coupling.valid and bool(coupling_meta.get("network_profile_is_same_job_witness")),
        },
        {
            "stage": "complete outage replay",
            "certificate": "all 37 finite non-islanding line outages for every frozen profile cell",
            "maximum_residual_or_violation": float(outage["max_postcontingency_loading"].max()),
            "passed": outage_ok,
        },
    ]
    lineage_checks = pd.DataFrame(checks)
    lineage_checks.to_csv(final / "end_to_end_lineage.csv", index=False)
    if not bool(lineage_checks["passed"].all()):
        raise RuntimeError("Exp26 lineage certificate contains a failed stage")

    metadata = {
        "experiment": "end-to-end evidence-chain lineage certificate",
        "schema_version": 1,
        "locked_days": int(len(risk_days)),
        "upstream_artifact_hashes": {record["profile_role"]: record["source_sha256"] for record in source_records},
        "chain": [
            "submit-time declarations -> exact indexed job witness",
            "indexed witness -> regional aggregation and nodal mapping",
            "validation-only aggregate risk target -> relative N-1 payment cap",
            "indexed witness -> RTS-24 N-1 network valuation",
            "frozen profiles -> all finite non-islanding outage replay",
        ],
        "profile_roles": {
            "risk_profile": "validation-fitted aggregate contract target from Exp2",
            "payment_profile": "Exp9 feasible profile selected under a relative N-1 cost cap",
            "indexed_job_witness": "Exp19 exact submitted-job service vector used by Exp22 network replay",
            "profile_identity_asserted": False,
            "role_separation_reason": "The aggregate risk target and indexed submitted-job witness are different ledgers; the certificate proves source integrity and prevents silent substitution rather than claiming they are numerically identical.",
        },
        "job_entitlement_semantics": {
            "central_fraction_q50": float(
                submission_calibration.get(
                    "declared_service_fraction",
                    submission_calibration.get("fraction_quantiles", {}).get("0.5", np.nan),
                )
            ),
            "lower_fraction_q10": float(
                submission_calibration.get(
                    "declared_service_fraction_lower",
                    submission_calibration.get("fraction_quantiles", {}).get("0.1", np.nan),
                )
            ),
            "physical_upper_fraction": float(
                submission_calibration.get("physical_upper_service_fraction", 1.0)
            ),
            "interpretation": "q50 is the central training-only entitlement, q10 is an empirical lower envelope for coverage diagnostics, and the requested GPU nameplate is the physical upper bound; none is replaced by post-event execution energy.",
        },
        "coupling_certificate": coupling.to_dict(),
        "payment_certificate_scope": "relative N-1 baseline-cost cap; no absolute no-overpayment, revenue-adequacy, or incentive-compatibility theorem is asserted",
        "payment_cap_maximum_violation_usd": max_violation,
        "payment_cap_minimum_margin_usd": min_margin,
        "realized_payment_audit": "realized_payment_audit.csv",
        "all_outage_replay": {
            "rows": int(len(outage)),
            "credible_contingencies_per_cell": 37,
            "all_finite_nonislanding_outages_evaluated": True,
            "all_solver_cells_successful": bool(outage["solver_success"].astype(bool).all()),
        },
        "reports": {
            "lineage": "end_to_end_lineage.csv",
            "profile_roles": "profile_role_lineage.csv",
            "relative_payment_cap": "payment_relative_cap_audit.csv",
            "realized_payment": "realized_payment_audit.csv",
        },
        "raw_source_requirement": "Exp26 uses locked processed and final artifacts only; raw scheduler/DCGM files remain required for a fresh Exp19/Exp25 regeneration.",
    }
    write_json(final / "end_to_end_certificate.json", metadata)
    write_json(final / "experiment_metadata.json", metadata)
    readme = """# Exp26: End-to-end evidence-chain certificate

This compact certificate checks the immutable chain from submit-time job
declarations to an indexed service witness, regional aggregation, nodal mapping,
validation-frozen risk/payment profiles, and the complete RTS-24 outage replay.
It recomputes residuals from the Exp19 service vector and records SHA-256 hashes
for every upstream artifact. The aggregate risk profile and indexed job witness
remain separate ledgers with explicit roles; the certificate prevents silent
profile substitution and does not claim that their numerical trajectories are
identical. Payment scope is a relative N--1 baseline-cost cap. It is not an
absolute no-overpayment, revenue-adequacy, or incentive-compatibility result.

Outputs: `end_to_end_lineage.csv`, `profile_role_lineage.csv`,
`payment_relative_cap_audit.csv`, `realized_payment_audit.csv`, and the JSON
certificate in `results/final/`.
"""
    (folder / "README.md").write_text(readme, encoding="utf-8")
    logger.info("Exp26 end-to-end lineage certificate [100%]: PASS")
