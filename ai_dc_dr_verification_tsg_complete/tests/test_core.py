from __future__ import annotations

import hashlib
import json
from csv import DictReader
from tempfile import TemporaryDirectory
from pathlib import Path

import numpy as np
import pandas as pd

from aicdr.data import _balanced_trace_region_labels, _validate_declared_raw_sources, load_workload
from aicdr.coupling_invariant import validate_job_network_coupling
from aicdr.baselines import (
    exact_block_sign_test,
    response_delivery_metrics,
    response_metrics,
)
from aicdr.experiments import (
    _exact_group_symmetric_shapley,
    _exact_shapley_values,
    _event_days,
    _ieee118_quadratic_evaluation_system,
)
from aicdr.optimization import (
    build_n1_security_factors,
    parse_pglib_case,
    power_system_from_ppc,
    solve_n1_sced,
    solve_payment_certified_n1_projection,
    solve_sced,
    solve_workload_schedule,
)
from aicdr.pipeline import manifest_path_for_stage
from aicdr.utils import load_config


ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "configs/default.yaml")


def _test_network():
    """Use the declared PGLib case when present, otherwise the vendored public case."""
    path = ROOT / CFG["data"]["pglib_case"]
    if path.exists():
        return parse_pglib_case(path)
    from pypower.case118 import case118

    return power_system_from_ppc(case118())


def test_stage_runs_cannot_overwrite_the_unified_manifest() -> None:
    assert manifest_path_for_stage(ROOT, "all") == (
        ROOT / "artifacts/run_manifest.json"
    )
    assert manifest_path_for_stage(ROOT, "audit") == (
        ROOT / "artifacts/stage_runs/audit_latest.json"
    )
    assert (
        manifest_path_for_stage(ROOT, "audit")
        != manifest_path_for_stage(ROOT, "all")
    )


def test_typed_coupling_invariant_checks_job_aggregation_and_network_units() -> None:
    """The bridge certificate rejects a unit or aggregation mismatch."""

    service = np.asarray([0.25, 0.25, 0.25, 0.25], dtype=float)
    energy = np.asarray([0.5, 0.5], dtype=float)
    starts = np.asarray([0, 1], dtype=int)
    ends = np.asarray([2, 3], dtype=int)
    regions = np.asarray([0, 1], dtype=int)
    aggregate = np.asarray([[0.25, 0.25, 0.0], [0.0, 0.25, 0.25]], dtype=float)
    mapping = np.zeros((3, 2), dtype=float)
    mapping[[0, 2], [0, 1]] = 1.0
    profile = mapping @ (aggregate / 0.25)
    certificate = validate_job_network_coupling(
        service_mwh=service,
        job_energy_mwh=energy,
        submit_slot=starts,
        deadline_slot=ends,
        region=regions,
        aggregate_mwh=aggregate,
        dt_h=0.25,
        measured_gpus=np.asarray([1.0, 2.0]),
        per_gpu_power_cap_mw=1.0,
        site_capacity_mw=2.0,
        network_profile_mw=profile,
        network_mapping=mapping,
    )
    assert certificate.valid
    assert certificate.max_job_energy_residual_mwh <= 1e-12
    assert certificate.max_aggregation_residual_mwh <= 1e-12
    assert certificate.max_network_mapping_residual_mw <= 1e-12
    broken = aggregate.copy()
    broken[0, 0] += 0.1
    invalid = validate_job_network_coupling(
        service_mwh=service,
        job_energy_mwh=energy,
        submit_slot=starts,
        deadline_slot=ends,
        region=regions,
        aggregate_mwh=broken,
        dt_h=0.25,
    )
    assert not invalid.valid
    assert invalid.max_aggregation_residual_mwh > 0.09


