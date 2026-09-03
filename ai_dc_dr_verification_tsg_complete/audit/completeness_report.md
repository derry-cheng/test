# Reproducibility and Result Audit

Overall status: **PASS**.

## Completeness

- [x] data:data/processed/workload_15min.npz: exists and non-empty
- [x] data:data/processed/workload_daily_summary.csv: exists and non-empty
- [x] data:data/processed/data_manifest.json: exists and non-empty
- [x] data:data/processed/data_flow_audit.csv: exists and non-empty
- [x] data:configs/capacity_commitment.json: exists and non-empty
- [x] experiment_1:experiments/exp1_manipulation/results/final/manipulation_grid.csv: exists and non-empty
- [x] experiment_1:experiments/exp1_manipulation/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_1:experiments/exp1_manipulation/figures/fig1_manipulation_phase_diagram.png: exists and non-empty
- [x] experiment_1:experiments/exp1_manipulation/figures/fig2_response_and_migration.png: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/intermediate/validation_profiles.npz: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/per_day_baseline_metrics.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/closest_literature_baselines.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/closest_literature_baselines_summary.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/structural_literature_baselines.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/structural_literature_baselines_summary.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/baseline_fairness_audit.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/risk_effect_decomposition.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/bootstrap_confidence_intervals.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/constraint_ablation.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/constraint_ablation_daily.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/specification_robustness.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/projection_candidate_validation.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/convex_projection_weights.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/risk_constrained_validation_certificate.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/risk_truth_source_audit.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/risk_reserve_nested_cv.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/risk_reserve_validation_summary.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/risk_cvar_stress_sensitivity.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/risk_envelope_validation.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/two_sided_credit_certificate.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/quantile_feasible_validation.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/intervention_robustness.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/blocked_validation_cv.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/information_set_audit.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/block_length_sensitivity.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/paired_block_randomization_tests.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/matched_comparator_effects.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/paired_counterfactual_block_tests.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/complexity_scaling.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/figures/fig3_baseline_verification_performance.png: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/figures/fig4_tuning_and_ablation.png: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/figures/fig4b_intervention_robustness.png: exists and non-empty
- [x] experiment_3:experiments/exp3_nodal_settlement/results/final/settlement_metrics.csv: exists and non-empty
- [x] experiment_3:experiments/exp3_nodal_settlement/results/final/interval_grid_value.csv: exists and non-empty
- [x] experiment_3:experiments/exp3_nodal_settlement/results/final/mean_line_loading.csv: exists and non-empty
- [x] experiment_3:experiments/exp3_nodal_settlement/results/final/paired_settlement_block_tests.csv: exists and non-empty
- [x] experiment_3:experiments/exp3_nodal_settlement/results/final/polyhedral_value_certificates.csv: exists and non-empty
- [x] experiment_3:experiments/exp3_nodal_settlement/results/final/settlement_factor_decomposition.csv: exists and non-empty
- [x] experiment_3:experiments/exp3_nodal_settlement/results/final/settlement_factor_decomposition_summary.csv: exists and non-empty
- [x] experiment_3:experiments/exp3_nodal_settlement/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_3:experiments/exp3_nodal_settlement/figures/fig5_settlement_value_alignment.png: exists and non-empty
- [x] experiment_3:experiments/exp3_nodal_settlement/figures/fig6_network_loading_heatmap.png: exists and non-empty
- [x] experiment_3:experiments/exp3_nodal_settlement/figures/fig6b_settlement_factor_decomposition.png: exists and non-empty
- [x] experiment_4:experiments/exp4_case_study/results/intermediate/case_selection_candidates.csv: exists and non-empty
- [x] experiment_4:experiments/exp4_case_study/results/final/spatial_case_timeseries.csv: exists and non-empty
- [x] experiment_4:experiments/exp4_case_study/results/final/case_summary_by_data_center.csv: exists and non-empty
- [x] experiment_4:experiments/exp4_case_study/results/final/case_metadata.json: exists and non-empty
- [x] experiment_4:experiments/exp4_case_study/figures/fig7_spatial_response_case.png: exists and non-empty
- [x] experiment_4:experiments/exp4_case_study/figures/fig8_ieee118_data_center_topology.png: exists and non-empty
- [x] experiment_5:experiments/exp5_network_robustness/results/final/network_robustness.csv: exists and non-empty
- [x] experiment_5:experiments/exp5_network_robustness/results/final/network_robustness_summary.csv: exists and non-empty
- [x] experiment_5:experiments/exp5_network_robustness/results/final/paired_network_block_tests.csv: exists and non-empty
- [x] experiment_5:experiments/exp5_network_robustness/results/final/resolution_convergence_daily.csv: exists and non-empty
- [x] experiment_5:experiments/exp5_network_robustness/results/final/resolution_convergence_summary.csv: exists and non-empty
- [x] experiment_5:experiments/exp5_network_robustness/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_5:experiments/exp5_network_robustness/figures/fig9_cross_network_robustness.png: exists and non-empty
- [x] experiment_6:experiments/exp6_physical_stress/results/final/physical_stress.csv: exists and non-empty
- [x] experiment_6:experiments/exp6_physical_stress/results/final/physical_stress_summary.csv: exists and non-empty
- [x] experiment_6:experiments/exp6_physical_stress/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_6:experiments/exp6_physical_stress/figures/fig10_binding_constraint_stress.png: exists and non-empty
- [x] experiment_7:experiments/exp7_value_allocation/results/final/value_allocation.csv: exists and non-empty
- [x] experiment_7:experiments/exp7_value_allocation/results/final/value_allocation_summary.csv: exists and non-empty
- [x] experiment_7:experiments/exp7_value_allocation/results/final/eight_participant_exact_scaling.csv: exists and non-empty
- [x] experiment_7:experiments/exp7_value_allocation/results/final/eight_participant_exact_scaling_summary.csv: exists and non-empty
- [x] experiment_7:experiments/exp7_value_allocation/results/final/group_symmetric_exact_scaling.csv: exists and non-empty
- [x] experiment_7:experiments/exp7_value_allocation/results/final/group_symmetric_exact_scaling_summary.csv: exists and non-empty
- [x] experiment_7:experiments/exp7_value_allocation/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_7:experiments/exp7_value_allocation/figures/fig11_exact_value_allocation.png: exists and non-empty
- [x] experiment_7:experiments/exp7_value_allocation/figures/fig12_eight_participant_scaling.png: exists and non-empty
- [x] experiment_7:experiments/exp7_value_allocation/figures/fig12b_exact_20_participant_scaling.png: exists and non-empty
- [x] experiment_8:experiments/exp8_n1_security/results/final/n1_security_interval_results.csv: exists and non-empty
- [x] experiment_8:experiments/exp8_n1_security/results/final/n1_security_daily_results.csv: exists and non-empty
- [x] experiment_8:experiments/exp8_n1_security/results/final/n1_security_summary.csv: exists and non-empty
- [x] experiment_8:experiments/exp8_n1_security/results/final/n1_security_paired_tests.csv: exists and non-empty
- [x] experiment_8:experiments/exp8_n1_security/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_8:experiments/exp8_n1_security/figures/fig13_n1_security_validation.png: exists and non-empty
- [x] experiment_9:experiments/exp9_payment_certificate/results/final/daily_payment_certificates.csv: exists and non-empty
- [x] experiment_9:experiments/exp9_payment_certificate/results/final/conversion_scenario_certificates.csv: exists and non-empty
- [x] experiment_9:experiments/exp9_payment_certificate/results/final/certified_counterfactual_profiles.npz: exists and non-empty
- [x] experiment_9:experiments/exp9_payment_certificate/results/final/payment_evaluation_intervals.csv: exists and non-empty
- [x] experiment_9:experiments/exp9_payment_certificate/results/final/payment_evaluation_daily.csv: exists and non-empty
- [x] experiment_9:experiments/exp9_payment_certificate/results/final/payment_evaluation_summary.csv: exists and non-empty
- [x] experiment_9:experiments/exp9_payment_certificate/results/final/payment_evaluation_unseen_scenarios.csv: exists and non-empty
- [x] experiment_9:experiments/exp9_payment_certificate/results/final/payment_evaluation_unseen_summary.csv: exists and non-empty
- [x] experiment_9:experiments/exp9_payment_certificate/results/final/paired_payment_noninferiority.csv: exists and non-empty
- [x] experiment_9:experiments/exp9_payment_certificate/results/final/payment_target_selection_validation.csv: exists and non-empty
- [x] experiment_9:experiments/exp9_payment_certificate/results/final/payment_non_tautology_audit.csv: exists and non-empty
- [x] experiment_9:experiments/exp9_payment_certificate/results/final/payment_pareto_paired_ci.csv: exists and non-empty
- [x] experiment_9:experiments/exp9_payment_certificate/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_9:experiments/exp9_payment_certificate/figures/fig14_payment_certificate.png: exists and non-empty
- [x] experiment_10:experiments/exp10_ac_validation/results/final/ac_opf_locked_day_results.csv: exists and non-empty
- [x] experiment_10:experiments/exp10_ac_validation/results/final/ac_opf_summary.csv: exists and non-empty
- [x] experiment_10:experiments/exp10_ac_validation/results/final/ac_n1_contingency_results.csv: exists and non-empty
- [x] experiment_10:experiments/exp10_ac_validation/results/final/ac_n1_contingency_summary.csv: exists and non-empty
- [x] experiment_10:experiments/exp10_ac_validation/results/final/preventive_ac_n1_results.csv: exists and non-empty
- [x] experiment_10:experiments/exp10_ac_validation/results/final/preventive_ac_n1_summary.csv: exists and non-empty
- [x] experiment_10:experiments/exp10_ac_validation/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_10:experiments/exp10_ac_validation/figures/fig15_ac_opf_validation.png: exists and non-empty
- [x] experiment_10:experiments/exp10_ac_validation/figures/fig15b_ac_n1_contingency_validation.png: exists and non-empty
- [x] experiment_10:experiments/exp10_ac_validation/figures/fig15c_preventive_ac_n1_validation.png: exists and non-empty
- [x] experiment_11:experiments/exp11_spatial_scale_robustness/results/final/spatial_scale_robustness.csv: exists and non-empty
- [x] experiment_11:experiments/exp11_spatial_scale_robustness/results/final/spatial_scale_summary.csv: exists and non-empty
- [x] experiment_11:experiments/exp11_spatial_scale_robustness/results/final/mapping_level_summary.csv: exists and non-empty
- [x] experiment_11:experiments/exp11_spatial_scale_robustness/results/final/spatial_trace_mapping_audit.csv: exists and non-empty
- [x] experiment_11:experiments/exp11_spatial_scale_robustness/results/final/spatial_trace_pairwise_correlation.csv: exists and non-empty
- [x] experiment_11:experiments/exp11_spatial_scale_robustness/results/final/spatial_trace_mapping_metadata.json: exists and non-empty
- [x] experiment_11:experiments/exp11_spatial_scale_robustness/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_11:experiments/exp11_spatial_scale_robustness/figures/fig16_spatial_scale_robustness.png: exists and non-empty
- [x] experiment_12:experiments/exp12_rolling_market_validation/results/final/rolling_market_validation.csv: exists and non-empty
- [x] experiment_12:experiments/exp12_rolling_market_validation/results/final/rolling_market_summary.csv: exists and non-empty
- [x] experiment_12:experiments/exp12_rolling_market_validation/results/final/site_space_time_allocations.csv: exists and non-empty
- [x] experiment_12:experiments/exp12_rolling_market_validation/results/final/paired_payment_comparisons.csv: exists and non-empty
- [x] experiment_12:experiments/exp12_rolling_market_validation/results/final/rolling_counterfactual_profiles.npz: exists and non-empty
- [x] experiment_12:experiments/exp12_rolling_market_validation/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_12:experiments/exp12_rolling_market_validation/figures/fig18_rolling_market_validation.png: exists and non-empty
- [x] experiment_13:experiments/exp13_real_trace_replay/results/final/real_trace_replay_daily.csv: exists and non-empty
- [x] experiment_13:experiments/exp13_real_trace_replay/results/final/real_trace_replay_trace.csv: exists and non-empty
- [x] experiment_13:experiments/exp13_real_trace_replay/results/final/real_trace_replay_summary.csv: exists and non-empty
- [x] experiment_13:experiments/exp13_real_trace_replay/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_13:experiments/exp13_real_trace_replay/figures/fig19_real_trace_replay.png: exists and non-empty
- [x] experiment_14:experiments/exp14_job_level_fidelity/results/final/job_level_flow_solution.npz: exists and non-empty
- [x] experiment_14:experiments/exp14_job_level_fidelity/results/final/job_level_slot_profile.csv: exists and non-empty
- [x] experiment_14:experiments/exp14_job_level_fidelity/results/final/job_level_fidelity_summary.csv: exists and non-empty
- [x] experiment_14:experiments/exp14_job_level_fidelity/results/final/job_interval_witness_summary.csv: exists and non-empty
- [x] experiment_14:experiments/exp14_job_level_fidelity/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_14:experiments/exp14_job_level_fidelity/figures/fig20_job_level_fidelity.png: exists and non-empty
- [x] experiment_15:experiments/exp15_interval_certificate/results/final/interval_endpoint_certificates.csv: exists and non-empty
- [x] experiment_15:experiments/exp15_interval_certificate/results/final/interval_certificate_summary.csv: exists and non-empty
- [x] experiment_15:experiments/exp15_interval_certificate/results/final/payment_value_interval_certificates.csv: exists and non-empty
- [x] experiment_15:experiments/exp15_interval_certificate/results/final/payment_value_interval_summary.csv: exists and non-empty
- [x] experiment_15:experiments/exp15_interval_certificate/results/final/interval_certified_counterfactual_profiles.npz: exists and non-empty
- [x] experiment_15:experiments/exp15_interval_certificate/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_15:experiments/exp15_interval_certificate/figures/fig21_interval_payment_certificate.png: exists and non-empty
- [x] experiment_16:experiments/exp16_ledger_capacity_provenance/results/final/ledger_provenance_summary.csv: exists and non-empty
- [x] experiment_16:experiments/exp16_ledger_capacity_provenance/results/final/capacity_reconciliation.csv: exists and non-empty
- [x] experiment_16:experiments/exp16_ledger_capacity_provenance/results/final/workload_power_calibration_sensitivity.csv: exists and non-empty
- [x] experiment_16:experiments/exp16_ledger_capacity_provenance/results/final/physical_calibration_summary.csv: exists and non-empty
- [x] experiment_16:experiments/exp16_ledger_capacity_provenance/results/final/ledger_provenance_certificate.json: exists and non-empty
- [x] experiment_16:experiments/exp16_ledger_capacity_provenance/results/final/source_hashes.json: exists and non-empty
- [x] experiment_16:experiments/exp16_ledger_capacity_provenance/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_16:experiments/exp16_ledger_capacity_provenance/figures/fig22_ledger_capacity_provenance.png: exists and non-empty
- [x] experiment_17:experiments/exp17_decision_time_information/results/final/decision_time_comparison.csv: exists and non-empty
- [x] experiment_17:experiments/exp17_decision_time_information/results/final/decision_time_summary.csv: exists and non-empty
- [x] experiment_17:experiments/exp17_decision_time_information/results/final/causal_reserve_validation_daily.csv: exists and non-empty
- [x] experiment_17:experiments/exp17_decision_time_information/results/final/causal_reserve_validation_summary.csv: exists and non-empty
- [x] experiment_17:experiments/exp17_decision_time_information/results/final/causal_reserve_test_daily.csv: exists and non-empty
- [x] experiment_17:experiments/exp17_decision_time_information/results/final/causal_reserve_test_summary.csv: exists and non-empty
- [x] experiment_17:experiments/exp17_decision_time_information/results/final/causal_response_candidate_validation_daily.csv: exists and non-empty
- [x] experiment_17:experiments/exp17_decision_time_information/results/final/causal_response_candidate_validation.csv: exists and non-empty
- [x] experiment_17:experiments/exp17_decision_time_information/results/final/decision_time_trace_replay.csv: exists and non-empty
- [x] experiment_17:experiments/exp17_decision_time_information/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_17:experiments/exp17_decision_time_information/figures/fig23_decision_time_information.png: exists and non-empty
- [x] experiment_18:experiments/exp18_preventive_ac_network_panel/results/final/preventive_ac_cross_network_results.csv: exists and non-empty
- [x] experiment_18:experiments/exp18_preventive_ac_network_panel/results/final/preventive_ac_cross_network_summary.csv: exists and non-empty
- [x] experiment_18:experiments/exp18_preventive_ac_network_panel/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_18:experiments/exp18_preventive_ac_network_panel/figures/fig24_preventive_ac_cross_network.png: exists and non-empty
- [x] experiment_19:experiments/exp19_job_level_counterfactual/results/final/job_level_counterfactual_summary.csv: exists and non-empty
- [x] experiment_19:experiments/exp19_job_level_counterfactual/results/final/job_level_counterfactual_profile.csv: exists and non-empty
- [x] experiment_19:experiments/exp19_job_level_counterfactual/results/final/job_level_counterfactual_solution.npz: exists and non-empty
- [x] experiment_19:experiments/exp19_job_level_counterfactual/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_20:experiments/exp20_trace_meter_replay/results/final/trace_meter_replay_daily.csv: exists and non-empty
- [x] experiment_20:experiments/exp20_trace_meter_replay/results/final/trace_meter_replay_summary.csv: exists and non-empty
- [x] experiment_20:experiments/exp20_trace_meter_replay/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_20:experiments/exp20_trace_meter_replay/figures/fig25_trace_meter_replay.png: exists and non-empty
- [x] experiment_21:experiments/exp21_scale_consistency/results/final/scale_consistency_summary.csv: exists and non-empty
- [x] experiment_21:experiments/exp21_scale_consistency/results/final/scale_consistency_profile.csv: exists and non-empty
- [x] experiment_21:experiments/exp21_scale_consistency/results/final/capacity_proportional_profile.csv: exists and non-empty
- [x] experiment_21:experiments/exp21_scale_consistency/results/final/scale_sensitivity.csv: exists and non-empty
- [x] experiment_21:experiments/exp21_scale_consistency/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_22:experiments/exp22_coupled_job_network_certificate/results/final/coupled_network_event_replay.csv: exists and non-empty
- [x] experiment_22:experiments/exp22_coupled_job_network_certificate/results/final/coupled_network_scale_replay.csv: exists and non-empty
- [x] experiment_22:experiments/exp22_coupled_job_network_certificate/results/final/coupled_network_summary.csv: exists and non-empty
- [x] experiment_22:experiments/exp22_coupled_job_network_certificate/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_22:experiments/exp22_coupled_job_network_certificate/results/final/coupling_invariant_certificate.json: exists and non-empty
- [x] experiment_22:experiments/exp22_coupled_job_network_certificate/README.md: exists and non-empty
- [x] experiment_23:experiments/exp23_independent_event_replay/results/final/independent_event_replay_daily.csv: exists and non-empty
- [x] experiment_23:experiments/exp23_independent_event_replay/results/final/independent_event_replay_summary.csv: exists and non-empty
- [x] experiment_23:experiments/exp23_independent_event_replay/results/final/independent_event_profiles.npz: exists and non-empty
- [x] experiment_23:experiments/exp23_independent_event_replay/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_23:experiments/exp23_independent_event_replay/figures/fig26_independent_event_replay.png: exists and non-empty
- [x] experiment_23:experiments/exp23_independent_event_replay/README.md: exists and non-empty
- [x] experiment_24:experiments/exp24_all_outage_security_panel/results/final/all_outage_security_replay.csv: exists and non-empty
- [x] experiment_24:experiments/exp24_all_outage_security_panel/results/final/all_outage_security_summary.csv: exists and non-empty
- [x] experiment_24:experiments/exp24_all_outage_security_panel/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_24:experiments/exp24_all_outage_security_panel/figures/fig27_all_outage_security.png: exists and non-empty
- [x] experiment_24:experiments/exp24_all_outage_security_panel/README.md: exists and non-empty
- [x] experiment_25:experiments/exp25_exante_job_validation/results/final/exante_job_validation_summary.csv: exists and non-empty
- [x] experiment_25:experiments/exp25_exante_job_validation/results/final/exante_job_validation_by_type.csv: exists and non-empty
- [x] experiment_25:experiments/exp25_exante_job_validation/results/final/job_level_capacity_stress_solution.npz: exists and non-empty
- [x] experiment_25:experiments/exp25_exante_job_validation/results/final/job_level_capacity_stress_summary.csv: exists and non-empty
- [x] experiment_25:experiments/exp25_exante_job_validation/results/final/job_level_capacity_stress_event_slots.csv: exists and non-empty
- [x] experiment_25:experiments/exp25_exante_job_validation/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_25:experiments/exp25_exante_job_validation/README.md: exists and non-empty
- [x] experiment_26:experiments/exp26_end_to_end_certificate/results/final/end_to_end_lineage.csv: exists and non-empty
- [x] experiment_26:experiments/exp26_end_to_end_certificate/results/final/profile_role_lineage.csv: exists and non-empty
- [x] experiment_26:experiments/exp26_end_to_end_certificate/results/final/payment_relative_cap_audit.csv: exists and non-empty
- [x] experiment_26:experiments/exp26_end_to_end_certificate/results/final/realized_payment_audit.csv: exists and non-empty
- [x] experiment_26:experiments/exp26_end_to_end_certificate/results/final/end_to_end_certificate.json: exists and non-empty
- [x] experiment_26:experiments/exp26_end_to_end_certificate/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_26:experiments/exp26_end_to_end_certificate/README.md: exists and non-empty
- [x] paper_sources:paper/main.tex: exists and non-empty
- [x] paper_sources:paper/main.pdf: exists and non-empty
- [x] paper_sources:paper/IEEEtran.cls: exists and non-empty
- [x] paper_sources:paper/references.bib: exists and non-empty
- [x] paper_sources:paper/formula_source_matrix.md: exists and non-empty
- [x] paper_sources:paper/model_formulation.md: exists and non-empty
- [x] paper_sources:paper/paper_outline_zh.md: exists and non-empty
- [x] paper_sources:paper/theoretical_results.md: exists and non-empty
- [x] paper_sources:paper/figures/framework_architecture.drawio: exists and non-empty
- [x] paper_sources:paper/figures/framework_architecture.svg: exists and non-empty
- [x] paper_sources:paper/figures/method_detail.drawio: exists and non-empty
- [x] paper_sources:paper/figures/method_detail.svg: exists and non-empty
- [x] paper_sources:paper/figures/fig0_framework.pdf: exists and non-empty
- [x] paper_sources:paper/figures/fig0_framework.png: exists and non-empty
- [x] paper_sources:paper/figures/fig_method_detail.pdf: exists and non-empty
- [x] paper_sources:paper/figures/fig_method_detail.png: exists and non-empty
- [x] paper_sources:paper/figures/fig17_cross_layer_robustness.png: exists and non-empty
- [x] paper_sources:paper/figures/fig17_cross_layer_robustness.pdf: exists and non-empty
- [x] canonical_unified_manifest_preserved: 28/28 stages recorded; canonical request=all; audit status=running
- [x] all_png_figures_decodable_and_high_resolution: fig15_ac_opf_validation.png=4195x1253; fig15b_ac_n1_contingency_validation.png=4069x1221; fig15c_preventive_ac_n1_validation.png=4069x1221; fig16_spatial_scale_robustness.png=4261x1253; fig18_rolling_market_validation.png=3493x2309; fig19_real_trace_replay.png=4133x1221; fig20_job_level_fidelity.png=4064x1221; fig21_interval_payment_certificate.png=4197x1221; fig22_ledger_capacity_provenance.png=4364x1189; fig23_decision_time_information.png=5093x1253; fig24_preventive_ac_cross_network.png=3877x1189; fig1_manipulation_phase_diagram.png=3042x1189; fig2_response_and_migration.png=3045x1125; fig25_trace_meter_replay.png=2341x1253; fig26_independent_event_replay.png=2309x1253; fig27_all_outage_security.png=2309x1253; fig3_baseline_verification_performance.png=4645x1365; fig4_tuning_and_ablation.png=3429x2277; fig4b_intervention_robustness.png=3493x1253; fig5_settlement_value_alignment.png=4181x1221; fig6_network_loading_heatmap.png=2975x1317; fig6b_settlement_factor_decomposition.png=3077x1221; fig7_spatial_response_case.png=2917x1957; fig8_ieee118_data_center_topology.png=2597x2213; fig9_cross_network_robustness.png=4345x1253; fig10_binding_constraint_stress.png=3619x1157; fig11_exact_value_allocation.png=4100x1221; fig12_eight_participant_scaling.png=4005x1221; fig12b_exact_20_participant_scaling.png=3973x1189; fig13_n1_security_validation.png=4069x1221; fig14_payment_certificate.png=4037x1205; fig0_framework.png=1800x797; fig17_cross_layer_robustness.png=4101x1189; fig_method_detail.png=1800x643
- [x] model_formula_citation_traceability: 26/26 required source keys in bibliography, formula-source matrix, and complete formulation
- [x] no_drafting_or_stale_claim_residue: none found
- [x] all_float_labels_are_referenced: all labels have an in-text reference
- [x] table_count_within_tsg_limit: 5 tables; the locked paper limit is five
- [x] figure_count_is_explicit: 2 figures in the manuscript source
- [x] introduction_has_no_subsections: Introduction is a single section
- [x] conclusion_has_no_subsections: Conclusion is a single section
- [x] critical_claim_scope_and_lineage_phrases_present: all C1--C5 scope anchors present
- [x] official_ieee_journal_template: manuscript uses the vendored official IEEEtran journal class
- [x] maximum_two_sources_per_citation_group: 38 in-text citation groups checked
- [x] complete_manuscript_bibliography: 30 verified bibliography entries; 30 unique in-text citations; uncited=[]; missing=[]
- [x] sha256:data/raw/burstgpt/BurstGPT_without_fails_1.csv: raw source deferred to verified archive; locked processed artifact retained
- [x] sha256:data/raw/burstgpt/BurstGPT_without_fails_2.csv: raw source deferred to verified archive; locked processed artifact retained
- [x] sha256:data/raw/mit_supercloud/scheduler_data.csv: raw source deferred to verified archive; locked processed artifact retained
- [x] sha256:data/raw/mit_supercloud/dcgm_verified_full.csv: raw source deferred to verified archive; locked processed artifact retained
- [x] sha256:data/raw/pglib/pglib_opf_case118_ieee.m: b1af0833849040c04babc3700631cff0d9afa66b79c5d3e13ae79bdf516cec78
- [x] full_burstgpt_rows: 5188507
- [x] full_measured_gpu_jobs: 68664
- [x] full_join_vs_common_trace_horizon_counts: full immutable join=71128, common tensor window=68664, excluded by horizon=2464
- [x] chronological_submit_time_calibration_boundary: submit-time entitlement calibration is chronological and kept separate from the complete scheduler population; execution matching is not an Exp19 eligibility filter
- [x] heldout_power_conversion_scenarios_complete: 40,768 held-out jobs; q01/q10/q50/q90/q99 measured-to-predicted energy factors=0.536697, 0.669059, 0.924071, 1.409561, 4.755718
- [x] complete_source_to_evaluation_data_flow: 7 source/join/window/split stages; full immutable join 71128 -> 68664 common-window jobs; calibration 44391 train + 50791 held out
- [x] processed_data_finite_nonnegative: (11616, 4, 3)
- [x] processed_data_nonempty: 68641.934 MWh
- [x] trace_observed_counterfactual_complete: (11616, 4)
- [x] locked_days_have_complete_history_and_future_coverage: days 45--114; 6 future days available for the 512-slot deadline
- [x] workload_conservation: max gap=8.882e-16 MWh
- [x] data_center_capacity: violation=0.000e+00 MW
- [x] deadline_feasibility: violation=0.000e+00 MWh
- [x] sced_power_balance: gap=0.000e+00 MW
- [x] sced_line_limits: max loading=1.000000 pu
- [x] complete_exp1_grid: 56/56
- [x] strategic_threshold_theory_matches_optimizer: 56/56 price-probability cells
- [x] locked_test_set_complete: 648/648 outcomes
- [x] two_sided_credit_band_certificate: 54/54 locked days satisfy the predeclared lower and upper physical credit band
- [x] decision_time_information_boundary_panel: 216/216 rows; post-gate arrivals are excluded from all committed deployment-time decisions; positive committed response is settled only after the observable contract-capped rule, while the complete-ledger row remains an explicit post-event information comparator
- [x] decision_time_independent_trace_replay: 216 event-gate profiles are scored against the independent meter tensor in a separate observational panel
- [x] decision_time_committed_response_protocol: committed-ledger response is a second masked-ledger LP with the declared DR-price objective, rolling state, and explicit contract cap
- [x] decision_time_protocol_role_separation: gate diagnostic, deployable response, and complete-ledger comparator are separately named
- [x] causal_response_grid_selection: 42 masked-ledger response candidates select one DR price/regularization pair on validation only under the declared false-credit budget
- [x] causal_reserve_is_validation_selected_and_payment_ineligible: 4 validation candidates select eta=0.60 under the declared false-credit budget; the held-out reserve is reported for capacity planning while committed-ledger payment remains separate
- [x] cross_network_ac_n1_admissibility_panel: 9648 AC outcomes over four public networks; native-case AC admissibility and validation-only scaling recorded
- [x] homogeneous_scale_has_fixed_nameplate_bound: capacity-proportional and fixed-nameplate scales are reported separately; the certified peak remains within the committed capacity without a second LP
- [x] declared_homogeneous_scale_sensitivity_panel: 4 predeclared homogeneous transforms replay the same witness and resource caps; the panel records where the fixed-GPU nameplate stops being respected
- [x] closest_literature_baseline_panel: 324/324 same-ledger published-equation translations; each implementation is identified as a transparent translation rather than a software reimplementation
- [x] exact_structural_dc_t_dc_st_baseline_panel: 108/108 same-ledger DC-T/DC-ST outcomes retain native-site and migration assignment as explicit structural controls
- [x] independent_trace_meter_replay_panel: 648 locked-day method scores against the measured DCGM execution tensor; no event intervention or simulated response is used as scoring truth
- [x] literature_baseline_fairness_contract: 8 controls use the same ledger, deadlines, capacities, event slots, and locked days; structural translations are not labelled as software reimplementations
- [x] risk_effect_decomposition_separates_envelope_and_fit: 9 validation/test ablations separate total-risk, CVaR, combined convex fitting, and the final pointwise envelope
- [x] cross_experiment_locked_day_identity: 10/10 main panels use the identical locked days 61--114; mismatches=[]
- [x] dependence_robust_exact_block_tests: 18 pre-declared 3-day blocks, exact sign randomization, attainable-p audit, and Holm family-wise correction
- [x] tail_risk_counterfactual_estimator_comparison: tail-risk feasible counterfactual improves credit F1 against the single feasible projection; its nRMSE change remains below 0.05 over 18 exact temporal blocks and is reported with the exact paired p-value
- [x] closest_feasible_baseline_comparison: risk verifier has significantly lower mean false-credit exposure than the complete-ledger feasible-quantile projection; the higher mean nRMSE is retained as an explicit tradeoff (0.323961 versus 0.300888)
- [x] active_cvar_frontier_certificate: the validation-only CVaR frontier is feasible at every predeclared reserve grid contains a boundary that touches the minimum achievable CVaR under the total-risk budget; the pooled contract uses the separately recorded 0.97 tail reserve
- [x] matched_effect_sizes_with_dependence_robust_intervals: false-credit improvement over feasible quantile has a positive three-day moving-block 95% interval, while all single-projection effects are contained in their dependence-aware intervals
- [x] complete_independent_intervention_panel: 864/864 rows; all matched interventions are evaluated without a comparator-derived cap
- [x] independent_pointwise_risk_envelope: locked test false-credit is compared to the feasible-quantile reference, while the LP cap and risk budget are anchored to the independent Metadata projection rho=0.03 candidate
- [x] independent_observed_scoring_truth: locked response scores use the observed DCGM/BurstGPT meter; any event-response LP is restricted to mechanism-isolation panels
- [x] source_separated_false_credit_certificate: locked-test false-credit diagnostics are recomputed separately for the observed meter and the mechanism-isolation trajectory; neither row is labelled as a causal utility-event outcome
- [x] risk_ceiling_truth_sources_explicit: the pointwise risk-fit ceiling is labelled as an offline union of the observational and mechanism-isolation trajectories; settlement scores retain the two truth sources separately and do not assert a causal event effect
- [x] nondegenerate_risk_verifier_output: the risk-fit profile differs from the single reference; the separately stored payment-contract profile retains the independently checked two-sided band
- [x] risk_constrained_validation_dominance: convex verifier has no larger validation MSE and satisfies both total and daily-tail CVaR false-credit budgets; its normalized total-exposure preference makes the joint fit distinct from the CVaR-only ablation
- [x] nested_daily_risk_reserve_selection: 12 reserve-fold cells; selected reserve=1.00
- [x] exact_pointwise_risk_envelope_selection: 6 globally solved envelope projections; selected weight=0.1
- [x] matched_post_event_information_protocol: statistical, single-projection, and convex verifiers share the full ledger and never observe execution truth
- [x] complete_predeclared_projection_validation: 7 pre-declared validation candidates
- [x] convex_projection_simplex: 7 coefficients; sum=0.999999999978
- [x] contiguous_blocked_validation: 4 held-out temporal folds
- [x] independent_full_constraint_certificates: 162 day-variant schedules certified
- [x] exact_sparse_complexity_scaling: log-log nonzero slope=1.0025
- [x] complete_settlement_factorial_panel: 3510/3510 rows; 65/65 complete cells
- [x] paired_settlement_factor_decomposition: 702 locked day-baseline rows and 52 one-factor paired summaries separate signed netting, locational pricing, and exact valuation
- [x] independent_high_resolution_value_evaluator: 10-segment settlement versus 80-segment evaluation; trace-reference max non-circular error=719.813176 USD/day
- [x] complete_settlement_mechanism_block_tests: 52 paired mechanism tests; Holm correction within each baseline-method family
- [x] global_polyhedral_value_certificate: 5616 interval-baseline certificates; maximum subgradient-inequality violation 1.447e-11 USD
- [x] complete_cross_network_panel: 6480/6480 rows; 120/120 complete cells across 4 networks
- [x] cross_network_paired_mechanism_inference: 24 paired exact block tests; positive estimated-baseline linear-minus-exact effect in 4/12 cells; minimum effect -0.012257 USD/day; no materially negative estimated-baseline effect survives Holm correction, while the trace-anchored reference remains nonnegative in every cell
- [x] complete_cross_network_resolution_convergence: 4 complete 54-day resolution levels; highest two mean effects=-0.002333, -0.002067 USD/day; final step=0.000266 versus initial step=0.003003 USD/day, and every 95% interval contains zero
- [x] native_rating_congestion_identification: 3/12 network-loading cells exhibit endogenous congestion
- [x] native_ratings_and_predeclared_sites: all thermal-rating factors equal 1.0; fixed-site specifications invariant in 4 networks
- [x] nodal_price_effect_identified: at least one cross-network cell has a nonzero uniform-versus-nodal error contrast
- [x] complete_exact_value_allocation_panel: 1728/1728 participant-day outcomes
- [x] exact_shapley_budget_balance: maximum absolute participant-sum minus grand-coalition value=2.558e-13 USD
- [x] complete_exact_eight_participant_scaling: 3456/3456 participant-interval outcomes; all 256 coalitions enumerated per interval
- [x] exact_group_symmetric_20_participant_scaling: 1080/1080 site-day-size outcomes; exact count-state summation through 20 participants
- [x] allocation_mechanism_identification: non-efficient marginal allocation rules exhibit a nonzero budget residual
- [x] complete_binding_constraint_panel: 810/810 rows; 15/15 complete cells; max capacity binding=0.094
- [x] complete_n1_security_panel: 2592/2592 interval-mechanism outcomes; all 37 non-islanding line outages enforced
- [x] n1_mechanism_identification: trace-reference N-1 exact MAE=0.990 USD versus base-case exact MAE=139.221 USD and N-1 linear MAE=2.208 USD
- [x] scenario_robust_exact_n1_payment_noninferiority_certificate: 54/54 lexicographically solved daily certificates across five held-out conversion scenarios; formal four-segment maximum cap violation=8.935e-09 USD; the independent 40-segment transfer comparison is evaluated by its paired mean
- [x] payment_panel_lineage_matches_current_profiles_and_manifest: the payment evaluator records the current Experiment-2 test and validation profile digests, data-manifest digest, configuration digest, and certified-profile byte digest; stale row-count-complete panels are rejected
- [x] payment_cap_and_target_are_not_a_fixed_plan_identity: the contractual cap is frozen by Experiment-2 nRMSE, while the payment target is selected by an independent high-resolution N-1 payment MAE on validation days; locked test days are excluded
- [x] complete_independent_payment_model_transfer_evaluation: 1080 method-day-scenario outcomes scored across five held-out conversion factors with the independent 40-segment N-1 evaluator; accuracy is reported as model-transfer evidence and is not part of Proposition 4
- [x] paired_payment_accuracy_and_overpayment_pareto: 15 comparator-scenario rows use paired moving-block intervals for both absolute error and overpayment; the payment-cap guarantee is kept separate from any universal MAE claim
- [x] unseen_conversion_factor_transfer_panel: 8 frozen-profile outcomes across two interior conversion factors absent from the certificate and target selection; the finer N-1 replay is independent of the contractual RHS
- [x] independent_endpoint_certificate_uses_selected_single_reference: 216/216 endpoint rows compare the payment-certified profile with the preselected single feasible reference; the quantile profile remains external
- [x] payment_uncertainty_interval_has_posthoc_oracle_audit_only: 108/108 endpoint rows retain the raw q01/q99 interval; fixed and flexible demand are separated and both endpoints are solved under the q99-calibrated scale, while oracle values remain post-hoc coverage diagnostics (10/108 inside)
- [x] independent_nondegenerate_payment_candidate_hull: six first-stage projection candidates plus an external matched feasible-quantile comparator; the selected single projection is the contractual reference; the risk verifier is excluded from the certificate input and evaluated as an external target; 24 distinct daily optimal weight vectors
- [x] validation_only_payment_target_selection: seven workload-feasible candidates ranked on 384 independent validation N-1 payment cells; the selected target and DC scale are frozen before locked test evaluation
- [x] complete_nonlinear_ac_opf_panel: 864/864 converged network-day-method outcomes with AC voltage and apparent-power limits enforced
- [x] complete_nonlinear_ac_n1_panel: 5400/5400 converged method-day-outage AC OPFs across all 6 IEEE-9 and 19 IEEE-14 non-islanding line outages
- [x] complete_shared_active_plan_preventive_ac_n1_panel: 3888/3888 converged penetration-method-day-outage cells across four matched counterfactuals; all six IEEE-9 outages share the intact-state non-reference active dispatch exactly
- [x] complete_spatial_scale_factorial_panel: 16848/16848 outcomes cover all 24 regional permutations plus two concentration controls, 3 penetrations, 54 locked days, and 4 methods
- [x] feature_stratified_trace_mapping_audit: 12 trace-region panels; feature-stratified scenario is separated from physical geography and paired with the complete 24-assignment network panel
- [x] complete_continuous_horizon_market_validation: 216/216 method-day outcomes use real future arrivals, lexicographic projection, complete-cycle energy accounting, exact site budget balance, and an individually rational bilateral outside option
- [x] immutable_ledger_provenance_and_capacity_reconciliation: 216,572 submit-time rows and 71,128 matched execution rows; submission digest 122179c57225..., execution telemetry is excluded from decision provenance, and raw-to-join energy is conserved for the post-event reconciliation
- [x] measured_contiguous_job_interval_witness: all 71,128 immutable joined jobs retain measured contiguous intervals, runtime/GPU/native-power fields, and zero release/deadline violations; the witness is separate from the aggregate flow LP
- [x] exact_job_indexed_counterfactual_certificate: all valid scheduler submissions enter an exact submit-time contiguous start-time model; execution matching is reported separately and declared-energy/job residuals are zero
- [x] declared_timelimit_counterfactual_boundary: submit-time runtime declarations plus the precommitted queue allowance are used (window slots 97--680), observed completion is excluded, and net/gross/rebound arithmetic is explicit
- [x] heldout_power_conversion_capacity_safe_sensitivity: 5 held-out ratio endpoints are explicit; capacity-safe clipping remains below the precommitted nameplate
- [x] physical_calibration_is_separate_from_utility_scale: 44,391/50,791 chronological train/test GPU-power observations are reconciled with finite MAE/RMSE/R2 while raw measurement and declared spatial mapping remain explicitly separated from utility-scale claims
- [x] exact_job_to_network_coupling_certificate: the submitted-job indexed witness is aggregated before secure N-1 settlement; residual is zero and no second profile optimization is used
- [x] coupled_replay_covers_all_rts24_n1_contingencies: the raw indexed witness and two homogeneous scale transforms solve the public RTS-24 native/counterfactual cases with all 37 finite outages
- [x] independent_job_primal_recheck_before_network_value: the stored indexed service vector independently satisfies every job-energy equality, committed GPU nameplate bound, and regional capacity row before the network replay
- [x] typed_dimension_preserving_coupling_certificate: one typed certificate checks job equalities, GPU/capacity bounds, job-to-region aggregation, and MWh-to-MW network mapping before settlement
- [x] independent_controlled_event_replay: 54 locked days are replayed under a predeclared tariff intervention; the independently parameterized meter policy differs from the gate policy, is scored without verifier outputs, and makes no field-causal claim
- [x] ex_ante_submission_job_validation_and_binding_capacity_panel: the declaration-only job validation covers the complete submitted population, while a compact 79-job stress cohort binds regional capacity and satisfies its service floor with numerical residuals below 1e-8
- [x] full_finite_n1_frozen_profile_panel: 864 frozen-profile cells evaluate all 37 finite RTS-24 non-islanding outages without AC screening or post-solution workload adjustment
- [x] end_to_end_lineage_certificate: Exp26 recomputes the indexed witness-to-network residuals, retains separate risk/payment roles, and closes the relative-cap and all-outage chain
- [x] no_stale_atomic_temporary_artifacts: no hidden atomic-writer temporary files remain

