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
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/risk_reserve_nested_cv.csv: exists and non-empty
- [x] experiment_2:experiments/exp2_baseline_verification/results/final/risk_reserve_validation_summary.csv: exists and non-empty
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
- [x] manuscript_sources:manuscript/main.tex: exists and non-empty
- [x] manuscript_sources:manuscript/main.pdf: exists and non-empty
- [x] manuscript_sources:manuscript/IEEEtran.cls: exists and non-empty
- [x] manuscript_sources:manuscript/references.bib: exists and non-empty
- [x] manuscript_sources:manuscript/formula_source_matrix.md: exists and non-empty
- [x] manuscript_sources:manuscript/model_formulation.md: exists and non-empty
- [x] manuscript_sources:manuscript/paper_outline_zh.md: exists and non-empty
- [x] manuscript_sources:manuscript/theoretical_results.md: exists and non-empty
- [x] manuscript_sources:manuscript/figures/framework_architecture.drawio: exists and non-empty
- [x] manuscript_sources:manuscript/figures/framework_architecture.svg: exists and non-empty
- [x] manuscript_sources:manuscript/figures/method_detail.drawio: exists and non-empty
- [x] manuscript_sources:manuscript/figures/method_detail.svg: exists and non-empty
- [x] manuscript_sources:manuscript/figures/fig0_framework.pdf: exists and non-empty
- [x] manuscript_sources:manuscript/figures/fig0_framework.png: exists and non-empty
- [x] manuscript_sources:manuscript/figures/fig_method_detail.pdf: exists and non-empty
- [x] manuscript_sources:manuscript/figures/fig_method_detail.png: exists and non-empty
- [x] manuscript_sources:manuscript/figures/fig17_cross_layer_robustness.png: exists and non-empty
- [x] manuscript_sources:manuscript/figures/fig17_cross_layer_robustness.pdf: exists and non-empty
- [x] canonical_unified_manifest_preserved: 21/21 stages recorded; canonical request=all; audit status=completed
- [x] all_png_figures_decodable_and_high_resolution: fig15_ac_opf_validation.png=4195x1253; fig15b_ac_n1_contingency_validation.png=4069x1221; fig15c_preventive_ac_n1_validation.png=4069x1221; fig16_spatial_scale_robustness.png=4261x1253; fig18_rolling_market_validation.png=3493x2309; fig19_real_trace_replay.png=4133x1221; fig20_job_level_fidelity.png=4064x1221; fig21_interval_payment_certificate.png=4197x1221; fig22_ledger_capacity_provenance.png=4364x1189; fig23_decision_time_information.png=5093x1253; fig24_preventive_ac_cross_network.png=3877x1189; fig1_manipulation_phase_diagram.png=3042x1189; fig2_response_and_migration.png=3045x1125; fig3_baseline_verification_performance.png=4261x1205; fig4_tuning_and_ablation.png=3429x2277; fig4b_intervention_robustness.png=3493x1253; fig5_settlement_value_alignment.png=4036x1221; fig6_network_loading_heatmap.png=2975x1317; fig6b_settlement_factor_decomposition.png=3077x1221; fig7_spatial_response_case.png=2917x1957; fig8_ieee118_data_center_topology.png=2597x2213; fig9_cross_network_robustness.png=4335x1253; fig10_binding_constraint_stress.png=3619x1157; fig11_exact_value_allocation.png=4100x1221; fig12_eight_participant_scaling.png=4005x1221; fig12b_exact_20_participant_scaling.png=3973x1189; fig13_n1_security_validation.png=4069x1221; fig14_payment_certificate.png=4037x1205; fig0_framework.png=1800x797; fig17_cross_layer_robustness.png=4101x1189; fig_method_detail.png=1800x643
- [x] model_formula_citation_traceability: 31/31 required source keys in bibliography, formula-source matrix, and complete formulation
- [x] official_ieee_journal_template: manuscript uses the vendored official IEEEtran journal class
- [x] maximum_two_sources_per_citation_group: 40 in-text citation groups checked
- [x] complete_manuscript_bibliography: 33 verified bibliography entries; 33 unique in-text citations; uncited=[]; missing=[]
- [x] sha256:data/raw/burstgpt/BurstGPT_without_fails_1.csv: a4d068a7113ec0290e74063a1b3447dc6001a30e4298eb313581b71006dda1f4
- [x] sha256:data/raw/burstgpt/BurstGPT_without_fails_2.csv: 56193aa9b2bb26128ded43d2d29a960df6bf5af062bcfc9b005f3fcaa4e6e501
- [x] sha256:data/raw/mit_supercloud/scheduler_data.csv: 80c0b5bbe1c99b3920aa088bbc583fab01379d948c3ad7bcfa9ce524b0e9c092
- [x] sha256:data/raw/mit_supercloud/dcgm_verified_full.csv: 1b0a31722ef297745d9741ec0e68eeda8e40e2e3838fefaf61f1cac792c509c4
- [x] sha256:data/raw/pglib/pglib_opf_case118_ieee.m: b1af0833849040c04babc3700631cff0d9afa66b79c5d3e13ae79bdf516cec78
- [x] full_burstgpt_rows: 5188507
- [x] full_measured_gpu_jobs: 68664
- [x] full_join_vs_common_trace_horizon_counts: full immutable join=71128, common tensor window=68664, excluded by horizon=2464
- [x] heldout_power_conversion_scenarios_complete: 21,919 held-out jobs; measured-to-predicted energy factors=0.734154, 0.995724, 1.278023
- [x] complete_source_to_evaluation_data_flow: 6 source/join/window/split stages; full immutable join 71128 -> 68664 common-window jobs; calibration 66769 train + 28413 held out
- [x] processed_data_finite_nonnegative: (11616, 4, 3)
- [x] processed_data_nonempty: 68641.934 MWh
- [x] trace_observed_counterfactual_complete: (11616, 4)
- [x] locked_days_have_complete_history_and_future_coverage: days 45--114; 6 future days available for the 512-slot deadline
- [x] workload_conservation: max gap=7.105e-15 MWh
- [x] data_center_capacity: violation=0.000e+00 MW
- [x] deadline_feasibility: violation=0.000e+00 MWh
- [x] sced_power_balance: gap=0.000e+00 MW
- [x] sced_line_limits: max loading=1.000000 pu
- [x] complete_exp1_grid: 56/56
- [x] strategic_threshold_theory_matches_optimizer: 56/56 price-probability cells
- [x] locked_test_set_complete: 648/648 outcomes
- [x] two_sided_credit_band_certificate: 54/54 locked days satisfy the predeclared lower and upper physical credit band
- [x] decision_time_information_boundary_panel: 216/216 rows; post-gate arrivals are excluded from all committed deployment-time decisions; positive committed response is settled only after the observable contract-capped rule, while the complete-ledger row remains an explicit post-event information comparator
- [x] decision_time_committed_response_protocol: committed-ledger response is a second masked-ledger LP with the declared DR-price objective, rolling state, and explicit contract cap
- [x] decision_time_protocol_role_separation: gate diagnostic, deployable response, and complete-ledger comparator are separately named
- [x] causal_response_grid_selection: 16 masked-ledger response candidates select one DR price/regularization pair on validation only under the declared false-credit budget
- [x] causal_reserve_is_validation_selected_and_payment_ineligible: 4 validation candidates select eta=0.60 under the declared false-credit budget; the held-out reserve is reported for capacity planning while committed-ledger payment remains separate
- [x] cross_network_ac_n1_admissibility_panel: 1704 AC outcomes over four public networks; native-case AC admissibility and validation-only scaling recorded
- [x] closest_literature_baseline_panel: 216/216 same-ledger structural-analogue outcomes; proxy labels and cited mechanisms are explicit rather than presented as reimplementations
- [x] exact_structural_dc_t_dc_st_baseline_panel: 108/108 same-ledger DC-T/DC-ST outcomes retain native-site and migration assignment as explicit structural controls
- [x] literature_baseline_fairness_contract: 6 controls use the same ledger, deadlines, capacities, event slots, and locked days; structural translations are not labelled as software reimplementations
- [x] risk_effect_decomposition_separates_envelope_and_fit: 9 validation/test ablations separate total-risk, CVaR, combined convex fitting, and the final pointwise envelope
- [x] cross_experiment_locked_day_identity: 10/10 main panels use the identical locked days 61--114; mismatches=[]
- [x] dependence_robust_exact_block_tests: 18 pre-declared 3-day blocks, exact sign randomization, attainable-p audit, and Holm family-wise correction
- [x] tail_risk_counterfactual_estimator_comparison: tail-risk feasible counterfactual improves credit F1 against the single feasible projection; its nRMSE change remains below 0.02 over 18 exact temporal blocks and is reported with the exact paired p-value
- [x] closest_feasible_baseline_comparison: risk verifier has significantly lower mean false-credit exposure than the complete-ledger feasible-quantile projection; the higher mean nRMSE is retained as an explicit tradeoff (0.343382 versus 0.321370)
- [x] matched_effect_sizes_with_dependence_robust_intervals: false-credit improvement over feasible quantile has a positive three-day moving-block 95% interval, while all single-projection effects are contained in their dependence-aware intervals
- [x] complete_independent_intervention_panel: 864/864 rows; all matched interventions are evaluated without a comparator-derived cap
- [x] independent_pointwise_risk_envelope: locked test false-credit is compared to the feasible-quantile reference, while the LP cap and risk budget are anchored to the independent Metadata projection rho=0.3 candidate
- [x] nondegenerate_risk_verifier_output: the final risk-constrained profile differs from the single feasible reference while retaining the independently checked two-sided feasible band
- [x] risk_constrained_validation_dominance: convex verifier has no larger validation MSE and satisfies both total and daily-tail CVaR false-credit budgets
- [x] nested_daily_risk_reserve_selection: 16 reserve-fold cells; selected reserve=1.00
- [x] exact_pointwise_risk_envelope_selection: 6 globally solved envelope projections; selected weight=0.3
- [x] matched_post_event_information_protocol: statistical, single-projection, and convex verifiers share the full ledger and never observe execution truth
- [x] complete_predeclared_projection_validation: 7 pre-declared validation candidates
- [x] convex_projection_simplex: 7 coefficients; sum=1.000000000000
- [x] contiguous_blocked_validation: 4 held-out temporal folds
- [x] independent_full_constraint_certificates: 162 day-variant schedules certified
- [x] exact_sparse_complexity_scaling: log-log nonzero slope=1.0025
- [x] complete_settlement_factorial_panel: 3510/3510 rows; 65/65 complete cells
- [x] paired_settlement_factor_decomposition: 702 locked day-baseline rows and 52 one-factor paired summaries separate signed netting, locational pricing, and exact valuation
- [x] independent_high_resolution_value_evaluator: 10-segment settlement versus 80-segment evaluation; trace-reference max non-circular error=719.813176 USD/day
- [x] complete_settlement_mechanism_block_tests: 52 paired mechanism tests; Holm correction within each baseline-method family
- [x] global_polyhedral_value_certificate: 5616 interval-baseline certificates; maximum subgradient-inequality violation 1.526e-11 USD
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
- [x] scenario_robust_exact_n1_payment_noninferiority_certificate: 54/54 lexicographically solved daily certificates across three held-out conversion scenarios; maximum cap violation=3.827e-09 USD
- [x] complete_independent_payment_model_transfer_evaluation: 648 method-day-scenario outcomes scored with the independent 40-segment N-1 evaluator; accuracy is reported as model-transfer evidence and is not part of Proposition 4
- [x] unseen_conversion_factor_transfer_panel: 8 frozen-profile outcomes across two interior conversion factors absent from the certificate and target selection; the finer N-1 replay is independent of the contractual RHS
- [x] independent_endpoint_certificate_uses_selected_single_reference: 216/216 endpoint rows compare the payment-certified profile with the preselected single feasible reference; the quantile profile remains external
- [x] payment_uncertainty_interval_has_posthoc_oracle_audit_only: 108/108 endpoint intervals use two validation-frozen feasible profiles; finite oracle values are retained only for post-hoc coverage auditing (4/108 inside) and cannot select the hull
- [x] independent_nondegenerate_payment_candidate_hull: six first-stage projection candidates plus an external matched feasible-quantile comparator; the selected single projection is the contractual reference; the risk verifier is excluded from the certificate input and evaluated as an external target; 9 distinct daily optimal weight vectors
- [x] validation_only_payment_target_selection: seven workload-feasible candidates ranked on 384 independent validation N-1 payment cells; the selected target and DC scale are frozen before locked test evaluation
- [x] complete_nonlinear_ac_opf_panel: 864/864 converged network-day-method outcomes with AC voltage and apparent-power limits enforced
- [x] complete_nonlinear_ac_n1_panel: 5400/5400 converged method-day-outage AC OPFs across all 6 IEEE-9 and 19 IEEE-14 non-islanding line outages
- [x] complete_shared_active_plan_preventive_ac_n1_panel: 3888/3888 converged penetration-method-day-outage cells across four matched counterfactuals; all six IEEE-9 outages share the intact-state non-reference active dispatch exactly
- [x] complete_spatial_scale_factorial_panel: 16848/16848 outcomes cover all 24 regional permutations plus two concentration controls, 3 penetrations, 54 locked days, and 4 methods
- [x] feature_stratified_trace_mapping_audit: 12 trace-region panels; feature-stratified scenario is separated from physical geography and paired with the complete 24-assignment network panel
- [x] complete_continuous_horizon_market_validation: 216/216 method-day outcomes use real future arrivals, lexicographic projection, complete-cycle energy accounting, exact site budget balance, and an individually rational bilateral outside option
- [x] immutable_ledger_provenance_and_capacity_reconciliation: 71,128 joined jobs, canonical digest fdf49ad75d30..., raw-to-join energy conserved, and the pre-split committed capacity is enforced through the declared capacity-safe calibration envelope
- [x] measured_contiguous_job_interval_witness: all 71,128 immutable joined jobs retain measured contiguous intervals, runtime/GPU/native-power fields, and zero release/deadline violations; the witness is separate from the aggregate flow LP
- [x] exact_job_indexed_counterfactual_certificate: all positive-energy jobs enter an exact release/deadline LP with GPU-count-derived bounds, zero job-energy residual, and no capacity violation; the counterfactual remains explicitly preemptive
- [x] declared_timelimit_counterfactual_boundary: submit-time declarations are used (window slots 1--584), observed completion is excluded, and net/gross/rebound arithmetic is explicit
- [x] heldout_power_conversion_capacity_safe_sensitivity: 5 held-out ratio endpoints are explicit; capacity-safe clipping remains below the precommitted nameplate
- [x] physical_calibration_is_separate_from_utility_scale: 66,769/28,413 held-out GPU-power observations are reconciled with finite MAE/RMSE/R2 while raw measurement and declared spatial mapping remain explicitly separated from utility-scale claims