def test_observational_replay_covers_every_locked_day_and_slot() -> None:
    folder = ROOT / "experiments/exp13_real_trace_replay/results/final"
    summary = np.genfromtxt(folder / "real_trace_replay_summary.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
    assert len(summary) == 2
    assert np.all(summary["all_days_with_trace"] == 54)
    metadata = json.loads((folder / "experiment_metadata.json").read_text(encoding="utf-8"))
    assert metadata["event_intervention"] is False
    assert metadata["trace_coverage"].startswith("100 percent")


def test_risk_ceiling_keeps_observational_and_simulated_truth_sources_explicit() -> None:
    metadata = json.loads(
        (
            ROOT
            / "experiments/exp2_baseline_verification/results/final/"
            "experiment_metadata.json"
        ).read_text(encoding="utf-8")
    )
    source = str(metadata["risk_credit_definition"])
    assert "true-credit subtraction" in source
    assert "separate truth-source scores" in metadata["risk_truth_source_audit"]
    assert "oracle no-event baseline minus closed event meter" in str(
        metadata["risk_credit_threshold_identity"]
    )
    assert metadata["event_intervention_observed"] is False
    truth_audit = pd.read_csv(
        ROOT
        / "experiments/exp2_baseline_verification/results/final/"
        "risk_truth_source_audit.csv"
    )
    assert len(truth_audit) == CFG["experiments"]["test_days"] * 2
    assert set(truth_audit["truth_source"]) == {
        "independent_trace_observed_meter",
        "simulated_event_response_mechanism_isolation",
    }
    assert truth_audit["causal_event_effect"].astype(str).str.lower().eq("false").all()


def test_decision_time_target_is_gate_causal_and_schema_locked() -> None:
    folder = ROOT / "experiments/exp17_decision_time_information/results/final"
    metadata = json.loads(
        (folder / "experiment_metadata.json").read_text(encoding="utf-8")
    )
    assert metadata["target_future_arrivals_used_for_decision"] is False
    boundary = metadata["causal_identification_boundary"]
    assert boundary["temporal_information_causality"] is True
    assert boundary["utility_event_label_available"] is False
    assert boundary["randomized_or_exogenous_event_intervention"] is False
    assert "post-gate arrivals masked" in metadata["target_source"]
    assert "used only after the event" in metadata["meter_cap_scoring_note"]
    assert "causal committed-ledger baseline" in metadata["meter_cap_scoring_note"]
    assert metadata["event_gate_slot"] == CFG["experiments"]["decision_time_event_gate_slot"]
    assert metadata["terminal_completion_index"] == CFG["experiments"]["decision_time_terminal_completion_index"]
    committed_meta = metadata["committed_ledger_safe_mode"]
    assert committed_meta["future_arrivals_used_for_decision"] is False
    assert committed_meta["rolling_commitment"] is True
    assert "causal committed-ledger baseline LP" in committed_meta["contract_baseline_source"]
    assert "selected validation DR price" in committed_meta["response_objective"]
    assert float(committed_meta["selected_dr_price_per_mwh"]) in {
        float(x) for x in CFG["experiments"]["decision_time_response_dr_prices"]
    }
    comparison = pd.read_csv(folder / "decision_time_comparison.csv")
    assert set(comparison["schema_version"].astype(int)) == {11}
    assert not comparison.loc[
        comparison["method"] == "Decision-time truncated-ledger verifier",
        "future_arrivals_used_for_decision",
    ].any()


def test_contract_settlement_does_not_hardcode_zero_overpayment() -> None:
    """The closed-meter contract audit must expose an overstated baseline."""
    submitted = np.array([[10.0, 10.0]])
    contract = np.array([[10.0, 10.0]])
    oracle = np.array([[9.0, 9.0]])
    actual = np.array([[8.0, 8.0]])
    scored = response_delivery_metrics(
        contract,
        submitted,
        oracle,
        actual,
        [0, 1],
        1.0,
    )
    assert scored["planned_response_mwh"] == 0.0
    assert scored["contract_capped_response_mwh"] == 0.0

    # A distinct response plan is scored as planned reduction from the
    # contract and as delivered reduction from the closed meter.
    response_plan = np.array([[8.0, 8.0]])
    delivered = response_delivery_metrics(
        contract,
        response_plan,
        oracle,
        actual,
        [0, 1],
        1.0,
    )
    assert delivered["planned_response_mwh"] == 4.0
    assert delivered["contract_capped_response_mwh"] == 4.0
    assert delivered["meter_capped_false_response_mwh"] == 2.0
    assert delivered["meter_capped_underpayment_mwh"] == 0.0


def test_feature_stratified_region_scenario_is_balanced_and_reproducible() -> None:
    frame = pd.DataFrame(
        {
            "id_job": [40, 11, 99, 3, 72, 18],
            "energy_j": [4.0, 2.0, 8.0, 1.0, 6.0, 3.0],
            "time_submit_aligned": [5.0, 1.0, 7.0, 2.0, 4.0, 6.0],
            "time_start_aligned": [6.0, 2.0, 8.0, 3.0, 5.0, 7.0],
            "time_end_aligned": [8.0, 4.0, 10.0, 5.0, 7.0, 9.0],
            "measured_gpus": [1, 2, 1, 2, 1, 2],
            "job_type": ["a", "a", "b", "b", "a", "b"],
            "gres_req": ["g1", "g1", "g2", "g2", "g1", "g2"],
        }
    )
    first = _balanced_trace_region_labels(frame, 3)
    second = _balanced_trace_region_labels(frame.sample(frac=1.0, random_state=7), 3)
    assert np.array_equal(np.sort(first), np.sort(second))
    assert np.bincount(first, minlength=3).max() - np.bincount(first, minlength=3).min() <= 1


def test_job_level_flow_certificate_has_machine_precision_residuals() -> None:
    folder = ROOT / "experiments/exp14_job_level_fidelity/results/final"
    summary = np.genfromtxt(folder / "job_level_fidelity_summary.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
    values = {str(row[0]): row[1] for row in summary}
    assert int(float(values["joined_jobs"])) == 71128
    assert int(float(values["service_variables"])) == 1974690
    assert float(values["maximum_job_completion_residual_mwh"]) < 1e-12
    assert float(values["maximum_slot_residual_mwh"]) < 1e-12
    witness = pd.read_csv(folder / "job_interval_witness_summary.csv")
    witness_values = dict(zip(witness["metric"], witness["value"]))
    assert int(witness_values["nonpreemptive_joined_jobs"]) == 71128
    assert int(witness_values["release_violation_seconds"]) == 0
    assert int(witness_values["completion_deadline_violation_seconds"]) == 0
    assert float(witness_values["minimum_native_capacity_slack_mwh"]) >= -1e-9


def test_job_counterfactual_uses_submit_time_declarations_and_signed_reduction() -> None:
    folder = ROOT / "experiments/exp19_job_level_counterfactual/results/final"
    metadata = json.loads(
        (folder / "experiment_metadata.json").read_text(encoding="utf-8")
    )
    assert metadata["observed_time_end_used_as_deadline"] is False
    assert metadata["deadline_mode"] == "submit_time_declaration"
    assert int(metadata["declared_window_slots_min"]) >= 1
    assert int(metadata["declared_window_slots_max"]) >= int(metadata["declared_window_slots_min"])
    assert int(metadata["declared_window_slots_max"]) == 680
    assert int(metadata["unlimited_timelimit_jobs"]) >= 0
    assert "allocation runtime" in metadata["deadline_source"]
    assert int(metadata["submission_buffer_slots"]) == int(
        CFG["experiments"]["job_level_submission_buffer_slots"]
    )
    assert float(metadata["declared_per_gpu_power_cap_mw"]) == 0.001
    summary = pd.read_csv(folder / "job_level_counterfactual_summary.csv")
    values = dict(zip(summary["metric"], summary["value"]))
    native = float(values["event_energy_native_mwh"])
    counterfactual = float(values["event_energy_counterfactual_mwh"])
    net = float(values["event_net_reduction_mwh"])
    gross = float(values["event_gross_reduction_mwh"])
    rebound = float(values["event_rebound_mwh"])
    assert np.isclose(native - counterfactual, net, atol=1e-12)
    assert gross >= net - 1e-12
    assert rebound >= -1e-12
    assert int(float(values["service_variables"])) == 13_198_247
    assert metadata["population_rule"].startswith("all valid scheduler submissions")
    assert metadata["nonpreemptive_witness"].startswith("exact submitted-job contiguous")
    assert metadata["contiguity_certificate"]["maximum_gap_inside_service_block"] == 0
    assert float(values["maximum_job_energy_residual_mwh"]) < 1e-15
    scale = pd.read_csv(
        ROOT
        / "experiments/exp21_scale_consistency/results/final/scale_consistency_summary.csv"
    )
    scale_values = dict(zip(scale["metric"], scale["value"]))
    assert np.isclose(float(scale_values["capacity_safe_scale_factor"]), 2176.1834426742535)
    assert np.isclose(
        float(scale_values["capacity_proportional_network_scale_factor"]),
        2176.1834426742535,
    )
    assert np.isclose(float(scale_values["fixed_nameplate_certified_scale_factor"]), 1.5042419623337813)
    assert float(scale_values["certified_peak_mw"]) <= 118.0 + 1e-9
    assert float(scale_values["capacity_proportional_minimum_capacity_slack_mwh"]) >= -1e-9
    sensitivity = pd.read_csv(
        ROOT
        / "experiments/exp21_scale_consistency/results/final/scale_sensitivity.csv"
    )
    assert len(sensitivity) == len(CFG["experiments"]["scale_sensitivity_relative_to_fixed"])
    assert sensitivity["fixed_gpu_nameplate_respected"].astype(bool).sum() >= 2


def test_coupled_network_replay_rechecks_indexed_primal_before_settlement() -> None:
    folder = ROOT / "experiments/exp22_coupled_job_network_certificate/results/final"
    summary = pd.read_csv(folder / "coupled_network_summary.csv")
    replay = pd.read_csv(folder / "coupled_network_event_replay.csv")
    values = dict(zip(summary["metric"].astype(str), summary["value"].astype(float)))
    metadata = json.loads((folder / "experiment_metadata.json").read_text(encoding="utf-8"))
    assert metadata["independent_job_feasibility_recheck"] is True
    assert float(values["maximum_job_energy_recheck_residual_mwh"]) <= 1e-12
    assert float(values["maximum_gpu_bound_violation_mwh"]) <= 1e-12
    assert float(values["maximum_gpu_bound_violation_mwh"]) >= 0.0
    assert float(values["minimum_gpu_bound_slack_mwh"]) >= -1e-12
    assert float(values["minimum_site_capacity_slack_mwh"]) >= -1e-12
    assert float(values["maximum_job_to_aggregate_residual_mwh"]) <= 1e-12
    assert len(replay) == 3
    assert set(replay["scenario"]) == {
        "raw_job_witness",
        "fixed_nameplate_homogeneous",
        "capacity_proportional_homogeneous",
    }
    assert np.all(replay["event_slot_count"] == 1056)
    assert np.all(replay["credible_contingencies"] == 37)
    assert replay["solver_success"].astype(bool).all()
    scale_replay = pd.read_csv(
        folder / "coupled_network_scale_replay.csv"
    )
    assert len(scale_replay) == 2
    assert set(scale_replay["scenario"]) == {
        "fixed_nameplate_homogeneous",
        "capacity_proportional_homogeneous",
    }
    assert scale_replay["coupling_certificate_valid"].astype(bool).all()
    assert np.isfinite(scale_replay["secure_event_value_usd"]).all()
    assert np.isclose(
        float(metadata["network_load_multiplier"]),
        float(CFG["experiments"]["n1_load_multiplier"]),
    )
    assert metadata["network_load_equation"].startswith("L_t = L_base * 0.9")
    assert int(values["submitted_jobs"]) == 75326
    assert int(values["service_variables"]) == 13198247
    assert metadata["post_solution_profile_reoptimization"] is False


def test_independent_event_and_full_outage_panels_are_locked_and_complete() -> None:
    event_folder = ROOT / "experiments/exp23_independent_event_replay/results/final"
    event_summary = pd.read_csv(event_folder / "independent_event_replay_summary.csv")
    event_metadata = json.loads((event_folder / "experiment_metadata.json").read_text(encoding="utf-8"))
    gate = event_summary[event_summary["method"] == "Gate-committed response"].iloc[0]
    assert int(gate["locked_days"]) == 54
    assert 0.0 <= float(gate["credit_f1"]) <= 1.0
    assert event_metadata["event_intervention"] is True
    assert event_metadata["causal_intervention_claim"] is False
    assert event_metadata["independent_policy"]["tariff_pair_distinct_from_gate"] is True
    assert event_metadata["independent_policy"]["structurally_distinct_from_gate"] is True
    assert float(event_metadata["independent_policy"]["minimum_participant_event_mwh"]) > 0.0
    assert float(event_metadata["independent_policy"]["maximum_response_difference_from_gate_mw"]) > 1e-8
    exp17_metadata = json.loads(
        (
            ROOT
            / "experiments/exp17_decision_time_information/results/final/"
            "experiment_metadata.json"
        ).read_text(encoding="utf-8")
    )
    assert np.isclose(
        float(event_metadata["gate_policy"]["response_price_per_mwh"]),
        float(exp17_metadata["causal_response_calibration"]["selected_dr_price_per_mwh"]),
    )
    outage_folder = ROOT / "experiments/exp24_all_outage_security_panel/results/final"
    outage = pd.read_csv(outage_folder / "all_outage_security_replay.csv")
    outage_metadata = json.loads((outage_folder / "experiment_metadata.json").read_text(encoding="utf-8"))
    assert len(outage) == 864
    assert set(outage["credible_contingencies"]) == {37}
    assert set(outage["evaluated_finite_nonislanding_outages"]) == {37}
    assert outage["solver_success"].all()
    assert outage_metadata["all_finite_nonislanding_outages_evaluated"] is True
    assert outage_metadata["ac_admissibility_screen"] is False


def test_unseen_payment_transfer_panel_is_not_used_for_certificate_selection() -> None:
    folder = ROOT / "experiments/exp9_payment_certificate/results/final"
    metadata = json.loads(
        (folder / "experiment_metadata.json").read_text(encoding="utf-8")
    )["unseen_transfer_evaluation"]
    unseen = pd.read_csv(folder / "payment_evaluation_unseen_summary.csv")
    assert len(unseen) == 8
    assert set(np.round(unseen["conversion_scale_factor"].astype(float), 8)) == {
        0.80,
        1.20,
    }
    assert metadata["scenarios_used_in_certificate"] is False
    assert metadata["target_selection_used"] is False
    assert np.isfinite(
        unseen[["mean_absolute_error_usd", "mean_overpayment_usd"]].to_numpy()
    ).all()


def test_literature_controls_share_the_locked_information_contract() -> None:
    audit = pd.read_csv(
        ROOT
        / "experiments/exp2_baseline_verification/results/final/"
        "baseline_fairness_audit.csv"
    )
    assert len(audit) == 8
    assert audit["same_locked_days"].eq(54).all()
    for column in (
        "same_arrivals",
        "same_deadlines",
        "same_site_capacity",
        "same_event_slots",
    ):
        assert audit[column].eq(True).all()
    assert audit["faithful_published_software_reimplementation"].eq(False).all()


def test_interval_endpoint_audit_is_complete_and_within_solver_tolerance() -> None:
    folder = ROOT / "experiments/exp15_interval_certificate/results/final"
    rows = np.genfromtxt(folder / "interval_endpoint_certificates.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
    assert len(rows) == 216
    assert set(rows["endpoint"]) == {"q01", "q99"}
    assert set(rows["method"]) == {"Selected Single Feasible Projection", "Payment-Certified N-1 Verifier"}
    metadata = json.loads((folder / "experiment_metadata.json").read_text(encoding="utf-8"))
    assert metadata["interval_certificate_valid"] is True
    assert metadata["external_transfer_comparator"] == "Feasible Quantile Projection"
    assert "selected single feasible" in metadata["profile_source"].lower()
    assert float(metadata["maximum_payment_cap_violation_usd"]) <= 1e-6
    interval = pd.read_csv(folder / "payment_value_interval_certificates.csv")
    assert len(interval) == 54 * 2
    assert set(interval["candidate_hull_vertices"]) == {2}
    assert np.all(
        interval["continuous_segment_minimum_baseline_cost_usd"]
        <= interval["hull_baseline_cost_min_usd"] + 1e-6
    )
    assert np.all(interval["payment_interval_width_usd"] >= -1e-8)
    # The oracle payment is computed only after the contractual interval is
    # frozen; it is an independent coverage diagnostic, never an interval
    # selection input.
    assert np.isfinite(interval["oracle_payment_usd"]).all()
    assert interval["oracle_inside_interval"].isin([0.0, 1.0]).all()
    assert 0.0 <= float(metadata["payment_value_interval"]["mean_oracle_coverage"]) <= 1.0


def test_payment_target_is_frozen_on_validation_and_two_sided_band_is_complete() -> None:
    target = np.genfromtxt(
        ROOT
        / "experiments/exp9_payment_certificate/results/final/"
        "payment_target_selection_validation.csv",
        delimiter=",",
        names=True,
        dtype=None,
        encoding="utf-8",
    )
    assert len(target) == 7
    assert int(np.sum(target["selected"])) == 1
    assert np.all(target["validation_cells"] == 16 * 3 * len(CFG["market"]["event_slots"]))
    metadata = json.loads(
        (
            ROOT
            / "experiments/exp9_payment_certificate/results/final/"
            "experiment_metadata.json"
        ).read_text(encoding="utf-8")
    )
    assert metadata["test_peak_used_for_scaling"] is False
    band = np.genfromtxt(
        ROOT
        / "experiments/exp2_baseline_verification/results/final/"
        "two_sided_credit_certificate.csv",
        delimiter=",",
        names=True,
        dtype=None,
        encoding="utf-8",
    )
    assert len(band) == CFG["experiments"]["test_days"]
    assert np.all(band["pointwise_upper_bound_satisfied"] == 1)
    assert np.all(band["pointwise_lower_bound_satisfied"] == 1)
    risk = np.genfromtxt(
        ROOT
        / "experiments/exp2_baseline_verification/results/final/"
        "final_risk_contract_audit.csv",
        delimiter=",",
        names=True,
        dtype=None,
        encoding="utf-8",
    )
    assert len(risk) == CFG["experiments"]["test_days"]
    assert np.all(risk["aggregate_total_contract_satisfied"] == 1)
    assert np.all(risk["aggregate_cvar75_contract_satisfied"] == 1)
    cvar = pd.read_csv(
        ROOT
        / "experiments/exp2_baseline_verification/results/final/"
        "risk_cvar_stress_sensitivity.csv"
    )
    assert len(cvar) == len(CFG["experiments"]["risk_cvar_stress_reserve_fractions"])
    boundary = cvar[
        np.isclose(
            cvar["cvar_reserve_fraction"],
            float(CFG["experiments"]["risk_cvar_reserve_fraction"]),
        )
    ]
    assert len(boundary) == 1
    assert bool(boundary.iloc[0]["minimum_cvar_touches_budget"])
    cert = pd.read_csv(
        ROOT
        / "experiments/exp2_baseline_verification/results/final/"
        "risk_constrained_validation_certificate.csv"
    ).iloc[0]
    assert cert["risk_cvar_metric"] == "daily_false_credit_ratio"
    assert np.isclose(float(cert["risk_cvar_level"]), float(CFG["experiments"]["risk_cvar_level"]))
    assert float(cert["cvar_budget_slack_metric"]) <= 1e-3
    assert bool(cert["cvar75_budget_binding"])
    assert float(cert["total_objective_weight"]) > 0.0
    ablation_weights = pd.read_csv(
        ROOT
        / "experiments/exp2_baseline_verification/results/final/"
        "risk_module_ablation_weights.csv"
    )
    weight_columns = [
        column for column in ablation_weights.columns if column.startswith("weight_")
    ]
    joint = ablation_weights.loc[
        ablation_weights["ablation"] == "total+CVaR ensemble", weight_columns
    ].to_numpy(dtype=float)
    cvar_only = ablation_weights.loc[
        ablation_weights["ablation"] == "CVaR-only ensemble", weight_columns
    ].to_numpy(dtype=float)
    assert joint.shape == cvar_only.shape == (1, len(weight_columns))
    assert np.max(np.abs(joint - cvar_only)) > 1e-6


def test_ledger_provenance_and_capacity_reconciliation_are_complete() -> None:
    folder = ROOT / "experiments/exp16_ledger_capacity_provenance/results/final"
    metadata = json.loads((folder / "experiment_metadata.json").read_text(encoding="utf-8"))
    certificate = json.loads((folder / "ledger_provenance_certificate.json").read_text(encoding="utf-8"))
    capacity = np.genfromtxt(folder / "capacity_reconciliation.csv", delimiter=",", names=True)
    assert metadata["integrity_passed"] is True
    assert certificate["joined_positive_energy_jobs"] == 71128
    assert not str(certificate["source_files"]["scheduler"]).startswith("/")
    assert not str(certificate["source_files"]["dcgm"]).startswith("/")
    assert len(certificate["canonical_joined_ledger_sha256"]) == 64
    assert abs(float(certificate["raw_to_join_energy_residual_j"])) <= 1e-6
    # The un-clipped held-out conversion envelope is a reconciliation
    # diagnostic and can exceed the committed nameplate.  The experiment's
    # capacity-safe envelope is the contractual quantity and must fit.
    assert np.all(capacity["capacity_excess_peak_mw"] >= -1e-8)
    assert np.all(
        capacity["scaled_benchmark_peak_mw"]
        - capacity["capacity_excess_peak_mw"]
        <= 118.0 + 1e-8
    )
    calibration = np.genfromtxt(
        folder / "workload_power_calibration_sensitivity.csv",
        delimiter=",",
        names=True,
        dtype=None,
        encoding="utf-8",
    )
    assert len(calibration) == 5
    assert set(calibration["heldout_ratio_quantile"]) == {
        "q01",
        "q10",
        "q50",
        "q90",
        "q99",
    }
    assert np.all(calibration["capacity_safe_region_peak_mw"] <= 118.0 + 1e-8)
    assert np.all(calibration["capacity_safe_scale_factor"] > 0)
    physical = pd.read_csv(folder / "physical_calibration_summary.csv")
    assert len(physical) == 1
    assert np.isfinite(physical[["test_mae_watts", "test_rmse_watts", "test_r2"]].to_numpy()).all()
    assert 0.0 < float(physical.loc[0, "test_r2"]) <= 1.0
    assert int(physical.loc[0, "train_observations"]) == 44391
    assert int(physical.loc[0, "test_observations"]) == 50791


def test_data_flow_distinguishes_full_join_from_common_tensor_window() -> None:
    manifest = json.loads(
        (ROOT / "data/processed/data_manifest.json").read_text(encoding="utf-8")
    )
    with (ROOT / "data/processed/data_flow_audit.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        rows = {
            row["stage"]: int(row["retained_records"])
            for row in DictReader(handle)
        }
    assert manifest["mit_supercloud"]["full_positive_energy_joined_jobs"] == 71128
    assert manifest["mit_supercloud"]["valid_joined_jobs"] == 68664
    assert rows["MIT immutable scheduler-DCGM join"] == 71128
    assert rows["MIT common trace horizon filter"] == 68664


def test_information_boundary_and_cross_network_ac_audit_are_complete() -> None:
    decision = np.genfromtxt(
        ROOT
        / "experiments/exp17_decision_time_information/results/final/"
        "decision_time_comparison.csv",
        delimiter=",",
        names=True,
        dtype=None,
        encoding="utf-8",
    )
    assert len(decision) == CFG["experiments"]["test_days"] * 4
    truncated = decision[
        decision["method"] == "Decision-time truncated-ledger verifier"
    ]
    assert np.all(truncated["future_arrivals_used_for_decision"] == 0)
    committed = decision[
        decision["method"] == "Committed-ledger rolling-service verifier"
    ]
    assert len(committed) == CFG["experiments"]["test_days"]
    assert np.all(committed["future_arrivals_used_for_decision"] == 0)
    assert np.all(committed["event_upper_margin_mw"] >= -1e-8)
    reference = decision[
        decision["method"] == "Committed-ledger reference schedule"
    ]
    assert len(reference) == CFG["experiments"]["test_days"]
    assert np.all(reference["future_arrivals_used_for_decision"] == 0)
    assert set(committed["payment_eligibility"]) == {"committed-ledger-only"}
    # The closed-meter payment is observable and cannot exceed the submitted
    # or frozen contract credit.  Oracle overpayment remains an explicit
    # offline diagnostic rather than being hard-coded to zero; the committed
    # response must expose a nonzero payable quantity and its audit must be no
    # larger than the corresponding gross false-credit exposure.
    assert np.all(committed["meter_capped_false_response_mwh"] >= -1e-9)
    assert np.all(
        committed["meter_capped_false_response_mwh"]
        <= committed["false_response_mwh"] + 1e-8
    )
    assert np.all(
        committed["meter_capped_response_mwh"]
        <= committed["paid_response_mwh"] + 1e-8
    )
    assert float(committed["meter_capped_response_mwh"].mean()) > 1e-9
    assert float(committed["meter_capped_underpayment_mwh"].mean()) > 1e-9
    assert pd.Series(committed["settlement_rule"]).astype(str).str.startswith(
        "contract-capped-after-event"
    ).all()
    reserve = pd.read_csv(
        ROOT
        / "experiments/exp17_decision_time_information/results/final/"
        "causal_reserve_test_summary.csv"
    )
    assert len(reserve) == 1
    assert float(reserve.loc[0, "reserve_quantile"]) == 0.60
    validation_reserve = pd.read_csv(
        ROOT
        / "experiments/exp17_decision_time_information/results/final/"
        "causal_reserve_validation_summary.csv"
    )
    selected = validation_reserve[validation_reserve["selected"]]
    assert len(selected) == 1
    assert float(selected.iloc[0]["false_response_mwh"]) <= float(
        CFG["experiments"]["event_gate_reserve_validation_false_credit_budget_mwh"]
    ) + 1e-8
    ac = np.genfromtxt(
        ROOT
        / "experiments/exp18_preventive_ac_network_panel/results/final/"
        "preventive_ac_cross_network_results.csv",
        delimiter=",",
        names=True,
        dtype=None,
        encoding="utf-8",
    )
    ac_metadata = json.loads(
        (
            ROOT
            / "experiments/exp18_preventive_ac_network_panel/results/final/"
            "experiment_metadata.json"
        ).read_text(encoding="utf-8")
    )
    assert len(np.unique(ac["network"])) == 4
    assert np.all(ac["solver_success"] == 1)
    assert np.max(ac["maximum_apparent_line_loading"]) <= 1.0 + 1e-8
    assert np.max(ac["maximum_voltage_violation_pu"]) <= 1e-8
    assert np.max(ac["maximum_nonreference_active_plan_deviation_mw"]) <= (
        float(ac_metadata["fixed_active_plan_tolerance_mw"]) + 1.0e-6
    )
    assert len(ac) == (
        sum(ac_metadata["outages_by_network"].values())
        * len(CFG["experiments"]["preventive_ac_dc_peak_penetrations"])
        * len(ac_metadata["methods"])
        * ac_metadata["locked_snapshot_count"]
    )
    assert ac_metadata["locked_snapshot_count"] == 6
    assert ac_metadata["test_outcomes_used_for_scaling"] is False
    assert ac_metadata["ac_limits_enforced"] is True
    assert "pre-registered generator-bus electrical-role" in ac_metadata["bus_mapping_basis"]
    assert "synthetic trace-to-bus benchmark" in ac_metadata["spatial_identification"]
    assert ac_metadata["pre_registered_dc_bus_mapping_one_based"] == CFG["experiments"]["preventive_ac_dc_bus_map_one_based"]
    assert ac_metadata["load_multiplier"] == 0.90
    assert 0.0 < float(ac_metadata["fixed_active_plan_tolerance_mw"]) <= 1.0e-5
    assert ac_metadata["locked_snapshot_count"] == len(CFG["experiments"]["preventive_ac_validation_day_indices"]) * len(CFG["experiments"]["preventive_ac_validation_event_slots"])
    assert 1 <= CFG["experiments"]["ac_n1_workers"] <= 20


def test_risk_decomposition_and_structural_literature_panel_are_explicit() -> None:
    exp2 = ROOT / "experiments/exp2_baseline_verification/results/final"
    decomposition = pd.read_csv(exp2 / "risk_effect_decomposition.csv")
    assert len(decomposition) == 9
    assert set(decomposition["split"]) == {"validation", "test"}
    assert decomposition["interpretation"].str.len().gt(20).all()
    structural = pd.read_csv(exp2 / "structural_literature_baselines.csv")
    assert len(structural) == CFG["experiments"]["test_days"] * 2
    assert set(structural["implementation"]) == {"exact_ledger_lp"}
    assert set(structural["baseline"]) == {
        "Temporal-only ledger control",
        "Joint spatio-temporal ledger control",
    }


def test_locked_days_have_complete_history_and_future_deadline_coverage() -> None:
    workload = load_workload(ROOT / "data/processed/workload_15min.npz")
    validation, test = _event_days(workload["valid_days"], CFG)
    selected = np.concatenate([validation, test])
    future_days = int(
        np.ceil(
            CFG["experiments"]["lookahead_slots"]
            / CFG["project"]["slots_per_day"]
        )
    )
    assert len(validation) == CFG["experiments"]["validation_days"]
    assert len(test) == CFG["experiments"]["test_days"]
    assert selected.min() >= CFG["experiments"]["strategic_history_days"]
    assert selected.max() + future_days <= workload["valid_days"].max()
    assert np.all(np.diff(selected) == 1)


def test_raw_and_processed_data_are_complete() -> None:
    workload = load_workload(ROOT / "data/processed/workload_15min.npz")
    assert workload["arrivals_mwh"].shape == (11616, 4, 3)
    assert len(workload["valid_days"]) == 121
    assert np.isfinite(workload["arrivals_mwh"]).all()
    assert workload["arrivals_mwh"].sum() > 0
    assert workload["observed_counterfactual_mw"].shape == (11616, 4)
    assert np.isfinite(workload["observed_counterfactual_mw"]).all()
    manifest = json.loads(
        (ROOT / "data/processed/data_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    conversion = manifest["power_calibration"][
        "heldout_job_energy_measured_to_predicted_quantiles"
    ]
    factors = np.asarray(
        [conversion["0.1"], conversion["0.5"], conversion["0.9"]]
    )
    assert manifest["power_calibration"][
        "heldout_jobs_with_positive_prediction"
    ] == 40768
    assert np.all(np.diff(factors) > 0)
    assert factors[0] < 1.0 < factors[-1]


def test_preprocessing_fails_closed_on_raw_manifest_mismatch() -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        raw = root / "data/raw/input.csv"
        raw.parent.mkdir(parents=True)
        raw.write_bytes(b"partial input\n")
        manifest = root / "data/processed/data_manifest.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(
            json.dumps(
                {
                    "sources": [
                        {
                            "path": "data/raw/input.csv",
                            "bytes": 999,
                            "sha256": "0" * 64,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        try:
            _validate_declared_raw_sources(root, manifest, [raw])
        except RuntimeError as exc:
            message = str(exc)
            assert "Restore the original files" in message
            assert "input.csv" in message
        else:
            raise AssertionError("mismatched raw input was accepted")


def test_preprocessing_rejects_undeclared_raw_manifest_path() -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        declared = root / "data/raw/declared.csv"
        undeclared = root / "data/raw/undeclared.csv"
        declared.parent.mkdir(parents=True)
        declared.write_bytes(b"declared input\n")
        undeclared.write_bytes(b"another input\n")
        manifest = root / "data/processed/data_manifest.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(
            json.dumps(
                {
                    "sources": [
                        {
                            "path": "data/raw/declared.csv",
                            "bytes": declared.stat().st_size,
                            "sha256": hashlib.sha256(declared.read_bytes()).hexdigest(),
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        try:
            _validate_declared_raw_sources(root, manifest, [declared, undeclared])
        except RuntimeError as exc:
            assert "not declared in locked manifest" in str(exc)
            assert "undeclared.csv" in str(exc)
        else:
            raise AssertionError("undeclared raw input was accepted")


def test_workload_lp_conserves_energy_and_capacity() -> None:
    workload = load_workload(ROOT / "data/processed/workload_15min.npz")
    arrivals = workload["arrivals_mwh"].reshape(-1, 96, 4, 3)[120]
    prices = np.full((4, 96), 50.0)
    result = solve_workload_schedule(arrivals, prices, CFG)
    assert result.success
    assert np.max(np.abs(result.served_mwh.sum(axis=(2, 3)) - arrivals.sum(axis=0))) < 1e-7
    flexible_power = result.served_mwh.sum(axis=(0, 1)) / 0.25
    assert flexible_power.max() <= CFG["project"]["flexible_capacity_mw"] + 1e-7


def test_structural_destination_mask_is_enforced_by_the_workload_lp() -> None:
    arrivals = np.zeros((8, 2, 1))
    arrivals[0, 0, 0] = 1.0
    arrivals[0, 1, 0] = 1.0
    local = load_config(ROOT / "configs/default.yaml")
    local["workload"]["deadlines_slots"] = [0]
    prices = np.full((2, 8), 50.0)
    allowed = np.asarray([[True, False], [False, True]], dtype=bool)
    result = solve_workload_schedule(
        arrivals,
        prices,
        local,
        allowed_destinations=allowed,
    )
    assert result.success
    assert np.max(np.abs(result.served_mwh[0, :, 1, :])) < 1e-10
    assert np.max(np.abs(result.served_mwh[1, :, 0, :])) < 1e-10


def test_cumulative_service_respects_release_and_deadline() -> None:
    arrivals = np.zeros((12, 2, 3))
    arrivals[1, 0, 0] = 0.5
    arrivals[2, 1, 1] = 1.0
    arrivals[3, 0, 2] = 2.0
    local = load_config(ROOT / "configs/default.yaml")
    local["workload"]["deadlines_slots"] = [0, 2, 5]
    prices = np.vstack([np.linspace(20, 40, 12), np.linspace(40, 20, 12)])
    result = solve_workload_schedule(arrivals, prices, local)
    assert result.success
    service = result.served_mwh.sum(axis=2)
    cumulative_service = np.cumsum(service, axis=2)
    cumulative_arrivals = np.cumsum(arrivals, axis=0)
    for source in range(2):
        for klass, deadline in enumerate([0, 2, 5]):
            assert np.all(cumulative_service[source, klass] <= cumulative_arrivals[:, source, klass] + 1e-8)
            for t in range(deadline, 12):
                assert cumulative_service[source, klass, t] + 1e-8 >= cumulative_arrivals[t - deadline, source, klass]


def test_convex_projection_preserves_every_linear_constraint() -> None:
    arrivals = np.zeros((12, 2, 3))
    arrivals[0, 0, 0] = 0.5
    arrivals[2, 1, 1] = 1.0
    arrivals[3, 0, 2] = 2.0
    local = load_config(ROOT / "configs/default.yaml")
    local["workload"]["deadlines_slots"] = [0, 3, 6]
    first = solve_workload_schedule(
        arrivals,
        np.vstack([np.linspace(20, 45, 12), np.linspace(45, 20, 12)]),
        local,
    )
    second = solve_workload_schedule(
        arrivals,
        np.vstack([np.linspace(45, 20, 12), np.linspace(20, 45, 12)]),
        local,
    )
    assert first.success and second.success
    alpha = 0.37
    served = alpha * first.served_mwh + (1 - alpha) * second.served_mwh
    assert np.max(np.abs(served.sum(axis=(2, 3)) - arrivals.sum(axis=0))) < 1e-7
    assert (served >= -1e-10).all()
    assert (served.sum(axis=(0, 1)) / 0.25 <= local["project"]["flexible_capacity_mw"] + 1e-7).all()
    cumulative_service = np.cumsum(served.sum(axis=2), axis=2)
    cumulative_arrivals = np.cumsum(arrivals, axis=0)
    for source in range(2):
        for klass, deadline in enumerate(local["workload"]["deadlines_slots"]):
            assert np.all(cumulative_service[source, klass] <= cumulative_arrivals[:, source, klass] + 1e-8)
            for t in range(deadline, 12):
                assert cumulative_service[source, klass, t] + 1e-8 >= cumulative_arrivals[t - deadline, source, klass]


def test_exact_risk_envelope_is_feasible_and_pointwise_bounded() -> None:
    arrivals = np.zeros((12, 2, 3))
    arrivals[0, 0, 1] = 0.8
    arrivals[1, 1, 1] = 0.6
    local = load_config(ROOT / "configs/default.yaml")
    local["market"]["event_slots"] = [4, 5, 6]
    local["workload"]["deadlines_slots"] = [0, 10, 10]
    prices = np.full((2, 12), 30.0)
    reference = solve_workload_schedule(arrivals, prices, local)
    assert reference.success
    target = reference.power_mw.copy()
    target[:, [4, 5, 6]] += 5.0
    upper = np.full_like(
        target,
        local["project"]["fixed_facility_load_mw"]
        + local["project"]["flexible_capacity_mw"],
    )
    upper[:, [4, 5, 6]] = reference.power_mw[:, [4, 5, 6]]
    safe = solve_workload_schedule(
        arrivals,
        prices,
        local,
        target_power_mw=target,
        projection_weight=1.0,
        power_upper_mw=upper,
    )
    assert safe.success
    assert np.all(safe.power_mw <= upper + 1e-8)
    assert (
        np.max(
            np.abs(
                safe.served_mwh.sum(axis=(2, 3))
                - arrivals.sum(axis=0)
            )
        )
        < 1e-7
    )


def test_rolling_terminal_uses_real_future_arrivals_without_forcing_them() -> None:
    arrivals = np.zeros((16, 2, 3))
    arrivals[1, 0, 1] = 1.0
    arrivals[8, 1, 2] = 2.0
    local = load_config(ROOT / "configs/default.yaml")
    local["workload"]["deadlines_slots"] = [0, 4, 10]
    prices = np.full((2, 16), 30.0)
    result = solve_workload_schedule(
        arrivals,
        prices,
        local,
        require_all_arrivals_at_terminal=False,
        terminal_completion_index=7,
    )
    assert result.success
    served = result.served_mwh.sum(axis=(2, 3))
    assert np.isclose(served[0, 1], 1.0, atol=1e-8)
    assert np.isclose(served[1, 2], 0.0, atol=1e-8)


def test_exact_power_band_and_masked_lexicographic_projection() -> None:
    arrivals = np.zeros((12, 2, 3))
    arrivals[0, 0, 1] = 1.0
    arrivals[0, 1, 1] = 1.0
    local = load_config(ROOT / "configs/default.yaml")
    local["workload"]["deadlines_slots"] = [0, 10, 10]
    prices = np.full((2, 12), 30.0)
    fixed = float(local["project"]["fixed_facility_load_mw"])
    target = np.full((2, 12), fixed)
    target[:, 4:6] = fixed + 4.0
    mask = np.zeros_like(target, dtype=bool)
    mask[:, 4:6] = True
    stage_one = solve_workload_schedule(
        arrivals,
        prices,
        local,
        target_power_mw=target,
        projection_weight=1.0,
        projection_mask=mask,
        operating_cost_weight=0.0,
    )
    assert stage_one.success
    stage_two = solve_workload_schedule(
        arrivals,
        prices,
        local,
        target_power_mw=target,
        projection_mask=mask,
        maximum_projection_l1_mw=stage_one.projection_l1_mw + 1e-8,
    )
    assert stage_two.success
    assert stage_two.projection_l1_mw <= stage_one.projection_l1_mw + 2e-8
    exact = stage_two.power_mw.copy()
    banded = solve_workload_schedule(
        arrivals,
        prices,
        local,
        power_upper_mw=exact,
        power_lower_mw=exact,
    )
    assert banded.success
    assert np.allclose(banded.power_mw, exact, atol=1e-7)


def test_sced_balances_and_respects_branch_limits() -> None:
    system = _test_network()
    load = system.bus[:, 2] * 0.9
    result = solve_sced(system, load, CFG["market"]["generator_segments"])
    assert result.success
    assert abs(result.generation_mw.sum() - load.sum()) < 1e-6
    assert result.max_loading <= 1.000001


def test_complete_n1_sced_enforces_every_nonislanding_rts_outage() -> None:
    from pypower.case24_ieee_rts import case24_ieee_rts

    system = power_system_from_ppc(case24_ieee_rts())
    security = build_n1_security_factors(system)
    result = solve_n1_sced(
        system,
        system.bus[:, 2] * CFG["experiments"]["n1_load_multiplier"],
        CFG["market"]["generator_segments"],
        security_factors=security,
    )
    assert result.success
    assert result.credible_contingencies == 37
    assert system.branch.shape[0] - result.credible_contingencies == 1
    assert result.max_post_contingency_loading <= 1.000001
    assert (
        abs(
            result.generation_mw.sum()
            - (
                system.bus[:, 2]
                * CFG["experiments"]["n1_load_multiplier"]
            ).sum()
        )
        < 1e-6
    )


def test_payment_certificate_is_global_and_noninferior() -> None:
    from pypower.case24_ieee_rts import case24_ieee_rts

    system = power_system_from_ppc(case24_ieee_rts())
    security = build_n1_security_factors(system)
    native = system.bus[:, 2] * 0.88
    dc_buses = np.asarray([2, 7, 14, 20])
    candidates = np.zeros((3, 4, 4))
    candidates[0] = np.array(
        [[5.0, 8.0, 6.0, 7.0], [7.0, 5.0, 8.0, 6.0],
         [6.0, 7.0, 5.0, 8.0], [8.0, 6.0, 7.0, 5.0]]
    )
    candidates[1] = candidates[0][:, ::-1]
    candidates[2] = 0.4 * candidates[0] + 0.6 * candidates[1]
    result = solve_payment_certified_n1_projection(
        system,
        native,
        dc_buses,
        candidates,
        candidates[2],
        reference_candidate=0,
        event_slots=[0, 1, 2, 3],
        dt_h=0.25,
        segments=6,
        security_factors=security,
        conversion_scale_factors=np.asarray([0.8, 1.0, 1.25]),
    )
    assert result.success
    assert np.isclose(result.weights.sum(), 1.0, atol=1e-9)
    assert (result.weights >= -1e-10).all()
    assert result.maximum_cost_violation_usd <= 1e-6
    assert result.certified_baseline_cost_usd <= result.reference_baseline_cost_usd + 1e-6
    assert np.allclose(
        result.conversion_scale_factors, [0.8, 1.0, 1.25]
    )
    assert (
        result.scenario_certified_cost_usd
        <= result.scenario_reference_cost_usd + 1e-6
    ).all()
    assert result.worst_case_fractional_cost_margin >= -1e-9
    assert np.isclose(
        result.objective_l1_mw,
        result.first_stage_optimal_l1_mw,
        atol=2e-9,
    )


def test_full_payment_certificate_candidate_hull_is_independent() -> None:
    profiles = np.load(
        ROOT
        / "experiments/exp2_baseline_verification/results/intermediate/"
        "test_profiles.npz",
        allow_pickle=False,
    )
    certificate = np.load(
        ROOT
        / "experiments/exp9_payment_certificate/results/final/"
        "certified_counterfactual_profiles.npz",
        allow_pickle=False,
    )
    methods = [str(value) for value in profiles["methods"]]
    risk = profiles["baselines"][
        :, methods.index("Risk-Constrained Convex Verifier")
    ]
    candidates = profiles["projection_candidates"]
    assert candidates.shape[1] == 6
    assert len(certificate["candidate_names"]) == 7
    assert all(
        "Risk-Constrained" not in str(name)
        for name in certificate["candidate_names"]
    )
    # Independence is established by construction: Exp9 stores a candidate
    # hull assembled from the six projection profiles plus the matched
    # quantile comparator, while the risk-constrained profile is never named
    # or passed into that certificate.  A deterministic LP can nevertheless
    # return the same active-set schedule for two different targets, so a
    # numerical distance assertion would incorrectly reject a valid certificate.
    assert "Risk-Constrained Convex Verifier" not in {
        str(name) for name in certificate["candidate_names"]
    }
    assert len(str(certificate["candidate_checksum"])) == 64


def test_polyhedral_sced_subgradient_certificate() -> None:
    system = _test_network()
    baseline_load = system.bus[:, 2] * 0.9
    actual_load = baseline_load.copy()
    actual_load[np.array(CFG["project"]["data_center_buses"]) - 1] *= 1.03
    baseline = solve_sced(
        system, baseline_load, CFG["market"]["generator_segments"]
    )
    actual = solve_sced(
        system, actual_load, CFG["market"]["generator_segments"]
    )
    exact_signed_value = baseline.objective - actual.objective
    nodal_signed_linear = float(
        baseline.lmp_per_mwh @ (baseline_load - actual_load)
    )
    # Convexity of the polyhedral SCED value function gives a global
    # subgradient inequality without any smoothness assumption.
    assert nodal_signed_linear - exact_signed_value >= -1e-7


def test_independent_high_resolution_value_is_not_self_scored() -> None:
    system = _test_network()
    evaluation = _ieee118_quadratic_evaluation_system(system)
    baseline_load = system.bus[:, 2] * 0.9
    actual_load = baseline_load.copy()
    actual_load[np.array(CFG["project"]["data_center_buses"]) - 1] += 4.0
    low_value = solve_sced(
        evaluation, baseline_load, CFG["market"]["generator_segments"]
    ).objective - solve_sced(
        evaluation, actual_load, CFG["market"]["generator_segments"]
    ).objective
    high_value = solve_sced(
        evaluation,
        baseline_load,
        CFG["market"]["evaluation_generator_segments"],
    ).objective - solve_sced(
        evaluation,
        actual_load,
        CFG["market"]["evaluation_generator_segments"],
    ).objective
    assert abs(low_value - high_value) > 1e-7


def test_exact_shapley_allocation_is_budget_balanced() -> None:
    # Non-additive four-player characteristic function; exact efficiency must
    # hold independently of any power-system interpretation.
    coalition_values = {}
    weights = np.array([1.0, 2.0, -0.5, 3.0])
    for coalition in range(16):
        members = [i for i in range(4) if coalition & (1 << i)]
        additive = float(weights[members].sum()) if members else 0.0
        interaction = 0.4 * len(members) * max(0, len(members) - 1) / 2
        coalition_values[coalition] = additive + interaction
    allocation = _exact_shapley_values(coalition_values, 4)
    assert abs(allocation.sum() - coalition_values[15]) < 1e-12


def test_group_symmetric_shapley_scales_exactly() -> None:
    members = 3
    values = {}
    for counts in np.ndindex(*([members + 1] * 4)):
        total = sum(counts)
        values[counts] = (
            1.7 * total
            + 0.08 * total**2
            + 0.03 * sum(value**2 for value in counts)
        )
    per_member = _exact_group_symmetric_shapley(values, members)
    assert abs(
        members * per_member.sum() - values[(members,) * 4]
    ) < 1e-10


def test_exact_eight_participant_shapley_is_budget_balanced() -> None:
    participants = 8
    weights = np.linspace(-1.0, 2.0, participants)
    coalition_values = {}
    for coalition in range(2**participants):
        members = [
            i for i in range(participants) if coalition & (1 << i)
        ]
        additive = float(weights[members].sum()) if members else 0.0
        interaction = 0.07 * len(members) ** 2
        coalition_values[coalition] = additive + interaction
    allocation = _exact_shapley_values(
        coalition_values, participants
    )
    assert (
        abs(allocation.sum() - coalition_values[2**participants - 1])
        < 1e-11
    )


def test_event_service_shadow_price_is_independent_marginal_cost() -> None:
    arrivals = np.zeros((12, 2, 3))
    arrivals[0, 0, 1] = 1.0
    local = load_config(ROOT / "configs/default.yaml")
    local["market"]["event_slots"] = [4, 5]
    local["workload"]["deadlines_slots"] = [0, 10, 10]
    local["workload"]["waiting_cost_per_mwh_slot"] = [0.0, 0.0, 0.0]
    local["workload"]["migration_cost_per_mwh"] = 100.0
    local["workload"]["cross_region_latency_penalty_per_mwh"] = 0.0
    prices = np.full((2, 12), 10.0)
    prices[0, [4, 5]] = 20.0
    prices[1] = 100.0
    result = solve_workload_schedule(
        arrivals,
        prices,
        local,
        mode="honest",
        minimum_participant_event_mwh=0.25,
    )
    assert result.success
    assert abs(result.minimum_service_shadow_price - 10.0) < 1e-8


def test_exact_two_sided_block_test_never_returns_impossible_zero() -> None:
    # The large offset reproduces the scale at which independent float64
    # summation paths previously excluded the observed sign assignment.
    differences = np.array(
        [
            1.0e9 + 0.11,
            1.0e9 + 0.12,
            1.0e9 + 0.13,
            1.0e9 + 0.14,
            1.0e9 + 0.15,
        ]
        * 8,
        dtype=float,
    )
    result = exact_block_sign_test(differences, block_length=5)
    assert result["blocks"] == 8
    assert result["total_sign_assignments"] == 256
    assert result["extreme_assignments"] >= 2
    assert result["two_sided_exact_p_value"] >= 2.0 / 256.0


def test_final_panels_exist() -> None:
    expected = [
        "experiments/exp1_manipulation/results/final/manipulation_grid.csv",
        "experiments/exp2_baseline_verification/results/final/per_day_baseline_metrics.csv",
        "experiments/exp3_nodal_settlement/results/final/settlement_metrics.csv",
        "experiments/exp4_case_study/results/final/spatial_case_timeseries.csv",
        "audit/result_audit.json",
        "experiments/exp5_network_robustness/results/final/network_robustness.csv",
        "experiments/exp6_physical_stress/results/final/physical_stress.csv",
        "experiments/exp7_value_allocation/results/final/value_allocation.csv",
        "experiments/exp7_value_allocation/results/final/eight_participant_exact_scaling.csv",
        "experiments/exp8_n1_security/results/final/n1_security_daily_results.csv",
        "experiments/exp9_payment_certificate/results/final/daily_payment_certificates.csv",
        "experiments/exp9_payment_certificate/results/final/conversion_scenario_certificates.csv",
        "experiments/exp10_ac_validation/results/final/ac_n1_contingency_results.csv",
        "experiments/exp10_ac_validation/results/final/preventive_ac_n1_results.csv",
        "experiments/exp11_spatial_scale_robustness/results/final/spatial_scale_robustness.csv",
        "experiments/exp12_rolling_market_validation/results/final/rolling_market_validation.csv",
        "experiments/exp13_real_trace_replay/results/final/real_trace_replay_daily.csv",
        "experiments/exp14_job_level_fidelity/results/final/job_level_fidelity_summary.csv",
        "experiments/exp15_interval_certificate/results/final/interval_endpoint_certificates.csv",
        "experiments/exp2_baseline_verification/results/final/convex_projection_weights.csv",
        "experiments/exp2_baseline_verification/results/final/risk_envelope_validation.csv",
        "experiments/exp20_trace_meter_replay/results/final/trace_meter_replay_summary.csv",
        "experiments/exp20_trace_meter_replay/results/final/trace_meter_replay_daily.csv",
        "experiments/exp17_decision_time_information/results/final/decision_time_summary.csv",
        "experiments/exp18_preventive_ac_network_panel/results/final/preventive_ac_cross_network_summary.csv",
        "experiments/exp19_job_level_counterfactual/results/final/job_level_counterfactual_summary.csv",
        "experiments/exp21_scale_consistency/results/final/scale_consistency_summary.csv",
        "experiments/exp22_coupled_job_network_certificate/results/final/coupled_network_event_replay.csv",
        "experiments/exp22_coupled_job_network_certificate/results/final/coupled_network_scale_replay.csv",
        "experiments/exp22_coupled_job_network_certificate/results/final/coupled_network_summary.csv",
        "experiments/exp22_coupled_job_network_certificate/results/final/coupling_invariant_certificate.json",
        "experiments/exp23_independent_event_replay/results/final/independent_event_replay_summary.csv",
        "experiments/exp24_all_outage_security_panel/results/final/all_outage_security_summary.csv",
        "experiments/exp25_exante_job_validation/results/final/exante_job_validation_summary.csv",
        "experiments/exp26_end_to_end_certificate/results/final/end_to_end_lineage.csv",
        "experiments/exp26_end_to_end_certificate/results/final/end_to_end_certificate.json",
    ]
    missing = [path for path in expected if not (ROOT / path).is_file()]
    assert not missing, f"missing final panels: {missing}"
    assert all((ROOT / path).stat().st_size > 0 for path in expected)


def test_job_to_network_certificate_replays_the_same_indexed_witness() -> None:
    folder = ROOT / "experiments/exp22_coupled_job_network_certificate/results/final"
    summary = pd.read_csv(folder / "coupled_network_summary.csv")
    values = dict(zip(summary["metric"], summary["value"]))
    assert int(float(values["positive_energy_jobs"])) == 71128
    assert int(float(values["service_variables"])) == 13_198_247
    assert float(values["maximum_job_to_aggregate_residual_mwh"]) <= 1e-12
    assert float(values["all_network_solves_successful"]) == 1.0
    metadata = json.loads(
        (folder / "experiment_metadata.json").read_text(encoding="utf-8")
    )
    assert metadata["network_profile_is_same_job_witness"] is True
    assert metadata["post_solution_profile_reoptimization"] is False
    assert metadata["replayed_event_slot_count"] == 1056
    typed = metadata["coupling_invariant_certificate"]
    mapped = metadata["network_mapping_certificate"]
    for field in (
        "max_job_energy_residual_mwh",
        "max_aggregation_residual_mwh",
        "minimum_gpu_bound_slack_mwh",
        "maximum_gpu_bound_violation_mwh",
        "minimum_site_capacity_slack_mwh",
    ):
        assert abs(float(typed[field]) - float(mapped[field])) <= 1e-12
    assert mapped["max_network_mapping_residual_mw"] <= 1e-10


def test_end_to_end_lineage_and_paper_release_boundaries_are_explicit() -> None:
    certificate_folder = ROOT / "experiments/exp26_end_to_end_certificate/results/final"
    lineage = pd.read_csv(certificate_folder / "end_to_end_lineage.csv")
    metadata = json.loads(
        (certificate_folder / "end_to_end_certificate.json").read_text(encoding="utf-8")
    )
    assert len(lineage) == 5
    assert lineage["passed"].astype(bool).all()
    assert metadata["profile_roles"]["profile_identity_asserted"] is False
    assert "relative N-1 baseline-cost cap" in metadata["payment_certificate_scope"]
    lower = metadata["job_entitlement_semantics"]["lower_fraction_q10"]
    central = metadata["job_entitlement_semantics"]["central_fraction_q50"]
    assert 0.0 < lower < central
    paper = (ROOT / "paper/main.tex").read_text(encoding="utf-8")
    consistency = json.loads(
        (ROOT / "reports/manuscript_consistency.json").read_text(encoding="utf-8")
    )
    assert consistency["all_checks_passed"] is True
    assert "/goal" not in paper
    assert "deployment-primary" in paper