## Locked test-set baseline results

| method | nrmse | false_response_ratio | false_response_mwh | credit_precision | credit_recall | credit_f1 | bias_mw |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Ex-post Metadata Gradient Boosting | 2.1259 | 0.8367 | 90.8070 | 0.1633 | 0.8767 | 0.2649 | 9.0931 |
| Ex-post Quantile Gradient Boosting | 0.9322 | 0.4946 | 23.1436 | 0.5054 | 0.8197 | 0.5333 | 0.1892 |
| Extra Trees | 3.3495 | 0.8977 | 133.9613 | 0.1023 | 0.7270 | 0.1712 | 13.0639 |
| Feasible Quantile Projection | 0.3009 | 0.1954 | 2.8114 | 0.8046 | 0.4542 | 0.5188 | -0.9650 |
| Gradient Boosting | 2.3433 | 0.8484 | 96.0767 | 0.1516 | 0.8517 | 0.2453 | 9.2695 |
| High-5-of-10 | 4.1963 | 0.9178 | 172.4553 | 0.0822 | 0.7280 | 0.1425 | 17.8099 |
| Metadata Gradient Boosting | 2.2012 | 0.8412 | 92.8741 | 0.1588 | 0.8767 | 0.2588 | 9.3419 |
| Ridge | 2.7608 | 0.8546 | 109.8169 | 0.1454 | 0.8304 | 0.2333 | 11.4544 |
| Risk-Constrained Convex Verifier | 0.3240 | 0.1712 | 1.7874 | 0.8288 | 0.3643 | 0.4510 | -0.9915 |
| Single Feasible Projection | 0.3393 | 0.1971 | 1.8234 | 0.8029 | 0.3352 | 0.4184 | -0.9967 |
| Synthetic Control | 2.5978 | 0.8730 | 104.9980 | 0.1270 | 0.6631 | 0.2015 | 9.2784 |
| Tail-Risk Feasible Counterfactual | 0.3233 | 0.1702 | 1.7909 | 0.8298 | 0.3655 | 0.4524 | -0.9912 |