## Locked test-set baseline results

| method | nrmse | false_response_ratio | false_response_mwh | credit_precision | credit_recall | credit_f1 | bias_mw |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Ex-post Metadata Gradient Boosting | 2.1237 | 0.8348 | 91.6033 | 0.1652 | 0.8688 | 0.2674 | 9.2494 |
| Ex-post Quantile Gradient Boosting | 0.9445 | 0.4892 | 24.1563 | 0.5108 | 0.8102 | 0.5316 | 0.3078 |
| Extra Trees | 3.3356 | 0.8928 | 132.9709 | 0.1072 | 0.7261 | 0.1768 | 13.0340 |
| Feasible Quantile Projection | 0.3214 | 0.1922 | 2.9175 | 0.8078 | 0.4379 | 0.5080 | -0.9680 |
| Gradient Boosting | 2.3514 | 0.8471 | 97.0571 | 0.1529 | 0.8409 | 0.2459 | 9.4688 |
| High-5-of-10 | 4.2144 | 0.9169 | 172.7089 | 0.0831 | 0.7226 | 0.1439 | 17.7745 |
| Metadata Gradient Boosting | 2.1329 | 0.8361 | 90.5894 | 0.1639 | 0.8669 | 0.2645 | 9.0619 |
| Ridge | 2.7724 | 0.8528 | 110.6662 | 0.1472 | 0.8297 | 0.2351 | 11.6048 |
| Risk-Constrained Convex Verifier | 0.3434 | 0.1412 | 1.7169 | 0.8588 | 0.3528 | 0.4416 | -0.9978 |
| Single Feasible Projection | 0.3452 | 0.1441 | 1.8492 | 0.8559 | 0.3539 | 0.4416 | -0.9738 |
| Synthetic Control | 2.5520 | 0.8672 | 101.8351 | 0.1328 | 0.6503 | 0.2063 | 8.8606 |
| Tail-Risk Feasible Counterfactual | 0.3308 | 0.1634 | 2.5236 | 0.8366 | 0.4077 | 0.4842 | -0.9107 |

