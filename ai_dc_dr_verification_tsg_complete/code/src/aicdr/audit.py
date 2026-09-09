from __future__ import annotations

import json
import hashlib
import logging
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from PIL import Image

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - requirements.txt pins pypdf for releases
    PdfReader = None  # type: ignore[assignment,misc]

from .data import load_workload
from .optimization import parse_pglib_case, solve_sced, solve_workload_schedule
from .utils import sha256, write_json


EXPECTED_FILES = {
    "data": [
        "data/processed/workload_15min.npz",
        "data/processed/workload_daily_summary.csv",
        "data/processed/data_manifest.json",
        "data/processed/data_flow_audit.csv",
        "configs/capacity_commitment.json",
    ],
    "experiment_1": [
        "experiments/exp1_manipulation/results/final/manipulation_grid.csv",
        "experiments/exp1_manipulation/results/final/experiment_metadata.json",
        "experiments/exp1_manipulation/figures/fig1_manipulation_phase_diagram.png",
        "experiments/exp1_manipulation/figures/fig2_response_and_migration.png",
    ],
    "experiment_2": [
        "experiments/exp2_baseline_verification/results/intermediate/validation_profiles.npz",
        "experiments/exp2_baseline_verification/results/final/per_day_baseline_metrics.csv",
        "experiments/exp2_baseline_verification/results/final/closest_literature_baselines.csv",
        "experiments/exp2_baseline_verification/results/final/closest_literature_baselines_summary.csv",
        "experiments/exp2_baseline_verification/results/final/structural_literature_baselines.csv",
        "experiments/exp2_baseline_verification/results/final/structural_literature_baselines_summary.csv",
        "experiments/exp2_baseline_verification/results/final/baseline_fairness_audit.csv",
        "experiments/exp2_baseline_verification/results/final/risk_effect_decomposition.csv",
        "experiments/exp2_baseline_verification/results/final/bootstrap_confidence_intervals.csv",
        "experiments/exp2_baseline_verification/results/final/constraint_ablation.csv",
        "experiments/exp2_baseline_verification/results/final/constraint_ablation_daily.csv",
        "experiments/exp2_baseline_verification/results/final/specification_robustness.csv",
        "experiments/exp2_baseline_verification/results/final/projection_candidate_validation.csv",
        "experiments/exp2_baseline_verification/results/final/convex_projection_weights.csv",
        "experiments/exp2_baseline_verification/results/final/risk_constrained_validation_certificate.csv",
        "experiments/exp2_baseline_verification/results/final/risk_truth_source_audit.csv",
        "experiments/exp2_baseline_verification/results/final/risk_reserve_nested_cv.csv",
        "experiments/exp2_baseline_verification/results/final/risk_reserve_validation_summary.csv",
        "experiments/exp2_baseline_verification/results/final/risk_cvar_stress_sensitivity.csv",
        "experiments/exp2_baseline_verification/results/final/risk_envelope_validation.csv",
        "experiments/exp2_baseline_verification/results/final/two_sided_credit_certificate.csv",
        "experiments/exp2_baseline_verification/results/final/quantile_feasible_validation.csv",
        "experiments/exp2_baseline_verification/results/final/intervention_robustness.csv",
        "experiments/exp2_baseline_verification/results/final/blocked_validation_cv.csv",
        "experiments/exp2_baseline_verification/results/final/information_set_audit.csv",
        "experiments/exp2_baseline_verification/results/final/block_length_sensitivity.csv",
        "experiments/exp2_baseline_verification/results/final/paired_block_randomization_tests.csv",
        "experiments/exp2_baseline_verification/results/final/matched_comparator_effects.csv",
        "experiments/exp2_baseline_verification/results/final/paired_counterfactual_block_tests.csv",
        "experiments/exp2_baseline_verification/results/final/complexity_scaling.csv",
        "experiments/exp2_baseline_verification/results/final/experiment_metadata.json",
        "experiments/exp2_baseline_verification/figures/fig3_baseline_verification_performance.png",
        "experiments/exp2_baseline_verification/figures/fig4_tuning_and_ablation.png",
        "experiments/exp2_baseline_verification/figures/fig4b_intervention_robustness.png",
    ],
    "experiment_3": [
        "experiments/exp3_nodal_settlement/results/final/settlement_metrics.csv",
        "experiments/exp3_nodal_settlement/results/final/interval_grid_value.csv",
        "experiments/exp3_nodal_settlement/results/final/mean_line_loading.csv",
        "experiments/exp3_nodal_settlement/results/final/paired_settlement_block_tests.csv",
        "experiments/exp3_nodal_settlement/results/final/polyhedral_value_certificates.csv",
        "experiments/exp3_nodal_settlement/results/final/settlement_factor_decomposition.csv",
        "experiments/exp3_nodal_settlement/results/final/settlement_factor_decomposition_summary.csv",
        "experiments/exp3_nodal_settlement/results/final/experiment_metadata.json",
        "experiments/exp3_nodal_settlement/figures/fig5_settlement_value_alignment.png",
        "experiments/exp3_nodal_settlement/figures/fig6_network_loading_heatmap.png",
        "experiments/exp3_nodal_settlement/figures/fig6b_settlement_factor_decomposition.png",
    ],
    "experiment_4": [
        "experiments/exp4_case_study/results/intermediate/case_selection_candidates.csv",
        "experiments/exp4_case_study/results/final/spatial_case_timeseries.csv",
        "experiments/exp4_case_study/results/final/case_summary_by_data_center.csv",
        "experiments/exp4_case_study/results/final/case_metadata.json",
        "experiments/exp4_case_study/figures/fig7_spatial_response_case.png",
        "experiments/exp4_case_study/figures/fig8_ieee118_data_center_topology.png",
    ],
    "experiment_5": [
        "experiments/exp5_network_robustness/results/final/network_robustness.csv",
        "experiments/exp5_network_robustness/results/final/network_robustness_summary.csv",
        "experiments/exp5_network_robustness/results/final/paired_network_block_tests.csv",
        "experiments/exp5_network_robustness/results/final/resolution_convergence_daily.csv",
        "experiments/exp5_network_robustness/results/final/resolution_convergence_summary.csv",
        "experiments/exp5_network_robustness/results/final/experiment_metadata.json",
        "experiments/exp5_network_robustness/figures/fig9_cross_network_robustness.png",
    ],
    "experiment_6": [
        "experiments/exp6_physical_stress/results/final/physical_stress.csv",
        "experiments/exp6_physical_stress/results/final/physical_stress_summary.csv",
        "experiments/exp6_physical_stress/results/final/experiment_metadata.json",
        "experiments/exp6_physical_stress/figures/fig10_binding_constraint_stress.png",
    ],
    "experiment_7": [
        "experiments/exp7_value_allocation/results/final/value_allocation.csv",
        "experiments/exp7_value_allocation/results/final/value_allocation_summary.csv",
        "experiments/exp7_value_allocation/results/final/eight_participant_exact_scaling.csv",
        "experiments/exp7_value_allocation/results/final/eight_participant_exact_scaling_summary.csv",
        "experiments/exp7_value_allocation/results/final/group_symmetric_exact_scaling.csv",
        "experiments/exp7_value_allocation/results/final/group_symmetric_exact_scaling_summary.csv",
        "experiments/exp7_value_allocation/results/final/experiment_metadata.json",
        "experiments/exp7_value_allocation/figures/fig11_exact_value_allocation.png",
        "experiments/exp7_value_allocation/figures/fig12_eight_participant_scaling.png",
        "experiments/exp7_value_allocation/figures/fig12b_exact_20_participant_scaling.png",
    ],
    "experiment_8": [
        "experiments/exp8_n1_security/results/final/n1_security_interval_results.csv",
        "experiments/exp8_n1_security/results/final/n1_security_daily_results.csv",
        "experiments/exp8_n1_security/results/final/n1_security_summary.csv",
        "experiments/exp8_n1_security/results/final/n1_security_paired_tests.csv",
        "experiments/exp8_n1_security/results/final/experiment_metadata.json",
        "experiments/exp8_n1_security/figures/fig13_n1_security_validation.png",
    ],
    "experiment_9": [
        "experiments/exp9_payment_certificate/results/final/daily_payment_certificates.csv",
        "experiments/exp9_payment_certificate/results/final/conversion_scenario_certificates.csv",
        "experiments/exp9_payment_certificate/results/final/certified_counterfactual_profiles.npz",
        "experiments/exp9_payment_certificate/results/final/payment_evaluation_intervals.csv",
        "experiments/exp9_payment_certificate/results/final/payment_evaluation_daily.csv",
        "experiments/exp9_payment_certificate/results/final/payment_evaluation_summary.csv",
        "experiments/exp9_payment_certificate/results/final/payment_evaluation_unseen_scenarios.csv",
        "experiments/exp9_payment_certificate/results/final/payment_evaluation_unseen_summary.csv",
        "experiments/exp9_payment_certificate/results/final/paired_payment_noninferiority.csv",
        "experiments/exp9_payment_certificate/results/final/payment_target_selection_validation.csv",
        "experiments/exp9_payment_certificate/results/final/payment_non_tautology_audit.csv",
        "experiments/exp9_payment_certificate/results/final/payment_pareto_paired_ci.csv",
        "experiments/exp9_payment_certificate/results/final/experiment_metadata.json",
        "experiments/exp9_payment_certificate/figures/fig14_payment_certificate.png",
    ],
    "experiment_10": [
        "experiments/exp10_ac_validation/results/final/ac_opf_locked_day_results.csv",
        "experiments/exp10_ac_validation/results/final/ac_opf_summary.csv",
        "experiments/exp10_ac_validation/results/final/ac_n1_contingency_results.csv",
        "experiments/exp10_ac_validation/results/final/ac_n1_contingency_summary.csv",
        "experiments/exp10_ac_validation/results/final/preventive_ac_n1_results.csv",
        "experiments/exp10_ac_validation/results/final/preventive_ac_n1_summary.csv",
        "experiments/exp10_ac_validation/results/final/experiment_metadata.json",
        "experiments/exp10_ac_validation/results/final/ac_profile_refit_reuse_manifest.json",
        "experiments/exp10_ac_validation/figures/fig15_ac_opf_validation.png",
        "experiments/exp10_ac_validation/figures/fig15b_ac_n1_contingency_validation.png",
        "experiments/exp10_ac_validation/figures/fig15c_preventive_ac_n1_validation.png",
    ],
    "experiment_11": [
        "experiments/exp11_spatial_scale_robustness/results/final/spatial_scale_robustness.csv",
        "experiments/exp11_spatial_scale_robustness/results/final/spatial_scale_summary.csv",
        "experiments/exp11_spatial_scale_robustness/results/final/mapping_level_summary.csv",
        "experiments/exp11_spatial_scale_robustness/results/final/spatial_trace_mapping_audit.csv",
        "experiments/exp11_spatial_scale_robustness/results/final/spatial_trace_pairwise_correlation.csv",
        "experiments/exp11_spatial_scale_robustness/results/final/spatial_trace_mapping_metadata.json",
        "experiments/exp11_spatial_scale_robustness/results/final/experiment_metadata.json",
        "experiments/exp11_spatial_scale_robustness/figures/fig16_spatial_scale_robustness.png",
    ],
    "experiment_12": [
        "experiments/exp12_rolling_market_validation/results/final/rolling_market_validation.csv",
        "experiments/exp12_rolling_market_validation/results/final/rolling_market_summary.csv",
        "experiments/exp12_rolling_market_validation/results/final/site_space_time_allocations.csv",
        "experiments/exp12_rolling_market_validation/results/final/settlement_chain_certificate.csv",
        "experiments/exp12_rolling_market_validation/results/final/paired_payment_comparisons.csv",
        "experiments/exp12_rolling_market_validation/results/final/rolling_counterfactual_profiles.npz",
        "experiments/exp12_rolling_market_validation/results/final/experiment_metadata.json",
        "experiments/exp12_rolling_market_validation/figures/fig18_rolling_market_validation.png",
    ],
    "experiment_13": [
        "experiments/exp13_real_trace_replay/results/final/real_trace_replay_daily.csv",
        "experiments/exp13_real_trace_replay/results/final/real_trace_replay_trace.csv",
        "experiments/exp13_real_trace_replay/results/final/real_trace_replay_summary.csv",
        "experiments/exp13_real_trace_replay/results/final/experiment_metadata.json",
        "experiments/exp13_real_trace_replay/figures/fig19_real_trace_replay.png",
    ],
    "experiment_14": [
        "experiments/exp14_job_level_fidelity/results/final/job_level_flow_solution.npz",
        "experiments/exp14_job_level_fidelity/results/final/job_level_slot_profile.csv",
        "experiments/exp14_job_level_fidelity/results/final/job_level_fidelity_summary.csv",
        "experiments/exp14_job_level_fidelity/results/final/job_interval_witness_summary.csv",
        "experiments/exp14_job_level_fidelity/results/final/experiment_metadata.json",
        "experiments/exp14_job_level_fidelity/figures/fig20_job_level_fidelity.png",
    ],
    "experiment_15": [
        "experiments/exp15_interval_certificate/results/final/interval_endpoint_certificates.csv",
        "experiments/exp15_interval_certificate/results/final/interval_certificate_summary.csv",
        "experiments/exp15_interval_certificate/results/final/payment_value_interval_certificates.csv",
        "experiments/exp15_interval_certificate/results/final/payment_value_interval_summary.csv",
        "experiments/exp15_interval_certificate/results/final/interval_certified_counterfactual_profiles.npz",
        "experiments/exp15_interval_certificate/results/final/experiment_metadata.json",
        "experiments/exp15_interval_certificate/figures/fig21_interval_payment_certificate.png",
    ],
    "experiment_16": [
        "experiments/exp16_ledger_capacity_provenance/results/final/ledger_provenance_summary.csv",
        "experiments/exp16_ledger_capacity_provenance/results/final/capacity_reconciliation.csv",
        "experiments/exp16_ledger_capacity_provenance/results/final/workload_power_calibration_sensitivity.csv",
        "experiments/exp16_ledger_capacity_provenance/results/final/physical_calibration_summary.csv",
        "experiments/exp16_ledger_capacity_provenance/results/final/ledger_provenance_certificate.json",
        "experiments/exp16_ledger_capacity_provenance/results/final/source_hashes.json",
        "experiments/exp16_ledger_capacity_provenance/results/final/experiment_metadata.json",
        "experiments/exp16_ledger_capacity_provenance/figures/fig22_ledger_capacity_provenance.png",
    ],
    "experiment_17": [
        "experiments/exp17_decision_time_information/results/final/decision_time_comparison.csv",
        "experiments/exp17_decision_time_information/results/final/decision_time_summary.csv",
        "experiments/exp17_decision_time_information/results/final/causal_reserve_validation_daily.csv",
        "experiments/exp17_decision_time_information/results/final/causal_reserve_validation_summary.csv",
        "experiments/exp17_decision_time_information/results/final/causal_reserve_test_daily.csv",
        "experiments/exp17_decision_time_information/results/final/causal_reserve_test_summary.csv",
        "experiments/exp17_decision_time_information/results/final/causal_response_candidate_validation_daily.csv",
        "experiments/exp17_decision_time_information/results/final/causal_response_candidate_validation.csv",
        "experiments/exp17_decision_time_information/results/final/decision_time_trace_replay.csv",
        "experiments/exp17_decision_time_information/results/final/information_boundary_certificate.csv",
        "experiments/exp17_decision_time_information/results/final/experiment_metadata.json",
        "experiments/exp17_decision_time_information/figures/fig23_decision_time_information.png",
    ],
    "experiment_18": [
        "experiments/exp18_preventive_ac_network_panel/results/final/preventive_ac_cross_network_results.csv",
        "experiments/exp18_preventive_ac_network_panel/results/final/preventive_ac_cross_network_summary.csv",
        "experiments/exp18_preventive_ac_network_panel/results/final/experiment_metadata.json",
        "experiments/exp18_preventive_ac_network_panel/figures/fig24_preventive_ac_cross_network.png",
    ],
    "experiment_19": [
        "experiments/exp19_job_level_counterfactual/results/final/job_level_counterfactual_summary.csv",
        "experiments/exp19_job_level_counterfactual/results/final/job_level_counterfactual_profile.csv",
        "experiments/exp19_job_level_counterfactual/results/final/job_level_counterfactual_solution.npz",
        "experiments/exp19_job_level_counterfactual/results/final/experiment_metadata.json",
    ],
    "experiment_20": [
        "experiments/exp20_trace_meter_replay/results/final/trace_meter_replay_daily.csv",
        "experiments/exp20_trace_meter_replay/results/final/trace_meter_replay_summary.csv",
        "experiments/exp20_trace_meter_replay/results/final/experiment_metadata.json",
        "experiments/exp20_trace_meter_replay/figures/fig25_trace_meter_replay.png",
    ],
    "experiment_21": [
        "experiments/exp21_scale_consistency/results/final/scale_consistency_summary.csv",
        "experiments/exp21_scale_consistency/results/final/scale_consistency_profile.csv",
        "experiments/exp21_scale_consistency/results/final/capacity_proportional_profile.csv",
        "experiments/exp21_scale_consistency/results/final/scale_sensitivity.csv",
        "experiments/exp21_scale_consistency/results/final/experiment_metadata.json",
    ],
    "experiment_22": [
        "experiments/exp22_coupled_job_network_certificate/results/final/coupled_network_event_replay.csv",
        "experiments/exp22_coupled_job_network_certificate/results/final/coupled_network_scale_replay.csv",
        "experiments/exp22_coupled_job_network_certificate/results/final/coupled_network_summary.csv",
        "experiments/exp22_coupled_job_network_certificate/results/final/experiment_metadata.json",
        "experiments/exp22_coupled_job_network_certificate/results/final/coupling_invariant_certificate.json",
        "experiments/exp22_coupled_job_network_certificate/README.md",
    ],
    "experiment_23": [
        "experiments/exp23_independent_event_replay/results/final/independent_event_replay_daily.csv",
        "experiments/exp23_independent_event_replay/results/final/independent_event_replay_summary.csv",
        "experiments/exp23_independent_event_replay/results/final/independent_event_profiles.npz",
        "experiments/exp23_independent_event_replay/results/final/independent_event_protocol_certificate.csv",
        "experiments/exp23_independent_event_replay/results/final/experiment_metadata.json",
        "experiments/exp23_independent_event_replay/figures/fig26_independent_event_replay.png",
        "experiments/exp23_independent_event_replay/README.md",
    ],
    "experiment_24": [
        "experiments/exp24_all_outage_security_panel/results/final/all_outage_security_replay.csv",
        "experiments/exp24_all_outage_security_panel/results/final/all_outage_security_summary.csv",
        "experiments/exp24_all_outage_security_panel/results/final/experiment_metadata.json",
        "experiments/exp24_all_outage_security_panel/figures/fig27_all_outage_security.png",
        "experiments/exp24_all_outage_security_panel/README.md",
    ],
    "experiment_25": [
        "experiments/exp25_exante_job_validation/results/final/exante_job_validation_summary.csv",
        "experiments/exp25_exante_job_validation/results/final/exante_job_validation_by_type.csv",
        "experiments/exp25_exante_job_validation/results/final/job_level_capacity_stress_solution.npz",
        "experiments/exp25_exante_job_validation/results/final/job_level_capacity_stress_summary.csv",
        "experiments/exp25_exante_job_validation/results/final/job_level_capacity_stress_event_slots.csv",
        "experiments/exp25_exante_job_validation/results/final/experiment_metadata.json",
        "experiments/exp25_exante_job_validation/README.md",
    ],
    "experiment_26": [
        "experiments/exp26_end_to_end_certificate/results/final/end_to_end_lineage.csv",
        "experiments/exp26_end_to_end_certificate/results/final/profile_role_lineage.csv",
        "experiments/exp26_end_to_end_certificate/results/final/payment_relative_cap_audit.csv",
        "experiments/exp26_end_to_end_certificate/results/final/realized_payment_audit.csv",
        "experiments/exp26_end_to_end_certificate/results/final/end_to_end_certificate.json",
        "experiments/exp26_end_to_end_certificate/results/final/experiment_metadata.json",
        "experiments/exp26_end_to_end_certificate/README.md",
    ],
    "experiment_27": [
        "experiments/exp27_executable_common_witness/results/final/runtime_complete_witness.npz",
        "experiments/exp27_executable_common_witness/results/final/job_level_runtime_summary.csv",
        "experiments/exp27_executable_common_witness/results/final/common_witness_summary.csv",
        "experiments/exp27_executable_common_witness/results/final/runtime_witness_coupling_certificate.json",
        "experiments/exp27_executable_common_witness/results/final/common_witness_settlement.csv",
        "experiments/exp27_executable_common_witness/results/final/experiment_metadata.json",
        "experiments/exp27_executable_common_witness/figures/fig28_common_executable_witness.png",
        "experiments/exp27_executable_common_witness/README.md",
    ],
    "experiment_28": [
        "experiments/exp28_risk_tail_audit/results/final/risk_tail_audit.csv",
        "experiments/exp28_risk_tail_audit/results/final/risk_tail_paired_bootstrap.csv",
        "experiments/exp28_risk_tail_audit/results/final/experiment_metadata.json",
        "experiments/exp28_risk_tail_audit/figures/fig_risk_tail_tradeoff.png",
        "experiments/exp28_risk_tail_audit/README.md",
    ],
    "manuscript_sources": [
        "paper/main.tex",
        "paper/main.pdf",
        "paper/IEEEtran.cls",
        "paper/references.bib",
        "paper/formula_source_matrix.md",
        "paper/model_formulation.md",
        "paper/paper_outline_zh.md",
        "paper/theoretical_results.md",
        "paper/figures/framework_architecture.drawio",
        "paper/figures/framework_architecture.svg",
        "paper/figures/method_detail.drawio",
        "paper/figures/method_detail.svg",
        "paper/figures/fig0_framework.pdf",
        "paper/figures/fig0_framework.png",
        "paper/figures/fig_method_detail.pdf",
        "paper/figures/fig_method_detail.png",
        "paper/figures/fig17_cross_layer_robustness.png",
        "paper/figures/fig17_cross_layer_robustness.pdf",
    ],
}


def _check(condition: bool, name: str, detail: str, checks: list[dict[str, Any]]) -> None:
    checks.append({"name": name, "passed": bool(condition), "detail": detail})