## Projection candidate validation

| candidate_index | projection_weight | validation_score | validation_score_std | event_window_deviation_from_optimization_only_mw | validation_credit_precision | validation_credit_recall | validation_credit_f1 | mean_contiguous_fold_nrmse | max_contiguous_fold_nrmse | selected_single_projection | candidate_type | ensemble_weight | selected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.03000 | 0.45148 | 0.28465 | 5.30061 | 0.77074 | 0.27445 | 0.37283 | 0.50115 | 0.76523 | True | metadata projection | 0.39769 | True |
| 2 | 0.10000 | 0.45148 | 0.28465 | 5.30061 | 0.77074 | 0.27445 | 0.37283 | 0.50115 | 0.76523 | False | metadata projection | 0.39769 | True |
| 3 | 0.30000 | 0.44700 | 0.28093 | 5.11314 | 0.75477 | 0.33357 | 0.42938 | 0.50224 | 0.77895 | False | metadata projection | 0.06027 | True |
| 4 | 1.00000 | 0.76564 | 0.45042 | 6.55524 | 0.55497 | 0.46973 | 0.46029 | 0.85085 | 1.20191 | False | metadata projection | 0.00000 | True |
| 5 | 3.00000 | 1.34890 | 0.71063 | 9.41060 | 0.37130 | 0.58542 | 0.39648 | 1.45326 | 1.75394 | False | metadata projection | 0.00000 | True |
| 6 | 10.00000 | 1.85273 | 0.89702 | 13.11613 | 0.26521 | 0.67491 | 0.33382 | 1.85924 | 2.25787 | False | metadata projection | 0.00000 | False |
| 6 | 1.00000 | 0.41656 | nan | nan | nan | nan | 0.54848 | nan | 0.59467 | False | feasible quantile projection | 0.14436 | True |