## Projection candidate validation

| candidate_index | projection_weight | validation_score | validation_score_std | event_window_deviation_from_optimization_only_mw | validation_credit_precision | validation_credit_recall | validation_credit_f1 | mean_contiguous_fold_nrmse | max_contiguous_fold_nrmse | selected_single_projection | candidate_type | ensemble_weight | selected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.03000 | 0.48309 | 0.31911 | 5.33742 | 0.81503 | 0.28109 | 0.38675 | 0.53945 | 0.83596 | False | metadata projection | 0.00257 | True |
| 2 | 0.10000 | 0.48309 | 0.31911 | 5.33742 | 0.81503 | 0.28109 | 0.38675 | 0.53945 | 0.83596 | False | metadata projection | 0.62515 | True |
| 3 | 0.30000 | 0.48634 | 0.30283 | 5.14402 | 0.78258 | 0.34029 | 0.44293 | 0.54433 | 0.82591 | True | metadata projection | 0.00000 | False |
| 4 | 1.00000 | 0.78049 | 0.45043 | 6.61277 | 0.52756 | 0.47463 | 0.45652 | 0.85843 | 1.25644 | False | metadata projection | 0.03872 | True |
| 5 | 3.00000 | 1.33323 | 0.66261 | 9.48856 | 0.36742 | 0.59564 | 0.40061 | 1.42633 | 1.68136 | False | metadata projection | 0.04151 | True |
| 6 | 10.00000 | 1.88254 | 0.88937 | 13.38139 | 0.26331 | 0.70522 | 0.34004 | 1.87155 | 2.35240 | False | metadata projection | 0.00059 | True |
| 6 | 1.00000 | 0.47066 | nan | nan | nan | nan | 0.52200 | nan | 0.68764 | False | feasible quantile projection | 0.29146 | True |