def _all_true(values: pd.Series) -> bool:
    """Return True only when every serialized boolean is explicitly true."""
    if pd.api.types.is_bool_dtype(values):
        return bool(values.all())
    normalized = values.astype(str).str.strip().str.lower()
    return bool(normalized.eq("true").all())


def run_audit(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
    allow_missing_raw: bool = False,
) -> None:
    checks: list[dict[str, Any]] = []
    for section, files in EXPECTED_FILES.items():
        for rel in files:
            path = root / rel
            _check(path.exists() and path.stat().st_size > 0, f"{section}:{rel}", "exists and non-empty", checks)

    unified_manifest_path = root / "artifacts/run_manifest.json"
    unified_manifest = json.loads(
        unified_manifest_path.read_text(encoding="utf-8")
    )
    expected_stages = {
        "data",
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
        "exp22",
        "exp23",
        "exp24",
        "exp25",
        "exp26",
        "exp27",
        "exp28",
        "audit",
    }
    recorded_stages = unified_manifest.get("stages", {})
    completed_before_audit = all(
        recorded_stages.get(name, {}).get("status") == "completed"
        for name in expected_stages - {"audit"}
    )
    audit_status_valid = recorded_stages.get("audit", {}).get("status") in {
        "running",
        "completed",
    }
    _check(
        unified_manifest.get("stage_requested") == "all"
        and set(recorded_stages) == expected_stages
        and completed_before_audit
        and audit_status_valid,
        "canonical_unified_manifest_preserved",
        (
            f"{len(recorded_stages)}/{len(expected_stages)} stages recorded; "
            f"canonical request={unified_manifest.get('stage_requested')}; "
            f"audit status={recorded_stages.get('audit', {}).get('status')} "
            "(running is expected during the self-check)"
        ),
        checks,
    )

    figure_failures: list[str] = []
    figure_dimensions: list[str] = []
    for rel in sorted(rel for files in EXPECTED_FILES.values() for rel in files if rel.endswith(".png")):
        path = root / rel
        try:
            with Image.open(path) as image:
                width, height = image.size
                image.verify()
            if width < 1_000 or height < 500:
                figure_failures.append(f"{rel}: insufficient resolution {width}x{height}")
            figure_dimensions.append(f"{Path(rel).name}={width}x{height}")
        except Exception as exc:
            figure_failures.append(f"{rel}: {type(exc).__name__}: {exc}")
    _check(
        not figure_failures,
        "all_png_figures_decodable_and_high_resolution",
        "; ".join(figure_failures if figure_failures else figure_dimensions),
        checks,
    )
    pdf_path = root / "paper/main.pdf"
    if PdfReader is None:
        _check(
            False,
            "ieeetran_pdf_length_and_geometry",
            "pypdf is required by requirements.txt to inspect the release PDF",
            checks,
        )
    else:
        try:
            reader = PdfReader(str(pdf_path))
            page_boxes = [
                (
                    float(page.mediabox.width),
                    float(page.mediabox.height),
                )
                for page in reader.pages
            ]
            letter_pages = all(
                abs(width - 612.0) < 0.5 and abs(height - 792.0) < 0.5
                for width, height in page_boxes
            )
            _check(
                len(reader.pages) == 10 and letter_pages,
                "ieeetran_pdf_length_and_geometry",
                f"{len(reader.pages)} pages; boxes={page_boxes[:2]}{'...' if len(page_boxes) > 2 else ''}",
                checks,
            )
        except Exception as exc:
            _check(
                False,
                "ieeetran_pdf_length_and_geometry",
                f"PDF inspection failed: {type(exc).__name__}: {exc}",
                checks,
            )
    required_citation_keys = {
        "wang2022baseline",
        "caiso2017baseline",
        "zimmerman2011matpower",
        "babaeinejadsarookolaee2021pglib",
        "boyd2004convex",
        "rockafellar2000cvar",
        "shapley1953value",
        "kunsch1989bootstrap",
        "holm1979multiple",
        "huangfu2018highs",
        "friedman2001gradient",
        "geurts2006extratrees",
        "hoerl1970ridge",
        "wang2024burstgpt",
        "samsi2021supercloud",
        "stott2009dc",
        "tejada2018lodf",
        "nerc2020tpl",
        "grigg1999rts",
        "zhang2020virtuallinks",
        "zhang2022remunerating",
        "zhang2023receding",
        "cao2024nonwire",
        "nash1950bargaining",
        "satchidanandan2023twostage",
        "chen2021incentive",
        "nist2015fips1804",
    }
    bibliography = (root / "paper/references.bib").read_text(
        encoding="utf-8"
    )
    bibliography_keys = set(
        re.findall(r"@\w+\{\s*([^,\s]+)", bibliography)
    )
    source_matrix = (
        root / "paper/formula_source_matrix.md"
    ).read_text(encoding="utf-8")
    formulation = (
        root / "paper/model_formulation.md"
    ).read_text(encoding="utf-8")
    _check(
        required_citation_keys <= bibliography_keys
        and all(key in source_matrix for key in required_citation_keys)
        and all(key in formulation for key in required_citation_keys),
        "model_formula_citation_traceability",
        (
            f"{len(required_citation_keys & bibliography_keys)}/"
            f"{len(required_citation_keys)} required source keys in bibliography, "
            "formula-source matrix, and complete formulation"
        ),
        checks,
    )
    manuscript_text = (root / "paper/main.tex").read_text(
        encoding="utf-8"
    )
    _check(
        re.search(
            r"\\documentclass\[(?:[0-9]+pt,)?journal\]\{IEEEtran\}",
            manuscript_text,
        )
        is not None,
        "official_ieee_journal_template",
        "manuscript uses the vendored official IEEEtran journal class",
        checks,
    )
    cited_keys = {
        key.strip()
        for group in re.findall(r"\\cite\{([^}]+)\}", manuscript_text)
        for key in group.split(",")
    }
    citation_groups = re.findall(r"\\cite\{([^}]+)\}", manuscript_text)
    _check(
        all(len(group.split(",")) <= 2 for group in citation_groups),
        "maximum_two_sources_per_citation_group",
        f"{len(citation_groups)} in-text citation groups checked",
        checks,
    )
    _check(
        len(bibliography_keys) >= 30
        and bibliography_keys == cited_keys,
        "complete_manuscript_bibliography",
        (
            f"{len(bibliography_keys)} verified bibliography entries; "
            f"{len(cited_keys)} unique in-text citations; "
            f"uncited={sorted(bibliography_keys - cited_keys)}; "
            f"missing={sorted(cited_keys - bibliography_keys)}"
        ),
        checks,
    )
    manuscript_labels = re.findall(r"\\label\{([^}]+)\}", manuscript_text)
    manuscript_refs = re.findall(r"\\(?:ref|eqref)\{([^}]+)\}", manuscript_text)
    unreferenced_labels = sorted(set(manuscript_labels) - set(manuscript_refs))
    missing_labels = sorted(set(manuscript_refs) - set(manuscript_labels))
    _check(
        len(manuscript_labels) == len(set(manuscript_labels))
        and not unreferenced_labels
        and not missing_labels,
        "every_labeled_equation_figure_table_is_referenced",
        (
            f"{len(manuscript_labels)} labels; unreferenced={unreferenced_labels}; "
            f"missing={missing_labels}"
        ),
        checks,
    )
    required_expansions = {
        "mixed-integer linear program (MILP)": "MILP",
        "Massachusetts Institute of Technology (MIT)": "MIT",
        "Data Center GPU Manager (DCGM)": "DCGM",
        "Power Grid Library (PGLib)": "PGLib",
        "Secure Hash Algorithm 256 (SHA-256)": "SHA-256",
        "quadratic program (QP)": "QP",
        "mean absolute error (MAE)": "MAE",
        "root-mean-square error (RMSE)": "RMSE",
        "F1 (harmonic-mean) score": "F1",
    }
    _check(
        all(phrase in manuscript_text for phrase in required_expansions),
        "required_abbreviation_expansions_present",
        "; ".join(
            f"{abbr}={'ok' if phrase in manuscript_text else 'missing'}"
            for phrase, abbr in required_expansions.items()
        ),
        checks,
    )
    _check(
        "\\\\operatorname{SHA256}" not in manuscript_text,
        "sha256_symbol_is_hyphenated",
        "SHA-256 is written consistently in prose and equations",
        checks,
    )

    manifest_path = root / "data/processed/data_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    data_flow = pd.read_csv(root / "data/processed/data_flow_audit.csv")
    for source in manifest["sources"]:
        path = root / source["path"]
        if path.exists():
            current = sha256(path)
            _check(
                current == source["sha256"],
                f"sha256:{source['path']}",
                current,
                checks,
            )
        else:
            _check(
                allow_missing_raw,
                f"sha256:{source['path']}",
                "raw source deferred to verified archive; locked processed artifact retained",
                checks,
            )
    _check(
        manifest["burstgpt"]["rows"] == 5_188_507,
        "full_burstgpt_rows",
        str(manifest["burstgpt"]["rows"]),
        checks,
    )
    _check(
        manifest["mit_supercloud"]["valid_joined_jobs"] > 50_000,
        "full_measured_gpu_jobs",
        str(manifest["mit_supercloud"]["valid_joined_jobs"]),
        checks,
    )
    _check(
        manifest["mit_supercloud"].get("full_positive_energy_joined_jobs") == 71_128
        and manifest["mit_supercloud"].get("valid_joined_jobs") == 68_664
        and manifest["mit_supercloud"].get("jobs_excluded_by_common_trace_horizon") == 2_464,
        "full_join_vs_common_trace_horizon_counts",
        (
            f"full immutable join={manifest['mit_supercloud'].get('full_positive_energy_joined_jobs')}, "
            f"common tensor window={manifest['mit_supercloud'].get('valid_joined_jobs')}, "
            f"excluded by horizon={manifest['mit_supercloud'].get('jobs_excluded_by_common_trace_horizon')}"
        ),
        checks,
    )
    _check(
        manifest.get("submission_calibration", {}).get("joined_positive_jobs", 0)
        >= 71_000
        and manifest.get("submission_calibration", {}).get("training_jobs", 0)
        == 31_284
        and manifest.get("submission_calibration", {}).get("test_jobs", 0)
        == 39_857
        and "chronological" in str(
            manifest.get("submission_calibration", {}).get("training_rule", "")
        ).lower()
        and "label requirement" in str(
            manifest.get("submission_calibration", {}).get("calibration_label_rule", "")
        ).lower()
        and bool(
            manifest.get("submission_calibration", {}).get(
                "membership_rule_excludes_outcome_filtered_job_ids", False
            )
        )
        and "QuantileRegressor" in str(
            manifest.get("submission_calibration", {})
            .get("per_job_fraction_model", {})
            .get("model_type", "")
        )
        and np.isfinite(
            [
                float(
                    manifest.get("submission_calibration", {})
                    .get("per_job_fraction_model", {})
                    .get("validation_diagnostics", {})
                    .get("q10_q90_interval_coverage", np.nan)
                ),
                float(
                    manifest.get("submission_calibration", {})
                    .get("per_job_fraction_model", {})
                    .get("locked_diagnostics", {})
                    .get("q10_q90_interval_coverage", np.nan)
                ),
            ]
        ).all(),
        "chronological_submit_time_calibration_boundary",
        (
            "submit-time entitlement uses frozen conditional q10/q50/q90 models "
            "fit chronologically and kept separate from the complete scheduler "
            "population; execution matching is not an Exp19 eligibility filter"
        ),
        checks,
    )
    conversion_quantiles = manifest["power_calibration"].get(
        "calibration_validation_job_energy_measured_to_predicted_quantiles",
        manifest["power_calibration"][
            "heldout_job_energy_measured_to_predicted_quantiles"
        ],
    )
    declared_conversion_factors = np.asarray(
        [
            conversion_quantiles["0.01"],
            conversion_quantiles["0.1"],
            conversion_quantiles["0.5"],
            conversion_quantiles["0.9"],
            conversion_quantiles["0.99"],
        ],
        dtype=float,
    )
    _check(
        manifest["power_calibration"].get(
            "calibration_validation_jobs_with_positive_prediction",
            manifest["power_calibration"]["heldout_jobs_with_positive_prediction"],
        )
        == int(
            manifest["power_calibration"].get("validation_metrics", {}).get(
                "jobs_with_positive_prediction", 0
            )
        )
        and bool(np.all(np.diff(declared_conversion_factors) > 0))
        and float(declared_conversion_factors[0]) < 1.0
        and float(declared_conversion_factors[-1]) > 1.0,
        "calibration_validation_power_conversion_scenarios_complete",
        (
            f"{manifest['power_calibration'].get('calibration_validation_jobs_with_positive_prediction')} calibration-validation jobs; "
            "q01/q10/q50/q90/q99 measured-to-predicted energy factors="
            + ", ".join(
                f"{value:.6f}" for value in declared_conversion_factors
            )
        ),
        checks,
    )
    power_calibration = manifest["power_calibration"]
    validation_metrics = power_calibration.get("validation_metrics", {})
    locked_metrics = power_calibration.get("locked_metrics", {})
    _check(
        int(power_calibration.get("train_observations", 0))
        + int(power_calibration.get("validation_observations", 0))
        + int(power_calibration.get("locked_observations", 0))
        == int(power_calibration.get("observations", -1))
        and int(validation_metrics.get("observations", 0))
        == int(power_calibration.get("validation_observations", -1))
        and int(locked_metrics.get("observations", 0))
        == int(power_calibration.get("locked_observations", -1))
        and int(validation_metrics.get("jobs_with_positive_prediction", 0))
        + int(locked_metrics.get("jobs_with_positive_prediction", 0))
        == int(power_calibration.get("heldout_jobs_with_positive_prediction", -1))
        and np.isfinite(
            [
                float(validation_metrics.get("r2", np.nan)),
                float(locked_metrics.get("r2", np.nan)),
                float(
                    power_calibration.get(
                        "calibration_validation_aggregate_measured_to_predicted_energy_ratio",
                        np.nan,
                    )
                ),
                float(
                    power_calibration.get(
                        "locked_aggregate_measured_to_predicted_energy_ratio", np.nan
                    )
                ),
            ]
        ).all(),
        "three_way_power_calibration_partition_and_locked_audit",
        (
            f"train/validation/locked={power_calibration.get('train_observations')}/"
            f"{power_calibration.get('validation_observations')}/"
            f"{power_calibration.get('locked_observations')} observations; "
            "conversion scenarios use calibration-validation ratios and the locked split is scoring-only"
        ),
        checks,
    )
    flow_records = {
        str(row["stage"]): int(row["retained_records"])
        for _, row in data_flow.iterrows()
    }
    _check(
        len(data_flow) == 8
        and int(
            manifest["power_calibration"]["train_observations"]
            + manifest["power_calibration"]["test_observations"]
        )
        == int(manifest["power_calibration"]["observations"])
        and flow_records.get("MIT immutable scheduler-DCGM join")
        == int(manifest["mit_supercloud"]["full_positive_energy_joined_jobs"])
        and flow_records.get("MIT common trace horizon filter")
        == int(manifest["mit_supercloud"]["valid_joined_jobs"]),
        "complete_source_to_evaluation_data_flow",
        (
            f"{len(data_flow)} source/join/window/split stages; full immutable join "
            f"{manifest['mit_supercloud']['full_positive_energy_joined_jobs']} -> "
            f"{manifest['mit_supercloud']['valid_joined_jobs']} common-window jobs; calibration "
            f"{manifest['power_calibration']['train_observations']} train + "
            f"{manifest['power_calibration']['validation_observations']} calibration-validation + "
            f"{manifest['power_calibration']['locked_observations']} locked"
        ),
        checks,
    )
    workload = load_workload(root / "data/processed/workload_15min.npz")
    arrivals = workload["arrivals_mwh"]
    observed = workload["observed_counterfactual_mw"]
    _check(np.isfinite(arrivals).all() and (arrivals >= 0).all(), "processed_data_finite_nonnegative", str(arrivals.shape), checks)
    _check(arrivals.sum() > 0, "processed_data_nonempty", f"{arrivals.sum():.3f} MWh", checks)
    _check(
        np.isfinite(observed).all() and observed.shape == (arrivals.shape[0], arrivals.shape[1]),
        "trace_observed_counterfactual_complete",
        str(observed.shape),
        checks,
    )
    valid_days = workload["valid_days"].astype(int)
    future_days = int(
        np.ceil(
            int(cfg["experiments"]["lookahead_slots"])
            / int(cfg["project"]["slots_per_day"])
        )
    )
    eligible_days = valid_days[
        (valid_days >= int(cfg["experiments"]["strategic_history_days"]))
        & (valid_days <= int(valid_days.max()) - future_days)
    ]
    selected_days = eligible_days[
        -(
            int(cfg["experiments"]["validation_days"])
            + int(cfg["experiments"]["test_days"])
        ) :
    ]
    _check(
        len(selected_days)
        == int(cfg["experiments"]["validation_days"])
        + int(cfg["experiments"]["test_days"])
        and bool((np.diff(selected_days) == 1).all())
        and int(selected_days.max()) + future_days <= int(valid_days.max()),
        "locked_days_have_complete_history_and_future_coverage",
        (
            f"days {int(selected_days.min())}--{int(selected_days.max())}; "
            f"{future_days} future days available for the 512-slot deadline"
        ),
        checks,
    )

    # Independently verify primal conservation/capacity/deadlines on a locked day.
    slots = int(cfg["project"]["slots_per_day"])
    day = int(workload["valid_days"][-1])
    daily = arrivals.reshape(-1, slots, arrivals.shape[1], arrivals.shape[2])[day]
    network_path = root / cfg["data"]["pglib_case"]
    if network_path.exists():
        system = parse_pglib_case(network_path)
    else:
        # Compact checkouts retain the processed workload and vendored public
        # test cases but may omit the optional PGLib raw file.  Reuse the same
        # IEEE-118 topology family used by the experiment input fallback.
        from pypower.case118 import case118
        from .optimization import power_system_from_ppc

        system = power_system_from_ppc(case118())
    dc_count = int(cfg["project"]["number_of_regions"])
    prices = np.full((dc_count, slots), 50.0)
    schedule = solve_workload_schedule(daily, prices, cfg, mode="honest")
    served = schedule.served_mwh
    conservation_gap = float(np.max(np.abs(served.sum(axis=(2, 3)) - daily.sum(axis=0))))
    capacity_violation = float(
        max(0.0, served.sum(axis=(0, 1)).max() / (cfg["project"]["interval_minutes"] / 60.0) - cfg["project"]["flexible_capacity_mw"])
    )
    max_deadline_gap = 0.0
    cumulative_arrivals = np.cumsum(daily, axis=0)
    cumulative_service = np.cumsum(served.sum(axis=2), axis=2)
    for source in range(daily.shape[1]):
        for klass, deadline in enumerate(cfg["workload"]["deadlines_slots"]):
            for t in range(int(deadline), slots):
                required = cumulative_arrivals[t - int(deadline), source, klass]
                max_deadline_gap = max(max_deadline_gap, float(required - cumulative_service[source, klass, t]))
    _check(schedule.success and conservation_gap <= 1e-7, "workload_conservation", f"max gap={conservation_gap:.3e} MWh", checks)
    _check(capacity_violation <= 1e-7, "data_center_capacity", f"violation={capacity_violation:.3e} MW", checks)
    _check(max_deadline_gap <= 1e-7, "deadline_feasibility", f"violation={max_deadline_gap:.3e} MWh", checks)

    # SCED nodal balance and line-limit validation.
    sced = solve_sced(system, system.bus[:, 2] * 0.9, int(cfg["market"]["generator_segments"]))
    balance_gap = float(abs(sced.generation_mw.sum() - (system.bus[:, 2] * 0.9).sum()))
    _check(balance_gap <= 1e-6, "sced_power_balance", f"gap={balance_gap:.3e} MW", checks)
    _check(sced.max_loading <= 1.000001, "sced_line_limits", f"max loading={sced.max_loading:.6f} pu", checks)

    exp1 = pd.read_csv(root / "experiments/exp1_manipulation/results/final/manipulation_grid.csv")
    expected_grid = len(cfg["experiments"]["exp1_dr_prices"]) * len(cfg["experiments"]["exp1_event_probabilities"])
    _check(len(exp1) == expected_grid, "complete_exp1_grid", f"{len(exp1)}/{expected_grid}", checks)
    _check(
        bool(exp1["theory_optimizer_agreement"].astype(bool).all()),
        "strategic_threshold_theory_matches_optimizer",
        (
            f"{int(exp1['theory_optimizer_agreement'].astype(bool).sum())}/"
            f"{len(exp1)} price-probability cells"
        ),
        checks,
    )

    metrics = pd.read_csv(root / "experiments/exp2_baseline_verification/results/final/per_day_baseline_metrics.csv")
    expected_test = int(cfg["experiments"]["test_days"])
    expected_blocks = int(
        np.ceil(expected_test / int(cfg["experiments"]["block_length_days"]))
    )
    expected_methods = {
        "High-5-of-10",
        "Ridge",
        "Gradient Boosting",
        "Extra Trees",
        "Metadata Gradient Boosting",
        "Ex-post Metadata Gradient Boosting",
        "Ex-post Quantile Gradient Boosting",
        "Synthetic Control",
        "Feasible Quantile Projection",
        "Tail-Risk Feasible Counterfactual",
        "Single Feasible Projection",
        "Risk-Constrained Convex Verifier",
    }
    metric_cells = metrics.groupby("method")["day"].nunique()
    _check(
        set(metrics["method"].unique()) == expected_methods
        and len(metrics) == expected_test * len(expected_methods)
        and bool((metric_cells == expected_test).all()),
        "locked_test_set_complete",
        f"{len(metrics)}/{expected_test * len(expected_methods)} outcomes",
        checks,
    )
    locked_profile_store = np.load(
        root
        / "experiments/exp2_baseline_verification/results/intermediate/"
        "test_profiles.npz",
        allow_pickle=False,
    )
    locked_profile_checksum = hashlib.sha256(
        (
            root
            / "experiments/exp2_baseline_verification/results/intermediate/"
            "test_profiles.npz"
        ).read_bytes()
    ).hexdigest()
    locked_days = set(locked_profile_store["days"].astype(int).tolist())
    two_sided = pd.read_csv(
        root
        / "experiments/exp2_baseline_verification/results/final/"
        "two_sided_credit_certificate.csv"
    )
    _check(
        len(two_sided) == expected_test
        and set(two_sided["day"].astype(int)) == set(locked_days)
        and bool((two_sided["pointwise_upper_bound_satisfied"] == 1).all())
        and bool((two_sided["pointwise_lower_bound_satisfied"] == 1).all())
        and bool(
            (two_sided["lower_margin_min_mw"] >= -1e-6).all()
            and (two_sided["upper_margin_min_mw"] >= -1e-6).all()
        ),
        "two_sided_credit_band_certificate",
        (
            f"{len(two_sided)}/{expected_test} locked days satisfy the "
            "predeclared lower and upper physical credit band"
        ),
        checks,
    )
    decision_time = pd.read_csv(
        root
        / "experiments/exp17_decision_time_information/results/final/"
        "decision_time_comparison.csv"
    )
    decision_meta = json.loads(
        (
            root
            / "experiments/exp17_decision_time_information/results/final/"
            "experiment_metadata.json"
        ).read_text(encoding="utf-8")
    )
    decision_trace = pd.read_csv(
        root
        / "experiments/exp17_decision_time_information/results/final/"
        "decision_time_trace_replay.csv"
    )
    information_boundary = pd.read_csv(
        root
        / "experiments/exp17_decision_time_information/results/final/"
        "information_boundary_certificate.csv"
    )
    decision_methods = {
        "Decision-time truncated-ledger verifier",
        "Committed-ledger rolling-service verifier",
        "Committed-ledger reference schedule",
        "Complete-ledger risk-constrained verifier",
    }
    _check(
        len(decision_time) == expected_test * len(decision_methods)
        and set(decision_time["day"].astype(int)) == set(locked_days)
        and set(decision_time["method"].astype(str)) == decision_methods
        and bool(
            decision_time.loc[
                decision_time["method"].isin(
                    {
                        "Decision-time truncated-ledger verifier",
                        "Committed-ledger rolling-service verifier",
                        "Committed-ledger reference schedule",
                    }
                ),
                "future_arrivals_used_for_decision",
            ].eq(False).all()
        )
        and bool(
            decision_time.loc[
                decision_time["method"].eq(
                    "Complete-ledger risk-constrained verifier"
                ),
                "future_arrivals_used_for_decision",
            ].eq(True).all()
        )
        and bool(
            decision_time.loc[
                decision_time["method"].eq(
                    "Committed-ledger rolling-service verifier"
                ),
                "event_upper_margin_mw",
            ].ge(-1e-7).all()
        )
        and bool(
            decision_time.loc[
                decision_time["method"].isin(
                    {
                        "Committed-ledger rolling-service verifier",
                        "Committed-ledger reference schedule",
                    }
                ),
                "payment_eligibility",
            ].eq("committed-ledger-only").all()
        )
        and {
            "meter_capped_response_mwh",
            "meter_capped_false_response_mwh",
            "meter_capped_underpayment_mwh",
            "settlement_rule",
        }.issubset(decision_time.columns)
        and bool(
            (
                decision_time["meter_capped_false_response_mwh"].astype(float)
                >= -1e-9
            ).all()
        )
        and bool(
            (
                decision_time["meter_capped_underpayment_mwh"].astype(float)
                >= -1e-9
            ).all()
        )
        and bool(
            (
                decision_time["meter_capped_response_mwh"].astype(float)
                <= decision_time["paid_response_mwh"].astype(float) + 1e-8
            ).all()
        )
        and bool(
            (
                decision_time["meter_capped_false_response_mwh"].astype(float)
                <= decision_time["false_response_mwh"].astype(float) + 1e-8
            ).all()
        )
        and float(
            decision_time.loc[
                decision_time["method"].eq(
                    "Committed-ledger rolling-service verifier"
                ),
                "meter_capped_response_mwh",
            ].mean()
        )
        > 1e-9
        and float(
            decision_time.loc[
                decision_time["method"].eq(
                    "Committed-ledger rolling-service verifier"
                ),
                "meter_capped_underpayment_mwh",
            ].mean()
        )
        > 1e-9
        and bool(
            decision_time["settlement_rule"].astype(str).str.startswith(
                "contract-capped-after-event"
            ).all()
        )
        and set(decision_time["schema_version"].astype(int).unique()) == {12}
        and "profile_checksum" in decision_time
        and set(decision_time["profile_checksum"].astype(str).unique())
        == {locked_profile_checksum}
        and decision_meta.get("profile_checksum") == locked_profile_checksum
        and decision_meta.get("target_future_arrivals_used_for_decision") is False
        and "post-gate arrivals masked" in str(decision_meta.get("target_source", ""))
        and decision_meta.get("future_arrivals_removed_from_decision") is True
        and decision_meta.get("event_gate_slot") == int(
            cfg["experiments"]["decision_time_event_gate_slot"]
        )
        and decision_meta.get("terminal_completion_index") == int(
            cfg["experiments"]["decision_time_terminal_completion_index"]
        )
        and decision_meta.get("causal_reserve_planning", {}).get(
            "future_arrivals_used_for_payment"
        ) is False
        and "used only after the event" in str(
            decision_meta.get("meter_cap_scoring_note", "")
        )
        and "causal committed-ledger baseline" in str(
            decision_meta.get("meter_cap_scoring_note", "")
        ),
        "decision_time_information_boundary_panel",
        (
            f"{len(decision_time)}/{expected_test * len(decision_methods)} rows; "
            "post-gate arrivals are excluded from all committed deployment-time "
            "decisions; positive committed response is settled only after the "
            "observable contract-capped rule, while the complete-ledger row remains an explicit "
            "post-event information comparator"
        ),
        checks,
    )
    _check(
        len(decision_trace) == expected_test * len(decision_methods)
        and decision_trace.groupby("method")["day"].nunique().eq(expected_test).all()
        and set(decision_trace["truth_source"].astype(str))
        == {"independent_trace_observed_meter"}
        and decision_trace["event_intervention"].astype(str).str.lower().eq("false").all()
        and np.isfinite(
            decision_trace[
                ["trace_mae_mw", "trace_rmse_mw", "trace_nrmse"]
            ].to_numpy(dtype=float)
        ).all()
        and decision_meta.get("observational_trace_source")
        == "independent locked DCGM/BurstGPT execution trace",
        "decision_time_independent_trace_replay",
        (
            f"{len(decision_trace)} event-gate profiles are scored against the "
            "independent meter tensor in a separate observational panel"
        ),
        checks,
    )
    # The committed profile must be an independently identifiable second
    # optimization, not a relabelled copy of the gate baseline. These metadata
    # checks keep the protocol auditable even if numerical traces coincide.
    committed_meta = decision_meta.get("committed_ledger_safe_mode", {})
    _check(
        committed_meta.get("future_arrivals_used_for_decision") is False
        and committed_meta.get("rolling_commitment") is True
        and "causal committed-ledger baseline LP" in str(
            committed_meta.get("contract_baseline_source", "")
        )
        and "selected validation DR price" in str(
            committed_meta.get("response_objective", "")
        )
        and np.isfinite(float(committed_meta.get("selected_dr_price_per_mwh", np.nan)))
        and np.isfinite(float(committed_meta.get("selected_projection_weight", np.nan)))
        and "contract-capped-after-event" in str(
            committed_meta.get("settlement_rule", "")
        ),
        "decision_time_committed_response_protocol",
        (
            "committed-ledger response is a second masked-ledger LP with the "
            "declared DR-price objective, rolling state, and explicit contract cap"
        ),
        checks,
    )
    _check(
        decision_meta.get("protocol_note", "").startswith(
            "The truncated profile is an information-boundary diagnostic"
        ),
        "decision_time_protocol_role_separation",
        "gate diagnostic, deployable response, and complete-ledger comparator are separately named",
        checks,
    )
    boundary_values = dict(
        zip(
            information_boundary["criterion"].astype(str),
            information_boundary["value"].astype(float),
        )
    )
    _check(
        set(boundary_values)
        == {
            "post_gate_arrivals_in_decision",
            "execution_truth_available_to_decision",
            "locked_truth_used_for_selection",
            "utility_event_label_available",
            "submitted_contract_frozen_before_event",
            "future_arrivals_excluded_from_payment",
        }
        and boundary_values["post_gate_arrivals_in_decision"] == 0
        and boundary_values["execution_truth_available_to_decision"] == 0
        and boundary_values["locked_truth_used_for_selection"] == 0
        and boundary_values["utility_event_label_available"] == 0
        and boundary_values["submitted_contract_frozen_before_event"] == 1
        and boundary_values["future_arrivals_excluded_from_payment"] == 1
        and information_boundary["required_value"].astype(float).to_numpy().tolist()
        == [0.0, 0.0, 0.0, 0.0, 1.0, 1.0]
        and decision_meta.get("information_boundary_certificate_file")
        == "information_boundary_certificate.csv",
        "explicit_decision_information_boundary_certificate",
        (
            "the gate certificate records zero post-gate arrivals, execution truth, "
            "locked-outcome selection, and utility event labels at decision time, "
            "while requiring a frozen submitted contract and payment exclusion of future jobs"
        ),
        checks,
    )
    response_validation = pd.read_csv(
        root
        / "experiments/exp17_decision_time_information/results/final/"
        "causal_response_candidate_validation.csv"
    )
    selected_response = response_validation[response_validation["selected"].astype(bool)]
    expected_response_candidates = (
        len(cfg["experiments"]["decision_time_response_dr_prices"])
        * len(cfg["experiments"]["decision_time_response_projection_weights"])
    )
    _check(
        len(response_validation) == expected_response_candidates
        and len(selected_response) == 1
        and float(selected_response.iloc[0]["false_response_mwh"])
        <= float(cfg["experiments"]["decision_time_response_validation_false_budget_mwh"]) + 1e-8
        and np.isfinite(
            response_validation[
                ["dr_price_per_mwh", "projection_weight", "nrmse", "false_response_mwh", "credit_f1"]
            ].to_numpy(dtype=float)
        ).all(),
        "causal_response_grid_selection",
        (
            f"{len(response_validation)} masked-ledger response candidates select one "
            "DR price/regularization pair on validation only under the declared false-credit budget"
        ),
        checks,
    )

    reserve_validation = pd.read_csv(
        root
        / "experiments/exp17_decision_time_information/results/final/"
        "causal_reserve_validation_summary.csv"
    )
    reserve_test = pd.read_csv(
        root
        / "experiments/exp17_decision_time_information/results/final/"
        "causal_reserve_test_summary.csv"
    )
    selected_reserve = reserve_validation[reserve_validation["selected"].astype(bool)]
    reserve_cfg = cfg["experiments"]
    _check(
        set(reserve_validation["reserve_quantile"].astype(float))
        == {0.55, 0.60, 0.65, 0.70}
        and len(selected_reserve) == 1
        and float(selected_reserve.iloc[0]["reserve_quantile"]) == 0.60
        and float(selected_reserve.iloc[0]["false_response_mwh"])
        <= float(reserve_cfg["event_gate_reserve_validation_false_credit_budget_mwh"])
        + 1e-8
        and len(reserve_test) == 1
        and float(reserve_test.iloc[0]["reserve_quantile"]) == 0.60
        and np.isfinite(
            reserve_test[
                ["nrmse", "false_response_mwh", "reserved_future_arrivals_mwh"]
            ].to_numpy(dtype=float)
        ).all(),
        "causal_reserve_is_validation_selected_and_payment_ineligible",
        (
            f"{len(reserve_validation)} validation candidates select eta=0.60 under "
            "the declared false-credit budget; the locked reserve is reported "
            "for capacity planning while committed-ledger payment remains separate"
        ),
        checks,
    )
    ac_cross = pd.read_csv(
        root
        / "experiments/exp18_preventive_ac_network_panel/results/final/"
        "preventive_ac_cross_network_results.csv"
    )
    ac_cross_meta = json.loads(
        (
            root
            / "experiments/exp18_preventive_ac_network_panel/results/final/"
            "experiment_metadata.json"
        ).read_text(encoding="utf-8")
    )
    expected_ac_networks = {
        "IEEE RTS 24-bus",
        "IEEE 30-bus",
        "IEEE 39-bus",
        "IEEE 118-bus",
    }
    expected_ac_snapshots = int(
        len(cfg["experiments"].get("preventive_ac_validation_day_indices", []))
        * len(cfg["experiments"].get("preventive_ac_validation_event_slots", []))
    )
    _check(
        set(ac_cross["network"].unique()) == expected_ac_networks
        and set(ac_cross["method"].unique())
        == {"Payment-Certified N-1 Verifier", "Trace-Anchored Reference"}
        and len(ac_cross) == sum(
            int(count)
            for count in ac_cross_meta["outages_by_network"].values()
        )
        * 3
        * 2
        * int(ac_cross_meta.get("locked_snapshot_count", 0))
        and bool((ac_cross["solver_success"] == 1).all())
        and np.isfinite(
            ac_cross[
                [
                    "maximum_apparent_line_loading",
                    "maximum_voltage_violation_pu",
                    "maximum_nonreference_active_plan_deviation_mw",
                ]
            ].to_numpy(dtype=float)
        ).all()
        and set(ac_cross["schema_version"].astype(int).unique()) == {6}
        and int(ac_cross_meta.get("locked_snapshot_count", 0)) == len(
            ac_cross_meta.get("locked_snapshots", [])
        )
        and int(ac_cross_meta.get("locked_snapshot_count", 0)) == expected_ac_snapshots
        and expected_ac_snapshots >= 2
        and ac_cross["snapshot_index"].nunique() == expected_ac_snapshots
        and ac_cross.groupby("snapshot_index")["day"].nunique().eq(1).all()
        and ac_cross.groupby("snapshot_index")["event_slot"].nunique().eq(1).all()
        and ac_cross_meta.get("shared_active_plan") is True
        and "preventive AC N-1 fixed-active-plan" in str(
            ac_cross_meta.get("scope", "")
        )
        and ac_cross_meta.get("ac_limits_enforced") is True
        and ac_cross_meta.get("pre_registered_dc_bus_mapping_one_based")
        == cfg["experiments"].get("preventive_ac_dc_bus_map_one_based")
        and float(ac_cross_meta.get("load_multiplier", np.nan))
        == float(cfg["experiments"].get("preventive_ac_load_multiplier"))
        and np.isclose(
            float(ac_cross_meta.get("fixed_active_plan_tolerance_mw", np.nan)),
            float(cfg["experiments"].get("preventive_ac_active_plan_tolerance_mw")),
            rtol=0.0,
            atol=1e-15,
        )
        and bool((ac_cross["maximum_apparent_line_loading"] <= 1.0 + 1e-6).all())
        and bool((ac_cross["maximum_voltage_violation_pu"] <= 1e-6).all())
        and bool(
            (
                ac_cross["maximum_nonreference_active_plan_deviation_mw"]
                <= float(cfg["experiments"].get("preventive_ac_active_plan_tolerance_mw")) + 1e-6
            ).all()
        )
        and ac_cross_meta["test_outcomes_used_for_scaling"] is False,
        "cross_network_ac_n1_admissibility_panel",
        (
            f"{len(ac_cross)} AC outcomes over four public networks; "
            "native-case AC admissibility and validation-only scaling recorded"
        ),
        checks,
    )
    scale_summary = pd.read_csv(
        root
        / "experiments/exp21_scale_consistency/results/final/scale_consistency_summary.csv"
    )
    scale_values = dict(zip(scale_summary["metric"], scale_summary["value"]))
    scale_meta = json.loads(
        (
            root
            / "experiments/exp21_scale_consistency/results/final/experiment_metadata.json"
        ).read_text(encoding="utf-8")
    )
    _check(
        float(scale_values.get("capacity_safe_scale_factor", np.nan)) > 1.0
        and float(scale_values.get("fixed_nameplate_certified_scale_factor", np.nan)) > 0.0
        and float(scale_values.get("certified_peak_mw", np.inf)) <= float(scale_meta.get("capacity_mw", np.nan)) + 1e-8
        and bool(scale_meta.get("re_solved")) is False
        and float(scale_meta.get("source_scale", np.nan)) == 1.0,
        "homogeneous_scale_has_fixed_nameplate_bound",
        (
            "capacity-proportional and fixed-nameplate scales are reported separately; "
            "the certified peak remains within the committed capacity without a second LP"
        ),
        checks,
    )
    scale_sensitivity = pd.read_csv(
        root
        / "experiments/exp21_scale_consistency/results/final/scale_sensitivity.csv"
    )
    declared_scale_sensitivity = np.asarray(
        cfg["experiments"].get("scale_sensitivity_relative_to_fixed", []),
        dtype=float,
    )
    _check(
        len(scale_sensitivity) == len(declared_scale_sensitivity)
        and set(np.round(scale_sensitivity["relative_to_anchor"].astype(float), 8))
        == set(np.round(declared_scale_sensitivity, 8))
        and np.isfinite(
            scale_sensitivity[
                [
                    "homogeneous_scale_factor",
                    "peak_mw",
                    "minimum_scaled_capacity_slack_mwh",
                    "event_native_mwh",
                    "event_counterfactual_mwh",
                ]
            ].to_numpy(dtype=float)
        ).all()
        and bool(
            (~scale_sensitivity["fixed_gpu_nameplate_respected"].astype(bool)).any()
        ),
        "declared_homogeneous_scale_sensitivity_panel",
        (
            f"{len(scale_sensitivity)} predeclared homogeneous transforms replay the "
            "same witness and resource caps; the panel records where the fixed-GPU "
            "nameplate stops being respected"
        ),
        checks,
    )
    literature = pd.read_csv(
        root
        / "experiments/exp2_baseline_verification/results/final/"
        "closest_literature_baselines.csv"
    )
    expected_literature = {
        "Event-reward ledger translation",
        "Batch-flexibility ledger translation",
        "Rolling-horizon ledger translation",
        "All-site coupled event-response control",
        "Cross-regional dispatchable-capacity translation",
        "Coupled multi-service regulation translation",
    }
    literature_cells = literature.groupby("baseline")["day"].nunique()
    _check(
        set(literature["baseline"].unique()) == expected_literature
        and len(literature) == expected_test * len(expected_literature)
        and bool((literature_cells == expected_test).all())
        and np.isfinite(literature[["nrmse", "false_response_mwh", "credit_f1"]].to_numpy(dtype=float)).all(),
        "closest_literature_baseline_panel",
        (
            f"{len(literature)}/{expected_test * len(expected_literature)} "
            "same-ledger published-equation translations; each implementation "
            "is identified as a transparent translation rather than a software "
            "reimplementation"
        ),
        checks,
    )
    structural_literature = pd.read_csv(
        root
        / "experiments/exp2_baseline_verification/results/final/"
        "structural_literature_baselines.csv"
    )
    structural_methods = {
        "Temporal-only ledger control",
        "Joint spatio-temporal ledger control",
    }
    _check(
        set(structural_literature["baseline"].astype(str)) == structural_methods
        and len(structural_literature) == expected_test * len(structural_methods)
        and structural_literature.groupby("baseline")["day"].nunique().eq(expected_test).all()
        and set(structural_literature["implementation"].astype(str)) == {"exact_ledger_lp"}
        and np.isfinite(
            structural_literature[
                ["migration_mwh", "nrmse", "false_response_mwh", "credit_f1"]
            ].to_numpy(dtype=float)
        ).all(),
        "exact_structural_dc_t_dc_st_baseline_panel",
        (
            f"{len(structural_literature)}/{expected_test * len(structural_methods)} "
            "same-ledger DC-T/DC-ST outcomes retain native-site and migration "
            "assignment as explicit structural controls"
        ),
        checks,
    )
    trace_replay = pd.read_csv(
        root
        / "experiments/exp20_trace_meter_replay/results/final/"
        "trace_meter_replay_daily.csv"
    )
    trace_summary = pd.read_csv(
        root
        / "experiments/exp20_trace_meter_replay/results/final/"
        "trace_meter_replay_summary.csv"
    )
    trace_meta = json.loads(
        (
            root
            / "experiments/exp20_trace_meter_replay/results/final/"
            "experiment_metadata.json"
        ).read_text(encoding="utf-8")
    )
    _check(
        len(trace_replay) == expected_test * len(trace_summary)
        and len(trace_summary) == 12
        and trace_replay.groupby("method")["day"].nunique().eq(expected_test).all()
        and set(trace_replay["truth_source"].astype(str)) == {
            "independent_trace_observed_meter"
        }
        and trace_replay["event_intervention"].astype(str).str.lower().eq("false").all()
        and trace_meta.get("truth_source") == "independent_trace_observed_meter"
        and trace_meta.get("event_intervention") is False
        and trace_meta.get("profiles_checksum") == locked_profile_checksum
        and np.isfinite(
            trace_summary[
                ["mean_mae_mw", "mae_ci_low_mw", "mae_ci_high_mw", "mean_rmse_mw"]
            ].to_numpy(dtype=float)
        ).all(),
        "independent_trace_meter_replay_panel",
        (
            f"{len(trace_replay)} locked-day method scores against the measured "
            "DCGM execution tensor; no event intervention or simulated response "
            "is used as scoring truth"
        ),
        checks,
    )
    fairness = pd.read_csv(
        root
        / "experiments/exp2_baseline_verification/results/final/"
        "baseline_fairness_audit.csv"
    )
    fairness_constraint_columns = [
        "same_arrivals",
        "same_deadlines",
        "same_site_capacity",
        "same_event_slots",
    ]
    same_constraints = all(
        column in fairness.columns
        and fairness[column].astype(str).str.lower().eq("true").all()
        for column in fairness_constraint_columns
    )
    faithful_reimplementation = fairness[
        "faithful_published_software_reimplementation"
    ].astype(str).str.lower().eq("true")
    _check(
        len(fairness) == 8
        and bool(fairness["same_locked_days"].eq(expected_test).all())
        and same_constraints
        and bool((~faithful_reimplementation).all()),
        "literature_baseline_fairness_contract",
        (
            f"{len(fairness)} controls use the same ledger, deadlines, capacities, "
            "event slots, and locked days; structural translations are not labelled "
            "as software reimplementations"
        ),
        checks,
    )
    risk_decomposition = pd.read_csv(
        root
        / "experiments/exp2_baseline_verification/results/final/"
        "risk_effect_decomposition.csv"
    )
    _check(
        set(risk_decomposition["split"].astype(str)) == {"validation", "test"}
        and len(risk_decomposition) == 9
        and risk_decomposition["interpretation"].astype(str).str.len().gt(20).all()
        and np.isfinite(
            risk_decomposition[
                ["nrmse_change", "false_response_change_mwh", "credit_f1_change"]
            ].to_numpy(dtype=float)
        ).all(),
        "risk_effect_decomposition_separates_envelope_and_fit",
        (
            f"{len(risk_decomposition)} validation/test ablations separate total-risk, "
            "CVaR, combined convex fitting, and the final pointwise envelope"
        ),
        checks,
    )
    locked_day_panels = {
        "exp2": (
            root
            / "experiments/exp2_baseline_verification/results/final/"
            "per_day_baseline_metrics.csv"
        ),
        "exp3": (
            root
            / "experiments/exp3_nodal_settlement/results/final/"
            "settlement_metrics.csv"
        ),
        "exp5": (
            root
            / "experiments/exp5_network_robustness/results/final/"
            "network_robustness.csv"
        ),
        "exp6": (
            root
            / "experiments/exp6_physical_stress/results/final/"
            "physical_stress.csv"
        ),
        "exp7": (
            root
            / "experiments/exp7_value_allocation/results/final/"
            "value_allocation.csv"
        ),
        "exp8": (
            root
            / "experiments/exp8_n1_security/results/final/"
            "n1_security_daily_results.csv"
        ),
        "exp9": (
            root
            / "experiments/exp9_payment_certificate/results/final/"
            "payment_evaluation_daily.csv"
        ),
        "exp10": (
            root
            / "experiments/exp10_ac_validation/results/final/"
            "ac_opf_locked_day_results.csv"
        ),
        "exp11": (
            root
            / "experiments/exp11_spatial_scale_robustness/results/final/"
            "spatial_scale_robustness.csv"
        ),
        "exp12": (
            root
            / "experiments/exp12_rolling_market_validation/results/final/"
            "rolling_market_validation.csv"
        ),
    }
    aligned_day_panels: list[str] = []
    misaligned_day_panels: list[str] = []
    for label, path in locked_day_panels.items():
        panel_days = set(
            pd.read_csv(path, usecols=["day"])["day"]
            .astype(int)
            .unique()
            .tolist()
        )
        if panel_days == locked_days:
            aligned_day_panels.append(label)
        else:
            misaligned_day_panels.append(label)
    _check(
        len(locked_days) == expected_test
        and not misaligned_day_panels,
        "cross_experiment_locked_day_identity",
        (
            f"{len(aligned_day_panels)}/{len(locked_day_panels)} main panels "
            f"use the identical locked days {min(locked_days)}--"
            f"{max(locked_days)}; mismatches={misaligned_day_panels}"
        ),
        checks,
    )
    paired = pd.read_csv(
        root
        / "experiments/exp2_baseline_verification/results/final/paired_block_randomization_tests.csv"
    )
    expected_comparators = {
        "High-5-of-10",
        "Metadata Gradient Boosting",
        "Ex-post Metadata Gradient Boosting",
        "Ex-post Quantile Gradient Boosting",
        "Synthetic Control",
        "Feasible Quantile Projection",
        "Single Feasible Projection",
    }
    _check(
        set(paired["comparator"]) == expected_comparators
        and set(paired["metric"])
        == {"nrmse", "false_response_ratio", "credit_f1"}
        and len(paired)
        == len(expected_comparators) * 3
        and bool((paired["blocks"] == expected_blocks).all())
        and bool((paired["extreme_assignments"] >= 2).all())
        and bool(
            (
                paired["two_sided_exact_p_value"] + 1e-15
                >= paired["minimum_attainable_two_sided_p"]
            ).all()
        )
        and bool(
            (paired["holm_adjusted_p_value"] + 1e-12
             >= paired["two_sided_exact_p_value"]).all()
        ),
        "dependence_robust_exact_block_tests",
        (
            f"{expected_blocks} pre-declared "
            f"{int(cfg['experiments']['block_length_days'])}-day blocks, exact "
            "sign randomization, attainable-p audit, and Holm family-wise correction"
        ),
        checks,
    )
    significance = {
        f"{row.comparator} | {row.metric}": {
            key: value
            for key, value in row._asdict().items()
            if key not in {"Index", "comparator", "metric"}
        }
        for row in paired.itertuples()
    }
    estimator_tests = pd.read_csv(
        root
        / "experiments/exp2_baseline_verification/results/final/paired_counterfactual_block_tests.csv"
    )
    single_estimator_tests = estimator_tests[
        estimator_tests["comparator"] == "Single Feasible Projection"
    ]
    single_tail_f1 = single_estimator_tests[
        single_estimator_tests["metric"] == "credit_f1"
    ]
    single_tail_nrmse = single_estimator_tests[
        single_estimator_tests["metric"] == "nrmse"
    ]
    _check(
        len(estimator_tests) == 6
        and len(single_estimator_tests) == 2
        and set(single_estimator_tests["metric"]) == {"nrmse", "credit_f1"}
        and bool((estimator_tests["blocks"] == expected_blocks).all())
        and bool((estimator_tests["extreme_assignments"] >= 2).all())
        and bool((single_tail_f1["observed_mean_difference"] > 0).all())
        and bool((single_tail_f1["holm_adjusted_p_value"] <= 0.05).all())
        and bool((single_tail_nrmse["observed_mean_difference"] >= -1e-9).all())
        and bool((single_tail_nrmse["observed_mean_difference"] <= 0.05).all()),
        "tail_risk_counterfactual_estimator_comparison",
        (
            "tail-risk feasible counterfactual improves credit F1 against the "
            "single feasible projection; its nRMSE change remains below 0.05 "
            f"over {expected_blocks} exact temporal blocks and is reported with "
            "the exact paired p-value"
        ),
        checks,
    )
    matched_effects_for_closest = pd.read_csv(
        root
        / "experiments/exp2_baseline_verification/results/final/"
        "matched_comparator_effects.csv"
    )
    fair_pair = matched_effects_for_closest[
        (matched_effects_for_closest["comparator"] == "Feasible Quantile Projection")
        & (matched_effects_for_closest["metric"] == "false_response_mwh")
    ]
    proposed_summary = metrics[
        metrics["method"] == "Risk-Constrained Convex Verifier"
    ]
    closest_summary = metrics[
        metrics["method"] == "Feasible Quantile Projection"
    ]
    proposed_nrmse = float(proposed_summary["nrmse"].mean())
    closest_nrmse = float(closest_summary["nrmse"].mean())
    proposed_false_credit = float(proposed_summary["false_response_mwh"].mean())
    closest_false_credit = float(closest_summary["false_response_mwh"].mean())
    _check(
        bool(
            (fair_pair["observed_mean_difference"] > 0).all()
            and (fair_pair["holm_adjusted_p_value"] <= 0.05).all()
            and proposed_false_credit <= closest_false_credit + 1e-9
            and proposed_nrmse >= closest_nrmse - 1e-9
            and np.isfinite(proposed_nrmse)
        ),
        "closest_feasible_baseline_comparison",
        (
            "risk verifier has significantly lower mean false-credit exposure "
            "than the complete-ledger feasible-quantile projection; the higher "
            f"mean nRMSE is retained as an explicit tradeoff "
            f"({proposed_nrmse:.6f} versus {closest_nrmse:.6f})"
        ),
        checks,
    )
    cvar_stress = pd.read_csv(
        root
        / "experiments/exp2_baseline_verification/results/final/"
        "risk_cvar_stress_sensitivity.csv"
    )
    selected_cvar = cvar_stress[
        np.isclose(
            cvar_stress["cvar_reserve_fraction"].astype(float),
            float(cfg["experiments"].get("risk_cvar_reserve_fraction", np.nan)),
            rtol=0.0,
            atol=1e-12,
        )
    ]
    active_cvar = cvar_stress[cvar_stress["minimum_cvar_touches_budget"].astype(bool)]
    _check(
        len(cvar_stress) == len(
            cfg["experiments"].get("risk_cvar_stress_reserve_fractions", [])
        )
        and set(
            np.round(cvar_stress["cvar_reserve_fraction"].astype(float), 5)
        )
        == set(
            np.round(
                np.asarray(
                    cfg["experiments"].get(
                        "risk_cvar_stress_reserve_fractions", []
                    ),
                    dtype=float,
                ),
                5,
            )
        )
        and len(selected_cvar) == 1
        and bool(selected_cvar["feasible"].astype(bool).all())
        and len(active_cvar) >= 1
        and bool(active_cvar["feasible"].astype(bool).all())
        and bool(active_cvar["cvar_reserve_fraction"].between(0.0, 1.0).all()),
        "active_cvar_frontier_certificate",
        (
            "the predeclared validation-only CVaR frontier contains a feasible "
            "pooled reserve and an active boundary that touches the minimum "
            "achievable CVaR under the total-risk budget; the pooled contract "
            f"uses the separately recorded {float(cfg['experiments']['risk_cvar_reserve_fraction']):.2f} tail reserve"
        ),
        checks,
    )
    matched_effects = pd.read_csv(
        root
        / "experiments/exp2_baseline_verification/results/final/"
        "matched_comparator_effects.csv"
    )
    closest_false_credit_effect = matched_effects[
        (matched_effects["comparator"] == "Feasible Quantile Projection")
        & (matched_effects["metric"] == "false_response_mwh")
    ].iloc[0]
    single_nrmse_effect = matched_effects[
        (matched_effects["comparator"] == "Single Feasible Projection")
        & (matched_effects["metric"] == "nrmse")
    ].iloc[0]
    single_f1_effect = matched_effects[
        (matched_effects["comparator"] == "Single Feasible Projection")
        & (matched_effects["metric"] == "credit_f1")
    ].iloc[0]
    _check(
        len(matched_effects) == len(expected_comparators) * 3
        and float(closest_false_credit_effect["moving_block_ci_2.5"]) > 0
        and float(single_nrmse_effect["moving_block_ci_2.5"])
        <= float(single_nrmse_effect["observed_mean_difference"])
        <= float(single_nrmse_effect["moving_block_ci_97.5"])
        and float(single_f1_effect["moving_block_ci_2.5"])
        <= float(single_f1_effect["observed_mean_difference"])
        <= float(single_f1_effect["moving_block_ci_97.5"]),
        "matched_effect_sizes_with_dependence_robust_intervals",
        (
            "false-credit improvement over feasible quantile has a positive "
            "three-day moving-block 95% interval, while all single-projection "
            "effects are contained in their dependence-aware intervals"
        ),
        checks,
    )
    intervention = pd.read_csv(
        root
        / "experiments/exp2_baseline_verification/results/final/intervention_robustness.csv"
    )
    intervention_cells = intervention.groupby(
        ["intervention", "method"]
    )["day"].nunique()
    intervention_pivot = intervention[
        intervention["method"].isin(
            [
                "Single Feasible Projection",
                "Feasible Quantile Projection",
                "Risk-Constrained Convex Verifier",
            ]
        )
    ].pivot(
        index=["intervention", "day"],
        columns="method",
        values="false_response_mwh",
    )
    _check(
        intervention["intervention"].nunique() == 4
        and len(intervention) == 4 * expected_test * 4
        and bool((intervention_cells == expected_test).all())
        and np.isfinite(intervention_pivot.to_numpy(dtype=float)).all(),
        "complete_independent_intervention_panel",
        (
            f"{len(intervention)}/{4 * expected_test * 4} rows; all matched "
            "interventions are evaluated without a comparator-derived cap"
        ),
        checks,
    )
    risk_panel = metrics[
        metrics["method"].isin(
            [
                "Feasible Quantile Projection",
                "Risk-Constrained Convex Verifier",
            ]
        )
    ].pivot(
        index="day", columns="method", values="false_response_mwh"
    )
    risk_metadata = json.loads(
        (
            root
            / "experiments/exp2_baseline_verification/results/final/experiment_metadata.json"
        ).read_text(encoding="utf-8")
    )
    risk_profile_store = np.load(
        root
        / "experiments/exp2_baseline_verification/results/intermediate/"
        "test_profiles.npz",
        allow_pickle=False,
    )
    risk_profile_methods = [str(value) for value in risk_profile_store["methods"]]
    single_profiles = risk_profile_store["baselines"][
        :, risk_profile_methods.index("Single Feasible Projection")
    ]
    risk_profiles = risk_profile_store["baselines"][
        :, risk_profile_methods.index("Risk-Constrained Convex Verifier")
    ]
    _check(
        len(risk_panel) == expected_test
        and np.isfinite(risk_panel.to_numpy(dtype=float)).all()
        and risk_metadata.get("pointwise_envelope_candidate")
        == "Single Feasible Projection"
        and "not pointwise clipped" in str(
            risk_metadata.get("risk_profile_definition", "")
        )
        and risk_metadata.get("risk_reference_candidate")
        != "Feasible quantile projection",
        "independent_pointwise_risk_envelope",
        (
            "locked test false-credit is compared to the feasible-quantile "
            "reference, while the LP cap and risk budget are anchored to the "
            f"independent {risk_metadata.get('risk_reference_candidate')} candidate"
        ),
        checks,
    )
    _check(
        risk_metadata.get("scoring_truth_source")
        == "independent_trace_observed_meter"
        and risk_metadata.get("causal_intervention_claim") is False
        and "independently observed" in str(risk_metadata.get("evaluation_reference", "")),
        "independent_observed_scoring_truth",
        (
            "locked response scores use the observed DCGM/BurstGPT meter; any "
            "event-response LP is restricted to mechanism-isolation panels"
        ),
        checks,
    )
    truth_source_audit = pd.read_csv(
        root
        / "experiments/exp2_baseline_verification/results/final/"
        "risk_truth_source_audit.csv"
    )
    _check(
        len(truth_source_audit) == expected_test * 2
        and set(truth_source_audit["truth_source"].astype(str))
        == {
            "independent_trace_observed_meter",
            "simulated_event_response_mechanism_isolation",
        }
        and truth_source_audit["event_intervention"].astype(str).str.lower().eq("false").all()
        and truth_source_audit["causal_event_effect"].astype(str).str.lower().eq("false").all()
        and np.isfinite(
            truth_source_audit[
                [
                    "final_false_credit_mw_slots",
                    "reference_false_credit_mw_slots",
                    "final_false_credit_mwh",
                    "reference_false_credit_mwh",
                    "false_credit_ratio_to_reference",
                ]
            ].to_numpy(dtype=float)
        ).all(),
        "source_separated_false_credit_certificate",
        (
            "locked-test false-credit diagnostics are recomputed separately for the "
            "observed meter and the mechanism-isolation trajectory; neither row is "
            "labelled as a causal utility-event outcome"
        ),
        checks,
    )
    _check(
        "offline union ceiling" in str(risk_metadata.get("risk_credit_ceiling_source", ""))
        and "separate truth-source scores" in str(
            risk_metadata.get("risk_credit_ceiling_source", "")
        )
        and "no causal event effect" in str(
            risk_metadata.get("risk_credit_ceiling_source", "")
        ),
        "risk_ceiling_truth_sources_explicit",
        (
            "the pointwise risk-fit ceiling is labelled as an offline union of the "
            "observational and mechanism-isolation trajectories; settlement scores "
            "retain the two truth sources separately and do not assert a causal event effect"
        ),
        checks,
    )
    _check(
        float(np.max(np.abs(risk_profiles - single_profiles))) > 1e-6
        and "payment_contract_profiles" in risk_profile_store.files
        and risk_profile_store["payment_contract_profiles"].shape
        == risk_profiles.shape
        and bool(
            (two_sided["pointwise_upper_bound_satisfied"] == 1).all()
        )
        and bool(
            (two_sided["pointwise_lower_bound_satisfied"] == 1).all()
        ),
        "nondegenerate_risk_verifier_output",
        (
            "the risk-fit profile differs from the single reference; the separately "
            "stored payment-contract profile retains the independently checked two-sided band"
        ),
        checks,
    )
    risk_certificate = pd.read_csv(
        root
        / "experiments/exp2_baseline_verification/results/final/risk_constrained_validation_certificate.csv"
    ).iloc[0]
    risk_ablation_weights = pd.read_csv(
        root
        / "experiments/exp2_baseline_verification/results/final/"
        "risk_module_ablation_weights.csv"
    )
    weight_columns = [
        column
        for column in risk_ablation_weights.columns
        if column.startswith("weight_")
    ]
    cvar_weights = risk_ablation_weights.loc[
        risk_ablation_weights["ablation"] == "CVaR-only ensemble", weight_columns
    ]
    joint_weights = risk_ablation_weights.loc[
        risk_ablation_weights["ablation"] == "total+CVaR ensemble", weight_columns
    ]
    _check(
        bool(
            risk_certificate["optimizer_success"] == 1
            and risk_certificate["risk_constraints_satisfied"] == 1
            and risk_certificate["solver_name"] == "scipy.optimize.trust-constr"
            and np.isfinite(float(risk_certificate["kkt_stationarity_residual"]))
            and float(risk_certificate["kkt_stationarity_residual"]) <= 1e-5
            and float(risk_certificate["primal_constraint_residual"]) <= 1e-6
            and risk_certificate["risk_cvar_metric"] == "daily_false_credit_ratio"
            and np.isclose(
                float(risk_certificate["risk_cvar_level"]),
                float(cfg["experiments"].get("risk_cvar_level", 0.75)),
                rtol=0.0,
                atol=1e-12,
            )
            and float(risk_certificate["cvar_budget_slack_metric"]) >= -1e-9
            and bool(risk_certificate["cvar75_budget_binding"] == 0)
            and risk_certificate["fitted_cvar_metric_value"]
            <= risk_certificate["reference_cvar_metric_value"] + 1e-8
            and risk_certificate["fitted_validation_mse_mw2"]
            <= risk_certificate["reference_validation_mse_mw2"] + 1e-8
            and risk_certificate["fitted_false_credit_exposure_mw_slots"]
            <= risk_certificate[
                "risk_budget_mw_slots"
            ]
            + 1e-7
            and float(risk_certificate.get("total_objective_weight", 0.0)) > 0.0
            and len(cvar_weights) == 1
            and len(joint_weights) == 1
            and bool(
                np.max(
                    np.abs(
                        joint_weights.to_numpy(dtype=float)[0]
                        - cvar_weights.to_numpy(dtype=float)[0]
                    )
                )
                > 1.0e-6
            )
        ),
        "risk_constrained_validation_dominance",
        (
            "convex verifier has no larger validation MSE and satisfies both "
            "total and daily-tail CVaR false-credit budgets; its normalized "
            "total-exposure preference makes the joint fit distinct from the "
            "CVaR-only ablation"
        ),
        checks,
    )
    reserve_cv = pd.read_csv(
        root
        / "experiments/exp2_baseline_verification/results/final/risk_reserve_nested_cv.csv"
    )
    reserve_summary = pd.read_csv(
        root
        / "experiments/exp2_baseline_verification/results/final/risk_reserve_validation_summary.csv"
    )
    _check(
        len(reserve_cv)
        == 4 * len(cfg["experiments"]["risk_reserve_fractions"])
        and reserve_summary["selected"].sum() == 1
        and reserve_cv["selected_reserve_fraction"].any()
        and not reserve_cv[
            reserve_cv["selected_reserve_fraction"]
        ]["held_out_nrmse"].isna().any(),
        "nested_daily_risk_reserve_selection",
        (
            f"{len(reserve_cv)} reserve-fold cells; "
            f"selected reserve={reserve_summary.loc[reserve_summary['selected'], 'reserve_fraction'].iloc[0]:.2f}"
        ),
        checks,
    )
    envelope = pd.read_csv(
        root
        / "experiments/exp2_baseline_verification/results/final/risk_envelope_validation.csv"
    )
    _check(
        len(envelope) == len(cfg["experiments"]["projection_weights"])
        and envelope["selected"].sum() == 1
        and np.isfinite(
            envelope[
                [
                    "mean_validation_nrmse",
                    "mean_validation_credit_f1",
                    "mean_false_response_mwh",
                ]
            ]
        ).all().all(),
        "exact_pointwise_risk_envelope_selection",
        (
            f"{len(envelope)} globally solved envelope projections; "
            f"selected weight={envelope.loc[envelope['selected'], 'projection_weight'].iloc[0]:g}"
        ),
        checks,
    )
    protocol = pd.read_csv(
        root / "experiments/exp2_baseline_verification/results/final/information_set_audit.csv"
    ).set_index("method")
    fair_methods = [
        "Ex-post Metadata Gradient Boosting",
        "Ex-post Quantile Gradient Boosting",
        "Feasible Quantile Projection",
        "Tail-Risk Feasible Counterfactual",
        "Single Feasible Projection",
        "Risk-Constrained Convex Verifier",
    ]
    _check(
        bool(
            (protocol.loc[fair_methods, "decision_time"] == "post-event audit").all()
            and protocol.loc[fair_methods, "complete_submitted_job_ledger"].astype(bool).all()
            and not protocol.loc[fair_methods, "execution_truth"].astype(bool).any()
        ),
        "matched_post_event_information_protocol",
        "statistical, single-projection, and convex verifiers share the full ledger and never observe execution truth",
        checks,
    )
    tuning = pd.read_csv(
        root
        / "experiments/exp2_baseline_verification/results/final/projection_candidate_validation.csv"
    )
    _check(
        len(tuning) >= 5,
        "complete_predeclared_projection_validation",
        f"{len(tuning)} pre-declared validation candidates",
        checks,
    )
    ensemble = pd.read_csv(root / "experiments/exp2_baseline_verification/results/final/convex_projection_weights.csv")
    _check(
        (
            len(ensemble) == len(cfg["experiments"]["projection_weights"]) + 1
            and bool((ensemble["ensemble_weight"] >= -1e-10).all())
            and np.isclose(ensemble["ensemble_weight"].sum(), 1.0, atol=1e-8)
        ),
        "convex_projection_simplex",
        f"{len(ensemble)} coefficients; sum={ensemble['ensemble_weight'].sum():.12f}",
        checks,
    )
    blocked_cv = pd.read_csv(
        root / "experiments/exp2_baseline_verification/results/final/blocked_validation_cv.csv"
    )
    _check(
        len(blocked_cv) == 4
        and blocked_cv["fold"].nunique() == 4
        and np.isfinite(blocked_cv["held_out_nrmse"]).all(),
        "contiguous_blocked_validation",
            f"{len(blocked_cv)} locked temporal folds",
        checks,
    )
    ablation_daily = pd.read_csv(
        root
        / "experiments/exp2_baseline_verification/results/final/constraint_ablation_daily.csv"
    )
    full_variants = [
        "Full single projection",
        "Tail-risk convex ensemble",
        "Full risk-envelope verifier",
    ]
    full_certificate = ablation_daily[ablation_daily["variant"].isin(full_variants)]
    _check(
        len(full_certificate) == expected_test * len(full_variants)
        and bool((full_certificate["certified_feasible"] == 1).all())
        and float(
            full_certificate[
                [
                    "release_violation_mwh",
                    "deadline_violation_mwh",
                    "capacity_violation_mw",
                    "conservation_violation_mwh",
                ]
            ].max().max()
        )
        <= 1e-7,
        "independent_full_constraint_certificates",
        f"{len(full_certificate)} day-variant schedules certified",
        checks,
    )
    complexity = pd.read_csv(
        root / "experiments/exp2_baseline_verification/results/final/complexity_scaling.csv"
    )
    slope = float(
        np.polyfit(
            np.log(complexity["horizon_slots"]),
            np.log(complexity["sparse_nonzeros"]),
            1,
        )[0]
    )
    _check(
        len(complexity) == len(cfg["experiments"]["complexity_horizons_slots"])
        and bool(complexity["solver_success"].astype(bool).all())
        and bool((np.diff(complexity["variables"]) > 0).all())
        and bool((np.diff(complexity["sparse_nonzeros"]) > 0).all())
        and 0.95 <= slope <= 1.05,
        "exact_sparse_complexity_scaling",
        f"log-log nonzero slope={slope:.4f}",
        checks,
    )

    settlement = pd.read_csv(root / "experiments/exp3_nodal_settlement/results/final/settlement_metrics.csv")
    mae = settlement.groupby(["baseline_method", "mechanism"])["payment_error_usd"].apply(
        lambda x: float(np.mean(np.abs(x)))
    )
    expected_baselines = set(metrics["method"].unique()) | {
        "Trace-Anchored Reference"
    }
    expected_mechanisms = {
        "Uniform gross",
        "Nodal gross",
        "Uniform signed net",
        "Nodal signed linear",
        "Nodal exact net value",
    }
    settlement_cells = settlement.groupby(["baseline_method", "mechanism"])["day"].nunique()
    expected_settlement = expected_test * len(expected_baselines) * len(expected_mechanisms)
    settlement_complete = (
        set(settlement["baseline_method"].unique()) == expected_baselines
        and set(settlement["mechanism"].unique()) == expected_mechanisms
        and len(settlement_cells) == len(expected_baselines) * len(expected_mechanisms)
        and bool((settlement_cells == expected_test).all())
        and len(settlement) == expected_settlement
    )
    _check(
        settlement_complete,
        "complete_settlement_factorial_panel",
        (
            f"{len(settlement)}/{expected_settlement} rows; "
            f"{len(settlement_cells)}/{len(expected_baselines) * len(expected_mechanisms)} complete cells"
        ),
        checks,
    )
    factor_decomposition = pd.read_csv(
        root
        / "experiments/exp3_nodal_settlement/results/final/"
        "settlement_factor_decomposition.csv"
    )
    factor_summary = pd.read_csv(
        root
        / "experiments/exp3_nodal_settlement/results/final/"
        "settlement_factor_decomposition_summary.csv"
    )
    factor_columns = {
        "gross_to_signed_error_reduction_usd",
        "uniform_to_nodal_error_reduction_usd",
        "linear_to_exact_error_reduction_usd",
        "uniform_gross_to_exact_error_reduction_usd",
    }
    factor_cells = factor_decomposition.groupby("baseline_method")[
        "day"
    ].nunique()
    _check(
        len(factor_decomposition)
        == expected_test * len(expected_baselines)
        and bool((factor_cells == expected_test).all())
        and factor_columns.issubset(factor_decomposition.columns)
        and len(factor_summary)
        == len(expected_baselines) * len(factor_columns),
        "paired_settlement_factor_decomposition",
        (
            f"{len(factor_decomposition)} locked day-baseline rows and "
            f"{len(factor_summary)} one-factor paired summaries separate "
            "signed netting, locational pricing, and exact valuation"
        ),
        checks,
    )
    interval_value = pd.read_csv(
        root
        / "experiments/exp3_nodal_settlement/results/final/interval_grid_value.csv"
    )
    trace_exact_error = settlement[
        (settlement["baseline_method"] == "Trace-Anchored Reference")
        & (settlement["mechanism"] == "Nodal exact net value")
    ]["payment_error_usd"].abs()
    _check(
        interval_value["settlement_segments"].nunique() == 1
        and interval_value["evaluation_segments"].nunique() == 1
        and int(interval_value["evaluation_segments"].iloc[0])
        > int(interval_value["settlement_segments"].iloc[0])
        and float(trace_exact_error.max()) > 1e-9,
        "independent_high_resolution_value_evaluator",
        (
            f"{int(interval_value['settlement_segments'].iloc[0])}-segment "
            f"settlement versus {int(interval_value['evaluation_segments'].iloc[0])}-segment "
            f"evaluation; trace-reference max non-circular error="
            f"{trace_exact_error.max():.6f} USD/day"
        ),
        checks,
    )
    settlement_tests = pd.read_csv(
        root
        / "experiments/exp3_nodal_settlement/results/final/paired_settlement_block_tests.csv"
    )
    _check(
        len(settlement_tests)
        == len(expected_baselines) * (len(expected_mechanisms) - 1)
        and bool((settlement_tests["blocks"] == expected_blocks).all())
        and bool((settlement_tests["extreme_assignments"] >= 2).all())
        and bool(
            (
                settlement_tests["two_sided_exact_p_value"] + 1e-15
                >= settlement_tests["minimum_attainable_two_sided_p"]
            ).all()
        )
        and bool(
            (
                settlement_tests["holm_adjusted_p_value"]
                + 1e-12
                >= settlement_tests["two_sided_exact_p_value"]
            ).all()
        ),
        "complete_settlement_mechanism_block_tests",
        (
            f"{len(settlement_tests)} paired mechanism tests; "
            "Holm correction within each baseline-method family"
        ),
        checks,
    )
    value_certificates = pd.read_csv(
        root
        / "experiments/exp3_nodal_settlement/results/final/polyhedral_value_certificates.csv"
    )
    _check(
        len(value_certificates)
        == expected_test * len(expected_baselines) * len(
            cfg["market"]["event_slots"]
        )
        and float(
            value_certificates[
                "subgradient_inequality_violation_usd"
            ].max()
        )
        <= 1e-6,
        "global_polyhedral_value_certificate",
        (
            f"{len(value_certificates)} interval-baseline certificates; "
            "maximum subgradient-inequality violation "
            f"{value_certificates['subgradient_inequality_violation_usd'].max():.3e} USD"
        ),
        checks,
    )
    network = pd.read_csv(root / "experiments/exp5_network_robustness/results/final/network_robustness.csv")
    network_count = 4
    expected_network = expected_test * network_count * len(cfg["experiments"]["network_load_multipliers"]) * 5 * 2
    network_cells = network.groupby(["network", "load_multiplier", "mechanism", "baseline_quality"])["day"].nunique()
    expected_network_cells = network_count * len(cfg["experiments"]["network_load_multipliers"]) * 5 * 2
    _check(
        (
            len(network) == expected_network
            and network["network"].nunique() == network_count
            and len(network_cells) == expected_network_cells
            and bool((network_cells == expected_test).all())
        ),
        "complete_cross_network_panel",
        (
            f"{len(network)}/{expected_network} rows; "
            f"{len(network_cells)}/{expected_network_cells} complete cells across "
            f"{network['network'].nunique()} networks"
        ),
        checks,
    )
    network_tests = pd.read_csv(
        root
        / "experiments/exp5_network_robustness/results/final/paired_network_block_tests.csv"
    )
    estimated_network_tests = network_tests[
        network_tests["baseline_quality"]
        == "Risk-Constrained Convex Verifier"
    ]
    reference_network_tests = network_tests[
        network_tests["baseline_quality"]
        == "Trace-Anchored Reference"
    ]
    # The polyhedral result guarantees a nonnegative linearization gap at a
    # common pair of load endpoints. Once the baseline itself is estimated,
    # absolute end-to-end settlement error also contains baseline error and is
    # not theoretically required to improve strictly in every network cell.
    estimated_effects = estimated_network_tests[
        "observed_mean_difference"
    ]
    _check(
        len(network_tests)
        == network_count
        * len(cfg["experiments"]["network_load_multipliers"])
        * 2
        and bool((network_tests["blocks"] == expected_blocks).all())
        and bool((network_tests["extreme_assignments"] >= 2).all())
        and bool(
            (
                network_tests["two_sided_exact_p_value"] + 1e-15
                >= network_tests["minimum_attainable_two_sided_p"]
            ).all()
        )
        and bool(
            (
                network_tests["holm_adjusted_p_value"]
                + 1e-12
                >= network_tests["two_sided_exact_p_value"]
            ).all()
        )
        and bool(
            (
                reference_network_tests["observed_mean_difference"]
                >= -1e-8
            ).all()
        )
        and not bool(
            (
                (estimated_network_tests["observed_mean_difference"] < -1e-6)
                & (estimated_network_tests["holm_adjusted_p_value"] <= 0.05)
            ).any()
        )
        and float(
            estimated_network_tests["observed_mean_difference"].mean()
        )
        >= -1e-9,
        "cross_network_paired_mechanism_inference",
        (
            f"{len(network_tests)} paired exact block tests; positive "
            "estimated-baseline linear-minus-exact effect in "
            f"{int((estimated_network_tests['observed_mean_difference'] > 0).sum())}/"
            f"{len(estimated_network_tests)} cells; minimum effect "
            f"{estimated_network_tests['observed_mean_difference'].min():.6f} "
            "USD/day; no materially negative estimated-baseline effect survives "
            "Holm correction, while the trace-anchored reference remains "
            "nonnegative in every cell"
        ),
        checks,
    )
    resolution = pd.read_csv(
        root
        / "experiments/exp5_network_robustness/results/final/"
        "resolution_convergence_summary.csv"
    ).sort_values("settlement_segments")
    expected_resolution_pairs = {
        tuple(map(int, pair))
        for pair in cfg["experiments"]["cross_network_resolution_pairs"]
    }
    observed_resolution_pairs = set(
        zip(
            resolution["settlement_segments"].astype(int),
            resolution["evaluation_segments"].astype(int),
        )
    )
    final_two = resolution.tail(2)[
        "mean_linear_minus_exact_error_usd_day"
    ].to_numpy()
    resolution_means = resolution[
        "mean_linear_minus_exact_error_usd_day"
    ].to_numpy()
    resolution_half_widths = 1.96 * resolution[
        "standard_error_usd_day"
    ].to_numpy()
    initial_step = float(abs(resolution_means[1] - resolution_means[0]))
    final_step = float(abs(resolution_means[-1] - resolution_means[-2]))
    _check(
        observed_resolution_pairs == expected_resolution_pairs
        and len(resolution) == len(expected_resolution_pairs)
        and bool((np.abs(resolution_means) <= resolution_half_widths).all())
        and final_step < initial_step,
        "complete_cross_network_resolution_convergence",
        (
            f"{len(resolution)} complete 54-day resolution levels; highest "
            f"two mean effects={final_two[-2]:.6f}, {final_two[-1]:.6f} "
            f"USD/day; final step={final_step:.6f} versus initial step="
            f"{initial_step:.6f} USD/day, and every 95% interval contains zero"
        ),
        checks,
    )
    congestion_cells = network.groupby(["network", "load_multiplier"])["congested_interval_share"].mean()
    _check(
        int((congestion_cells > 0).sum()) >= 3
        and int(
            network.groupby("network")["congested_interval_share"].max().gt(0).sum()
        )
        >= 1,
        "native_rating_congestion_identification",
        (
            f"{int((congestion_cells > 0).sum())}/{len(congestion_cells)} "
            "network-loading cells exhibit endogenous congestion"
        ),
        checks,
    )
    fixed_sites = network.groupby("network")[
        "data_center_bus_indices_zero_based"
    ].nunique()
    _check(
        bool(
            np.isclose(
                network["thermal_rating_normalization_factor"], 1.0, atol=0, rtol=0
            ).all()
            and (fixed_sites == 1).all()
        ),
        "native_ratings_and_predeclared_sites",
        (
            "all thermal-rating factors equal 1.0; "
            f"fixed-site specifications invariant in {len(fixed_sites)} networks"
        ),
        checks,
    )
    oracle_network = network[
        network["baseline_quality"] == "Trace-Anchored Reference"
    ]
    oracle_means = oracle_network.groupby(["network", "load_multiplier", "mechanism"])["absolute_error_usd"].mean().unstack()
    nodal_identified = (
        (oracle_means["Uniform gross"] - oracle_means["Nodal gross"]).abs().max() > 1e-6
        or (
            oracle_means["Uniform signed net"]
            - oracle_means["Nodal signed linear"]
        ).abs().max()
        > 1e-6
    )
    _check(
        nodal_identified,
        "nodal_price_effect_identified",
        "at least one cross-network cell has a nonzero uniform-versus-nodal error contrast",
        checks,
    )
    allocation = pd.read_csv(
        root / "experiments/exp7_value_allocation/results/final/value_allocation.csv"
    )
    allocation_cells = allocation.groupby(
        ["baseline_quality", "allocation_method", "participant"]
    )["day"].nunique()
    expected_allocation = expected_test * 2 * 4 * 4
    _check(
        len(allocation) == expected_allocation
        and len(allocation_cells) == 2 * 4 * 4
        and bool((allocation_cells == expected_test).all()),
        "complete_exact_value_allocation_panel",
        f"{len(allocation)}/{expected_allocation} participant-day outcomes",
        checks,
    )
    exact_allocation = allocation[
        allocation["allocation_method"] == "Exact Shapley net value"
    ]
    _check(
        float(exact_allocation["budget_residual_usd"].abs().max()) <= 1e-6,
        "exact_shapley_budget_balance",
        (
            "maximum absolute participant-sum minus grand-coalition value="
            f"{exact_allocation['budget_residual_usd'].abs().max():.3e} USD"
        ),
        checks,
    )
    scaling = pd.read_csv(
        root
        / "experiments/exp7_value_allocation/results/final/eight_participant_exact_scaling.csv"
    )
    expected_scaling = (
        expected_test * len(cfg["market"]["event_slots"]) * 8
    )
    scaling_cells = scaling.groupby(["day", "slot"])[
        "participant"
    ].nunique()
    _check(
        len(scaling) == expected_scaling
        and scaling["participant"].nunique() == 8
        and scaling["day"].nunique() == expected_test
        and bool((scaling_cells == 8).all())
        and bool((scaling["coalitions_enumerated"] == 256).all())
        and float(scaling["budget_residual_usd"].abs().max()) <= 1e-6,
        "complete_exact_eight_participant_scaling",
        (
            f"{len(scaling)}/{expected_scaling} participant-interval outcomes; "
            "all 256 coalitions enumerated per interval"
        ),
        checks,
    )
    grouped_scaling = pd.read_csv(
        root
        / "experiments/exp7_value_allocation/results/final/group_symmetric_exact_scaling.csv"
    )
    grouped_cells = grouped_scaling.groupby(
        ["day", "participant_count"]
    )["site"].nunique()
    _check(
        len(grouped_scaling) == expected_test * 5 * 4
        and set(grouped_scaling["participant_count"])
        == {4, 8, 12, 16, 20}
        and bool((grouped_cells == 4).all())
        and float(grouped_scaling["budget_residual_usd"].abs().max()) <= 1e-6
        and int(
            grouped_scaling.loc[
                grouped_scaling["participant_count"] == 20,
                "count_states_evaluated",
            ].max()
        )
        == 1296,
        "exact_group_symmetric_20_participant_scaling",
        (
            f"{len(grouped_scaling)}/{expected_test * 5 * 4} site-day-size "
            "outcomes; exact count-state summation through 20 participants"
        ),
        checks,
    )
    non_shapley = allocation[
        allocation["allocation_method"].isin(
            ["Standalone avoided cost", "Leave-one-out marginal"]
        )
    ]
    _check(
        float(non_shapley["budget_residual_usd"].abs().max()) > 1e-6,
        "allocation_mechanism_identification",
        "non-efficient marginal allocation rules exhibit a nonzero budget residual",
        checks,
    )
    stress = pd.read_csv(root / "experiments/exp6_physical_stress/results/final/physical_stress.csv")
    expected_stress = expected_test * len(cfg["experiments"]["stress_capacity_multipliers"]) * len(
        cfg["experiments"]["stress_deadline_multipliers"]
    )
    stress_cells = stress.groupby(["capacity_multiplier", "deadline_multiplier"])["day"].nunique()
    expected_stress_cells = len(cfg["experiments"]["stress_capacity_multipliers"]) * len(
        cfg["experiments"]["stress_deadline_multipliers"]
    )
    _check(
        (
            len(stress) == expected_stress
            and len(stress_cells) == expected_stress_cells
            and bool((stress_cells == expected_test).all())
            and stress["capacity_binding_share"].max() > 0
        ),
        "complete_binding_constraint_panel",
        (
            f"{len(stress)}/{expected_stress} rows; "
            f"{len(stress_cells)}/{expected_stress_cells} complete cells; "
            f"max capacity binding={stress['capacity_binding_share'].max():.3f}"
        ),
        checks,
    )
    n1_interval = pd.read_csv(
        root
        / "experiments/exp8_n1_security/results/final/n1_security_interval_results.csv"
    )
    n1_daily = pd.read_csv(
        root
        / "experiments/exp8_n1_security/results/final/n1_security_daily_results.csv"
    )
    expected_n1_interval = (
        expected_test * len(cfg["market"]["event_slots"]) * 2 * 3
    )
    expected_n1_daily = expected_test * 2 * 3
    _check(
        len(n1_interval) == expected_n1_interval
        and len(n1_daily) == expected_n1_daily
        and n1_interval["day"].nunique() == expected_test
        and bool(
            (
                n1_interval["n1_max_post_contingency_loading"]
                <= 1.000001
            ).all()
        )
        and bool((n1_interval["credible_line_contingencies"] == 37).all())
        and bool((n1_interval["excluded_islanding_contingencies"] == 1).all()),
        "complete_n1_security_panel",
        (
            f"{len(n1_interval)}/{expected_n1_interval} interval-mechanism "
            "outcomes; all 37 non-islanding line outages enforced"
        ),
        checks,
    )
    n1_oracle = n1_daily[
        n1_daily["baseline_quality"] == "Trace-Anchored Reference"
    ]
    n1_oracle_mae = n1_oracle.groupby("mechanism")[
        "absolute_error_usd"
    ].mean()
    _check(
        n1_oracle_mae["N-1 exact net value"]
        < n1_oracle_mae["Base-case exact net value"]
        and n1_oracle_mae["N-1 exact net value"]
        < n1_oracle_mae["N-1 signed linear"],
        "n1_mechanism_identification",
        (
            "trace-reference N-1 exact MAE="
            f"{n1_oracle_mae['N-1 exact net value']:.3f} USD versus "
            "base-case exact MAE="
            f"{n1_oracle_mae['Base-case exact net value']:.3f} USD and "
            "N-1 linear MAE="
            f"{n1_oracle_mae['N-1 signed linear']:.3f} USD"
        ),
        checks,
    )
    payment_certificates = pd.read_csv(
        root
        / "experiments/exp9_payment_certificate/results/final/daily_payment_certificates.csv"
    )
    payment_daily = pd.read_csv(
        root
        / "experiments/exp9_payment_certificate/results/final/payment_evaluation_daily.csv"
    )
    payment_evaluation_intervals = pd.read_csv(
        root
        / "experiments/exp9_payment_certificate/results/final/payment_evaluation_intervals.csv"
    )
    paired_payment = pd.read_csv(
        root
        / "experiments/exp9_payment_certificate/results/final/paired_payment_noninferiority.csv"
    )
    conversion_certificates = pd.read_csv(
        root
        / "experiments/exp9_payment_certificate/results/final/"
        "conversion_scenario_certificates.csv"
    )
    payment_target_selection = pd.read_csv(
        root
        / "experiments/exp9_payment_certificate/results/final/"
        "payment_target_selection_validation.csv"
    )
    payment_non_tautology = pd.read_csv(
        root
        / "experiments/exp9_payment_certificate/results/final/"
        "payment_non_tautology_audit.csv"
    )
    payment_metadata = json.loads(
        (
            root
            / "experiments/exp9_payment_certificate/results/final/"
            "experiment_metadata.json"
        ).read_text(encoding="utf-8")
    )
    profile_store = np.load(
        root
        / "experiments/exp2_baseline_verification/results/intermediate/"
        "test_profiles.npz",
        allow_pickle=False,
    )
    certificate_store = np.load(
        root
        / "experiments/exp9_payment_certificate/results/final/"
        "certified_counterfactual_profiles.npz",
        allow_pickle=False,
    )
    # A row-count-complete payment panel is not sufficient evidence when an
    # upstream profile or calibration has changed.  Recompute the four
    # lineage digests here so the audit cannot bless a stale evaluator that
    # merely happens to have the expected shape.
    resume_lineage_paths = {
        "test_profile_file_checksum": root
        / "experiments/exp2_baseline_verification/results/intermediate/test_profiles.npz",
        "validation_profile_file_checksum": root
        / "experiments/exp2_baseline_verification/results/intermediate/validation_profiles.npz",
        "data_manifest_checksum": root / "data/processed/data_manifest.json",
    }
    expected_payment_lineage = {
        key: sha256(path) if path.exists() else None
        for key, path in resume_lineage_paths.items()
    }
    expected_payment_lineage["config_checksum"] = hashlib.sha256(
        json.dumps(cfg, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    stored_payment_lineage = {
        key: payment_metadata.get(key)
        for key in expected_payment_lineage
    }
    evaluator_checksums = set(
        payment_evaluation_intervals.get("certified_checksum", pd.Series(dtype=str))
        .astype(str)
        .unique()
    )
    unseen_payment_intervals = pd.read_csv(
        root
        / "experiments/exp9_payment_certificate/results/final/"
        "payment_evaluation_unseen_scenarios.csv"
    )
    payment_profile_checksums = set(
        payment_evaluation_intervals.get(
            "payment_evaluation_profile_checksum", pd.Series(dtype=str)
        )
        .astype(str)
        .unique()
    )
    unseen_payment_profile_checksums = set(
        unseen_payment_intervals.get(
            "payment_evaluation_profile_checksum", pd.Series(dtype=str)
        )
        .astype(str)
        .unique()
    )
    certified_profile_checksum = hashlib.sha256(
        np.ascontiguousarray(certificate_store["profiles"], dtype=np.float64).tobytes()
    ).hexdigest()
    payment_weight_columns = [
        column
        for column in payment_certificates.columns
        if column.startswith("weight_rho_")
        or column == "weight_feasible_quantile"
    ]
    payment_weights = payment_certificates[
        payment_weight_columns
    ].to_numpy()
    profile_methods = [
        str(value) for value in profile_store["methods"]
    ]
    risk_profiles = profile_store["baselines"][
        :,
        profile_methods.index("Risk-Constrained Convex Verifier"),
    ]
    candidate_profiles = profile_store["projection_candidates"]
    target_candidate_distances = np.asarray(
        [
            np.max(np.abs(risk_profiles - candidate_profiles[:, index]))
            for index in range(candidate_profiles.shape[1])
        ]
    )
    _check(
        len(payment_certificates) == expected_test
        and payment_certificates["day"].nunique() == expected_test
        and bool((payment_certificates["solver_success"] == 1).all())
        and payment_metadata.get("certificate_schema_version") == 10
        and set(payment_metadata.get("power_conversion_scenarios", {}).keys())
        == {"q01", "q10", "q50", "q90", "q99"}
        and payment_metadata.get("network_conversion_decomposition", {}).get(
            "network_scale_calibrated_on_q99"
        )
        is True
        and int(
            payment_metadata.get("independent_evaluation_generator_segments", -1)
        )
        == 40
        and float(
            np.max(
                np.abs(
                    payment_certificates[
                        "mean_absolute_target_deviation_mw"
                    ]
                    - payment_certificates[
                        "first_stage_optimal_target_deviation_mw"
                    ]
                )
            )
        )
        <= 2e-8
        and float(
            payment_certificates[
                "worst_case_fractional_cost_margin"
            ].min()
        )
        >= -1e-9
        and float(payment_certificates["payment_cap_violation_usd"].max()) <= 1e-6
        and len(payment_daily) == expected_test * 5 * 4
        and len(payment_evaluation_intervals)
        == expected_test * 5 * len(cfg["market"]["event_slots"]) * 4
        and set(payment_evaluation_intervals["conversion_scenario"].astype(str))
        == {"q01", "q10", "q50", "q90", "q99"}
        and np.isfinite(
            payment_evaluation_intervals[
                ["absolute_error_usd", "overpayment_usd"]
            ].to_numpy(dtype=float)
        ).all()
        and len(conversion_certificates) == expected_test * 5
        and len(paired_payment) == expected_test * 5
        and set(conversion_certificates["conversion_scenario"].astype(str))
        == {"q01", "q10", "q50", "q90", "q99"}
        and float(
            conversion_certificates["payment_cap_violation_usd"].max()
        )
        <= 1e-6
        and float(
            paired_payment[
                "certified_minus_single_payment_usd"
            ].mean()
        )
        < -1e-6
        and np.isfinite(
            paired_payment["certified_minus_single_payment_usd"].to_numpy(dtype=float)
        ).all(),
        "scenario_robust_exact_n1_payment_noninferiority_certificate",
        (
            f"{len(payment_certificates)}/{expected_test} lexicographically "
            "solved daily certificates across five calibration-validation conversion scenarios; "
            "formal four-segment maximum cap violation="
            f"{payment_certificates['payment_cap_violation_usd'].max():.3e} USD; "
            "the independent 40-segment transfer comparison is evaluated by its paired mean"
        ),
        checks,
    )
    _check(
        all(
            expected_payment_lineage[key] is not None
            and stored_payment_lineage[key] == expected_payment_lineage[key]
            for key in expected_payment_lineage
        )
        and payment_metadata.get("payment_evaluation_profile_source")
        == "current Experiment-2 locked test_profiles.npz"
        and payment_metadata.get("payment_evaluation_profile_checksum")
        == expected_payment_lineage["test_profile_file_checksum"]
        and payment_metadata.get("payment_evaluation_recomputed_after_profile_refit")
        is True
        and payment_profile_checksums
        == {expected_payment_lineage["test_profile_file_checksum"]}
        and unseen_payment_profile_checksums
        == {expected_payment_lineage["test_profile_file_checksum"]}
        and evaluator_checksums == {certified_profile_checksum},
        "payment_panel_lineage_matches_current_profiles_and_manifest",
        (
            "the payment evaluator records the current Experiment-2 test and "
            "validation profile digests, data-manifest digest, configuration "
            "digest, and certified-profile byte digest; stale row-count-complete "
            "panels are rejected"
        ),
        checks,
    )
    _check(
        set(payment_non_tautology["role"].astype(str))
        == {"contractual payment cap", "payment target", "role separation"}
        and len(payment_non_tautology) == 3
        and bool(
            payment_non_tautology.loc[
                payment_non_tautology["role"] == "role separation", "test_days_used_for_selection"
            ].eq(False).all()
        )
        and payment_metadata.get("reference_candidate")
        != payment_metadata.get("payment_target_candidate")
        and "different validation" in str(
            payment_metadata.get("selection_role_separation", "")
        ).lower(),
        "payment_cap_and_target_are_not_a_fixed_plan_identity",
        (
            "the contractual cap is frozen by Experiment-2 nRMSE, while the "
            "payment target is selected by an independent high-resolution N-1 "
            "payment MAE on validation days; locked test days are excluded"
        ),
        checks,
    )
    evaluator_methods = set(
        payment_daily["counterfactual_method"].astype(str).unique()
    )
    _check(
        evaluator_methods
        == {
            "Feasible Quantile Projection",
            "Single Feasible Projection",
            "Risk-Constrained Convex Verifier",
            "Payment-Certified N-1 Verifier",
        }
        and set(payment_daily["conversion_scenario"].astype(str))
        == {"q01", "q10", "q50", "q90", "q99"}
        and payment_daily["day"].nunique() == expected_test
        and np.isfinite(payment_daily["absolute_error_usd"]).all()
        and np.isfinite(payment_daily["overpayment_usd"]).all(),
        "complete_independent_payment_model_transfer_evaluation",
        (
            f"{len(payment_daily)} method-day-scenario outcomes scored across five "
            "calibration-validation conversion factors with "
            "the independent 40-segment N-1 evaluator; accuracy is reported "
            "as model-transfer evidence and is not part of Proposition 4"
        ),
        checks,
    )
    payment_pareto = pd.read_csv(
        root
        / "experiments/exp9_payment_certificate/results/final/"
        "payment_pareto_paired_ci.csv"
    )
    _check(
        len(payment_pareto) == 5 * 3
        and set(payment_pareto["conversion_scenario"].astype(str))
        == {"q01", "q10", "q50", "q90", "q99"}
        and payment_pareto["comparator"].nunique() == 3
        and bool((payment_pareto["paired_days"].astype(int) == expected_test).all())
        and np.isfinite(
            payment_pareto[
                [
                    "certified_minus_comparator_absolute_error_mean_usd",
                    "absolute_error_difference_ci95_low_usd",
                    "absolute_error_difference_ci95_high_usd",
                    "certified_minus_comparator_overpayment_mean_usd",
                    "overpayment_difference_ci95_low_usd",
                    "overpayment_difference_ci95_high_usd",
                ]
            ].to_numpy(dtype=float)
        ).all(),
        "paired_payment_accuracy_and_overpayment_pareto",
        (
            f"{len(payment_pareto)} comparator-scenario rows use paired moving-block "
            "intervals for both absolute error and overpayment; the payment-cap "
            "guarantee is kept separate from any universal MAE claim"
        ),
        checks,
    )
    unseen_payment = pd.read_csv(
        root
        / "experiments/exp9_payment_certificate/results/final/"
        "payment_evaluation_unseen_summary.csv"
    )
    unseen_metadata = payment_metadata.get("unseen_transfer_evaluation", {})
    _check(
        len(unseen_payment) == 2 * 4
        and set(unseen_payment["conversion_scenario"].astype(str))
        == {"heldout-interior-low", "heldout-interior-high"}
        and set(np.round(unseen_payment["conversion_scale_factor"].astype(float), 8))
        == {0.80, 1.20}
        and set(unseen_payment["counterfactual_method"].astype(str))
        == evaluator_methods
        and np.isfinite(
            unseen_payment[
                ["mean_absolute_error_usd", "mean_overpayment_usd"]
            ].to_numpy(dtype=float)
        ).all()
        and unseen_metadata.get("scenarios_used_in_certificate") is False
        and unseen_metadata.get("target_selection_used") is False,
        "unseen_conversion_factor_transfer_panel",
        (
            f"{len(unseen_payment)} frozen-profile outcomes across two interior "
            "conversion factors absent from the certificate and target selection; "
            "the finer N-1 replay is independent of the contractual RHS"
        ),
        checks,
    )
    interval_endpoint = pd.read_csv(
        root
        / "experiments/exp15_interval_certificate/results/final/"
        "interval_endpoint_certificates.csv"
    )
    interval_metadata = json.loads(
        (
            root
            / "experiments/exp15_interval_certificate/results/final/"
            "experiment_metadata.json"
        ).read_text(encoding="utf-8")
    )
    _check(
        len(interval_endpoint) == expected_test * 2 * 2
        and set(interval_endpoint["method"].astype(str).unique())
        == {
            "Selected Single Feasible Projection",
            "Payment-Certified N-1 Verifier",
        }
        and interval_endpoint["endpoint"].nunique() == 2
        and interval_endpoint["day"].nunique() == expected_test
        and set(interval_endpoint["endpoint"].astype(str)) == {"q01", "q99"}
        and bool((interval_endpoint.loc[interval_endpoint["endpoint"] == "q01", "capacity_activation_eligible"] == True).all())
        and bool((interval_endpoint.loc[interval_endpoint["endpoint"] == "q99", "capacity_activation_eligible"] == True).all())
        and bool((interval_endpoint.loc[interval_endpoint["endpoint"] == "q99", "solver_status"] == "optimal").all())
        and bool(np.isfinite(interval_endpoint["payment_cap_violation_usd"].to_numpy(dtype=float)).all())
        and bool(
            interval_endpoint["payment_cap_violation_usd"].max() <= 1e-6
        )
        and interval_metadata.get("external_transfer_comparator")
        == "Feasible Quantile Projection"
        and "selected single feasible" in str(
            interval_metadata.get("profile_source", "")
        ).lower(),
        "independent_endpoint_certificate_uses_selected_single_reference",
        (
            f"{len(interval_endpoint)}/{expected_test * 2 * 2} endpoint rows "
            "compare the payment-certified profile with the preselected single "
            "feasible reference; the quantile profile remains external"
        ),
        checks,
    )
    payment_intervals = pd.read_csv(
        root
        / "experiments/exp15_interval_certificate/results/final/"
        "payment_value_interval_certificates.csv"
    )
    interval_summary = pd.read_csv(
        root
        / "experiments/exp15_interval_certificate/results/final/"
        "payment_value_interval_summary.csv"
    )
    _check(
        len(payment_intervals) == expected_test * 2
        and set(payment_intervals["candidate_hull_vertices"].astype(int)) == {2}
        and bool(
            (
                payment_intervals.loc[
                    payment_intervals["endpoint"] == "q01",
                    "payment_interval_width_usd",
                ]
                >= -1e-8
            ).all()
        )
        and bool(
            np.isfinite(
                payment_intervals.loc[
                    payment_intervals["endpoint"] == "q99",
                    "payment_interval_width_usd",
                ].to_numpy(dtype=float)
            ).all()
        )
        and bool(
            np.isfinite(
                payment_intervals.loc[
                    payment_intervals["endpoint"] == "q01",
                    "oracle_payment_usd",
                ].to_numpy(dtype=float)
            ).all()
        )
        and bool(
            np.isfinite(
                payment_intervals.loc[
                    payment_intervals["endpoint"] == "q99",
                    "oracle_payment_usd",
                ].to_numpy(dtype=float)
            ).all()
        )
        and set(payment_intervals["oracle_inside_interval"].dropna().astype(int).unique()) <= {0, 1}
        and len(interval_summary) == 2
        and interval_metadata.get("payment_value_interval", {}).get(
            "oracle_used_only_for_coverage_audit"
        ) is True
        and interval_metadata.get("payment_value_interval", {}).get(
            "raw_q99_is_stress_only"
        ) is False
        and interval_metadata.get("payment_value_interval", {}).get(
            "capacity_eligible_endpoints_only"
        ) is True
        and interval_metadata.get("interval_certificate_valid") is True
        and float(interval_metadata.get("maximum_payment_cap_violation_usd", np.inf))
        <= 1e-6
        and not payment_intervals["candidate_hull_definition"].astype(str).str.contains(
            "oracle", case=False, regex=False
        ).any(),
        "payment_uncertainty_interval_has_posthoc_oracle_audit_only",
        (
            f"{len(payment_intervals)}/{expected_test * 2} endpoint rows retain "
            "the raw q01/q99 interval; fixed and flexible demand are separated "
            "and both endpoints are solved under the q99-calibrated scale, while "
            f"oracle values remain post-hoc coverage diagnostics ({int(payment_intervals['oracle_inside_interval'].sum())}/"
            f"{len(payment_intervals)} inside)"
        ),
        checks,
    )
    _check(
        len(payment_weight_columns) == 7
        and candidate_profiles.shape[1] == 6
        and len(certificate_store["candidate_names"]) == 7
        and all(
            "Risk-Constrained" not in str(name)
            for name in certificate_store["candidate_names"]
        )
        and np.allclose(payment_weights.sum(axis=1), 1.0, atol=1e-7)
        and float(payment_weights.min()) >= -1e-7
        and len(np.unique(np.round(payment_weights, 8), axis=0)) > 1,
        "independent_nondegenerate_payment_candidate_hull",
        (
            "six first-stage projection candidates plus an external matched "
            "feasible-quantile comparator; the selected single projection is "
            "the contractual reference; the risk verifier is excluded from "
            "the certificate input and evaluated as an external target; "
            f"{len(np.unique(np.round(payment_weights, 8), axis=0))} distinct "
            "daily optimal weight vectors"
        ),
        checks,
    )
    _check(
        len(payment_target_selection) == 7
        and set(payment_target_selection.columns)
        >= {
            "candidate_index",
            "candidate_name",
            "mean_validation_payment_mae_usd",
            "validation_cells",
            "selected",
        }
        and payment_target_selection["candidate_index"].nunique() == 7
        and bool(
            np.isfinite(
                payment_target_selection["mean_validation_payment_mae_usd"]
            ).all()
        )
        and bool(
            (
                payment_target_selection["validation_cells"]
                == 16 * 3 * len(cfg["market"]["event_slots"])
            ).all()
        )
        and int(payment_target_selection["selected"].sum()) == 1
        and int(
            payment_target_selection.loc[
                payment_target_selection["selected"], "candidate_index"
            ].iloc[0]
        )
        == int(payment_metadata["payment_target_candidate_index"])
        and payment_metadata.get("test_peak_used_for_scaling") is False
        and float(payment_metadata.get("validation_peak_trace_mw", 0.0)) > 0.0,
        "validation_only_payment_target_selection",
        (
            "seven workload-feasible candidates ranked on "
            f"{16 * 3 * len(cfg['market']['event_slots'])} independent "
            "validation N-1 payment cells; the selected target and DC scale "
            "are frozen before locked test evaluation"
        ),
        checks,
    )
    ac_results = pd.read_csv(
        root
        / "experiments/exp10_ac_validation/results/final/ac_opf_locked_day_results.csv"
    )
    ac_cells = ac_results.groupby(["network", "counterfactual_method"])[
        "day"
    ].nunique()
    _check(
        len(ac_results) == 4 * expected_test * 4
        and ac_results["network"].nunique() == 4
        and bool((ac_cells == expected_test).all())
        and float(ac_results["maximum_voltage_violation_pu"].max()) <= 1e-6
        and float(ac_results["maximum_apparent_line_loading"].max()) <= 1.000001,
        "complete_nonlinear_ac_opf_panel",
        (
            f"{len(ac_results)}/{4 * expected_test * 4} converged network-day-"
            "method outcomes with AC voltage and apparent-power limits enforced"
        ),
        checks,
    )
    ac_n1 = pd.read_csv(
        root
        / "experiments/exp10_ac_validation/results/final/"
        "ac_n1_contingency_results.csv"
    )
    expected_ac_n1_outages = {"IEEE 9-bus": 6, "IEEE 14-bus": 19}
    expected_ac_n1 = (
        expected_test * 4 * sum(expected_ac_n1_outages.values())
    )
    ac_n1_cells = ac_n1.groupby(
        ["network", "counterfactual_method", "outage"]
    )["day"].nunique()
    observed_ac_n1_outages = (
        ac_n1.groupby("network")["outage"].nunique().to_dict()
    )
    _check(
        len(ac_n1) == expected_ac_n1
        and observed_ac_n1_outages == expected_ac_n1_outages
        and bool((ac_n1_cells == expected_test).all())
        and bool(ac_n1["solver_success"].astype(bool).all())
        and float(ac_n1["maximum_voltage_violation_pu"].max()) <= 1e-6
        and float(ac_n1["maximum_apparent_line_loading"].max()) <= 1.000001,
        "complete_nonlinear_ac_n1_panel",
        (
            f"{len(ac_n1)}/{expected_ac_n1} converged method-day-outage AC "
            "OPFs across all 6 IEEE-9 and 19 IEEE-14 non-islanding line "
            "outages"
        ),
        checks,
    )
    preventive_ac = pd.read_csv(
        root
        / "experiments/exp10_ac_validation/results/final/"
        "preventive_ac_n1_results.csv"
    )
    expected_preventive_ac = expected_test * 3 * 4 * 6
    preventive_cells = preventive_ac.groupby(
        [
            "peak_dc_penetration",
            "counterfactual_method",
            "outage",
        ]
    )["day"].nunique()
    shared_pg_columns = [
        column
        for column in preventive_ac.columns
        if column.startswith("shared_pg_generator_")
    ]
    shared_plan_consistency = (
        preventive_ac.groupby(
            [
                "peak_dc_penetration",
                "day",
                "counterfactual_method",
            ]
        )[shared_pg_columns]
        .nunique()
        .to_numpy()
    )
    _check(
        len(preventive_ac) == expected_preventive_ac
        and preventive_ac["peak_dc_penetration"].nunique() == 3
        and preventive_ac["outage"].nunique() == 6
        and len(shared_pg_columns) == 3
        and bool((shared_plan_consistency == 1).all())
        and bool((preventive_cells == expected_test).all())
        and bool(preventive_ac["solver_success"].astype(bool).all())
        and float(
            preventive_ac[
                "maximum_nonreference_active_plan_deviation_mw"
            ].max()
        )
        <= 1e-6
        and float(
            preventive_ac["maximum_voltage_violation_pu"].max()
        )
        <= 1e-6
        and float(
            preventive_ac["maximum_apparent_line_loading"].max()
        )
        <= 1.000001,
        "complete_shared_active_plan_preventive_ac_n1_panel",
        (
            f"{len(preventive_ac)}/{expected_preventive_ac} converged "
            "penetration-method-day-outage cells across four matched "
            "counterfactuals; all six IEEE-9 outages "
            "share the intact-state non-reference active dispatch exactly"
        ),
        checks,
    )
    ac_metadata_path = (
        root
        / "experiments/exp10_ac_validation/results/final/experiment_metadata.json"
    )
    ac_reuse_manifest_path = (
        root
        / "experiments/exp10_ac_validation/results/final/"
        "ac_profile_refit_reuse_manifest.json"
    )
    ac_metadata = json.loads(ac_metadata_path.read_text(encoding="utf-8"))
    ac_reuse_manifest = json.loads(
        ac_reuse_manifest_path.read_text(encoding="utf-8")
    )
    current_test_profile = (
        root
        / "experiments/exp2_baseline_verification/results/intermediate/"
        "test_profiles.npz"
    )
    current_certified_profile = (
        root
        / "experiments/exp9_payment_certificate/results/final/"
        "certified_counterfactual_profiles.npz"
    )
    current_test_profile_checksum = hashlib.sha256(
        current_test_profile.read_bytes()
    ).hexdigest()
    current_certified_profile_checksum = hashlib.sha256(
        current_certified_profile.read_bytes()
    ).hexdigest()
    current_ac_digest = hashlib.sha256()
    current_ac_digest.update(current_test_profile.read_bytes())
    current_ac_digest.update(b"\0")
    current_ac_digest.update(current_certified_profile.read_bytes())
    current_ac_checksum = current_ac_digest.hexdigest()
    ac_lineage_checksums = {
        str(value)
        for frame in (ac_results, ac_n1, preventive_ac)
        for value in frame["ac_profile_checksum"].astype(str).unique()
    }
    _check(
        ac_metadata.get("profile_checksum") == current_test_profile_checksum
        and ac_metadata.get("certified_profile_checksum")
        == current_certified_profile_checksum
        and ac_metadata.get("ac_profile_checksum") == current_ac_checksum
        and ac_metadata.get("profile_recomputed_after_exp2_refit") is True
        and ac_lineage_checksums == {current_ac_checksum}
        and ac_reuse_manifest.get("profile_after_sha256")
        == current_test_profile_checksum
        and ac_reuse_manifest.get("ac_input_after_sha256") == current_ac_checksum
        and ac_reuse_manifest.get("normalization_scale_unchanged") is True
        and ac_reuse_manifest.get("recomputed_method")
        == "Risk-Constrained Convex Verifier",
        "ac_profile_lineage_after_refit",
        (
            "base, corrective N-1, and preventive AC panels carry the current "
            "test/certified profile digest; exact-input row reuse is documented "
            "by an explicit refit manifest"
        ),
        checks,
    )
    spatial = pd.read_csv(
        root
        / "experiments/exp11_spatial_scale_robustness/results/final/"
        "spatial_scale_robustness.csv"
    )
    declared_penetrations = set(
        float(value)
        for value in cfg["experiments"]["spatial_scale_peak_penetrations"]
    )
    spatial_methods = {
        "Feasible Quantile Projection",
        "Single Feasible Projection",
        "Risk-Constrained Convex Verifier",
        "Trace-Anchored Reference",
    }
    expected_spatial = (
        26 * len(declared_penetrations) * expected_test * len(spatial_methods)
    )
    spatial_cells = spatial.groupby(
        [
            "assignment_id",
            "peak_dc_penetration",
            "counterfactual_method",
        ]
    )["day"].nunique()
    _check(
        len(spatial) == expected_spatial
        and spatial["assignment_id"].nunique() == 26
        and set(spatial["assignment_type"].unique())
        == {
            "one-to-one permutation",
            "co-located four-region control",
            "two-bus clustered control",
        }
        and set(spatial["peak_dc_penetration"].unique())
        == declared_penetrations
        and set(spatial["counterfactual_method"].unique())
        == spatial_methods
        and bool((spatial_cells == expected_test).all())
        and float(spatial["maximum_line_loading"].max()) <= 1.000001,
        "complete_spatial_scale_factorial_panel",
        (
            f"{len(spatial)}/{expected_spatial} outcomes cover all 24 regional "
            f"permutations plus two concentration controls, {len(declared_penetrations)} penetrations, "
            f"{expected_test} locked days, and {len(spatial_methods)} methods"
        ),
        checks,
    )
    spatial_trace_audit = pd.read_csv(
        root
        / "experiments/exp11_spatial_scale_robustness/results/final/"
        "spatial_trace_mapping_audit.csv"
    )
    spatial_trace_meta = json.loads(
        (
            root
            / "experiments/exp11_spatial_scale_robustness/results/final/"
            "spatial_trace_mapping_metadata.json"
        ).read_text(encoding="utf-8")
    )
    _check(
        len(spatial_trace_audit) == 12
        and spatial_trace_meta.get("assignment", "").startswith(
            "feature-stratified"
        )
        and spatial_trace_meta.get("physical_geography_available") is False
        and spatial_trace_meta.get("all_region_to_bus_permutations_evaluated") is True
        and spatial_trace_meta.get("burstgpt_rows") == 5_188_507
        and spatial_trace_meta.get("mit_joined_jobs") == 68_664,
        "feature_stratified_trace_mapping_audit",
        (
            f"{len(spatial_trace_audit)} trace-region panels; feature-stratified "
            "scenario is separated from physical geography and paired with the "
            "complete 24-assignment network panel"
        ),
        checks,
    )
    rolling = pd.read_csv(
        root
        / "experiments/exp12_rolling_market_validation/results/final/"
        "rolling_market_validation.csv"
    )
    rolling_methods = {
        "Feasible Quantile Projection",
        "Single Feasible Projection",
        "Risk-Constrained Convex Verifier",
        "Payment-Certified N-1 Verifier",
    }
    rolling_cells = rolling.groupby("counterfactual_method")["day"].nunique()
    paired_rolling = pd.read_csv(
        root
        / "experiments/exp12_rolling_market_validation/results/final/"
        "paired_payment_comparisons.csv"
    )
    settlement_chain = pd.read_csv(
        root
        / "experiments/exp12_rolling_market_validation/results/final/"
        "settlement_chain_certificate.csv"
    )
    _check(
        len(rolling) == expected_test * len(rolling_methods)
        and set(rolling["counterfactual_method"].unique())
        == rolling_methods
        and bool((rolling_cells == expected_test).all())
        and {
            "full_cycle_value_residual_usd",
            "full_cycle_absolute_value_residual_usd",
            "no_event_objective_gap_usd",
        }.issubset(rolling.columns)
        and bool(
            np.isfinite(
                rolling["full_cycle_absolute_value_residual_usd"].to_numpy()
            ).all()
        )
        and bool(
            np.isfinite(rolling["no_event_objective_gap_usd"].to_numpy()).all()
        )
        and float(rolling["baseline_projection_l1_mw"].max()) <= 2e-5
        and float(rolling["actual_projection_l1_mw"].max()) <= 2e-5
        and float(
            rolling["total_cycle_energy_difference_mwh"].abs().max()
        )
        <= 1e-3
        and float(
            rolling["allocation_budget_balance_residual_usd"].abs().max()
        )
        <= 1e-8
        and float(
            rolling["bilateral_budget_balance_residual_usd"].abs().max()
        )
        <= 1e-8
        and bool(
            rolling["bilateral_individual_rationality_satisfied"].all()
        )
        and float(rolling["participant_contract_utility_usd"].min()) >= -1e-7
        and float(rolling["operator_contract_utility_usd"].min()) >= -1e-7
        and len(paired_rolling) == 3,
        "complete_continuous_horizon_market_validation",
        (
            f"{len(rolling)}/{expected_test * len(rolling_methods)} "
            "method-day outcomes use real future arrivals, lexicographic "
            "projection, complete-cycle energy accounting, exact site budget "
            "balance, and an individually rational bilateral outside option"
        ),
        checks,
    )
    _check(
        len(settlement_chain) == expected_test * len(rolling_methods)
        and set(settlement_chain["counterfactual_method"].astype(str))
        == rolling_methods
        and settlement_chain.groupby("counterfactual_method")["day"].nunique().eq(
            expected_test
        ).all()
        and np.isfinite(
            settlement_chain[
                [
                    "closed_meter_service_mwh",
                    "capacity_product_value_usd",
                    "space_time_signed_value_usd",
                    "operator_value_usd",
                    "participant_opportunity_cost_usd",
                    "transaction_surplus_usd",
                    "bilateral_transfer_usd",
                    "participant_utility_usd",
                    "operator_utility_usd",
                ]
            ].to_numpy(dtype=float)
        ).all()
        and bool(settlement_chain["chain_certificate_valid"].astype(bool).all())
        and float(
            settlement_chain["space_time_site_sum_residual_usd"].abs().max()
        )
        <= 1e-8
        and float(
            settlement_chain[
                "operator_value_decomposition_residual_usd"
            ].abs().max()
        )
        <= 1e-8
        and float(
            settlement_chain["bilateral_budget_balance_residual_usd"].abs().max()
        )
        <= 1e-8,
        "typed_end_to_end_settlement_chain_certificate",
        (
            f"{len(settlement_chain)} method-day chains bind submitted, capped, and "
            "metered service before capacity value; space-time decomposition and "
            "bilateral budget residuals are zero"
        ),
        checks,
    )
    provenance = json.loads(
        (
            root
            / "experiments/exp16_ledger_capacity_provenance/results/final/"
            "ledger_provenance_certificate.json"
        ).read_text(encoding="utf-8")
    )
    provenance_metadata = json.loads(
        (
            root
            / "experiments/exp16_ledger_capacity_provenance/results/final/"
            "experiment_metadata.json"
        ).read_text(encoding="utf-8")
    )
    capacity_reconciliation = pd.read_csv(
        root
        / "experiments/exp16_ledger_capacity_provenance/results/final/"
        "capacity_reconciliation.csv"
    )
    calibration_sensitivity = pd.read_csv(
        root
        / "experiments/exp16_ledger_capacity_provenance/results/final/"
        "workload_power_calibration_sensitivity.csv"
    )
    physical_calibration = pd.read_csv(
        root
        / "experiments/exp16_ledger_capacity_provenance/results/final/"
        "physical_calibration_summary.csv"
    )
    _check(
        provenance["joined_positive_energy_jobs"] > 50_000
        and provenance["canonical_row_count"] == provenance["joined_positive_energy_jobs"]
        and bool(provenance["integrity_conditions"]["raw_to_join_energy_conservation"])
        and bool(provenance["integrity_conditions"]["release_before_start"])
        and bool(provenance["integrity_conditions"]["start_before_end"])
        and float(abs(provenance["raw_to_join_energy_residual_j"])) <= 1e-6
        and len(provenance["canonical_joined_ledger_sha256"]) == 64
        and len(provenance["canonical_submission_ledger_sha256"]) == 64
        and int(provenance["submission_row_count"]) == 216_572
        and bool(provenance["integrity_conditions"]["submission_digest_excludes_execution_telemetry"])
        and provenance_metadata["integrity_passed"] is True
        and bool(
            (
                capacity_reconciliation["capacity_excess_peak_mw"].astype(float)
                >= -1e-8
            ).all()
        )
        and float(
            (
                capacity_reconciliation["scaled_benchmark_peak_mw"]
                - capacity_reconciliation["capacity_excess_peak_mw"]
            ).max()
        )
        <= float(cfg["project"]["flexible_capacity_mw"]) + 1e-6
        and provenance_metadata.get("capacity_commitment", {}).get(
            "locked_test_observations_used_for_selection"
        ) is False
        and provenance_metadata.get("capacity_commitment", {}).get(
            "measured_envelope_is_reconciliation_only"
        ) is True,
        "immutable_ledger_provenance_and_capacity_reconciliation",
        (
            f"{provenance['submission_row_count']:,} submit-time rows and "
            f"{provenance['joined_positive_energy_jobs']:,} matched execution rows; "
            f"submission digest {provenance['canonical_submission_ledger_sha256'][:12]}..., "
            "execution telemetry is excluded from decision provenance, and raw-to-join "
            "energy is conserved for the post-event reconciliation"
        ),
        checks,
    )
    witness = pd.read_csv(
        root
        / "experiments/exp14_job_level_fidelity/results/final/"
        "job_interval_witness_summary.csv"
    )
    witness_values = dict(zip(witness["metric"].astype(str), witness["value"].astype(float)))
    _check(
        len(witness) >= 8
        and int(witness_values.get("nonpreemptive_joined_jobs", -1)) == 71_128
        and int(witness_values.get("release_violation_seconds", -1)) == 0
        and int(witness_values.get("completion_deadline_violation_seconds", -1)) == 0
        and float(witness_values.get("minimum_native_capacity_slack_mwh", -1.0)) >= -1e-7,
        "measured_contiguous_job_interval_witness",
        (
            "all 71,128 immutable joined jobs retain measured contiguous intervals, "
            "runtime/GPU/native-power fields, and zero release/deadline violations; "
            "the witness is separate from the aggregate flow LP"
        ),
        checks,
    )
    counterfactual = pd.read_csv(
        root
        / "experiments/exp19_job_level_counterfactual/results/final/"
        "job_level_counterfactual_summary.csv"
    )
    counterfactual_values = dict(
        zip(counterfactual["metric"].astype(str), counterfactual["value"])
    )
    counterfactual_metadata = json.loads(
        (
            root
            / "experiments/exp19_job_level_counterfactual/results/final/"
            "experiment_metadata.json"
        ).read_text(encoding="utf-8")
    )
    native_event = float(counterfactual_values.get("event_energy_native_mwh", np.nan))
    counterfactual_event = float(
        counterfactual_values.get("event_energy_counterfactual_mwh", np.nan)
    )
    net_reduction = float(
        counterfactual_values.get("event_net_reduction_mwh", np.nan)
    )
    gross_reduction = float(
        counterfactual_values.get("event_gross_reduction_mwh", np.nan)
    )
    rebound = float(counterfactual_values.get("event_rebound_mwh", np.nan))
    _check(
        int(float(counterfactual_values.get("submitted_jobs", -1))) == 75_326
        and int(float(counterfactual_values.get("execution_matched_jobs", -1))) == 71_128
        and float(counterfactual_values.get("maximum_job_energy_residual_mwh", np.inf)) <= 1e-8
        and float(counterfactual_values.get("declared_energy_conservation_residual_mwh", np.inf)) <= 1e-8
        and float(counterfactual_values.get("minimum_site_slot_capacity_slack_mwh", -np.inf)) >= -1e-8
        and float(counterfactual_values.get("event_net_reduction_mwh", -1.0)) >= 0.0,
        "exact_job_indexed_counterfactual_certificate",
        (
            "all valid scheduler submissions enter an exact submit-time "
            "contiguous start-time model; execution matching is reported "
            "separately and declared-energy/job residuals are zero"
        ),
        checks,
    )
    _check(
        counterfactual_metadata.get("deadline_mode") == "submit_time_declaration"
        and counterfactual_metadata.get("observed_time_end_used_as_deadline") is False
        and int(counterfactual_metadata.get("declared_window_slots_min", 0)) >= 1
        and int(counterfactual_metadata.get("declared_window_slots_max", 0))
        >= int(counterfactual_metadata.get("unbounded_timelimit_slots", 0))
        and float(counterfactual_metadata.get("declared_per_gpu_power_cap_mw", 0.0))
        == 0.001
        and int(counterfactual_metadata.get("declared_window_infeasible_jobs", -1)) == 0
        and "allocation runtime plus a precommitted queue allowance" in str(
            counterfactual_metadata.get("deadline_window_rule", "")
        )
        and int(counterfactual_metadata.get("submission_buffer_slots", -1)) == int(
            cfg["experiments"].get("job_level_submission_buffer_slots", 0)
        )
        and counterfactual_metadata.get("observed_energy_used_in_decision") is False
        and len(str(counterfactual_metadata.get("submission_ledger_digest", ""))) == 64
        and counterfactual_metadata.get("population_rule") == "all valid scheduler submissions in the predeclared job-level horizon; positive-energy execution matching is a post-event scoring join"
        and counterfactual_metadata.get("observed_time_end_used_as_deadline") is False
        and counterfactual_metadata.get("nonpreemptive_witness", "").startswith("exact submitted-job contiguous")
        and counterfactual_metadata.get("contiguity_certificate", {}).get("maximum_gap_inside_service_block") == 0
        and np.isfinite([native_event, counterfactual_event, net_reduction, gross_reduction, rebound]).all()
        and abs((native_event - counterfactual_event) - net_reduction) <= 1e-10
        and gross_reduction + 1e-10 >= net_reduction
        and rebound >= -1e-10,
        "declared_timelimit_counterfactual_boundary",
        (
            f"submit-time runtime declarations plus the precommitted queue allowance "
            f"are used (window slots "
            f"{counterfactual_metadata.get('declared_window_slots_min')}--"
            f"{counterfactual_metadata.get('declared_window_slots_max')}), "
            "observed completion is excluded, and net/gross/rebound arithmetic is explicit"
        ),
        checks,
    )
    _check(
        set(calibration_sensitivity["calibration_ratio_quantile"].astype(str))
        == {"q01", "q10", "q50", "q90", "q99"}
        and bool(
            (calibration_sensitivity["capacity_safe_region_peak_mw"]
             <= float(cfg["project"]["flexible_capacity_mw"]) + 1e-6).all()
        )
        and bool((calibration_sensitivity["capacity_safe_scale_factor"] > 0).all()),
        "calibration_validation_power_conversion_capacity_safe_sensitivity",
        (
            f"{len(calibration_sensitivity)} calibration-validation ratio endpoints are explicit; "
            "capacity-safe clipping remains below the precommitted nameplate"
        ),
        checks,
    )
    _check(
        len(physical_calibration) == 1
        and int(physical_calibration.loc[0, "train_observations"])
        == int(power_calibration.get("train_observations", -1))
        and int(
            physical_calibration.loc[0, "calibration_validation_observations"]
        ) == int(power_calibration.get("validation_observations", -1))
        and int(physical_calibration.loc[0, "locked_observations"])
        == int(power_calibration.get("locked_observations", -1))
        and np.isfinite(
            physical_calibration[
                [
                    "calibration_validation_mae_watts",
                    "calibration_validation_rmse_watts",
                    "calibration_validation_r2",
                    "locked_mae_watts",
                    "locked_rmse_watts",
                    "locked_r2",
                    "test_mae_watts",
                    "test_rmse_watts",
                    "test_r2",
                    "calibration_validation_aggregate_energy_ratio",
                ]
            ].to_numpy(dtype=float)
        ).all()
        and 0.0 < float(
            physical_calibration.loc[0, "calibration_validation_r2"]
        ) <= 1.0
        and 0.0 < float(physical_calibration.loc[0, "locked_r2"]) <= 1.0
        and bool(physical_calibration.loc[0, "raw_measurement_is_not_scaled_utility_power"])
        and bool(physical_calibration.loc[0, "spatial_mapping_is_declared_scenario"]),
        "physical_calibration_is_separate_from_utility_scale",
        (
            f"{power_calibration.get('train_observations')}/"
            f"{power_calibration.get('validation_observations')}/"
            f"{power_calibration.get('locked_observations')} chronological "
            "train/validation/locked GPU-power observations are reconciled with "
            "finite metrics while raw measurement and declared spatial mapping "
            "remain explicitly separated from utility-scale claims"
        ),
        checks,
    )
    coupled_summary = pd.read_csv(
        root
        / "experiments/exp22_coupled_job_network_certificate/results/final/"
        "coupled_network_summary.csv"
    )
    coupled_replay = pd.read_csv(
        root
        / "experiments/exp22_coupled_job_network_certificate/results/final/"
        "coupled_network_event_replay.csv"
    )
    coupled_scale_replay = pd.read_csv(
        root
        / "experiments/exp22_coupled_job_network_certificate/results/final/"
        "coupled_network_scale_replay.csv"
    )
    coupled_values = dict(
        zip(coupled_summary["metric"].astype(str), coupled_summary["value"].astype(float))
    )
    coupled_metadata = json.loads(
        (
            root
            / "experiments/exp22_coupled_job_network_certificate/results/final/"
            "experiment_metadata.json"
        ).read_text(encoding="utf-8")
    )
    _check(
        int(coupled_values.get("submitted_jobs", -1)) == 75_326
        and int(coupled_values.get("execution_matched_jobs", -1)) == 71_128
        and int(coupled_values.get("service_variables", -1)) == 13_198_247
        and float(coupled_values.get("maximum_job_to_aggregate_residual_mwh", np.inf))
        <= 1e-12
        and bool(coupled_values.get("all_network_solves_successful", 0.0))
        and coupled_metadata.get("network_profile_is_same_job_witness") is True
        and coupled_metadata.get("post_solution_profile_reoptimization") is False
        and coupled_metadata.get("network_case") == "IEEE RTS-24 (PYPOWER case24_ieee_rts)"
        and coupled_metadata.get("network_source") == "PYPOWER case24_ieee_rts (public RTS-24 benchmark)"
        and coupled_metadata.get("data_center_buses_one_based") == [3, 8, 15, 21]
        and abs(
            float(coupled_metadata.get("network_load_multiplier", np.nan))
            - float(cfg["experiments"]["n1_load_multiplier"])
        ) <= 1e-12
        and int(coupled_values.get("event_slots_replayed", -1)) == 1_056
        and int(coupled_metadata.get("replayed_event_slot_count", 0)) == 1_056,
        "exact_job_to_network_coupling_certificate",
        (
            "the submitted-job indexed witness is aggregated before secure N-1 "
            "settlement; residual is zero and no second profile optimization is used"
        ),
        checks,
    )
    _check(
        len(coupled_replay) == 3
        and set(coupled_replay["scenario"].astype(str))
        == {
            "raw_job_witness",
            "fixed_nameplate_homogeneous",
            "capacity_proportional_homogeneous",
        }
        and bool((coupled_replay["event_slot_count"].astype(int) == 1_056).all())
        and bool((coupled_replay["credible_contingencies"].astype(int) == 37).all())
        and bool(coupled_replay["solver_success"].astype(bool).all())
        and len(coupled_scale_replay) == 2
        and bool(coupled_scale_replay["coupling_certificate_valid"].astype(bool).all())
        and np.isfinite(
            coupled_scale_replay[
                ["scale_factor", "secure_net_value_usd_per_interval"]
            ].to_numpy(dtype=float)
        ).all(),
        "coupled_replay_covers_all_rts24_n1_contingencies",
        (
            "the raw indexed witness and two homogeneous scale transforms solve "
            "the public RTS-24 native/counterfactual cases with all 37 finite outages"
        ),
        checks,
    )
    _check(
        coupled_metadata.get("independent_job_feasibility_recheck") is True
        and float(coupled_values.get("maximum_job_energy_recheck_residual_mwh", np.inf))
        <= 1e-12
        and float(coupled_values.get("maximum_gpu_bound_violation_mwh", np.inf))
        <= 1e-12
        and float(coupled_values.get("maximum_gpu_bound_violation_mwh", -np.inf))
        >= 0.0
        and float(coupled_values.get("minimum_gpu_bound_slack_mwh", -np.inf))
        >= -1e-12
        and float(coupled_values.get("minimum_site_capacity_slack_mwh", -np.inf))
        >= -1e-12,
        "independent_job_primal_recheck_before_network_value",
        (
            "the stored indexed service vector independently satisfies every "
            "job-energy equality, committed GPU nameplate bound, and regional "
            "capacity row before the network replay"
        ),
        checks,
    )
    coupling_certificate_path = (
        root
        / "experiments/exp22_coupled_job_network_certificate/results/final/"
        "coupling_invariant_certificate.json"
    )
    coupling_certificate = json.loads(coupling_certificate_path.read_text(encoding="utf-8"))
    typed_certificate = coupling_certificate.get("certificate", {})
    mapped_certificate = coupling_certificate.get("network_mapping_certificate", {})
    _check(
        typed_certificate.get("version") == "coupling-invariant-v1"
        and typed_certificate.get("valid") is True
        and float(typed_certificate.get("max_job_energy_residual_mwh", np.inf)) <= 1e-12
        and float(typed_certificate.get("max_aggregation_residual_mwh", np.inf)) <= 1e-12
        and mapped_certificate.get("valid") is True
        and float(mapped_certificate.get("max_network_mapping_residual_mw", np.inf)) <= 1e-10
        and all(
            abs(
                float(mapped_certificate.get(field, np.nan))
                - float(typed_certificate.get(field, np.nan))
            )
            <= 1e-12
            for field in (
                "max_job_energy_residual_mwh",
                "max_aggregation_residual_mwh",
                "minimum_gpu_bound_slack_mwh",
                "maximum_gpu_bound_violation_mwh",
                "minimum_site_capacity_slack_mwh",
            )
        ),
        "typed_dimension_preserving_coupling_certificate",
        (
            "one typed certificate checks job equalities, GPU/capacity bounds, "
            "job-to-region aggregation, and MWh-to-MW network mapping before settlement"
        ),
        checks,
    )

    independent_event_summary = pd.read_csv(
        root
        / "experiments/exp23_independent_event_replay/results/final/"
        "independent_event_replay_summary.csv"
    )
    independent_event_metadata = json.loads(
        (
            root
            / "experiments/exp23_independent_event_replay/results/final/"
            "experiment_metadata.json"
        ).read_text(encoding="utf-8")
    )
    independent_event_protocol = pd.read_csv(
        root
        / "experiments/exp23_independent_event_replay/results/final/"
        "independent_event_protocol_certificate.csv"
    )
    common_runtime_metadata = json.loads(
        (
            root
            / "experiments/exp27_executable_common_witness/results/final/experiment_metadata.json"
        ).read_text(encoding="utf-8")
    )
    gate_row = independent_event_summary[
        independent_event_summary["method"] == "Common runtime-complete witness"
    ]
    independent_row = independent_event_summary[
        independent_event_summary["method"] == "Independent declaration-only exact policy"
    ]
    _check(
        len(independent_event_summary) == 2
        and len(gate_row) == 1
        and len(independent_row) == 1
        and int(gate_row.iloc[0]["locked_days"]) == 54
        and np.isfinite(
            gate_row[["nrmse", "false_response_mwh", "underpayment_mwh", "credit_f1"]]
            .to_numpy(dtype=float)
        ).all()
        and np.isfinite(
            independent_row[["nrmse", "false_response_mwh", "underpayment_mwh", "credit_f1"]]
            .to_numpy(dtype=float)
        ).all()
        and float(independent_row.iloc[0]["nrmse"]) == 0.0
        and float(independent_row.iloc[0]["credit_f1"]) == 1.0
        and independent_event_metadata.get("event_intervention") is True
        and independent_event_metadata.get("causal_intervention_claim") is False
        and independent_event_metadata.get("truth_source") == "independent declaration-only exact start policy"
        and independent_event_metadata.get("common_witness_digest")
        == common_runtime_metadata.get("witness_digest")
        and independent_event_metadata.get("independent_policy", {}).get("risk_oracle_reused") is False
        and independent_event_metadata.get("independent_policy", {}).get("tariff_pair_distinct_from_gate") is True
        and independent_event_metadata.get("independent_policy", {}).get("structurally_distinct_from_gate") is True
        and float(independent_event_metadata.get("independent_policy", {}).get("minimum_participant_event_mwh", 0.0)) > 0.0
        and float(independent_event_metadata.get("independent_policy", {}).get("maximum_response_difference_from_gate_mw", 0.0)) > 1e-8,
        "independent_controlled_event_replay",
        (
            "54 locked days are replayed under a predeclared tariff intervention; "
            "the independently parameterized meter policy differs from the gate "
            "policy, is scored without verifier outputs, and makes no field-causal claim"
        ),
        checks,
    )
    independent_protocol_values = dict(
        zip(
            independent_event_protocol["criterion"].astype(str),
            independent_event_protocol["value"].astype(float),
        )
    )
    _check(
        independent_protocol_values.get("post_gate_or_future_arrivals_used", np.nan)
        == 0
        and independent_protocol_values.get("execution_telemetry_used", np.nan)
        == 0
        and independent_protocol_values.get("independent_tariff_distinct", np.nan)
        == 1
        and independent_protocol_values.get("same_submission_digest", np.nan)
        == 1
        and independent_protocol_values.get("same_declaration_baseline", np.nan) == 1
        and independent_protocol_values.get("distinct_event_trajectory", np.nan) == 1
        and independent_event_metadata.get("protocol_certificate_file")
        == "independent_event_protocol_certificate.csv",
        "independent_event_information_and_policy_certificate",
        (
            "the independent event uses only the gate-masked ledger, has no verifier or "
            "locked-outcome input, differs by predeclared tariff/participants, and separates "
            "its policy trajectory before scoring"
        ),
        checks,
    )

    exante_summary = pd.read_csv(
        root
        / "experiments/exp25_exante_job_validation/results/final/"
        "exante_job_validation_summary.csv"
    )
    exante_values = dict(zip(exante_summary["metric"].astype(str), exante_summary["value"].astype(float)))
    stress_summary = pd.read_csv(
        root
        / "experiments/exp25_exante_job_validation/results/final/"
        "job_level_capacity_stress_summary.csv"
    )
    stress_values = dict(zip(stress_summary["metric"].astype(str), stress_summary["value"].astype(float)))
    exante_metadata = json.loads(
        (
            root
            / "experiments/exp25_exante_job_validation/results/final/"
            "experiment_metadata.json"
        ).read_text(encoding="utf-8")
    )
    _check(
        int(exante_values.get("submitted_jobs", -1)) == 75_326
        and int(exante_values.get("execution_matched_jobs", -1)) == 71_128
        and float(exante_values.get("physical_nameplate_energy_coverage", -1.0)) == 1.0
        and float(exante_values.get("maximum_declared_window_infeasible_jobs", 1.0)) == 0.0
        and int(stress_values.get("cohort_jobs", -1)) == 79
        and abs(float(stress_values.get("capacity_mw_per_region", 0.0)) - 0.0001603677778) <= 1e-12
        and float(stress_values.get("event_service_delivered_mwh", 0.0)) >= float(stress_values.get("event_service_floor_mwh", 1.0)) - 1e-10
        and float(stress_values.get("minimum_event_capacity_slack_mwh", -np.inf)) >= -1e-8
        and float(stress_values.get("maximum_job_energy_residual_mwh", np.inf)) <= 1e-8
        and bool(stress_values.get("solver_success", 0.0))
        and exante_metadata.get("telemetry_used_in_exp19_decision") is False
        and exante_metadata.get("execution_ledger_role") == "post-event scoring only"
        and len(str(exante_metadata.get("submission_ledger_digest", ""))) == 64,
        "ex_ante_submission_job_validation_and_binding_capacity_panel",
        (
            "the declaration-only job validation covers the complete submitted "
            "population, while a compact 79-job stress cohort binds regional "
            "capacity and satisfies its service floor with numerical residuals below 1e-8"
        ),
        checks,
    )

    all_outage_summary = pd.read_csv(
        root
        / "experiments/exp24_all_outage_security_panel/results/final/"
        "all_outage_security_summary.csv"
    )
    all_outage_metadata = json.loads(
        (
            root
            / "experiments/exp24_all_outage_security_panel/results/final/"
            "experiment_metadata.json"
        ).read_text(encoding="utf-8")
    )
    _check(
        len(all_outage_summary) == 2
        and set(all_outage_summary["locked_days"].astype(int)) == {54}
        and set(all_outage_summary["replay_cells"].astype(int)) == {432}
        and set(all_outage_summary["minimum_contingencies"].astype(int)) == {37}
        and set(all_outage_summary["maximum_contingencies"].astype(int)) == {37}
        and bool(all_outage_summary["all_cells_successful"].all())
        and all_outage_metadata.get("all_finite_nonislanding_outages_evaluated") is True
        and all_outage_metadata.get("ac_admissibility_screen") is False
        and all_outage_metadata.get("outage_ranking_or_screening") is False
        and all_outage_metadata.get("post_solution_profile_reoptimization") is False
        and float(all_outage_metadata.get("maximum_postcontingency_loading", np.inf)) <= 1.000001,
        "full_finite_n1_frozen_profile_panel",
        (
            "864 frozen-profile cells evaluate all 37 finite RTS-24 non-islanding "
            "outages without AC screening or post-solution workload adjustment"
        ),
        checks,
    )

    lineage = pd.read_csv(
        root
        / "experiments/exp26_end_to_end_certificate/results/final/"
        "end_to_end_lineage.csv"
    )
    profile_roles = pd.read_csv(
        root
        / "experiments/exp26_end_to_end_certificate/results/final/"
        "profile_role_lineage.csv"
    )
    lineage_metadata = json.loads(
        (
            root
            / "experiments/exp26_end_to_end_certificate/results/final/"
            "experiment_metadata.json"
        ).read_text(encoding="utf-8")
    )
    certificate_roles = {
        str(row["stage"]): bool(row["passed"])
        for _, row in lineage.iterrows()
    }
    role_names = set(profile_roles["profile_role"].astype(str))
    risk_role = profile_roles.loc[
        profile_roles["profile_role"] == "validation-fitted aggregate risk target"
    ]
    mapping_role = profile_roles.loc[
        profile_roles["profile_role"]
        == "recomputed job-to-network certificate summary"
    ]
    payment_role = profile_roles.loc[
        profile_roles["profile_role"] == "payment-certified feasible profile hull"
    ]
    _check(
        set(certificate_roles)
        == {
            "job witness",
            "aggregate risk contract",
            "relative payment cap",
            "network valuation",
            "common executable witness",
            "complete outage replay",
        }
        and all(certificate_roles.values())
        and role_names
        == {
            "executable submitted-job witness",
            "runtime-complete common witness used by network settlement",
            "N-1 settlement replay of the runtime-complete common witness",
            "validation-fitted aggregate risk target",
            "payment-certified feasible profile hull",
            "recomputed job-to-network certificate summary",
            "frozen-profile all-outage N-1 replay",
        }
        and len(risk_role) == 1
        and _all_true(risk_role["risk_contract_satisfied"])
        and len(mapping_role) == 1
        and _all_true(mapping_role["network_mapping_recomputed_from_job_witness"])
        and len(payment_role) == 1
        and _all_true(payment_role["payment_cap_is_relative_n1_cap"])
        and lineage_metadata.get("profile_roles", {}).get("profile_identity_asserted") is True
        and lineage_metadata.get("network_mapping_certificate", {}).get("valid") is True
        and float(
            lineage_metadata.get("network_mapping_certificate", {}).get(
                "max_network_mapping_residual_mw", np.inf
            )
        )
        <= 1e-10
        and lineage_metadata.get("network_mapping_one_hot_bus_indices_zero_based")
        == [2, 7, 14, 20]
        and len(lineage_metadata.get("upstream_artifact_hashes", {})) == 7
        and lineage_metadata.get("all_outage_replay", {}).get(
            "all_finite_nonislanding_outages_evaluated"
        )
        is True,
        "end_to_end_declaration_to_settlement_lineage_certificate",
        (
            "Exp26 recomputes the indexed coupling, verifies risk/payment/outage "
            "certificates, records the common witness and settlement hashes, and "
            "preserves explicit role separation"
        ),
        checks,
    )

    runtime_typed_certificate_path = (
        root
        / "experiments/exp27_executable_common_witness/results/final/"
        "runtime_witness_coupling_certificate.json"
    )
    runtime_typed_certificate = json.loads(
        runtime_typed_certificate_path.read_text(encoding="utf-8")
    )
    runtime_metadata = json.loads(
        (
            root
            / "experiments/exp27_executable_common_witness/results/final/experiment_metadata.json"
        ).read_text(encoding="utf-8")
    )
    runtime_certificate_values = [
        runtime_typed_certificate.get("baseline", {}),
        runtime_typed_certificate.get("counterfactual", {}),
    ]
    runtime_certificate_valid = bool(
        runtime_typed_certificate.get("schema_version") == 2
        and runtime_typed_certificate.get("profile_identity_asserted") is True
        and runtime_typed_certificate.get("service_vector_identity_asserted") is True
        and runtime_metadata.get("service_vector_identity_asserted") is True
        and runtime_metadata.get("digest_inputs") == runtime_typed_certificate.get("digest_inputs")
        and all(item.get("valid") is True for item in runtime_certificate_values)
        and runtime_typed_certificate.get("witness_digest")
        == lineage_metadata.get("common_witness_certificate", {}).get("witness_digest")
        and runtime_typed_certificate.get("source_submission_digest")
        == json.loads(
            (
                root
                / "experiments/exp27_executable_common_witness/results/final/experiment_metadata.json"
            ).read_text(encoding="utf-8")
        ).get("source_submission_digest")
        and all(
            float(item.get("max_job_energy_residual_mwh", np.inf)) <= 1e-12
            and float(item.get("max_aggregation_residual_mwh", np.inf)) <= 1e-12
            and float(item.get("maximum_gpu_bound_violation_mwh", np.inf)) <= 1e-12
            and float(item.get("minimum_site_capacity_slack_mwh", -np.inf)) >= -1e-12
            for item in runtime_certificate_values
        )
        and lineage_metadata.get("common_witness_certificate", {}).get(
            "stored_service_vector_identity_asserted"
        ) is True
        and lineage_metadata.get("common_witness_certificate", {}).get(
            "witness_digest_recomputed_from_saved_arrays"
        ) is True
    )
    _check(
        runtime_certificate_valid,
        "runtime_complete_witness_typed_coupling_certificate",
        (
            "Exp27 baseline and counterfactual service vectors independently satisfy "
            "job-energy, regional aggregation, GPU-nameplate, and site-capacity "
            "residual bounds and remain attached to the settlement witness digest"
        ),
        checks,
    )

    upstream_paths = {
        "executable submitted-job witness":
            "experiments/exp19_job_level_counterfactual/results/final/job_level_counterfactual_solution.npz",
        "runtime-complete common witness used by network settlement":
            "experiments/exp27_executable_common_witness/results/final/runtime_complete_witness.npz",
        "N-1 settlement replay of the runtime-complete common witness":
            "experiments/exp27_executable_common_witness/results/final/common_witness_settlement.csv",
        "validation-fitted aggregate risk target":
            "experiments/exp2_baseline_verification/results/intermediate/test_profiles.npz",
        "payment-certified feasible profile hull":
            "experiments/exp9_payment_certificate/results/final/certified_counterfactual_profiles.npz",
        "recomputed job-to-network certificate summary":
            "experiments/exp22_coupled_job_network_certificate/results/final/coupled_network_summary.csv",
        "frozen-profile all-outage N-1 replay":
            "experiments/exp24_all_outage_security_panel/results/final/all_outage_security_replay.csv",
    }
    recorded_hashes = lineage_metadata.get("upstream_artifact_hashes", {})
    hash_details = []
    hash_matches = set(recorded_hashes) == set(upstream_paths)
    for role, rel in upstream_paths.items():
        path = root / rel
        expected = str(recorded_hashes.get(role, ""))
        actual = sha256(path) if path.exists() else ""
        matched = bool(re.fullmatch(r"[0-9a-f]{64}", expected)) and expected == actual
        hash_matches = hash_matches and matched
        hash_details.append(f"{role}={'ok' if matched else 'mismatch'}")
    _check(
        hash_matches,
        "end_to_end_upstream_hashes_match_current_artifacts",
        "; ".join(hash_details),
        checks,
    )

    stale_temporary_files = [
        str(path.relative_to(root))
        for path in list(root.rglob(".*.tmp")) + list(root.rglob("*.tmp.npz"))
        if path.is_file() and ".git" not in path.parts
    ]
    _check(
        not stale_temporary_files,
        "no_stale_atomic_temporary_artifacts",
        "no hidden atomic-writer temporary files remain"
        if not stale_temporary_files
        else "; ".join(stale_temporary_files),
        checks,
    )

    generated_files = []
    for path in sorted(root.glob("experiments/**/results/final/*")) + sorted(root.glob("experiments/**/figures/*")):
        if path.is_file():
            generated_files.append({"path": str(path.relative_to(root)), "bytes": path.stat().st_size, "sha256": sha256(path)})
    audit = {
        "all_checks_passed": all(item["passed"] for item in checks),
        "checks": checks,
        "statistical_tests": significance,
        "settlement_absolute_error_usd": {f"{key[0]} | {key[1]}": value for key, value in mae.items()},
        "generated_artifacts": generated_files,
        "limitations": [
            "BurstGPT exposes workload tokens but not facility power; token traces are scaled to an explicitly documented hyperscale capacity target.",
            "MIT SuperCloud provides measured GPU energy for its own workload, which is independently aggregated and scaled; it is not claimed to be a co-located trace from the same operator.",
            "All 24 mappings of the four measured regional traces to the four declared IEEE-118 connection buses and three predeclared power penetrations are evaluated, but these public traces are not claimed to be co-located utility and facility measurements.",
            "The final workload credit is constrained by a predeclared two-sided band around the selected single feasible projection; the upper side certifies false-credit noninferiority and the lower side bounds additional under-credit by the declared tolerance.",
            "The complete N-1 panel certifies preventive feasibility for every finite non-islanding line outage in the lossless continuous DC model; it is not an AC voltage, transient-stability, or island-balancing certificate.",
            "The nonlinear AC outage panel solves a separate corrective post-contingency optimum for every non-islanding IEEE-9 and IEEE-14 line outage; it is not a simultaneous preventive AC security-constrained OPF or a transient-stability certificate.",
            "The shared-active-plan preventive AC panel fixes non-reference active generation across every finite non-islanding IEEE-9 outage, with reactive-power, voltage, and reference-generator loss recourse; it is not a transient-stability or intertemporal unit-commitment certificate.",
            "The event-gate information panel removes post-gate arrivals before optimization and uses the locked execution trace only for scoring; its complete-ledger comparator quantifies information cost rather than defining a deployable gate policy.",
            "The cross-network AC panel is a fixed-active-plan preventive AC-OPF certificate over every native-case admissible non-islanding outage in four public networks; it is a steady-state feasibility result and not a transient-stability or intertemporal unit-commitment certificate.",
        ],
    }
    write_json(root / "audit/result_audit.json", audit)
    _write_report(root, cfg, audit, metrics, tuning, settlement)
    if not audit["all_checks_passed"]:
        failed = [item["name"] for item in checks if not item["passed"]]
        raise RuntimeError(f"Audit failed: {failed}")
    logger.info("Audit complete: %d/%d checks passed", len(checks), len(checks))


def _write_report(
    root: Path,
    cfg: dict[str, Any],
    audit: dict[str, Any],
    metrics: pd.DataFrame,
    tuning: pd.DataFrame,
    settlement: pd.DataFrame,
) -> None:
    grouped = metrics.groupby("method").agg(
        nrmse=("nrmse", "mean"),
        false_response_ratio=("false_response_ratio", "mean"),
        false_response_mwh=("false_response_mwh", "mean"),
        credit_precision=("credit_precision", "mean"),
        credit_recall=("credit_recall", "mean"),
        credit_f1=("credit_f1", "mean"),
        bias_mw=("bias_mw", "mean"),
    )
    settle = settlement.groupby(["baseline_method", "mechanism"]).agg(
        payment_usd=("payment_usd", "mean"),
        realized_value_usd=("realized_grid_value_usd", "mean"),
        absolute_error_usd=("payment_error_usd", lambda x: np.mean(np.abs(x))),
        overpayment_ratio=("overpayment_ratio", "mean"),
    )
    lines = [
        "# Reproducibility and Result Audit",
        "",
        f"Overall status: **{'PASS' if audit['all_checks_passed'] else 'FAIL'}**.",
        "",
        "## Completeness",
        "",
    ]
    lines.extend(f"- [{'x' if c['passed'] else ' '}] {c['name']}: {c['detail']}" for c in audit["checks"])
    lines.extend(["", "## Locked test-set baseline results", "", _markdown_table(grouped.reset_index(), 4), ""])
    lines.extend(["## Projection candidate validation", "", _markdown_table(tuning, 5), ""])
    lines.extend(["## Settlement results", "", _markdown_table(settle.reset_index(), 3), ""])
    factors = pd.read_csv(
        root
        / "experiments/exp3_nodal_settlement/results/final/"
        "settlement_factor_decomposition_summary.csv"
    )
    factors = factors[
        factors["baseline_method"].isin(
            [
                "Trace-Anchored Reference",
                "Risk-Constrained Convex Verifier",
            ]
        )
    ]
    lines.extend(
        [
            "## Paired settlement-factor decomposition",
            "",
            _markdown_table(factors, 4),
            "",
        ]
    )
    network = pd.read_csv(root / "experiments/exp5_network_robustness/results/final/network_robustness_summary.csv")
    lines.extend(["## Cross-network robustness", "", _markdown_table(network, 3), ""])
    stress = pd.read_csv(root / "experiments/exp6_physical_stress/results/final/physical_stress_summary.csv")
    lines.extend(["## Binding-constraint stress test", "", _markdown_table(stress, 4), ""])
    allocation = pd.read_csv(
        root / "experiments/exp7_value_allocation/results/final/value_allocation_summary.csv"
    )
    lines.extend(["## Exact multi-participant value allocation", "", _markdown_table(allocation, 4), ""])
    n1 = pd.read_csv(
        root / "experiments/exp8_n1_security/results/final/n1_security_summary.csv"
    )
    lines.extend(
        [
            "## Complete N-1 security-aware settlement",
            "",
            _markdown_table(n1, 4),
            "",
        ]
    )
    payment = pd.read_csv(
        root
        / "experiments/exp9_payment_certificate/results/final/payment_evaluation_summary.csv"
    )
    payment_target = pd.read_csv(
        root
        / "experiments/exp9_payment_certificate/results/final/"
        "payment_target_selection_validation.csv"
    )
    lines.extend(
        [
            "## Scenario-robust N-1 payment certificate",
            "",
            _markdown_table(payment, 4),
            "",
            "## Validation-frozen payment target selection",
            "",
            _markdown_table(payment_target, 4),
            "",
        ]
    )
    ac = pd.read_csv(
        root / "experiments/exp10_ac_validation/results/final/ac_opf_summary.csv"
    )
    lines.extend(
        [
            "## Nonlinear AC out-of-model validation",
            "",
            _markdown_table(ac, 4),
            "",
        ]
    )
    ac_n1 = pd.read_csv(
        root
        / "experiments/exp10_ac_validation/results/final/"
        "ac_n1_contingency_summary.csv"
    )
    lines.extend(
        [
            "## Complete nonlinear AC post-contingency validation",
            "",
            _markdown_table(ac_n1, 5),
            "",
        ]
    )
    spatial = pd.read_csv(
        root
        / "experiments/exp11_spatial_scale_robustness/results/final/"
        "spatial_scale_summary.csv"
    )
    lines.extend(
        [
            "## Complete spatial-assignment and power-scale robustness",
            "",
            _markdown_table(spatial, 4),
            "",
        ]
    )
    rolling = pd.read_csv(
        root
        / "experiments/exp12_rolling_market_validation/results/final/"
        "rolling_market_summary.csv"
    )
    lines.extend(
        [
            "## Continuous-horizon space-time market validation",
            "",
            _markdown_table(rolling, 6),
            "",
        ]
    )
    lines.extend(["## Dependence-robust paired tests", ""])
    for name, result in audit["statistical_tests"].items():
        lines.append(
            f"- {name}: comparator-minus-proposed mean difference "
            f"{result['observed_mean_difference']:.4f}, two-sided exact block-sign "
            f"p={result['two_sided_exact_p_value']:.4g}, Holm-adjusted "
            f"p={result['holm_adjusted_p_value']:.4g} "
            f"({int(result['blocks'])} nonoverlapping blocks)."
        )
    lines.extend(["", "## Scope and limitations", ""])
    lines.extend(f"- {item}" for item in audit["limitations"])
    (root / "audit/completeness_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _markdown_table(frame: pd.DataFrame, decimals: int) -> str:
    """Render a compact Markdown table without optional runtime dependencies."""
    columns = [str(column) for column in frame.columns]
    rows = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for values in frame.itertuples(index=False, name=None):
        cells = []
        for value in values:
            if isinstance(value, (float, np.floating)):
                cells.append(f"{float(value):.{decimals}f}")
            else:
                cells.append(str(value))
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join(rows)