## Settlement results

| baseline_method | mechanism | payment_usd | realized_value_usd | absolute_error_usd | overpayment_ratio |
| --- | --- | --- | --- | --- | --- |
| Ex-post Metadata Gradient Boosting | Nodal exact net value | 2110.604 | 317.512 | 1841.156 | 0.828 |
| Ex-post Metadata Gradient Boosting | Nodal gross | 2872.704 | 317.512 | 2555.191 | 0.888 |
| Ex-post Metadata Gradient Boosting | Nodal signed linear | 2144.346 | 317.512 | 1874.654 | 0.833 |
| Ex-post Metadata Gradient Boosting | Uniform gross | 2864.828 | 317.512 | 2547.316 | 0.887 |
| Ex-post Metadata Gradient Boosting | Uniform signed net | 2140.347 | 317.512 | 1870.602 | 0.832 |
| Ex-post Quantile Gradient Boosting | Nodal exact net value | 241.779 | 317.512 | 967.038 | 0.404 |
| Ex-post Quantile Gradient Boosting | Nodal gross | 1011.379 | 317.512 | 774.655 | 0.647 |
| Ex-post Quantile Gradient Boosting | Nodal signed linear | 250.057 | 317.512 | 962.865 | 0.404 |
| Ex-post Quantile Gradient Boosting | Uniform gross | 1010.680 | 317.512 | 774.107 | 0.647 |
| Ex-post Quantile Gradient Boosting | Uniform signed net | 251.224 | 317.512 | 961.274 | 0.404 |
| Extra Trees | Nodal exact net value | 3164.674 | 317.512 | 2879.672 | 0.907 |
| Extra Trees | Nodal gross | 6345.242 | 317.512 | 6027.730 | 0.940 |
| Extra Trees | Nodal signed linear | 5302.589 | 317.512 | 4985.077 | 0.929 |
| Extra Trees | Uniform gross | 4723.082 | 317.512 | 4405.570 | 0.926 |
| Extra Trees | Uniform signed net | 3561.593 | 317.512 | 3272.243 | 0.907 |
| Feasible Quantile Projection | Nodal exact net value | 6.352 | 317.512 | 449.516 | 0.145 |
| Feasible Quantile Projection | Nodal gross | 361.071 | 317.512 | 433.173 | 0.394 |
| Feasible Quantile Projection | Nodal signed linear | 8.077 | 317.512 | 449.545 | 0.149 |
| Feasible Quantile Projection | Uniform gross | 360.431 | 317.512 | 432.748 | 0.394 |
| Feasible Quantile Projection | Uniform signed net | 11.013 | 317.512 | 448.132 | 0.185 |
| Gradient Boosting | Nodal exact net value | 2145.244 | 317.512 | 1872.353 | 0.835 |
| Gradient Boosting | Nodal gross | 2991.546 | 317.512 | 2674.033 | 0.899 |
| Gradient Boosting | Nodal signed linear | 2176.590 | 317.512 | 1903.454 | 0.838 |
| Gradient Boosting | Uniform gross | 2983.940 | 317.512 | 2666.428 | 0.899 |
| Gradient Boosting | Uniform signed net | 2173.120 | 317.512 | 1899.876 | 0.838 |
| High-5-of-10 | Nodal exact net value | 4723.662 | 317.512 | 4406.149 | 0.927 |
| High-5-of-10 | Nodal gross | 10688.261 | 317.512 | 10370.749 | 0.963 |
| High-5-of-10 | Nodal signed linear | 9577.407 | 317.512 | 9259.895 | 0.960 |
| High-5-of-10 | Uniform gross | 6879.455 | 317.512 | 6561.943 | 0.946 |
| High-5-of-10 | Uniform signed net | 5572.984 | 317.512 | 5255.472 | 0.940 |
| Metadata Gradient Boosting | Nodal exact net value | 2162.381 | 317.512 | 1873.731 | 0.834 |
| Metadata Gradient Boosting | Nodal gross | 2926.176 | 317.512 | 2608.664 | 0.885 |
| Metadata Gradient Boosting | Nodal signed linear | 2196.876 | 317.512 | 1907.998 | 0.839 |
| Metadata Gradient Boosting | Uniform gross | 2918.324 | 317.512 | 2600.812 | 0.885 |
| Metadata Gradient Boosting | Uniform signed net | 2192.820 | 317.512 | 1903.944 | 0.838 |
| Ridge | Nodal exact net value | 2668.061 | 317.512 | 2369.069 | 0.854 |
| Ridge | Nodal gross | 4363.175 | 317.512 | 4045.662 | 0.912 |
| Ridge | Nodal signed linear | 3647.013 | 317.512 | 3345.002 | 0.879 |
| Ridge | Uniform gross | 3668.740 | 317.512 | 3351.228 | 0.905 |
| Ridge | Uniform signed net | 2936.953 | 317.512 | 2636.254 | 0.867 |
| Risk-Constrained Convex Verifier | Nodal exact net value | 1.579 | 317.512 | 455.865 | 0.141 |
| Risk-Constrained Convex Verifier | Nodal gross | 265.256 | 317.512 | 421.677 | 0.342 |
| Risk-Constrained Convex Verifier | Nodal signed linear | 1.682 | 317.512 | 455.842 | 0.142 |
| Risk-Constrained Convex Verifier | Uniform gross | 264.436 | 317.512 | 421.230 | 0.341 |
| Risk-Constrained Convex Verifier | Uniform signed net | 5.304 | 317.512 | 454.651 | 0.193 |
| Single Feasible Projection | Nodal exact net value | 1.579 | 317.512 | 455.865 | 0.141 |
| Single Feasible Projection | Nodal gross | 265.256 | 317.512 | 421.677 | 0.342 |
| Single Feasible Projection | Nodal signed linear | 1.682 | 317.512 | 455.842 | 0.142 |
| Single Feasible Projection | Uniform gross | 264.436 | 317.512 | 421.230 | 0.341 |
| Single Feasible Projection | Uniform signed net | 5.304 | 317.512 | 454.651 | 0.193 |
| Synthetic Control | Nodal exact net value | 2318.645 | 317.512 | 2026.037 | 0.812 |
| Synthetic Control | Nodal gross | 4961.598 | 317.512 | 4644.086 | 0.902 |
| Synthetic Control | Nodal signed linear | 3927.015 | 317.512 | 3627.014 | 0.853 |
| Synthetic Control | Uniform gross | 3734.332 | 317.512 | 3416.820 | 0.888 |
| Synthetic Control | Uniform signed net | 2603.472 | 317.512 | 2311.198 | 0.825 |
| Tail-Risk Feasible Counterfactual | Nodal exact net value | 2.791 | 317.512 | 453.879 | 0.136 |
| Tail-Risk Feasible Counterfactual | Nodal gross | 290.218 | 317.512 | 419.451 | 0.353 |
| Tail-Risk Feasible Counterfactual | Nodal signed linear | 3.557 | 317.512 | 453.248 | 0.137 |
| Tail-Risk Feasible Counterfactual | Uniform gross | 289.525 | 317.512 | 419.053 | 0.352 |
| Tail-Risk Feasible Counterfactual | Uniform signed net | 6.653 | 317.512 | 452.186 | 0.178 |
| Trace-Anchored Reference | Nodal exact net value | 206.907 | 317.512 | 151.719 | 0.040 |
| Trace-Anchored Reference | Nodal gross | 567.725 | 317.512 | 360.580 | 0.454 |
| Trace-Anchored Reference | Nodal signed linear | 212.768 | 317.512 | 152.390 | 0.054 |
| Trace-Anchored Reference | Uniform gross | 568.004 | 317.512 | 360.528 | 0.454 |
| Trace-Anchored Reference | Uniform signed net | 214.746 | 317.512 | 150.928 | 0.097 |