## Settlement results

| baseline_method | mechanism | payment_usd | realized_value_usd | absolute_error_usd | overpayment_ratio |
| --- | --- | --- | --- | --- | --- |
| Ex-post Metadata Gradient Boosting | Nodal exact net value | 2144.301 | 317.512 | 1850.140 | 0.836 |
| Ex-post Metadata Gradient Boosting | Nodal gross | 2896.950 | 317.512 | 2579.438 | 0.888 |
| Ex-post Metadata Gradient Boosting | Nodal signed linear | 2176.972 | 317.512 | 1882.566 | 0.840 |
| Ex-post Metadata Gradient Boosting | Uniform gross | 2889.067 | 317.512 | 2571.555 | 0.888 |
| Ex-post Metadata Gradient Boosting | Uniform signed net | 2173.171 | 317.512 | 1878.809 | 0.840 |
| Ex-post Quantile Gradient Boosting | Nodal exact net value | 266.008 | 317.512 | 964.718 | 0.389 |
| Ex-post Quantile Gradient Boosting | Nodal gross | 1039.369 | 317.512 | 808.641 | 0.646 |
| Ex-post Quantile Gradient Boosting | Nodal signed linear | 275.454 | 317.512 | 963.641 | 0.389 |
| Ex-post Quantile Gradient Boosting | Uniform gross | 1038.584 | 317.512 | 808.017 | 0.646 |
| Ex-post Quantile Gradient Boosting | Uniform signed net | 276.792 | 317.512 | 961.728 | 0.389 |
| Extra Trees | Nodal exact net value | 3145.749 | 317.512 | 2868.989 | 0.916 |
| Extra Trees | Nodal gross | 6199.321 | 317.512 | 5881.809 | 0.942 |
| Extra Trees | Nodal signed linear | 5177.039 | 317.512 | 4861.475 | 0.940 |
| Extra Trees | Uniform gross | 4659.471 | 317.512 | 4341.958 | 0.928 |
| Extra Trees | Uniform signed net | 3527.361 | 317.512 | 3248.249 | 0.916 |
| Feasible Quantile Projection | Nodal exact net value | 2.966 | 317.512 | 448.611 | 0.131 |
| Feasible Quantile Projection | Nodal gross | 356.120 | 317.512 | 434.484 | 0.390 |
| Feasible Quantile Projection | Nodal signed linear | 5.049 | 317.512 | 448.281 | 0.135 |
| Feasible Quantile Projection | Uniform gross | 355.525 | 317.512 | 434.105 | 0.390 |
| Feasible Quantile Projection | Uniform signed net | 7.920 | 317.512 | 446.932 | 0.172 |
| Gradient Boosting | Nodal exact net value | 2187.861 | 317.512 | 1926.384 | 0.839 |
| Gradient Boosting | Nodal gross | 3018.758 | 317.512 | 2701.246 | 0.898 |
| Gradient Boosting | Nodal signed linear | 2219.979 | 317.512 | 1958.257 | 0.841 |
| Gradient Boosting | Uniform gross | 3011.087 | 317.512 | 2693.575 | 0.898 |
| Gradient Boosting | Uniform signed net | 2216.946 | 317.512 | 1955.116 | 0.841 |
| High-5-of-10 | Nodal exact net value | 4722.207 | 317.512 | 4404.694 | 0.927 |
| High-5-of-10 | Nodal gross | 10766.576 | 317.512 | 10449.064 | 0.963 |
| High-5-of-10 | Nodal signed linear | 9624.105 | 317.512 | 9306.593 | 0.960 |
| High-5-of-10 | Uniform gross | 6911.856 | 317.512 | 6594.344 | 0.946 |
| High-5-of-10 | Uniform signed net | 5568.716 | 317.512 | 5251.204 | 0.940 |
| Metadata Gradient Boosting | Nodal exact net value | 2102.714 | 317.512 | 1808.555 | 0.825 |
| Metadata Gradient Boosting | Nodal gross | 2864.843 | 317.512 | 2547.331 | 0.881 |
| Metadata Gradient Boosting | Nodal signed linear | 2134.938 | 317.512 | 1840.417 | 0.830 |
| Metadata Gradient Boosting | Uniform gross | 2857.436 | 317.512 | 2539.924 | 0.881 |
| Metadata Gradient Boosting | Uniform signed net | 2131.610 | 317.512 | 1837.107 | 0.829 |
| Ridge | Nodal exact net value | 2700.683 | 317.512 | 2400.709 | 0.858 |
| Ridge | Nodal gross | 4513.889 | 317.512 | 4196.377 | 0.914 |
| Ridge | Nodal signed linear | 3800.636 | 317.512 | 3497.644 | 0.886 |
| Ridge | Uniform gross | 3730.004 | 317.512 | 3412.492 | 0.906 |
| Ridge | Uniform signed net | 2996.953 | 317.512 | 2695.290 | 0.872 |
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
| Synthetic Control | Nodal exact net value | 2215.233 | 317.512 | 1931.950 | 0.812 |
| Synthetic Control | Nodal gross | 4696.890 | 317.512 | 4379.378 | 0.902 |
| Synthetic Control | Nodal signed linear | 3667.676 | 317.512 | 3368.008 | 0.862 |
| Synthetic Control | Uniform gross | 3588.203 | 317.512 | 3270.690 | 0.888 |
| Synthetic Control | Uniform signed net | 2477.829 | 317.512 | 2189.369 | 0.820 |
| Tail-Risk Feasible Counterfactual | Nodal exact net value | 1.827 | 317.512 | 455.730 | 0.141 |
| Tail-Risk Feasible Counterfactual | Nodal gross | 266.481 | 317.512 | 421.459 | 0.341 |
| Tail-Risk Feasible Counterfactual | Nodal signed linear | 2.303 | 317.512 | 455.334 | 0.142 |
| Tail-Risk Feasible Counterfactual | Uniform gross | 265.738 | 317.512 | 421.086 | 0.341 |
| Tail-Risk Feasible Counterfactual | Uniform signed net | 5.549 | 317.512 | 454.515 | 0.193 |
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
| Risk-Constrained Convex Verifier | linear_to_exact_error_reduction_usd | -0.0233 | 0.0000 | 54 | 3 | 18 | -0.0233 | 191590 | 262144 | 0.0000 | 0.7309 | -0.0100 |
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
| 0.5500 | 0.2500 | 87.5000 | 0.0313 | 0.9107 | 3.0000 | 2.6474 | 3.6403 | 0.2864 | 0.2106 | 12.0798 | -1.1166 | 10.6374 | 12.9720 | 12.9720 | 12.9720 | 2.7408 | 11.4916 | 10.2312 | 21.7228 | 2.7408 | 0.1983 | 11.4916 | 0.8017 | 0.4273 | 0.4910 | -0.7594 |
| 0.5500 | 0.5000 | 87.5000 | 0.0313 | 0.9001 | 3.0000 | 2.6474 | 3.6419 | 0.2865 | 0.2106 | 12.0798 | -1.1166 | 10.6658 | 12.9756 | 12.9756 | 12.9756 | 2.7408 | 11.4880 | 10.2348 | 21.7228 | 2.7408 | 0.1983 | 11.4880 | 0.8017 | 0.4275 | 0.4911 | -0.7594 |
| 0.5500 | 1.0000 | 87.5000 | 0.0313 | 0.8723 | 3.0000 | 2.6467 | 3.6412 | 0.2865 | 0.2106 | 12.0798 | -1.1166 | 10.6658 | 12.9660 | 12.9660 | 12.9660 | 2.7381 | 11.4948 | 10.2279 | 21.7228 | 2.7381 | 0.1982 | 11.4948 | 0.8018 | 0.4272 | 0.4909 | -0.7594 |
| 0.7000 | 0.2500 | 87.5000 | 0.0208 | 0.9107 | 3.0000 | 2.6568 | 3.7354 | 0.2920 | 0.2111 | 12.0798 | -1.1158 | 11.4404 | 12.7411 | 12.7411 | 12.7411 | 2.5140 | 11.4957 | 10.2271 | 21.7228 | 2.5140 | 0.1932 | 11.4957 | 0.8068 | 0.4273 | 0.4939 | -0.7534 |
| 0.7000 | 0.5000 | 87.5000 | 0.0208 | 0.9001 | 3.0000 | 2.6567 | 3.7348 | 0.2919 | 0.2111 | 12.0798 | -1.1158 | 11.4404 | 12.7367 | 12.7367 | 12.7367 | 2.5134 | 11.4995 | 10.2233 | 21.7228 | 2.5134 | 0.1932 | 11.4995 | 0.8068 | 0.4270 | 0.4937 | -0.7534 |
| 0.7000 | 1.0000 | 87.5000 | 0.0208 | 0.8723 | 3.0000 | 2.6551 | 3.7338 | 0.2918 | 0.2110 | 12.0798 | -1.1158 | 11.4404 | 12.7203 | 12.7203 | 12.7203 | 2.5069 | 11.5094 | 10.2134 | 21.7228 | 2.5069 | 0.1930 | 11.5094 | 0.8070 | 0.4267 | 0.4935 | -0.7534 |
| 0.8500 | 0.2500 | 87.5000 | 0.0150 | 0.9107 | 3.0000 | 2.6711 | 3.8332 | 0.2980 | 0.2120 | 12.0798 | -1.1122 | 11.9382 | 12.6416 | 12.6416 | 12.6416 | 2.4436 | 11.5248 | 10.1980 | 21.7228 | 2.4436 | 0.1913 | 11.5248 | 0.8087 | 0.4262 | 0.4942 | -0.7240 |
| 0.8500 | 0.5000 | 87.5000 | 0.0150 | 0.9001 | 3.0000 | 2.6710 | 3.8326 | 0.2979 | 0.2120 | 12.0798 | -1.1122 | 11.9382 | 12.6371 | 12.6371 | 12.6371 | 2.4429 | 11.5286 | 10.1942 | 21.7228 | 2.4429 | 0.1914 | 11.5286 | 0.8086 | 0.4259 | 0.4940 | -0.7240 |
| 0.8500 | 1.0000 | 87.5000 | 0.0150 | 0.8723 | 3.0000 | 2.6693 | 3.8317 | 0.2979 | 0.2119 | 12.0798 | -1.1122 | 11.9382 | 12.6208 | 12.6208 | 12.6208 | 2.4364 | 11.5385 | 10.1843 | 21.7228 | 2.4364 | 0.1912 | 11.5385 | 0.8088 | 0.4256 | 0.4939 | -0.7240 |
| 1.0000 | 0.2500 | 87.5000 | 0.0112 | 0.9107 | 3.0000 | 2.6706 | 3.8368 | 0.2982 | 0.2119 | 12.0798 | -1.1119 | 12.1278 | 12.5597 | 12.5597 | 12.5597 | 2.3761 | 11.5391 | 10.1836 | 21.7228 | 2.3761 | 0.1893 | 11.5391 | 0.8107 | 0.4255 | 0.4948 | -0.7218 |
| 1.0000 | 0.5000 | 87.5000 | 0.0112 | 0.9001 | 3.0000 | 2.6694 | 3.8376 | 0.2982 | 0.2119 | 12.0798 | -1.1119 | 12.1562 | 12.5533 | 12.5533 | 12.5533 | 2.3717 | 11.5411 | 10.1816 | 21.7228 | 2.3717 | 0.1892 | 11.5411 | 0.8108 | 0.4254 | 0.4948 | -0.7218 |
| 1.0000 | 1.0000 | 87.5000 | 0.0112 | 0.8723 | 3.0000 | 2.6703 | 3.8372 | 0.2982 | 0.2119 | 12.0798 | -1.1119 | 12.1278 | 12.5626 | 12.5626 | 12.5626 | 2.3750 | 11.5352 | 10.1875 | 21.7228 | 2.3750 | 0.1892 | 11.5352 | 0.8108 | 0.4257 | 0.4950 | -0.7218 |
| 1.2000 | 0.2500 | 87.5000 | 0.0076 | 0.9107 | 3.0000 | 2.6707 | 3.8688 | 0.3002 | 0.2120 | 12.0798 | -1.1119 | 12.5649 | 12.6723 | 12.6723 | 12.6723 | 2.4860 | 11.5365 | 10.1863 | 21.7228 | 2.4860 | 0.1925 | 11.5365 | 0.8075 | 0.4257 | 0.4932 | -0.7218 |
| 1.2000 | 0.5000 | 87.5000 | 0.0076 | 0.9001 | 3.0000 | 2.6696 | 3.8696 | 0.3002 | 0.2119 | 12.0798 | -1.1119 | 12.5933 | 12.6659 | 12.6659 | 12.6659 | 2.4816 | 11.5385 | 10.1843 | 21.7228 | 2.4816 | 0.1923 | 11.5385 | 0.8077 | 0.4256 | 0.4932 | -0.7218 |
| 1.2000 | 1.0000 | 87.5000 | 0.0076 | 0.8723 | 3.0000 | 2.6701 | 3.8682 | 0.3001 | 0.2119 | 12.0798 | -1.1119 | 12.5649 | 12.6685 | 12.6685 | 12.6685 | 2.4836 | 11.5379 | 10.1848 | 21.7228 | 2.4836 | 0.1924 | 11.5379 | 0.8076 | 0.4255 | 0.4931 | -0.7218 |

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
| q10 | 0.7342 | Feasible Quantile Projection | -142.3448 | -59.8285 | 138.9900 | 28.2368 | 1.0000 |
| q10 | 0.7342 | Payment-Certified N-1 Verifier | -145.2914 | -59.8285 | 141.9366 | 28.2368 | 1.0000 |
| q10 | 0.7342 | Risk-Constrained Convex Verifier | -128.2378 | -59.8285 | 131.0399 | 31.3153 | 1.0000 |
| q10 | 0.7342 | Single Feasible Projection | -127.9646 | -59.8285 | 131.0316 | 31.4477 | 1.0000 |
| q50 | 0.9957 | Feasible Quantile Projection | -193.9601 | -82.5630 | 189.0998 | 38.8514 | 1.0000 |
| q50 | 0.9957 | Payment-Certified N-1 Verifier | -197.9336 | -82.5630 | 193.0733 | 38.8514 | 1.0000 |
| q50 | 0.9957 | Risk-Constrained Convex Verifier | -174.5203 | -82.5630 | 178.0943 | 43.0685 | 1.0000 |
| q50 | 0.9957 | Single Feasible Projection | -174.1497 | -82.5630 | 178.0829 | 43.2481 | 1.0000 |
| q90 | 1.2780 | Feasible Quantile Projection | -249.8611 | -108.3053 | 242.7635 | 50.6038 | 1.0000 |
| q90 | 1.2780 | Payment-Certified N-1 Verifier | -254.9343 | -108.3053 | 247.8367 | 50.6038 | 1.0000 |
| q90 | 1.2780 | Risk-Constrained Convex Verifier | -224.6296 | -108.3053 | 228.6828 | 56.1792 | 1.0000 |
| q90 | 1.2780 | Single Feasible Projection | -224.1519 | -108.3053 | 228.6685 | 56.4109 | 1.0000 |

## Validation-frozen payment target selection

| candidate_index | candidate_name | mean_validation_payment_mae_usd | validation_cells | selected | candidate_checksum |
| --- | --- | --- | --- | --- | --- |
| 6 | Feasible Quantile Projection | 53.4708 | 384 | True | 0da32ae68e32dcca5f87bf3587984a1b3caac3c6702e32f6b95781c9a96496d0 |
| 3 | Projection rho=1 | 55.5653 | 384 | False | 0da32ae68e32dcca5f87bf3587984a1b3caac3c6702e32f6b95781c9a96496d0 |
| 4 | Projection rho=3 | 64.0555 | 384 | False | 0da32ae68e32dcca5f87bf3587984a1b3caac3c6702e32f6b95781c9a96496d0 |
| 2 | Projection rho=0.3 | 65.1271 | 384 | False | 0da32ae68e32dcca5f87bf3587984a1b3caac3c6702e32f6b95781c9a96496d0 |
| 0 | Projection rho=0.03 | 70.5223 | 384 | False | 0da32ae68e32dcca5f87bf3587984a1b3caac3c6702e32f6b95781c9a96496d0 |
| 1 | Projection rho=0.1 | 70.5223 | 384 | False | 0da32ae68e32dcca5f87bf3587984a1b3caac3c6702e32f6b95781c9a96496d0 |
| 5 | Projection rho=10 | 92.9437 | 384 | False | 0da32ae68e32dcca5f87bf3587984a1b3caac3c6702e32f6b95781c9a96496d0 |