## Paired settlement-factor decomposition

| baseline_method | factor | mean_error_reduction_usd | median_error_reduction_usd | paired_days | block_length_days | blocks | observed_mean_difference | extreme_assignments | total_sign_assignments | minimum_attainable_two_sided_p | two_sided_exact_p_value | block_sum_lag1_autocorrelation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Risk-Constrained Convex Verifier | gross_to_signed_error_reduction_usd | -34.1649 | -37.3378 | 54 | 3 | 18 | -34.1649 | 103848 | 262144 | 0.0000 | 0.3961 | -0.4495 |
| Risk-Constrained Convex Verifier | uniform_to_nodal_error_reduction_usd | -1.1907 | -0.2174 | 54 | 3 | 18 | -1.1907 | 75428 | 262144 | 0.0000 | 0.2877 | 0.2022 |
| Risk-Constrained Convex Verifier | linear_to_exact_error_reduction_usd | -0.0233 | 0.0000 | 54 | 3 | 18 | -0.0233 | 191602 | 262144 | 0.0000 | 0.7309 | -0.0100 |
| Risk-Constrained Convex Verifier | uniform_gross_to_exact_error_reduction_usd | -34.6349 | -37.3294 | 54 | 3 | 18 | -34.6349 | 101712 | 262144 | 0.0000 | 0.3880 | -0.4472 |
| Trace-Anchored Reference | gross_to_signed_error_reduction_usd | 208.1900 | 29.2381 | 54 | 3 | 18 | 208.1900 | 102 | 262144 | 0.0000 | 0.0004 | -0.4358 |
| Trace-Anchored Reference | uniform_to_nodal_error_reduction_usd | -1.4628 | -0.3804 | 54 | 3 | 18 | -1.4628 | 3092 | 262144 | 0.0000 | 0.0118 | 0.2293 |
| Trace-Anchored Reference | linear_to_exact_error_reduction_usd | 0.6713 | -0.0000 | 54 | 3 | 18 | 0.6713 | 210408 | 262144 | 0.0000 | 0.8026 | -0.0282 |
| Trace-Anchored Reference | uniform_gross_to_exact_error_reduction_usd | 208.8086 | 28.3550 | 54 | 3 | 18 | 208.8086 | 116 | 262144 | 0.0000 | 0.0004 | -0.4317 |

## Cross-network robustness