## Nonlinear AC out-of-model validation

| network | counterfactual_method | mean_absolute_error_usd_per_h | mean_overpayment_usd_per_h | maximum_apparent_line_loading | maximum_voltage_violation_pu |
| --- | --- | --- | --- | --- | --- |
| IEEE 118-bus | Feasible Quantile Projection | 724.5547 | 590.0024 | 0.0422 | 0.0000 |
| IEEE 118-bus | Payment-Certified N-1 Verifier | 753.9903 | 625.9294 | 0.0422 | 0.0000 |
| IEEE 118-bus | Risk-Constrained Convex Verifier | 1035.4820 | 917.0893 | 0.0422 | 0.0000 |
| IEEE 118-bus | Single Feasible Projection | 1035.4820 | 917.0893 | 0.0422 | 0.0000 |
| IEEE 30-bus | Feasible Quantile Projection | 3.1857 | 2.5950 | 1.0000 | 0.0000 |
| IEEE 30-bus | Payment-Certified N-1 Verifier | 3.3302 | 2.7681 | 1.0000 | 0.0000 |
| IEEE 30-bus | Risk-Constrained Convex Verifier | 4.5631 | 4.0439 | 1.0000 | 0.0000 |
| IEEE 30-bus | Single Feasible Projection | 4.5631 | 4.0439 | 1.0000 | 0.0000 |
| IEEE 39-bus | Feasible Quantile Projection | 396.0524 | 324.5256 | 1.0000 | 0.0000 |
| IEEE 39-bus | Payment-Certified N-1 Verifier | 412.7755 | 344.6725 | 1.0000 | 0.0000 |
| IEEE 39-bus | Risk-Constrained Convex Verifier | 565.5102 | 502.5390 | 1.0000 | 0.0000 |
| IEEE 39-bus | Single Feasible Projection | 565.5102 | 502.5390 | 1.0000 | 0.0000 |
| IEEE RTS 24-bus | Feasible Quantile Projection | 610.3006 | 496.4845 | 0.9387 | 0.0000 |
| IEEE RTS 24-bus | Payment-Certified N-1 Verifier | 635.0652 | 526.7818 | 0.9387 | 0.0000 |
| IEEE RTS 24-bus | Risk-Constrained Convex Verifier | 873.2920 | 773.4511 | 0.9391 | 0.0000 |
| IEEE RTS 24-bus | Single Feasible Projection | 873.2920 | 773.4511 | 0.9391 | 0.0000 |

## Complete nonlinear AC post-contingency validation

| network | counterfactual_method | maximum_apparent_line_loading | maximum_voltage_violation_pu | minimum_voltage_pu | maximum_voltage_pu | evaluated_outages | locked_days |
| --- | --- | --- | --- | --- | --- | --- | --- |
| IEEE 14-bus | Feasible Quantile Projection | 0.01815 | 0.00000 | 0.95541 | 1.06000 | 19 | 54 |
| IEEE 14-bus | Payment-Certified N-1 Verifier | 0.01815 | 0.00000 | 0.95541 | 1.06000 | 19 | 54 |
| IEEE 14-bus | Risk-Constrained Convex Verifier | 0.01815 | 0.00000 | 0.95541 | 1.06000 | 19 | 54 |
| IEEE 14-bus | Single Feasible Projection | 0.01815 | 0.00000 | 0.95541 | 1.06000 | 19 | 54 |
| IEEE 9-bus | Feasible Quantile Projection | 0.88395 | 0.00000 | 0.93331 | 1.10000 | 6 | 54 |
| IEEE 9-bus | Payment-Certified N-1 Verifier | 0.88395 | 0.00000 | 0.93331 | 1.10000 | 6 | 54 |
| IEEE 9-bus | Risk-Constrained Convex Verifier | 0.88507 | 0.00000 | 0.93331 | 1.10000 | 6 | 54 |
| IEEE 9-bus | Single Feasible Projection | 0.88507 | 0.00000 | 0.93331 | 1.10000 | 6 | 54 |

## Complete spatial-assignment and power-scale robustness

| peak_dc_penetration | counterfactual_method | mean_absolute_error_usd | median_absolute_error_usd | maximum_absolute_error_usd | mean_overpayment_usd | maximum_line_loading | maximum_lmp_spread_usd_per_mwh | assignments | locked_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.0300 | Feasible Quantile Projection | 81.7204 | 29.5778 | 755.6629 | 69.2642 | 1.0000 | 0.1442 | 26 | 54 |
| 0.0300 | Risk-Constrained Convex Verifier | 98.3513 | 33.5644 | 765.8542 | 86.0609 | 1.0000 | 0.1442 | 26 | 54 |
| 0.0300 | Single Feasible Projection | 104.8677 | 34.6821 | 765.5620 | 92.7488 | 1.0000 | 0.1442 | 26 | 54 |
| 0.0300 | Trace-Anchored Reference | 31.8196 | 11.1439 | 236.9023 | 28.1129 | 1.0000 | 0.1442 | 26 | 54 |
| 0.0600 | Feasible Quantile Projection | 164.4639 | 59.3048 | 1524.1357 | 139.4771 | 1.0000 | 0.1442 | 26 | 54 |
| 0.0600 | Risk-Constrained Convex Verifier | 197.7537 | 67.3604 | 1544.6190 | 173.0917 | 1.0000 | 0.1442 | 26 | 54 |
| 0.0600 | Single Feasible Projection | 210.7905 | 69.7503 | 1544.0345 | 186.4715 | 1.0000 | 0.1442 | 26 | 54 |
| 0.0600 | Trace-Anchored Reference | 64.6541 | 22.5669 | 484.1751 | 57.1606 | 1.0000 | 0.1442 | 26 | 54 |
| 0.0900 | Feasible Quantile Projection | 244.8043 | 89.0001 | 2309.2032 | 207.2226 | 1.0000 | 16.9387 | 26 | 54 |
| 0.0900 | Risk-Constrained Convex Verifier | 291.9398 | 101.2432 | 2343.2311 | 254.6492 | 1.0000 | 20.1363 | 26 | 54 |
| 0.0900 | Single Feasible Projection | 314.3418 | 104.8636 | 2339.7169 | 277.7578 | 1.0000 | 16.9387 | 26 | 54 |
| 0.0900 | Trace-Anchored Reference | 96.7004 | 33.4172 | 848.5617 | 84.1850 | 1.0000 | 0.1442 | 26 | 54 |