| network | load_multiplier | baseline_quality | mechanism | mean_absolute_error_usd | median_normalized_error | mean_overpayment_usd | congestion_share |
| --- | --- | --- | --- | --- | --- | --- | --- |
| IEEE 300-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal exact net value | 1988.066 | 1.000 | 315.867 | 0.000 |
| IEEE 300-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal gross | 2066.703 | 0.890 | 1197.678 | 0.000 |
| IEEE 300-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal signed linear | 1988.063 | 1.000 | 315.869 | 0.000 |
| IEEE 300-bus | 0.900 | Risk-Constrained Convex Verifier | Uniform gross | 2066.703 | 0.890 | 1197.678 | 0.000 |
| IEEE 300-bus | 0.900 | Risk-Constrained Convex Verifier | Uniform signed net | 1988.063 | 1.000 | 315.869 | 0.000 |
| IEEE 300-bus | 0.900 | Trace-Anchored Reference | Nodal exact net value | 6.338 | 0.002 | 6.159 | 0.000 |
| IEEE 300-bus | 0.900 | Trace-Anchored Reference | Nodal gross | 2334.594 | 1.153 | 2334.594 | 0.000 |
| IEEE 300-bus | 0.900 | Trace-Anchored Reference | Nodal signed linear | 10.033 | 0.002 | 10.019 | 0.000 |
| IEEE 300-bus | 0.900 | Trace-Anchored Reference | Uniform gross | 2334.594 | 1.153 | 2334.594 | 0.000 |
| IEEE 300-bus | 0.900 | Trace-Anchored Reference | Uniform signed net | 10.033 | 0.002 | 10.019 | 0.000 |
| IEEE 300-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal exact net value | 2255.309 | 1.000 | 357.691 | 0.000 |
| IEEE 300-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal gross | 2345.456 | 0.891 | 1360.462 | 0.000 |
| IEEE 300-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal signed linear | 2255.309 | 1.000 | 357.691 | 0.000 |
| IEEE 300-bus | 0.980 | Risk-Constrained Convex Verifier | Uniform gross | 2345.456 | 0.891 | 1360.462 | 0.000 |
| IEEE 300-bus | 0.980 | Risk-Constrained Convex Verifier | Uniform signed net | 2255.309 | 1.000 | 357.691 | 0.000 |
| IEEE 300-bus | 0.980 | Trace-Anchored Reference | Nodal exact net value | 12.271 | 0.006 | 12.152 | 0.000 |
| IEEE 300-bus | 0.980 | Trace-Anchored Reference | Nodal gross | 2657.793 | 1.158 | 2657.793 | 0.000 |
| IEEE 300-bus | 0.980 | Trace-Anchored Reference | Nodal signed linear | 15.301 | 0.006 | 15.191 | 0.000 |
| IEEE 300-bus | 0.980 | Trace-Anchored Reference | Uniform gross | 2657.793 | 1.158 | 2657.793 | 0.000 |
| IEEE 300-bus | 0.980 | Trace-Anchored Reference | Uniform signed net | 15.301 | 0.006 | 15.191 | 0.000 |
| IEEE 300-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal exact net value | 2381.084 | 1.000 | 376.594 | 0.000 |
| IEEE 300-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal gross | 2473.464 | 0.890 | 1432.147 | 0.000 |
| IEEE 300-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal signed linear | 2381.099 | 1.000 | 376.615 | 0.000 |
| IEEE 300-bus | 1.020 | Risk-Constrained Convex Verifier | Uniform gross | 2473.464 | 0.890 | 1432.147 | 0.000 |
| IEEE 300-bus | 1.020 | Risk-Constrained Convex Verifier | Uniform signed net | 2381.099 | 1.000 | 376.615 | 0.000 |
| IEEE 300-bus | 1.020 | Trace-Anchored Reference | Nodal exact net value | 7.993 | 0.003 | 7.854 | 0.000 |
| IEEE 300-bus | 1.020 | Trace-Anchored Reference | Nodal gross | 2797.691 | 1.151 | 2797.691 | 0.000 |
| IEEE 300-bus | 1.020 | Trace-Anchored Reference | Nodal signed linear | 11.360 | 0.004 | 11.313 | 0.000 |
| IEEE 300-bus | 1.020 | Trace-Anchored Reference | Uniform gross | 2797.691 | 1.151 | 2797.691 | 0.000 |
| IEEE 300-bus | 1.020 | Trace-Anchored Reference | Uniform signed net | 11.360 | 0.004 | 11.313 | 0.000 |
| IEEE 39-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal exact net value | 163.941 | 1.000 | 26.700 | 0.000 |
| IEEE 39-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal gross | 171.064 | 0.890 | 99.589 | 0.000 |
| IEEE 39-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal signed linear | 163.929 | 1.000 | 26.709 | 0.000 |
| IEEE 39-bus | 0.900 | Risk-Constrained Convex Verifier | Uniform gross | 171.064 | 0.890 | 99.589 | 0.000 |
| IEEE 39-bus | 0.900 | Risk-Constrained Convex Verifier | Uniform signed net | 163.929 | 1.000 | 26.709 | 0.000 |
| IEEE 39-bus | 0.900 | Trace-Anchored Reference | Nodal exact net value | 1.019 | 0.003 | 0.172 | 0.000 |
| IEEE 39-bus | 0.900 | Trace-Anchored Reference | Nodal gross | 191.658 | 1.152 | 191.614 | 0.000 |
| IEEE 39-bus | 0.900 | Trace-Anchored Reference | Nodal signed linear | 2.138 | 0.003 | 1.743 | 0.000 |
| IEEE 39-bus | 0.900 | Trace-Anchored Reference | Uniform gross | 191.658 | 1.152 | 191.614 | 0.000 |
| IEEE 39-bus | 0.900 | Trace-Anchored Reference | Uniform signed net | 2.138 | 0.003 | 1.743 | 0.000 |
| IEEE 39-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal exact net value | 200.574 | 1.000 | 33.119 | 0.000 |
| IEEE 39-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal gross | 210.266 | 0.889 | 123.475 | 0.000 |
| IEEE 39-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal signed linear | 200.574 | 1.000 | 33.119 | 0.000 |
| IEEE 39-bus | 0.980 | Risk-Constrained Convex Verifier | Uniform gross | 210.266 | 0.889 | 123.475 | 0.000 |
| IEEE 39-bus | 0.980 | Risk-Constrained Convex Verifier | Uniform signed net | 200.574 | 1.000 | 33.119 | 0.000 |
| IEEE 39-bus | 0.980 | Trace-Anchored Reference | Nodal exact net value | 1.609 | 0.007 | 1.246 | 0.000 |
| IEEE 39-bus | 0.980 | Trace-Anchored Reference | Nodal gross | 237.987 | 1.186 | 237.987 | 0.000 |
| IEEE 39-bus | 0.980 | Trace-Anchored Reference | Nodal signed linear | 3.639 | 0.007 | 3.479 | 0.000 |
| IEEE 39-bus | 0.980 | Trace-Anchored Reference | Uniform gross | 237.987 | 1.186 | 237.987 | 0.000 |
| IEEE 39-bus | 0.980 | Trace-Anchored Reference | Uniform signed net | 3.639 | 0.007 | 3.479 | 0.000 |
| IEEE 39-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal exact net value | 228.902 | 1.000 | 41.037 | 0.012 |
| IEEE 39-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal gross | 248.436 | 0.895 | 151.005 | 0.012 |
| IEEE 39-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal signed linear | 229.168 | 1.000 | 41.314 | 0.012 |
| IEEE 39-bus | 1.020 | Risk-Constrained Convex Verifier | Uniform gross | 245.719 | 0.895 | 148.088 | 0.012 |
| IEEE 39-bus | 1.020 | Risk-Constrained Convex Verifier | Uniform signed net | 227.721 | 1.000 | 39.722 | 0.012 |
| IEEE 39-bus | 1.020 | Trace-Anchored Reference | Nodal exact net value | 2.985 | 0.013 | 0.935 | 0.012 |
| IEEE 39-bus | 1.020 | Trace-Anchored Reference | Nodal gross | 271.158 | 1.200 | 270.859 | 0.012 |
| IEEE 39-bus | 1.020 | Trace-Anchored Reference | Nodal signed linear | 7.433 | 0.013 | 6.333 | 0.012 |
| IEEE 39-bus | 1.020 | Trace-Anchored Reference | Uniform gross | 271.158 | 1.200 | 270.859 | 0.012 |
| IEEE 39-bus | 1.020 | Trace-Anchored Reference | Uniform signed net | 7.433 | 0.013 | 6.333 | 0.012 |
| IEEE RTS 24-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal exact net value | 108.843 | 1.000 | 17.551 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal gross | 113.538 | 0.890 | 66.156 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal signed linear | 108.839 | 1.000 | 17.554 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Risk-Constrained Convex Verifier | Uniform gross | 113.538 | 0.890 | 66.156 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Risk-Constrained Convex Verifier | Uniform signed net | 108.839 | 1.000 | 17.554 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Trace-Anchored Reference | Nodal exact net value | 0.200 | 0.002 | 0.030 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Trace-Anchored Reference | Nodal gross | 128.133 | 1.160 | 128.125 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Trace-Anchored Reference | Nodal signed linear | 1.050 | 0.003 | 0.994 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Trace-Anchored Reference | Uniform gross | 128.133 | 1.160 | 128.125 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Trace-Anchored Reference | Uniform signed net | 1.050 | 0.003 | 0.994 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal exact net value | 338.369 | 1.000 | 53.722 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal gross | 351.854 | 0.891 | 204.264 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal signed linear | 338.359 | 1.000 | 53.722 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Risk-Constrained Convex Verifier | Uniform gross | 351.854 | 0.891 | 204.264 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Risk-Constrained Convex Verifier | Uniform signed net | 338.359 | 1.000 | 53.722 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Trace-Anchored Reference | Nodal exact net value | 0.571 | 0.002 | 0.219 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Trace-Anchored Reference | Nodal gross | 398.225 | 1.158 | 398.141 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Trace-Anchored Reference | Nodal signed linear | 1.527 | 0.002 | 1.380 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Trace-Anchored Reference | Uniform gross | 398.225 | 1.158 | 398.141 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Trace-Anchored Reference | Uniform signed net | 1.527 | 0.002 | 1.380 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal exact net value | 357.342 | 1.000 | 56.291 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal gross | 370.739 | 0.890 | 214.186 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal signed linear | 357.338 | 1.000 | 56.295 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Risk-Constrained Convex Verifier | Uniform gross | 370.739 | 0.890 | 214.186 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Risk-Constrained Convex Verifier | Uniform signed net | 357.338 | 1.000 | 56.295 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Trace-Anchored Reference | Nodal exact net value | 0.311 | 0.001 | 0.209 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Trace-Anchored Reference | Nodal gross | 418.046 | 1.142 | 418.046 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Trace-Anchored Reference | Nodal signed linear | 0.840 | 0.001 | 0.810 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Trace-Anchored Reference | Uniform gross | 418.046 | 1.142 | 418.046 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Trace-Anchored Reference | Uniform signed net | 0.840 | 0.001 | 0.810 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal exact net value | 352.853 | 1.000 | 55.906 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal gross | 367.291 | 0.895 | 213.560 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal signed linear | 352.853 | 1.000 | 55.906 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Risk-Constrained Convex Verifier | Uniform gross | 367.293 | 0.895 | 213.563 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Risk-Constrained Convex Verifier | Uniform signed net | 352.853 | 1.000 | 55.906 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Trace-Anchored Reference | Nodal exact net value | 3.007 | 0.009 | 2.864 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Trace-Anchored Reference | Nodal gross | 418.523 | 1.161 | 418.523 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Trace-Anchored Reference | Nodal signed linear | 3.375 | 0.010 | 3.251 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Trace-Anchored Reference | Uniform gross | 418.526 | 1.161 | 418.526 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Trace-Anchored Reference | Uniform signed net | 3.376 | 0.009 | 3.251 | 0.000 |
| PGLib IEEE 118-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal exact net value | 400.727 | 1.000 | 63.832 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal gross | 416.125 | 0.889 | 240.941 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal signed linear | 400.724 | 1.000 | 63.832 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Risk-Constrained Convex Verifier | Uniform gross | 416.126 | 0.889 | 240.942 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Risk-Constrained Convex Verifier | Uniform signed net | 400.725 | 1.000 | 63.833 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Trace-Anchored Reference | Nodal exact net value | 2.231 | 0.006 | 0.690 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Trace-Anchored Reference | Nodal gross | 467.501 | 1.135 | 467.431 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Trace-Anchored Reference | Nodal signed linear | 3.141 | 0.005 | 2.183 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Trace-Anchored Reference | Uniform gross | 467.501 | 1.135 | 467.431 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Trace-Anchored Reference | Uniform signed net | 3.141 | 0.005 | 2.183 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal exact net value | 426.528 | 1.000 | 68.053 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal gross | 445.144 | 0.895 | 259.467 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal signed linear | 426.882 | 1.000 | 68.450 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Risk-Constrained Convex Verifier | Uniform gross | 445.154 | 0.895 | 259.483 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Risk-Constrained Convex Verifier | Uniform signed net | 426.882 | 1.000 | 68.453 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Trace-Anchored Reference | Nodal exact net value | 3.170 | 0.007 | 3.013 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Trace-Anchored Reference | Nodal gross | 506.570 | 1.167 | 506.570 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Trace-Anchored Reference | Nodal signed linear | 4.824 | 0.007 | 4.713 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Trace-Anchored Reference | Uniform gross | 506.583 | 1.167 | 506.583 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Trace-Anchored Reference | Uniform signed net | 4.828 | 0.007 | 4.716 | 1.000 |

## Binding-constraint stress test