## Continuous-horizon space-time market validation

| counterfactual_method | mean_event_only_error_usd | mean_full_cycle_error_usd | mean_recovery_adjustment_usd | mean_post_event_rebound_mwh | maximum_absolute_cycle_energy_residual_mwh | maximum_baseline_projection_l1_mw | space_time_only_participant_ir_rate | bilateral_contract_activation_rate | bilateral_individual_rationality_rate | minimum_participant_contract_utility_usd | minimum_operator_contract_utility_usd | maximum_budget_balance_residual_usd | maximum_bilateral_budget_balance_residual_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Feasible Quantile Projection | 29.286748 | 0.658284 | -7.947954 | 0.102389 | 0.000002 | 0.000005 | 0.000000 | 1.000000 | 1.000000 | 1.932376 | 1.932376 | 0.000000 | 0.000000 |
| Payment-Certified N-1 Verifier | 21.882164 | 0.641214 | -0.557013 | 0.102389 | 0.000002 | 0.000005 | 0.000000 | 1.000000 | 1.000000 | 1.932376 | 1.932376 | 0.000000 | 0.000000 |
| Risk-Constrained Convex Verifier | 5.325029 | 0.000000 | -5.325019 | 0.199456 | 0.000001 | 0.000005 | 0.000000 | 1.000000 | 1.000000 | 1.932376 | 1.932376 | 0.000000 | 0.000000 |
| Single Feasible Projection | 5.325029 | 0.000000 | -5.325019 | 0.199456 | 0.000001 | 0.000005 | 0.000000 | 1.000000 | 1.000000 | 1.932376 | 1.932376 | 0.000000 | 0.000000 |

## Dependence-robust paired tests

- High-5-of-10 | nrmse: comparator-minus-proposed mean difference 3.8710, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- High-5-of-10 | false_response_ratio: comparator-minus-proposed mean difference 0.7756, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- High-5-of-10 | credit_f1: comparator-minus-proposed mean difference 0.2978, two-sided exact block-sign p=2.289e-05, Holm-adjusted p=0.0001373 (18 nonoverlapping blocks).
- Metadata Gradient Boosting | nrmse: comparator-minus-proposed mean difference 1.7895, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Metadata Gradient Boosting | false_response_ratio: comparator-minus-proposed mean difference 0.6949, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Metadata Gradient Boosting | credit_f1: comparator-minus-proposed mean difference 0.1772, two-sided exact block-sign p=0.005508, Holm-adjusted p=0.02203 (18 nonoverlapping blocks).
- Ex-post Metadata Gradient Boosting | nrmse: comparator-minus-proposed mean difference 1.7803, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Ex-post Metadata Gradient Boosting | false_response_ratio: comparator-minus-proposed mean difference 0.6935, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Ex-post Metadata Gradient Boosting | credit_f1: comparator-minus-proposed mean difference 0.1742, two-sided exact block-sign p=0.008461, Holm-adjusted p=0.02538 (18 nonoverlapping blocks).
- Ex-post Quantile Gradient Boosting | nrmse: comparator-minus-proposed mean difference 0.6011, two-sided exact block-sign p=0.0001907, Holm-adjusted p=0.0005722 (18 nonoverlapping blocks).
- Ex-post Quantile Gradient Boosting | false_response_ratio: comparator-minus-proposed mean difference 0.3480, two-sided exact block-sign p=3.052e-05, Holm-adjusted p=9.155e-05 (18 nonoverlapping blocks).
- Ex-post Quantile Gradient Boosting | credit_f1: comparator-minus-proposed mean difference -0.0900, two-sided exact block-sign p=0.06565, Holm-adjusted p=0.1313 (18 nonoverlapping blocks).
- Synthetic Control | nrmse: comparator-minus-proposed mean difference 2.2087, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Synthetic Control | false_response_ratio: comparator-minus-proposed mean difference 0.7259, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Synthetic Control | credit_f1: comparator-minus-proposed mean difference 0.2354, two-sided exact block-sign p=0.0009384, Holm-adjusted p=0.004692 (18 nonoverlapping blocks).
- Feasible Quantile Projection | nrmse: comparator-minus-proposed mean difference -0.0220, two-sided exact block-sign p=0.3126, Holm-adjusted p=0.3126 (18 nonoverlapping blocks).
- Feasible Quantile Projection | false_response_ratio: comparator-minus-proposed mean difference 0.0510, two-sided exact block-sign p=0.005524, Holm-adjusted p=0.01105 (18 nonoverlapping blocks).
- Feasible Quantile Projection | credit_f1: comparator-minus-proposed mean difference -0.0664, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Single Feasible Projection | nrmse: comparator-minus-proposed mean difference 0.0018, two-sided exact block-sign p=0.05371, Holm-adjusted p=0.1074 (18 nonoverlapping blocks).
- Single Feasible Projection | false_response_ratio: comparator-minus-proposed mean difference 0.0029, two-sided exact block-sign p=0.08148, Holm-adjusted p=0.08148 (18 nonoverlapping blocks).
- Single Feasible Projection | credit_f1: comparator-minus-proposed mean difference 0.0001, two-sided exact block-sign p=0.8939, Holm-adjusted p=0.8939 (18 nonoverlapping blocks).

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