| capacity_multiplier | deadline_multiplier | day | capacity_binding_share | deadline_binding_share | estimator_schema_version | mae_mw | rmse_mw | nrmse | nmae | normalization_mean_truth_mw | bias_mw | max_abs_error_mw | paid_response_mwh | contract_capped_response_mwh | meter_capped_response_mwh | meter_capped_false_response_mwh | meter_capped_underpayment_mwh | oracle_matched_response_mwh | oracle_response_mwh | false_response_mwh | false_response_ratio | underestimation_mwh | credit_precision | credit_recall | credit_f1 | net_system_response_mwh |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.5500 | 0.2500 | 87.5000 | 0.0313 | 0.9107 | 3.0000 | 2.6825 | 3.6677 | 0.2866 | 0.2128 | 12.0798 | -1.1020 | 10.5725 | 13.1666 | 13.1666 | 13.1666 | 2.7836 | 11.3397 | 10.3830 | 21.7228 | 2.7836 | 0.2025 | 11.3397 | 0.7975 | 0.4307 | 0.4913 | -0.6425 |
| 0.5500 | 0.5000 | 87.5000 | 0.0313 | 0.9001 | 3.0000 | 2.6825 | 3.6694 | 0.2867 | 0.2128 | 12.0798 | -1.1020 | 10.6207 | 13.1742 | 13.1742 | 13.1742 | 2.7836 | 11.3322 | 10.3906 | 21.7228 | 2.7836 | 0.2025 | 11.3322 | 0.7975 | 0.4310 | 0.4916 | -0.6425 |
| 0.5500 | 1.0000 | 87.5000 | 0.0313 | 0.8723 | 3.0000 | 2.6816 | 3.6682 | 0.2867 | 0.2127 | 12.0798 | -1.1020 | 10.6207 | 13.1640 | 13.1640 | 13.1640 | 2.7803 | 11.3390 | 10.3837 | 21.7228 | 2.7803 | 0.2023 | 11.3390 | 0.7977 | 0.4308 | 0.4914 | -0.6425 |
| 0.7000 | 0.2500 | 87.5000 | 0.0208 | 0.9107 | 3.0000 | 2.6905 | 3.7668 | 0.2925 | 0.2132 | 12.0798 | -1.1017 | 11.3953 | 12.9355 | 12.9355 | 12.9355 | 2.5491 | 11.3363 | 10.3865 | 21.7228 | 2.5491 | 0.1973 | 11.3363 | 0.8027 | 0.4310 | 0.4945 | -0.6405 |
| 0.7000 | 0.5000 | 87.5000 | 0.0208 | 0.9001 | 3.0000 | 2.6905 | 3.7662 | 0.2924 | 0.2132 | 12.0798 | -1.1017 | 11.3953 | 12.9319 | 12.9319 | 12.9319 | 2.5491 | 11.3400 | 10.3828 | 21.7228 | 2.5491 | 0.1974 | 11.3400 | 0.8026 | 0.4307 | 0.4943 | -0.6405 |
| 0.7000 | 1.0000 | 87.5000 | 0.0208 | 0.8723 | 3.0000 | 2.6886 | 3.7643 | 0.2923 | 0.2131 | 12.0798 | -1.1017 | 11.3953 | 12.9133 | 12.9133 | 12.9133 | 2.5415 | 11.3510 | 10.3718 | 21.7228 | 2.5415 | 0.1969 | 11.3510 | 0.8031 | 0.4303 | 0.4941 | -0.6405 |
| 0.8500 | 0.2500 | 87.5000 | 0.0150 | 0.9107 | 3.0000 | 2.7043 | 3.8620 | 0.2983 | 0.2140 | 12.0798 | -1.0997 | 11.8931 | 12.8273 | 12.8273 | 12.8273 | 2.4700 | 11.3654 | 10.3574 | 21.7228 | 2.4700 | 0.1955 | 11.3654 | 0.8045 | 0.4299 | 0.4950 | -0.6243 |
| 0.8500 | 0.5000 | 87.5000 | 0.0150 | 0.9001 | 3.0000 | 2.7043 | 3.8614 | 0.2983 | 0.2140 | 12.0798 | -1.0997 | 11.8931 | 12.8237 | 12.8237 | 12.8237 | 2.4700 | 11.3691 | 10.3537 | 21.7228 | 2.4700 | 0.1955 | 11.3691 | 0.8045 | 0.4296 | 0.4948 | -0.6243 |
| 0.8500 | 1.0000 | 87.5000 | 0.0150 | 0.8723 | 3.0000 | 2.7024 | 3.8595 | 0.2981 | 0.2139 | 12.0798 | -1.0997 | 11.8931 | 12.8051 | 12.8051 | 12.8051 | 2.4624 | 11.3801 | 10.3427 | 21.7228 | 2.4624 | 0.1950 | 11.3801 | 0.8050 | 0.4292 | 0.4946 | -0.6243 |
| 1.0000 | 0.2500 | 87.5000 | 0.0112 | 0.9107 | 3.0000 | 2.7042 | 3.8667 | 0.2986 | 0.2140 | 12.0798 | -1.0989 | 12.0629 | 12.7418 | 12.7418 | 12.7418 | 2.4026 | 11.3835 | 10.3393 | 21.7228 | 2.4026 | 0.1932 | 11.3835 | 0.8068 | 0.4290 | 0.4955 | -0.6179 |
| 1.0000 | 0.5000 | 87.5000 | 0.0112 | 0.9001 | 3.0000 | 2.7032 | 3.8672 | 0.2986 | 0.2139 | 12.0798 | -1.0989 | 12.1111 | 12.7395 | 12.7395 | 12.7395 | 2.3983 | 11.3816 | 10.3412 | 21.7228 | 2.3983 | 0.1929 | 11.3816 | 0.8071 | 0.4291 | 0.4957 | -0.6179 |
| 1.0000 | 1.0000 | 87.5000 | 0.0112 | 0.8723 | 3.0000 | 2.7040 | 3.8671 | 0.2986 | 0.2140 | 12.0798 | -1.0989 | 12.0629 | 12.7437 | 12.7437 | 12.7437 | 2.4017 | 11.3808 | 10.3420 | 21.7228 | 2.4017 | 0.1931 | 11.3808 | 0.8069 | 0.4292 | 0.4957 | -0.6179 |
| 1.2000 | 0.2500 | 87.5000 | 0.0076 | 0.9107 | 3.0000 | 2.7042 | 3.8980 | 0.3005 | 0.2140 | 12.0798 | -1.0989 | 12.4999 | 12.8526 | 12.8526 | 12.8526 | 2.5118 | 11.3820 | 10.3408 | 21.7228 | 2.5118 | 0.1965 | 11.3820 | 0.8035 | 0.4291 | 0.4938 | -0.6179 |
| 1.2000 | 0.5000 | 87.5000 | 0.0076 | 0.9001 | 3.0000 | 2.7032 | 3.8985 | 0.3006 | 0.2139 | 12.0798 | -1.0989 | 12.5481 | 12.8503 | 12.8503 | 12.8503 | 2.5076 | 11.3801 | 10.3427 | 21.7228 | 2.5076 | 0.1963 | 11.3801 | 0.8037 | 0.4292 | 0.4939 | -0.6179 |
| 1.2000 | 1.0000 | 87.5000 | 0.0076 | 0.8723 | 3.0000 | 2.7040 | 3.8976 | 0.3005 | 0.2140 | 12.0798 | -1.0989 | 12.4999 | 12.8514 | 12.8514 | 12.8514 | 2.5110 | 11.3823 | 10.3405 | 21.7228 | 2.5110 | 0.1965 | 11.3823 | 0.8035 | 0.4290 | 0.4937 | -0.6179 |

## Exact multi-participant value allocation

| baseline_quality | allocation_method | mean_participant_absolute_error_usd | mean_absolute_budget_residual_usd | max_absolute_budget_residual_usd | mean_absolute_total_value_error_usd |
| --- | --- | --- | --- | --- | --- |
| Risk-Constrained Convex Verifier | Exact Shapley net value | 86.0122 | 0.0000 | 0.0000 | 304.3777 |
| Risk-Constrained Convex Verifier | Leave-one-out marginal | 87.9307 | 22.3985 | 1095.7696 | 323.9489 |
| Risk-Constrained Convex Verifier | Nodal signed linear | 83.1864 | 0.1030 | 1.5533 | 304.3545 |
| Risk-Constrained Convex Verifier | Standalone avoided cost | 86.4065 | 22.0835 | 1078.7588 | 294.5093 |
| Trace-Anchored Reference | Exact Shapley net value | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Trace-Anchored Reference | Leave-one-out marginal | 0.7937 | 2.4323 | 32.7110 | 2.4323 |
| Trace-Anchored Reference | Nodal signed linear | 1.7944 | 5.8614 | 96.5283 | 5.8614 |
| Trace-Anchored Reference | Standalone avoided cost | 0.7766 | 2.1226 | 23.9720 | 2.1226 |

## Complete N-1 security-aware settlement

| baseline_quality | mechanism | mean_absolute_error_usd | median_absolute_error_usd | mean_overpayment_usd | mean_payment_usd | mean_realized_n1_value_usd | maximum_post_contingency_loading |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Risk-Constrained Convex Verifier | Base-case exact net value | 167.3667 | 121.0110 | 107.6921 | 1.8774 | -46.1401 | 1.0000 |
| Risk-Constrained Convex Verifier | N-1 exact net value | 150.9550 | 113.4349 | 20.1779 | -156.7394 | -46.1401 | 1.0000 |
| Risk-Constrained Convex Verifier | N-1 signed linear | 150.4607 | 113.4349 | 20.3755 | -155.8498 | -46.1401 | 1.0000 |
| Trace-Anchored Reference | Base-case exact net value | 139.2210 | 79.7874 | 130.4194 | 75.4777 | -46.1401 | 1.0000 |
| Trace-Anchored Reference | N-1 exact net value | 0.9897 | 0.8727 | 0.0066 | -47.1166 | -46.1401 | 1.0000 |
| Trace-Anchored Reference | N-1 signed linear | 2.2076 | 0.5963 | 1.9122 | -44.5233 | -46.1401 | 1.0000 |

## Scenario-robust N-1 payment certificate

| conversion_scenario | conversion_scale_factor | counterfactual_method | mean_payment_usd | mean_realized_value_usd | mean_absolute_error_usd | mean_overpayment_usd | maximum_post_contingency_loading |
| --- | --- | --- | --- | --- | --- | --- | --- |
| q01 | 0.5367 | Feasible Quantile Projection | -22.3602 | -5.9360 | 21.2247 | 2.4002 | 1.0000 |
| q01 | 0.5367 | Payment-Certified N-1 Verifier | -28.1598 | -5.9360 | 24.2490 | 1.0126 | 1.0000 |
| q01 | 0.5367 | Risk-Constrained Convex Verifier | -21.0918 | -5.9360 | 20.4044 | 2.6243 | 1.0000 |
| q01 | 0.5367 | Single Feasible Projection | -20.8976 | -5.9360 | 20.2928 | 2.6656 | 1.0000 |
| q10 | 0.6691 | Feasible Quantile Projection | -27.8914 | -7.4033 | 26.4681 | 2.9900 | 1.0000 |
| q10 | 0.6691 | Payment-Certified N-1 Verifier | -35.1237 | -7.4033 | 30.2468 | 1.2632 | 1.0000 |
| q10 | 0.6691 | Risk-Constrained Convex Verifier | -26.3101 | -7.4033 | 25.4455 | 3.2693 | 1.0000 |
| q10 | 0.6691 | Single Feasible Projection | -26.0680 | -7.4033 | 25.3061 | 3.3207 | 1.0000 |
| q50 | 0.9241 | Feasible Quantile Projection | -38.5658 | -10.2390 | 36.5873 | 4.1302 | 1.0000 |
| q50 | 0.9241 | Payment-Certified N-1 Verifier | -48.5384 | -10.2390 | 41.7930 | 1.7468 | 1.0000 |
| q50 | 0.9241 | Risk-Constrained Convex Verifier | -36.3787 | -10.2390 | 35.1732 | 4.5167 | 1.0000 |
| q50 | 0.9241 | Single Feasible Projection | -36.0429 | -10.2390 | 34.9784 | 4.5873 | 1.0000 |
| q90 | 1.4096 | Feasible Quantile Projection | -58.9879 | -15.6883 | 55.8960 | 6.2982 | 1.0000 |
| q90 | 1.4096 | Payment-Certified N-1 Verifier | -74.1436 | -15.6883 | 63.7789 | 2.6618 | 1.0000 |
| q90 | 1.4096 | Risk-Constrained Convex Verifier | -55.6302 | -15.6883 | 53.7319 | 6.8950 | 1.0000 |
| q90 | 1.4096 | Single Feasible Projection | -55.1126 | -15.6883 | 53.4274 | 7.0015 | 1.0000 |
| q99 | 4.7557 | Feasible Quantile Projection | -203.3368 | -56.5548 | 191.2669 | 22.2424 | 1.0000 |
| q99 | 4.7557 | Payment-Certified N-1 Verifier | -255.1526 | -56.5548 | 217.4971 | 9.4497 | 1.0000 |
| q99 | 4.7557 | Risk-Constrained Convex Verifier | -191.7283 | -56.5548 | 183.9120 | 24.3692 | 1.0000 |
| q99 | 4.7557 | Single Feasible Projection | -189.8408 | -56.5548 | 182.6756 | 24.6948 | 1.0000 |

## Validation-frozen payment target selection

| candidate_index | candidate_name | mean_validation_payment_mae_usd | validation_cells | selected | candidate_checksum |
| --- | --- | --- | --- | --- | --- |
| 3 | Projection rho=1 | 12.5631 | 384 | True | 9e53280068a735b675241dc6686cb31f5b545478184e5edb6066e8fd86e7f132 |
| 6 | Feasible Quantile Projection | 13.1483 | 384 | False | 9e53280068a735b675241dc6686cb31f5b545478184e5edb6066e8fd86e7f132 |
| 4 | Projection rho=3 | 13.8716 | 384 | False | 9e53280068a735b675241dc6686cb31f5b545478184e5edb6066e8fd86e7f132 |
| 2 | Projection rho=0.3 | 15.1405 | 384 | False | 9e53280068a735b675241dc6686cb31f5b545478184e5edb6066e8fd86e7f132 |
| 0 | Projection rho=0.03 | 16.5716 | 384 | False | 9e53280068a735b675241dc6686cb31f5b545478184e5edb6066e8fd86e7f132 |
| 1 | Projection rho=0.1 | 16.5716 | 384 | False | 9e53280068a735b675241dc6686cb31f5b545478184e5edb6066e8fd86e7f132 |
| 5 | Projection rho=10 | 19.2951 | 384 | False | 9e53280068a735b675241dc6686cb31f5b545478184e5edb6066e8fd86e7f132 |

## Nonlinear AC out-of-model validation

| network | counterfactual_method | mean_absolute_error_usd_per_h | mean_overpayment_usd_per_h | maximum_apparent_line_loading | maximum_voltage_violation_pu |
| --- | --- | --- | --- | --- | --- |
| IEEE 118-bus | Feasible Quantile Projection | 742.6245 | 609.1889 | 0.0422 | 0.0000 |
| IEEE 118-bus | Payment-Certified N-1 Verifier | 608.1960 | 514.0094 | 0.0422 | 0.0000 |
| IEEE 118-bus | Risk-Constrained Convex Verifier | 984.5385 | 865.9394 | 0.0422 | 0.0000 |
| IEEE 118-bus | Single Feasible Projection | 1035.4820 | 917.0893 | 0.0422 | 0.0000 |
| IEEE 30-bus | Feasible Quantile Projection | 3.2676 | 2.6808 | 1.0000 | 0.0000 |
| IEEE 30-bus | Payment-Certified N-1 Verifier | 2.6186 | 2.1530 | 1.0000 | 0.0000 |
| IEEE 30-bus | Risk-Constrained Convex Verifier | 4.3372 | 3.8169 | 1.0000 | 0.0000 |
| IEEE 30-bus | Single Feasible Projection | 4.5631 | 4.0439 | 1.0000 | 0.0000 |
| IEEE 39-bus | Feasible Quantile Projection | 405.8947 | 334.8821 | 1.0000 | 0.0000 |
| IEEE 39-bus | Payment-Certified N-1 Verifier | 324.5776 | 272.1122 | 0.9918 | 0.0000 |
| IEEE 39-bus | Risk-Constrained Convex Verifier | 537.5825 | 474.5058 | 1.0000 | 0.0000 |
| IEEE 39-bus | Single Feasible Projection | 565.5102 | 502.5390 | 1.0000 | 0.0000 |
| IEEE RTS 24-bus | Feasible Quantile Projection | 625.6584 | 512.8464 | 0.9387 | 0.0000 |
| IEEE RTS 24-bus | Payment-Certified N-1 Verifier | 508.0135 | 427.1849 | 0.9430 | 0.0000 |
| IEEE RTS 24-bus | Risk-Constrained Convex Verifier | 830.1866 | 730.1277 | 0.9391 | 0.0000 |
| IEEE RTS 24-bus | Single Feasible Projection | 873.2920 | 773.4511 | 0.9391 | 0.0000 |

## Complete nonlinear AC post-contingency validation

| network | counterfactual_method | maximum_apparent_line_loading | maximum_voltage_violation_pu | minimum_voltage_pu | maximum_voltage_pu | evaluated_outages | locked_days |
| --- | --- | --- | --- | --- | --- | --- | --- |
| IEEE 14-bus | Feasible Quantile Projection | 0.01815 | 0.00000 | 0.95541 | 1.06000 | 19 | 54 |
| IEEE 14-bus | Payment-Certified N-1 Verifier | 0.01813 | 0.00000 | 0.95541 | 1.06000 | 19 | 54 |
| IEEE 14-bus | Risk-Constrained Convex Verifier | 0.01815 | 0.00000 | 0.95541 | 1.06000 | 19 | 54 |
| IEEE 14-bus | Single Feasible Projection | 0.01815 | 0.00000 | 0.95541 | 1.06000 | 19 | 54 |
| IEEE 9-bus | Feasible Quantile Projection | 0.88374 | 0.00000 | 0.93331 | 1.10000 | 6 | 54 |
| IEEE 9-bus | Payment-Certified N-1 Verifier | 0.88390 | 0.00000 | 0.93334 | 1.10000 | 6 | 54 |
| IEEE 9-bus | Risk-Constrained Convex Verifier | 0.88498 | 0.00000 | 0.93331 | 1.10000 | 6 | 54 |
| IEEE 9-bus | Single Feasible Projection | 0.88507 | 0.00000 | 0.93331 | 1.10000 | 6 | 54 |

## Complete spatial-assignment and power-scale robustness

| peak_dc_penetration | counterfactual_method | mean_absolute_error_usd | median_absolute_error_usd | maximum_absolute_error_usd | mean_overpayment_usd | maximum_line_loading | maximum_lmp_spread_usd_per_mwh | assignments | locked_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.0300 | Feasible Quantile Projection | 81.6129 | 29.0419 | 755.3907 | 69.1606 | 1.0000 | 0.1442 | 26 | 54 |
| 0.0300 | Risk-Constrained Convex Verifier | 101.6242 | 36.7083 | 764.7427 | 89.5042 | 1.0000 | 0.1442 | 26 | 54 |
| 0.0300 | Single Feasible Projection | 105.2496 | 36.3022 | 765.5620 | 93.1447 | 1.0000 | 0.1442 | 26 | 54 |
| 0.0300 | Trace-Anchored Reference | 31.7764 | 11.1439 | 236.9023 | 28.0696 | 1.0000 | 0.1442 | 26 | 54 |
| 0.0600 | Feasible Quantile Projection | 164.2485 | 58.2876 | 1523.6920 | 139.2696 | 1.0000 | 0.1442 | 26 | 54 |
| 0.0600 | Risk-Constrained Convex Verifier | 204.3001 | 73.6957 | 1542.3960 | 179.9786 | 1.0000 | 0.1442 | 26 | 54 |
| 0.0600 | Single Feasible Projection | 211.5555 | 72.8835 | 1544.0345 | 187.2643 | 1.0000 | 0.1442 | 26 | 54 |
| 0.0600 | Trace-Anchored Reference | 64.5669 | 22.5669 | 484.1751 | 57.0734 | 1.0000 | 0.1442 | 26 | 54 |
| 0.0900 | Feasible Quantile Projection | 244.4809 | 87.5899 | 2309.2032 | 206.9110 | 1.0000 | 16.9387 | 26 | 54 |
| 0.0900 | Risk-Constrained Convex Verifier | 304.6033 | 110.7297 | 2337.2591 | 268.0156 | 1.0000 | 16.9387 | 26 | 54 |
| 0.0900 | Single Feasible Projection | 315.4901 | 109.5114 | 2339.7169 | 278.9480 | 1.0000 | 16.9387 | 26 | 54 |
| 0.0900 | Trace-Anchored Reference | 96.5696 | 33.4172 | 848.5617 | 84.0543 | 1.0000 | 0.1442 | 26 | 54 |

## Continuous-horizon space-time market validation

| counterfactual_method | mean_event_only_absolute_error_usd | mean_full_cycle_absolute_value_residual_usd | maximum_absolute_no_event_objective_gap_usd | mean_recovery_adjustment_usd | mean_post_event_rebound_mwh | maximum_absolute_cycle_energy_residual_mwh | maximum_baseline_projection_l1_mw | space_time_only_participant_ir_rate | bilateral_contract_activation_rate | bilateral_individual_rationality_rate | minimum_participant_contract_utility_usd | minimum_operator_contract_utility_usd | maximum_budget_balance_residual_usd | maximum_bilateral_budget_balance_residual_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Feasible Quantile Projection | 26.936862 | 0.620640 | 99.894857 | -11.214153 | 0.118606 | 0.000001 | 0.000005 | 0.000000 | 1.000000 | 1.000000 | 1.932376 | 1.932376 | 0.000000 | 0.000000 |
| Payment-Certified N-1 Verifier | 15.968885 | 0.606818 | 100.762481 | -0.255946 | 0.118606 | 0.000001 | 0.000005 | 0.000000 | 1.000000 | 1.000000 | 1.932376 | 1.932376 | 0.000000 | 0.000000 |
| Risk-Constrained Convex Verifier | 5.325029 | 0.000000 | 0.000000 | -5.325019 | 0.199456 | 0.000001 | 0.000005 | 0.000000 | 1.000000 | 1.000000 | 1.932376 | 1.932376 | 0.000000 | 0.000000 |
| Single Feasible Projection | 5.325029 | 0.000000 | 0.000000 | -5.325019 | 0.199456 | 0.000001 | 0.000005 | 0.000000 | 1.000000 | 1.000000 | 1.932376 | 1.932376 | 0.000000 | 0.000000 |

## Dependence-robust paired tests

- High-5-of-10 | nrmse: comparator-minus-proposed mean difference 3.8724, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- High-5-of-10 | false_response_ratio: comparator-minus-proposed mean difference 0.7466, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- High-5-of-10 | credit_f1: comparator-minus-proposed mean difference 0.3085, two-sided exact block-sign p=1.526e-05, Holm-adjusted p=0.0001068 (18 nonoverlapping blocks).
- Metadata Gradient Boosting | nrmse: comparator-minus-proposed mean difference 1.8772, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Metadata Gradient Boosting | false_response_ratio: comparator-minus-proposed mean difference 0.6699, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Metadata Gradient Boosting | credit_f1: comparator-minus-proposed mean difference 0.1922, two-sided exact block-sign p=0.003281, Holm-adjusted p=0.009842 (18 nonoverlapping blocks).
- Ex-post Metadata Gradient Boosting | nrmse: comparator-minus-proposed mean difference 1.8019, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Ex-post Metadata Gradient Boosting | false_response_ratio: comparator-minus-proposed mean difference 0.6654, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Ex-post Metadata Gradient Boosting | credit_f1: comparator-minus-proposed mean difference 0.1861, two-sided exact block-sign p=0.004982, Holm-adjusted p=0.009964 (18 nonoverlapping blocks).
- Ex-post Quantile Gradient Boosting | nrmse: comparator-minus-proposed mean difference 0.6083, two-sided exact block-sign p=8.392e-05, Holm-adjusted p=0.0001831 (18 nonoverlapping blocks).
- Ex-post Quantile Gradient Boosting | false_response_ratio: comparator-minus-proposed mean difference 0.3234, two-sided exact block-sign p=4.578e-05, Holm-adjusted p=0.0001373 (18 nonoverlapping blocks).
- Ex-post Quantile Gradient Boosting | credit_f1: comparator-minus-proposed mean difference -0.0823, two-sided exact block-sign p=0.07497, Holm-adjusted p=0.07497 (18 nonoverlapping blocks).
- Synthetic Control | nrmse: comparator-minus-proposed mean difference 2.2739, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Synthetic Control | false_response_ratio: comparator-minus-proposed mean difference 0.7018, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Synthetic Control | credit_f1: comparator-minus-proposed mean difference 0.2495, two-sided exact block-sign p=0.0006943, Holm-adjusted p=0.002777 (18 nonoverlapping blocks).
- Feasible Quantile Projection | nrmse: comparator-minus-proposed mean difference -0.0231, two-sided exact block-sign p=0.135, Holm-adjusted p=0.135 (18 nonoverlapping blocks).
- Feasible Quantile Projection | false_response_ratio: comparator-minus-proposed mean difference 0.0242, two-sided exact block-sign p=0.1106, Holm-adjusted p=0.1106 (18 nonoverlapping blocks).
- Feasible Quantile Projection | credit_f1: comparator-minus-proposed mean difference -0.0677, two-sided exact block-sign p=3.815e-05, Holm-adjusted p=0.0001907 (18 nonoverlapping blocks).
- Single Feasible Projection | nrmse: comparator-minus-proposed mean difference 0.0153, two-sided exact block-sign p=6.104e-05, Holm-adjusted p=0.0001831 (18 nonoverlapping blocks).
- Single Feasible Projection | false_response_ratio: comparator-minus-proposed mean difference 0.0259, two-sided exact block-sign p=0.0001526, Holm-adjusted p=0.0003052 (18 nonoverlapping blocks).
- Single Feasible Projection | credit_f1: comparator-minus-proposed mean difference 0.0326, two-sided exact block-sign p=1.526e-05, Holm-adjusted p=0.0001068 (18 nonoverlapping blocks).

## Scope and limitations

- BurstGPT exposes workload tokens but not facility power; token traces are scaled to an explicitly documented hyperscale capacity target.
- MIT SuperCloud provides measured GPU energy for its own workload, which is independently aggregated and scaled; it is not claimed to be a co-located trace from the same operator.
- All 24 mappings of the four measured regional traces to the four declared IEEE-118 connection buses and three predeclared power penetrations are evaluated, but these public traces are not claimed to be co-located utility and facility measurements.
- The final workload credit is constrained by a predeclared two-sided band around the selected single feasible projection; the upper side certifies false-credit noninferiority and the lower side bounds additional under-credit by the declared tolerance.
- The complete N-1 panel certifies preventive feasibility for every finite non-islanding line outage in the lossless continuous DC model; it is not an AC voltage, transient-stability, or island-balancing certificate.
- The nonlinear AC outage panel solves a separate corrective post-contingency optimum for every non-islanding IEEE-9 and IEEE-14 line outage; it is not a simultaneous preventive AC security-constrained OPF or a transient-stability certificate.
- The shared-active-plan preventive AC panel fixes non-reference active generation across every finite non-islanding IEEE-9 outage, with reactive-power, voltage, and reference-generator loss recourse; it is not a transient-stability or intertemporal unit-commitment certificate.
- The event-gate information panel removes post-gate arrivals before optimization and uses the locked execution trace only for scoring; its complete-ledger comparator quantifies information cost rather than defining a deployable gate policy.
- The cross-network AC panel is a fixed-active-plan preventive AC-OPF certificate over every native-case admissible non-islanding outage in four public networks; it is a steady-state feasibility result and not a transient-stability or intertemporal unit-commitment certificate.
