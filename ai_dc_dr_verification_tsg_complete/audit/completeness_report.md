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
- [x] experiment_17:experiments/exp17_decision_time_information/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_17:experiments/exp17_decision_time_information/figures/fig23_decision_time_information.png: exists and non-empty
- [x] experiment_18:experiments/exp18_preventive_ac_network_panel/results/final/preventive_ac_cross_network_results.csv: exists and non-empty
- [x] experiment_18:experiments/exp18_preventive_ac_network_panel/results/final/preventive_ac_cross_network_summary.csv: exists and non-empty
- [x] experiment_18:experiments/exp18_preventive_ac_network_panel/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_18:experiments/exp18_preventive_ac_network_panel/figures/fig24_preventive_ac_cross_network.png: exists and non-empty
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
- [x] canonical_unified_manifest_preserved: 20/20 stages recorded; canonical request=all; audit status=completed
- [x] all_png_figures_decodable_and_high_resolution: fig15_ac_opf_validation.png=4195x1253; fig15b_ac_n1_contingency_validation.png=4069x1221; fig15c_preventive_ac_n1_validation.png=4069x1221; fig16_spatial_scale_robustness.png=4261x1253; fig18_rolling_market_validation.png=3493x2309; fig19_real_trace_replay.png=4133x1221; fig20_job_level_fidelity.png=4064x1221; fig21_interval_payment_certificate.png=4197x1221; fig22_ledger_capacity_provenance.png=4364x1189; fig23_decision_time_information.png=5093x1253; fig24_preventive_ac_cross_network.png=3877x1189; fig1_manipulation_phase_diagram.png=3042x1189; fig2_response_and_migration.png=3045x1125; fig3_baseline_verification_performance.png=4261x1205; fig4_tuning_and_ablation.png=3429x2277; fig4b_intervention_robustness.png=3493x1253; fig5_settlement_value_alignment.png=4036x1221; fig6_network_loading_heatmap.png=2975x1317; fig6b_settlement_factor_decomposition.png=3077x1221; fig7_spatial_response_case.png=2917x1957; fig8_ieee118_data_center_topology.png=2597x2213; fig9_cross_network_robustness.png=4335x1253; fig10_binding_constraint_stress.png=3619x1157; fig11_exact_value_allocation.png=4100x1221; fig12_eight_participant_scaling.png=4005x1221; fig12b_exact_20_participant_scaling.png=3973x1189; fig13_n1_security_validation.png=4069x1221; fig14_payment_certificate.png=4037x1205; fig0_framework.png=1800x797; fig17_cross_layer_robustness.png=4101x1189; fig_method_detail.png=1800x643
- [x] model_formula_citation_traceability: 28/28 required source keys in bibliography, formula-source matrix, and complete formulation
- [x] official_ieee_journal_template: manuscript uses the vendored official IEEEtran journal class
- [x] maximum_two_sources_per_citation_group: 44 in-text citation groups checked
- [x] complete_manuscript_bibliography: 35 verified bibliography entries; 35 unique in-text citations; uncited=[]; missing=[]
- [x] sha256:data/raw/burstgpt/BurstGPT_without_fails_1.csv: raw source deferred to verified archive; locked processed artifact retained
- [x] sha256:data/raw/burstgpt/BurstGPT_without_fails_2.csv: raw source deferred to verified archive; locked processed artifact retained
- [x] sha256:data/raw/mit_supercloud/scheduler_data.csv: raw source deferred to verified archive; locked processed artifact retained
- [x] sha256:data/raw/mit_supercloud/dcgm_verified_full.csv: raw source deferred to verified archive; locked processed artifact retained
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
- [x] decision_time_information_boundary_panel: 216/216 rows; post-gate arrivals are excluded from all committed deployment-time decisions; positive committed response is settled only after the meter-capped rule, while the complete-ledger row remains an explicit post-event information comparator
- [x] causal_reserve_is_validation_selected_and_payment_ineligible: 4 validation candidates select eta=0.60 under the declared false-credit budget; the held-out reserve is reported for capacity planning while committed-ledger payment remains separate
- [x] cross_network_ac_n1_admissibility_panel: 1698 AC outcomes over four public networks; native-case AC admissibility and validation-only scaling recorded
- [x] closest_literature_baseline_panel: 216/216 same-ledger structural-analogue outcomes; proxy labels and cited mechanisms are explicit rather than presented as reimplementations
- [x] exact_structural_dc_t_dc_st_baseline_panel: 108/108 same-ledger DC-T/DC-ST outcomes retain native-site and migration assignment as explicit structural controls
- [x] risk_effect_decomposition_separates_envelope_and_fit: 9 validation/test ablations separate total-risk, CVaR, combined convex fitting, and the final pointwise envelope
- [x] cross_experiment_locked_day_identity: 10/10 main panels use the identical locked days 61--114; mismatches=[]
- [x] dependence_robust_exact_block_tests: 18 pre-declared 3-day blocks, exact sign randomization, attainable-p audit, and Holm family-wise correction
- [x] tail_risk_counterfactual_estimator_comparison: tail-risk feasible counterfactual improves credit F1 against the single feasible projection, while its nRMSE difference is retained and nonsignificant over 18 exact temporal blocks
- [x] closest_feasible_baseline_comparison: risk verifier has significantly lower mean false-credit exposure than the complete-ledger feasible-quantile projection; the higher mean nRMSE is retained as an explicit tradeoff (0.345019 versus 0.321370)
- [x] matched_effect_sizes_with_dependence_robust_intervals: false-credit improvement over feasible quantile has a positive three-day moving-block 95% interval, while all single-projection effects are contained in their dependence-aware intervals
- [x] complete_independent_intervention_panel: 864/864 rows; all matched interventions are evaluated without a comparator-derived cap
- [x] independent_pointwise_risk_envelope: locked test false-credit is compared to the feasible-quantile reference, while the LP cap and risk budget are anchored to the independent Metadata projection rho=0.3 candidate
- [x] risk_constrained_validation_dominance: convex verifier has no larger validation MSE and satisfies both total and daily-tail CVaR false-credit budgets
- [x] nested_daily_risk_reserve_selection: 16 reserve-fold cells; selected reserve=1.00
- [x] exact_pointwise_risk_envelope_selection: 6 globally solved envelope projections; selected weight=0.03
- [x] matched_post_event_information_protocol: statistical, single-projection, and convex verifiers share the full ledger and never observe execution truth
- [x] complete_predeclared_projection_validation: 7 pre-declared validation candidates
- [x] convex_projection_simplex: 7 coefficients; sum=1.000000000000
- [x] contiguous_blocked_validation: 4 held-out temporal folds
- [x] independent_full_constraint_certificates: 162 day-variant schedules certified
- [x] exact_sparse_complexity_scaling: log-log nonzero slope=1.0025
- [x] complete_settlement_factorial_panel: 3510/3510 rows; 65/65 complete cells
- [x] paired_settlement_factor_decomposition: 702 locked day-baseline rows and 52 one-factor paired summaries separate signed netting, locational pricing, and exact valuation
- [x] independent_high_resolution_value_evaluator: 10-segment settlement versus 80-segment evaluation; trace-reference max non-circular error=9.688038 USD/day
- [x] complete_settlement_mechanism_block_tests: 52 paired mechanism tests; Holm correction within each baseline-method family
- [x] global_polyhedral_value_certificate: 5616 interval-baseline certificates; maximum subgradient-inequality violation 2.180e-11 USD
- [x] complete_cross_network_panel: 6480/6480 rows; 120/120 complete cells across 4 networks
- [x] cross_network_paired_mechanism_inference: 24 paired exact block tests; positive estimated-baseline linear-minus-exact effect in 12/12 cells; minimum effect 0.008485 USD/day; all estimated-baseline effects are nonnegative, while the trace-anchored reference must remain nonnegative in every cell
- [x] complete_cross_network_resolution_convergence: 4 complete 54-day resolution levels; highest two mean effects=0.025515, 0.030576 USD/day; final step=0.005061 versus initial step=0.010946 USD/day, and every 95% interval contains zero
- [x] native_rating_congestion_identification: 3/12 network-loading cells exhibit endogenous congestion
- [x] native_ratings_and_predeclared_sites: all thermal-rating factors equal 1.0; fixed-site specifications invariant in 4 networks
- [x] nodal_price_effect_identified: at least one cross-network cell has a nonzero uniform-versus-nodal error contrast
- [x] complete_exact_value_allocation_panel: 1728/1728 participant-day outcomes
- [x] exact_shapley_budget_balance: maximum absolute participant-sum minus grand-coalition value=2.274e-13 USD
- [x] complete_exact_eight_participant_scaling: 3456/3456 participant-interval outcomes; all 256 coalitions enumerated per interval
- [x] exact_group_symmetric_20_participant_scaling: 1080/1080 site-day-size outcomes; exact count-state summation through 20 participants
- [x] allocation_mechanism_identification: non-efficient marginal allocation rules exhibit a nonzero budget residual
- [x] complete_binding_constraint_panel: 810/810 rows; 15/15 complete cells; max capacity binding=0.099
- [x] complete_n1_security_panel: 2592/2592 interval-mechanism outcomes; all 37 non-islanding line outages enforced
- [x] n1_mechanism_identification: trace-reference N-1 exact MAE=1.018 USD versus base-case exact MAE=165.288 USD and N-1 linear MAE=2.253 USD
- [x] scenario_robust_exact_n1_payment_noninferiority_certificate: 54/54 lexicographically solved daily certificates across three held-out conversion scenarios; maximum cap violation=3.827e-09 USD
- [x] complete_independent_payment_model_transfer_evaluation: 648 method-day-scenario outcomes scored with the independent 40-segment N-1 evaluator; accuracy is reported as model-transfer evidence and is not part of Proposition 4
- [x] independent_endpoint_certificate_uses_selected_single_reference: 216/216 endpoint rows compare the payment-certified profile with the preselected single feasible reference; the quantile profile remains external
- [x] payment_uncertainty_interval_has_posthoc_oracle_audit_only: 108/108 endpoint intervals use two validation-frozen feasible profiles; finite oracle values are retained only for post-hoc coverage auditing and cannot select the hull
- [x] independent_nondegenerate_payment_candidate_hull: six first-stage projection candidates plus an external matched feasible-quantile comparator; the selected single projection is the contractual reference and the risk verifier is an external target with minimum maximum-distance 25.232 MW; 9 distinct daily optimal weight vectors
- [x] validation_only_payment_target_selection: seven workload-feasible candidates ranked on 384 independent validation N-1 payment cells; the selected target and DC scale are frozen before locked test evaluation
- [x] complete_nonlinear_ac_opf_panel: 864/864 converged network-day-method outcomes with AC voltage and apparent-power limits enforced
- [x] complete_nonlinear_ac_n1_panel: 5400/5400 converged method-day-outage AC OPFs across all 6 IEEE-9 and 19 IEEE-14 non-islanding line outages
- [x] complete_shared_active_plan_preventive_ac_n1_panel: 3888/3888 converged penetration-method-day-outage cells across four matched counterfactuals; all six IEEE-9 outages share the intact-state non-reference active dispatch exactly
- [x] complete_spatial_scale_factorial_panel: 15552/15552 outcomes cover all 24 regional assignments, 3 penetrations, 54 locked days, and 4 methods
- [x] complete_continuous_horizon_market_validation: 216/216 method-day outcomes use real future arrivals, lexicographic projection, complete-cycle energy accounting, exact site budget balance, and an individually rational bilateral outside option
- [x] immutable_ledger_provenance_and_capacity_reconciliation: 71,128 joined jobs, canonical digest fdf49ad75d30..., raw-to-join energy conserved, and the pre-split committed capacity covers the observed regional envelope as a reconciliation
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
| Risk-Constrained Convex Verifier | 0.3450 | 0.1437 | 1.8263 | 0.8563 | 0.3534 | 0.4412 | -0.9785 |
| Single Feasible Projection | 0.3452 | 0.1441 | 1.8492 | 0.8559 | 0.3539 | 0.4416 | -0.9738 |
| Synthetic Control | 2.5520 | 0.8672 | 101.8351 | 0.1328 | 0.6503 | 0.2063 | 8.8606 |
| Tail-Risk Feasible Counterfactual | 0.3308 | 0.1634 | 2.5235 | 0.8366 | 0.4077 | 0.4842 | -0.9105 |

## Projection candidate validation

| candidate_index | projection_weight | validation_score | validation_score_std | event_window_deviation_from_optimization_only_mw | validation_credit_precision | validation_credit_recall | validation_credit_f1 | mean_contiguous_fold_nrmse | max_contiguous_fold_nrmse | selected_single_projection | candidate_type | ensemble_weight | selected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.03000 | 0.48309 | 0.31911 | 5.33742 | 0.81503 | 0.28109 | 0.38675 | 0.53945 | 0.83596 | False | metadata projection | 0.31390 | True |
| 2 | 0.10000 | 0.48309 | 0.31911 | 5.33742 | 0.81503 | 0.28109 | 0.38675 | 0.53945 | 0.83596 | False | metadata projection | 0.31390 | True |
| 3 | 0.30000 | 0.48634 | 0.30283 | 5.14402 | 0.78258 | 0.34029 | 0.44293 | 0.54433 | 0.82591 | True | metadata projection | 0.00001 | True |
| 4 | 1.00000 | 0.78049 | 0.45043 | 6.61277 | 0.52756 | 0.47463 | 0.45652 | 0.85843 | 1.25644 | False | metadata projection | 0.03867 | True |
| 5 | 3.00000 | 1.33323 | 0.66261 | 9.48856 | 0.36742 | 0.59564 | 0.40061 | 1.42633 | 1.68136 | False | metadata projection | 0.04143 | True |
| 6 | 10.00000 | 1.88254 | 0.88937 | 13.38139 | 0.26331 | 0.70522 | 0.34004 | 1.87155 | 2.35240 | False | metadata projection | 0.00067 | True |
| 6 | 1.00000 | 0.47066 | nan | nan | nan | nan | 0.52200 | nan | 0.68764 | False | feasible quantile projection | 0.29141 | True |

## Settlement results

| baseline_method | mechanism | payment_usd | realized_value_usd | absolute_error_usd | overpayment_ratio |
| --- | --- | --- | --- | --- | --- |
| Ex-post Metadata Gradient Boosting | Nodal exact net value | 3195.705 | 312.936 | 2882.769 | 0.889 |
| Ex-post Metadata Gradient Boosting | Nodal gross | 4277.571 | 312.936 | 3964.635 | 0.926 |
| Ex-post Metadata Gradient Boosting | Nodal signed linear | 3210.299 | 312.936 | 2897.363 | 0.890 |
| Ex-post Metadata Gradient Boosting | Uniform gross | 4277.860 | 312.936 | 3964.923 | 0.926 |
| Ex-post Metadata Gradient Boosting | Uniform signed net | 3210.587 | 312.936 | 2897.651 | 0.890 |
| Ex-post Quantile Gradient Boosting | Nodal exact net value | 404.127 | 312.936 | 1468.268 | 0.459 |
| Ex-post Quantile Gradient Boosting | Nodal gross | 1551.190 | 312.936 | 1293.399 | 0.760 |
| Ex-post Quantile Gradient Boosting | Nodal signed linear | 413.638 | 312.936 | 1468.731 | 0.460 |
| Ex-post Quantile Gradient Boosting | Uniform gross | 1551.275 | 312.936 | 1293.481 | 0.760 |
| Ex-post Quantile Gradient Boosting | Uniform signed net | 413.723 | 312.936 | 1468.788 | 0.460 |
| Extra Trees | Nodal exact net value | 4381.131 | 312.936 | 4095.680 | 0.937 |
| Extra Trees | Nodal gross | 5888.288 | 312.936 | 5575.351 | 0.945 |
| Extra Trees | Nodal signed linear | 4476.903 | 312.936 | 4191.439 | 0.937 |
| Extra Trees | Uniform gross | 5837.395 | 312.936 | 5524.458 | 0.945 |
| Extra Trees | Uniform signed net | 4421.103 | 312.936 | 4135.624 | 0.938 |
| Feasible Quantile Projection | Nodal exact net value | 11.332 | 312.936 | 442.303 | 0.124 |
| Feasible Quantile Projection | Nodal gross | 534.669 | 312.936 | 549.310 | 0.459 |
| Feasible Quantile Projection | Nodal signed linear | 12.479 | 312.936 | 442.263 | 0.125 |
| Feasible Quantile Projection | Uniform gross | 534.772 | 312.936 | 549.406 | 0.459 |
| Feasible Quantile Projection | Uniform signed net | 12.167 | 312.936 | 441.934 | 0.162 |
| Gradient Boosting | Nodal exact net value | 3263.298 | 312.936 | 2994.724 | 0.883 |
| Gradient Boosting | Nodal gross | 4459.075 | 312.936 | 4146.138 | 0.933 |
| Gradient Boosting | Nodal signed linear | 3278.175 | 312.936 | 3009.571 | 0.884 |
| Gradient Boosting | Uniform gross | 4459.387 | 312.936 | 4146.450 | 0.933 |
| Gradient Boosting | Uniform signed net | 3278.492 | 312.936 | 3009.877 | 0.884 |
| High-5-of-10 | Nodal exact net value | 5920.771 | 312.936 | 5607.834 | 0.947 |
| High-5-of-10 | Nodal gross | 8277.693 | 312.936 | 7964.756 | 0.956 |
| High-5-of-10 | Nodal signed linear | 6777.955 | 312.936 | 6465.018 | 0.950 |
| High-5-of-10 | Uniform gross | 7684.860 | 312.936 | 7371.924 | 0.954 |
| High-5-of-10 | Uniform signed net | 6161.604 | 312.936 | 5848.668 | 0.949 |
| Metadata Gradient Boosting | Nodal exact net value | 3136.321 | 312.936 | 2823.384 | 0.884 |
| Metadata Gradient Boosting | Nodal gross | 4232.578 | 312.936 | 3919.641 | 0.921 |
| Metadata Gradient Boosting | Nodal signed linear | 3149.960 | 312.936 | 2837.024 | 0.885 |
| Metadata Gradient Boosting | Uniform gross | 4232.867 | 312.936 | 3919.931 | 0.921 |
| Metadata Gradient Boosting | Uniform signed net | 3150.250 | 312.936 | 2837.314 | 0.885 |
| Ridge | Nodal exact net value | 3936.687 | 312.936 | 3628.484 | 0.913 |
| Ridge | Nodal gross | 5000.435 | 312.936 | 4687.498 | 0.935 |
| Ridge | Nodal signed linear | 3965.235 | 312.936 | 3656.529 | 0.916 |
| Ridge | Uniform gross | 4999.837 | 312.936 | 4686.900 | 0.935 |
| Ridge | Uniform signed net | 3964.585 | 312.936 | 3655.874 | 0.916 |
| Risk-Constrained Convex Verifier | Nodal exact net value | 9.367 | 312.936 | 454.238 | 0.163 |
| Risk-Constrained Convex Verifier | Nodal gross | 417.265 | 312.936 | 501.324 | 0.398 |
| Risk-Constrained Convex Verifier | Nodal signed linear | 9.801 | 312.936 | 454.366 | 0.164 |
| Risk-Constrained Convex Verifier | Uniform gross | 417.463 | 312.936 | 501.511 | 0.398 |
| Risk-Constrained Convex Verifier | Uniform signed net | 9.557 | 312.936 | 454.116 | 0.200 |
| Single Feasible Projection | Nodal exact net value | 10.847 | 312.936 | 454.191 | 0.165 |
| Single Feasible Projection | Nodal gross | 418.745 | 312.936 | 501.700 | 0.398 |
| Single Feasible Projection | Nodal signed linear | 11.281 | 312.936 | 454.320 | 0.166 |
| Single Feasible Projection | Uniform gross | 418.943 | 312.936 | 501.888 | 0.398 |
| Single Feasible Projection | Uniform signed net | 11.037 | 312.936 | 454.069 | 0.203 |
| Synthetic Control | Nodal exact net value | 3075.486 | 312.936 | 2794.322 | 0.862 |
| Synthetic Control | Nodal gross | 4581.831 | 312.936 | 4268.895 | 0.920 |
| Synthetic Control | Nodal signed linear | 3141.501 | 312.936 | 2859.517 | 0.863 |
| Synthetic Control | Uniform gross | 4544.896 | 312.936 | 4231.959 | 0.920 |
| Synthetic Control | Uniform signed net | 3100.265 | 312.936 | 2818.277 | 0.864 |
| Tail-Risk Feasible Counterfactual | Nodal exact net value | 29.673 | 312.936 | 431.722 | 0.209 |
| Tail-Risk Feasible Counterfactual | Nodal gross | 501.044 | 312.936 | 536.256 | 0.433 |
| Tail-Risk Feasible Counterfactual | Nodal signed linear | 30.069 | 312.936 | 431.743 | 0.209 |
| Tail-Risk Feasible Counterfactual | Uniform gross | 501.149 | 312.936 | 536.352 | 0.433 |
| Tail-Risk Feasible Counterfactual | Uniform signed net | 29.864 | 312.936 | 431.520 | 0.209 |
| Trace-Anchored Reference | Nodal exact net value | 310.897 | 312.936 | 2.230 | 0.002 |
| Trace-Anchored Reference | Nodal gross | 868.403 | 312.936 | 555.910 | 0.573 |
| Trace-Anchored Reference | Nodal signed linear | 314.571 | 312.936 | 3.953 | 0.009 |
| Trace-Anchored Reference | Uniform gross | 868.416 | 312.936 | 555.923 | 0.573 |
| Trace-Anchored Reference | Uniform signed net | 314.577 | 312.936 | 3.956 | 0.046 |

## Paired settlement-factor decomposition

| baseline_method | factor | mean_error_reduction_usd | median_error_reduction_usd | paired_days | block_length_days | blocks | observed_mean_difference | extreme_assignments | total_sign_assignments | minimum_attainable_two_sided_p | two_sided_exact_p_value | block_sum_lag1_autocorrelation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Risk-Constrained Convex Verifier | gross_to_signed_error_reduction_usd | 46.9578 | -23.5317 | 54 | 3 | 18 | 46.9578 | 108380 | 262144 | 0.0000 | 0.4134 | -0.6667 |
| Risk-Constrained Convex Verifier | uniform_to_nodal_error_reduction_usd | -0.2503 | -0.0005 | 54 | 3 | 18 | -0.2503 | 5744 | 262144 | 0.0000 | 0.0219 | -0.0628 |
| Risk-Constrained Convex Verifier | linear_to_exact_error_reduction_usd | 0.1285 | -0.0000 | 54 | 3 | 18 | 0.1285 | 186086 | 262144 | 0.0000 | 0.7099 | -0.0215 |
| Risk-Constrained Convex Verifier | uniform_gross_to_exact_error_reduction_usd | 47.2736 | -23.5323 | 54 | 3 | 18 | 47.2736 | 108412 | 262144 | 0.0000 | 0.4136 | -0.6646 |
| Trace-Anchored Reference | gross_to_signed_error_reduction_usd | 551.9574 | 451.9675 | 54 | 3 | 18 | 551.9574 | 2 | 262144 | 0.0000 | 0.0000 | -0.2213 |
| Trace-Anchored Reference | uniform_to_nodal_error_reduction_usd | 0.0032 | -0.0003 | 54 | 3 | 18 | 0.0032 | 123902 | 262144 | 0.0000 | 0.4726 | 0.2946 |
| Trace-Anchored Reference | linear_to_exact_error_reduction_usd | 1.7231 | -0.2023 | 54 | 3 | 18 | 1.7231 | 72072 | 262144 | 0.0000 | 0.2749 | -0.1439 |
| Trace-Anchored Reference | uniform_gross_to_exact_error_reduction_usd | 553.6931 | 451.7300 | 54 | 3 | 18 | 553.6931 | 2 | 262144 | 0.0000 | 0.0000 | -0.2220 |

## Cross-network robustness

| network | load_multiplier | baseline_quality | mechanism | mean_absolute_error_usd | median_normalized_error | mean_overpayment_usd | congestion_share |
| --- | --- | --- | --- | --- | --- | --- | --- |
| IEEE 300-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal exact net value | 1984.254 | 1.000 | 326.225 | 0.000 |
| IEEE 300-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal gross | 2194.024 | 0.939 | 1326.470 | 0.000 |
| IEEE 300-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal signed linear | 1984.325 | 1.000 | 326.329 | 0.000 |
| IEEE 300-bus | 0.900 | Risk-Constrained Convex Verifier | Uniform gross | 2194.024 | 0.939 | 1326.470 | 0.000 |
| IEEE 300-bus | 0.900 | Risk-Constrained Convex Verifier | Uniform signed net | 1984.325 | 1.000 | 326.329 | 0.000 |
| IEEE 300-bus | 0.900 | Trace-Anchored Reference | Nodal exact net value | 6.338 | 0.002 | 6.162 | 0.000 |
| IEEE 300-bus | 0.900 | Trace-Anchored Reference | Nodal gross | 2449.096 | 1.360 | 2449.096 | 0.000 |
| IEEE 300-bus | 0.900 | Trace-Anchored Reference | Nodal signed linear | 10.105 | 0.002 | 10.091 | 0.000 |
| IEEE 300-bus | 0.900 | Trace-Anchored Reference | Uniform gross | 2449.096 | 1.360 | 2449.096 | 0.000 |
| IEEE 300-bus | 0.900 | Trace-Anchored Reference | Uniform signed net | 10.105 | 0.002 | 10.091 | 0.000 |
| IEEE 300-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal exact net value | 2251.082 | 1.000 | 369.676 | 0.000 |
| IEEE 300-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal gross | 2490.401 | 0.939 | 1507.113 | 0.000 |
| IEEE 300-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal signed linear | 2251.151 | 1.000 | 369.761 | 0.000 |
| IEEE 300-bus | 0.980 | Risk-Constrained Convex Verifier | Uniform gross | 2490.401 | 0.939 | 1507.113 | 0.000 |
| IEEE 300-bus | 0.980 | Risk-Constrained Convex Verifier | Uniform signed net | 2251.151 | 1.000 | 369.761 | 0.000 |
| IEEE 300-bus | 0.980 | Trace-Anchored Reference | Nodal exact net value | 12.280 | 0.006 | 12.158 | 0.000 |
| IEEE 300-bus | 0.980 | Trace-Anchored Reference | Nodal gross | 2787.923 | 1.368 | 2787.923 | 0.000 |
| IEEE 300-bus | 0.980 | Trace-Anchored Reference | Nodal signed linear | 15.312 | 0.006 | 15.204 | 0.000 |
| IEEE 300-bus | 0.980 | Trace-Anchored Reference | Uniform gross | 2787.923 | 1.368 | 2787.923 | 0.000 |
| IEEE 300-bus | 0.980 | Trace-Anchored Reference | Uniform signed net | 15.312 | 0.006 | 15.204 | 0.000 |
| IEEE 300-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal exact net value | 2376.548 | 1.000 | 389.133 | 0.000 |
| IEEE 300-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal gross | 2626.196 | 0.939 | 1586.673 | 0.000 |
| IEEE 300-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal signed linear | 2376.572 | 1.000 | 389.208 | 0.000 |
| IEEE 300-bus | 1.020 | Risk-Constrained Convex Verifier | Uniform gross | 2626.196 | 0.939 | 1586.673 | 0.000 |
| IEEE 300-bus | 1.020 | Risk-Constrained Convex Verifier | Uniform signed net | 2376.572 | 1.000 | 389.208 | 0.000 |
| IEEE 300-bus | 1.020 | Trace-Anchored Reference | Nodal exact net value | 8.000 | 0.003 | 7.863 | 0.000 |
| IEEE 300-bus | 1.020 | Trace-Anchored Reference | Nodal gross | 2934.905 | 1.362 | 2934.905 | 0.000 |
| IEEE 300-bus | 1.020 | Trace-Anchored Reference | Nodal signed linear | 11.374 | 0.004 | 11.335 | 0.000 |
| IEEE 300-bus | 1.020 | Trace-Anchored Reference | Uniform gross | 2934.905 | 1.362 | 2934.905 | 0.000 |
| IEEE 300-bus | 1.020 | Trace-Anchored Reference | Uniform signed net | 11.374 | 0.004 | 11.335 | 0.000 |
| IEEE 39-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal exact net value | 163.598 | 1.000 | 27.466 | 0.000 |
| IEEE 39-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal gross | 181.554 | 0.939 | 110.132 | 0.000 |
| IEEE 39-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal signed linear | 163.654 | 1.000 | 27.534 | 0.000 |
| IEEE 39-bus | 0.900 | Risk-Constrained Convex Verifier | Uniform gross | 181.554 | 0.939 | 110.132 | 0.000 |
| IEEE 39-bus | 0.900 | Risk-Constrained Convex Verifier | Uniform signed net | 163.654 | 1.000 | 27.534 | 0.000 |
| IEEE 39-bus | 0.900 | Trace-Anchored Reference | Nodal exact net value | 1.050 | 0.003 | 0.201 | 0.000 |
| IEEE 39-bus | 0.900 | Trace-Anchored Reference | Nodal gross | 201.023 | 1.345 | 200.993 | 0.000 |
| IEEE 39-bus | 0.900 | Trace-Anchored Reference | Nodal signed linear | 2.173 | 0.003 | 1.778 | 0.000 |
| IEEE 39-bus | 0.900 | Trace-Anchored Reference | Uniform gross | 201.023 | 1.345 | 200.993 | 0.000 |
| IEEE 39-bus | 0.900 | Trace-Anchored Reference | Uniform signed net | 2.173 | 0.003 | 1.778 | 0.000 |
| IEEE 39-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal exact net value | 200.150 | 1.000 | 34.071 | 0.000 |
| IEEE 39-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal gross | 223.272 | 0.939 | 136.555 | 0.000 |
| IEEE 39-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal signed linear | 200.163 | 1.000 | 34.095 | 0.000 |
| IEEE 39-bus | 0.980 | Risk-Constrained Convex Verifier | Uniform gross | 223.256 | 0.939 | 136.540 | 0.000 |
| IEEE 39-bus | 0.980 | Risk-Constrained Convex Verifier | Uniform signed net | 200.142 | 1.000 | 34.074 | 0.000 |
| IEEE 39-bus | 0.980 | Trace-Anchored Reference | Nodal exact net value | 1.635 | 0.007 | 1.272 | 0.000 |
| IEEE 39-bus | 0.980 | Trace-Anchored Reference | Nodal gross | 249.572 | 1.373 | 249.572 | 0.000 |
| IEEE 39-bus | 0.980 | Trace-Anchored Reference | Nodal signed linear | 3.682 | 0.007 | 3.523 | 0.000 |
| IEEE 39-bus | 0.980 | Trace-Anchored Reference | Uniform gross | 249.572 | 1.373 | 249.572 | 0.000 |
| IEEE 39-bus | 0.980 | Trace-Anchored Reference | Uniform signed net | 3.682 | 0.007 | 3.523 | 0.000 |
| IEEE 39-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal exact net value | 229.766 | 1.000 | 43.183 | 0.016 |
| IEEE 39-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal gross | 266.066 | 0.940 | 168.332 | 0.016 |
| IEEE 39-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal signed linear | 230.401 | 1.000 | 43.852 | 0.016 |
| IEEE 39-bus | 1.020 | Risk-Constrained Convex Verifier | Uniform gross | 262.845 | 0.940 | 165.112 | 0.016 |
| IEEE 39-bus | 1.020 | Risk-Constrained Convex Verifier | Uniform signed net | 229.369 | 1.000 | 42.662 | 0.016 |
| IEEE 39-bus | 1.020 | Trace-Anchored Reference | Nodal exact net value | 2.930 | 0.013 | 0.700 | 0.016 |
| IEEE 39-bus | 1.020 | Trace-Anchored Reference | Nodal gross | 286.126 | 1.376 | 285.778 | 0.016 |
| IEEE 39-bus | 1.020 | Trace-Anchored Reference | Nodal signed linear | 9.212 | 0.013 | 8.152 | 0.016 |
| IEEE 39-bus | 1.020 | Trace-Anchored Reference | Uniform gross | 286.126 | 1.376 | 285.778 | 0.016 |
| IEEE 39-bus | 1.020 | Trace-Anchored Reference | Uniform signed net | 9.212 | 0.013 | 8.152 | 0.016 |
| IEEE RTS 24-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal exact net value | 108.637 | 1.000 | 18.074 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal gross | 120.543 | 0.939 | 73.198 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal signed linear | 108.660 | 1.000 | 18.109 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Risk-Constrained Convex Verifier | Uniform gross | 120.543 | 0.939 | 73.198 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Risk-Constrained Convex Verifier | Uniform signed net | 108.660 | 1.000 | 18.109 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Trace-Anchored Reference | Nodal exact net value | 0.199 | 0.002 | 0.031 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Trace-Anchored Reference | Nodal gross | 134.418 | 1.354 | 134.404 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Trace-Anchored Reference | Nodal signed linear | 1.068 | 0.003 | 1.011 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Trace-Anchored Reference | Uniform gross | 134.418 | 1.354 | 134.404 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Trace-Anchored Reference | Uniform signed net | 1.068 | 0.003 | 1.011 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal exact net value | 337.704 | 1.000 | 55.403 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal gross | 373.602 | 0.939 | 226.179 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal signed linear | 337.715 | 1.000 | 55.444 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Risk-Constrained Convex Verifier | Uniform gross | 373.602 | 0.939 | 226.179 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Risk-Constrained Convex Verifier | Uniform signed net | 337.715 | 1.000 | 55.444 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Trace-Anchored Reference | Nodal exact net value | 0.572 | 0.001 | 0.218 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Trace-Anchored Reference | Nodal gross | 417.687 | 1.363 | 417.652 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Trace-Anchored Reference | Nodal signed linear | 1.575 | 0.002 | 1.432 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Trace-Anchored Reference | Uniform gross | 417.687 | 1.363 | 417.652 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Trace-Anchored Reference | Uniform signed net | 1.575 | 0.002 | 1.432 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal exact net value | 356.650 | 1.000 | 58.157 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal gross | 393.643 | 0.939 | 237.334 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal signed linear | 356.658 | 1.000 | 58.170 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Risk-Constrained Convex Verifier | Uniform gross | 393.643 | 0.939 | 237.334 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Risk-Constrained Convex Verifier | Uniform signed net | 356.658 | 1.000 | 58.170 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Trace-Anchored Reference | Nodal exact net value | 0.318 | 0.001 | 0.217 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Trace-Anchored Reference | Nodal gross | 438.595 | 1.356 | 438.595 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Trace-Anchored Reference | Nodal signed linear | 0.848 | 0.001 | 0.818 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Trace-Anchored Reference | Uniform gross | 438.595 | 1.356 | 438.595 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Trace-Anchored Reference | Uniform signed net | 0.848 | 0.001 | 0.818 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal exact net value | 352.177 | 1.000 | 57.763 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal gross | 390.120 | 0.938 | 236.612 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal signed linear | 352.198 | 1.000 | 57.784 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Risk-Constrained Convex Verifier | Uniform gross | 390.123 | 0.938 | 236.615 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Risk-Constrained Convex Verifier | Uniform signed net | 352.198 | 1.000 | 57.784 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Trace-Anchored Reference | Nodal exact net value | 3.002 | 0.009 | 2.851 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Trace-Anchored Reference | Nodal gross | 438.957 | 1.377 | 438.957 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Trace-Anchored Reference | Nodal signed linear | 3.375 | 0.010 | 3.246 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Trace-Anchored Reference | Uniform gross | 438.960 | 1.377 | 438.960 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Trace-Anchored Reference | Uniform signed net | 3.376 | 0.009 | 3.247 | 0.000 |
| PGLib IEEE 118-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal exact net value | 400.113 | 1.000 | 66.047 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal gross | 442.183 | 0.939 | 267.148 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal signed linear | 400.221 | 1.000 | 66.180 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Risk-Constrained Convex Verifier | Uniform gross | 442.245 | 0.939 | 267.211 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Risk-Constrained Convex Verifier | Uniform signed net | 400.133 | 1.000 | 66.092 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Trace-Anchored Reference | Nodal exact net value | 2.321 | 0.006 | 0.772 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Trace-Anchored Reference | Nodal gross | 490.437 | 1.358 | 490.415 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Trace-Anchored Reference | Nodal signed linear | 3.231 | 0.005 | 2.269 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Trace-Anchored Reference | Uniform gross | 490.437 | 1.358 | 490.415 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Trace-Anchored Reference | Uniform signed net | 3.231 | 0.005 | 2.269 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal exact net value | 426.870 | 1.000 | 71.454 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal gross | 474.493 | 0.939 | 289.051 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal signed linear | 427.598 | 1.000 | 72.316 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Risk-Constrained Convex Verifier | Uniform gross | 474.862 | 0.939 | 289.425 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Risk-Constrained Convex Verifier | Uniform signed net | 427.337 | 1.000 | 72.058 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Trace-Anchored Reference | Nodal exact net value | 3.216 | 0.007 | 3.039 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Trace-Anchored Reference | Nodal gross | 532.020 | 1.376 | 532.020 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Trace-Anchored Reference | Nodal signed linear | 5.413 | 0.008 | 5.381 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Trace-Anchored Reference | Uniform gross | 532.032 | 1.376 | 532.032 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Trace-Anchored Reference | Uniform signed net | 5.416 | 0.008 | 5.384 | 1.000 |

## Binding-constraint stress test

| capacity_multiplier | deadline_multiplier | day | capacity_binding_share | deadline_binding_share | estimator_schema_version | mae_mw | rmse_mw | nrmse | nmae | normalization_mean_truth_mw | bias_mw | max_abs_error_mw | paid_response_mwh | oracle_response_mwh | false_response_mwh | false_response_ratio | underestimation_mwh | credit_precision | credit_recall | credit_f1 | net_system_response_mwh |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.5500 | 0.2500 | 87.5000 | 0.0334 | 0.9118 | 3.0000 | 2.6795 | 3.8382 | 0.3007 | 0.2129 | 12.0798 | -1.1237 | 12.4930 | 12.9282 | 22.2880 | 2.7004 | 0.1759 | 12.0602 | 0.8241 | 0.4126 | 0.4805 | -0.9182 |
| 0.5500 | 0.5000 | 87.5000 | 0.0334 | 0.9013 | 3.0000 | 2.6789 | 3.8372 | 0.3007 | 0.2128 | 12.0798 | -1.1237 | 12.4930 | 12.9324 | 22.2880 | 2.6980 | 0.1757 | 12.0535 | 0.8243 | 0.4128 | 0.4807 | -0.9182 |
| 0.5500 | 1.0000 | 87.5000 | 0.0334 | 0.8738 | 3.0000 | 2.6795 | 3.8372 | 0.3007 | 0.2129 | 12.0798 | -1.1237 | 12.4721 | 12.9170 | 22.2880 | 2.7004 | 0.1760 | 12.0713 | 0.8240 | 0.4122 | 0.4802 | -0.9182 |
| 0.7000 | 0.2500 | 87.5000 | 0.0227 | 0.9118 | 3.0000 | 2.6812 | 3.9412 | 0.3065 | 0.2129 | 12.0798 | -1.1237 | 13.4031 | 12.6312 | 22.2880 | 2.4066 | 0.1687 | 12.0634 | 0.8313 | 0.4125 | 0.4839 | -0.9182 |
| 0.7000 | 0.5000 | 87.5000 | 0.0227 | 0.9013 | 3.0000 | 2.6806 | 3.9418 | 0.3065 | 0.2128 | 12.0798 | -1.1237 | 13.4031 | 12.6278 | 22.2880 | 2.4041 | 0.1685 | 12.0643 | 0.8315 | 0.4124 | 0.4839 | -0.9182 |
| 0.7000 | 1.0000 | 87.5000 | 0.0227 | 0.8738 | 3.0000 | 2.6824 | 3.9423 | 0.3066 | 0.2130 | 12.0798 | -1.1237 | 13.3822 | 12.6310 | 22.2880 | 2.4115 | 0.1690 | 12.0685 | 0.8310 | 0.4122 | 0.4836 | -0.9182 |
| 0.8500 | 0.2500 | 87.5000 | 0.0159 | 0.9118 | 3.0000 | 2.6988 | 4.0467 | 0.3126 | 0.2139 | 12.0798 | -1.1213 | 13.9499 | 12.4945 | 22.2880 | 2.3022 | 0.1659 | 12.0957 | 0.8341 | 0.4116 | 0.4847 | -0.8989 |
| 0.8500 | 0.5000 | 87.5000 | 0.0159 | 0.9013 | 3.0000 | 2.6982 | 4.0482 | 0.3127 | 0.2138 | 12.0798 | -1.1213 | 13.9708 | 12.5022 | 22.2880 | 2.2997 | 0.1656 | 12.0854 | 0.8344 | 0.4120 | 0.4851 | -0.8989 |
| 0.8500 | 1.0000 | 87.5000 | 0.0159 | 0.8738 | 3.0000 | 2.7000 | 4.0497 | 0.3128 | 0.2140 | 12.0798 | -1.1213 | 13.9708 | 12.5166 | 22.2880 | 2.3071 | 0.1660 | 12.0784 | 0.8340 | 0.4122 | 0.4851 | -0.8989 |
| 1.0000 | 0.2500 | 87.5000 | 0.0117 | 0.9118 | 3.0000 | 2.6988 | 4.0553 | 0.3131 | 0.2139 | 12.0798 | -1.1213 | 14.2777 | 12.4892 | 22.2880 | 2.2982 | 0.1658 | 12.0969 | 0.8342 | 0.4115 | 0.4847 | -0.8989 |
| 1.0000 | 0.5000 | 87.5000 | 0.0117 | 0.9013 | 3.0000 | 2.6982 | 4.0570 | 0.3132 | 0.2138 | 12.0798 | -1.1213 | 14.2985 | 12.4995 | 22.2880 | 2.2957 | 0.1654 | 12.0842 | 0.8346 | 0.4121 | 0.4852 | -0.8989 |
| 1.0000 | 1.0000 | 87.5000 | 0.0117 | 0.8738 | 3.0000 | 2.6985 | 4.0576 | 0.3132 | 0.2139 | 12.0798 | -1.1213 | 14.2985 | 12.5077 | 22.2880 | 2.2969 | 0.1654 | 12.0772 | 0.8346 | 0.4123 | 0.4854 | -0.8989 |
| 1.2000 | 0.2500 | 87.5000 | 0.0087 | 0.9118 | 3.0000 | 2.6988 | 4.0927 | 0.3155 | 0.2139 | 12.0798 | -1.1213 | 14.7356 | 12.6109 | 22.2880 | 2.4075 | 0.1693 | 12.0845 | 0.8307 | 0.4121 | 0.4833 | -0.8989 |
| 1.2000 | 0.5000 | 87.5000 | 0.0087 | 0.9013 | 3.0000 | 2.6985 | 4.0938 | 0.3155 | 0.2139 | 12.0798 | -1.1213 | 14.7356 | 12.6157 | 22.2880 | 2.4062 | 0.1691 | 12.0784 | 0.8309 | 0.4122 | 0.4835 | -0.8989 |
| 1.2000 | 1.0000 | 87.5000 | 0.0087 | 0.8738 | 3.0000 | 2.6985 | 4.0938 | 0.3155 | 0.2139 | 12.0798 | -1.1213 | 14.7356 | 12.6157 | 22.2880 | 2.4062 | 0.1691 | 12.0784 | 0.8309 | 0.4122 | 0.4835 | -0.8989 |

## Exact multi-participant value allocation

| baseline_quality | allocation_method | mean_participant_absolute_error_usd | mean_absolute_budget_residual_usd | max_absolute_budget_residual_usd | mean_absolute_total_value_error_usd |
| --- | --- | --- | --- | --- | --- |
| Risk-Constrained Convex Verifier | Exact Shapley net value | 92.5191 | 0.0000 | 0.0000 | 306.0661 |
| Risk-Constrained Convex Verifier | Leave-one-out marginal | 92.7148 | 22.9814 | 1106.3335 | 326.4203 |
| Risk-Constrained Convex Verifier | Nodal signed linear | 88.0916 | 0.7420 | 25.3297 | 305.7781 |
| Risk-Constrained Convex Verifier | Standalone avoided cost | 92.9111 | 23.0101 | 1106.3335 | 297.4515 |
| Trace-Anchored Reference | Exact Shapley net value | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Trace-Anchored Reference | Leave-one-out marginal | 0.6640 | 1.9721 | 19.0041 | 1.9721 |
| Trace-Anchored Reference | Nodal signed linear | 2.4368 | 8.0559 | 116.3197 | 8.0559 |
| Trace-Anchored Reference | Standalone avoided cost | 0.6803 | 2.0216 | 18.2290 | 2.0216 |

## Complete N-1 security-aware settlement

| baseline_quality | mechanism | mean_absolute_error_usd | median_absolute_error_usd | mean_overpayment_usd | mean_payment_usd | mean_realized_n1_value_usd | maximum_post_contingency_loading |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Risk-Constrained Convex Verifier | Base-case exact net value | 192.9781 | 121.7505 | 134.2852 | 2.1665 | -73.4257 | 1.0000 |
| Risk-Constrained Convex Verifier | N-1 exact net value | 159.4832 | 116.4653 | 38.3713 | -156.1663 | -73.4257 | 1.0000 |
| Risk-Constrained Convex Verifier | N-1 signed linear | 159.5142 | 115.9647 | 38.9619 | -155.0162 | -73.4257 | 1.0000 |
| Trace-Anchored Reference | Base-case exact net value | 165.2880 | 85.2083 | 156.6165 | 74.5193 | -73.4257 | 1.0000 |
| Trace-Anchored Reference | N-1 exact net value | 1.0178 | 0.9790 | 0.0069 | -74.4297 | -73.4257 | 1.0000 |
| Trace-Anchored Reference | N-1 signed linear | 2.2530 | 0.5885 | 1.9695 | -71.7399 | -73.4257 | 1.0000 |

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
| IEEE 118-bus | Feasible Quantile Projection | 763.6594 | 628.9813 | 0.0422 | 0.0000 |
| IEEE 118-bus | Payment-Certified N-1 Verifier | 806.7824 | 677.6089 | 0.0422 | 0.0000 |
| IEEE 118-bus | Risk-Constrained Convex Verifier | 963.9089 | 843.2970 | 0.0422 | 0.0000 |
| IEEE 118-bus | Single Feasible Projection | 964.6491 | 844.0854 | 0.0422 | 0.0000 |
| IEEE 30-bus | Feasible Quantile Projection | 3.3206 | 2.7261 | 1.0000 | 0.0000 |
| IEEE 30-bus | Payment-Certified N-1 Verifier | 3.5214 | 2.9527 | 1.0000 | 0.0000 |
| IEEE 30-bus | Risk-Constrained Convex Verifier | 4.2145 | 3.6834 | 1.0000 | 0.0000 |
| IEEE 30-bus | Single Feasible Projection | 4.2176 | 3.6867 | 1.0000 | 0.0000 |
| IEEE 39-bus | Feasible Quantile Projection | 410.5336 | 338.6147 | 1.0000 | 0.0000 |
| IEEE 39-bus | Payment-Certified N-1 Verifier | 433.9645 | 365.0807 | 1.0000 | 0.0000 |
| IEEE 39-bus | Risk-Constrained Convex Verifier | 520.8031 | 456.4160 | 1.0000 | 0.0000 |
| IEEE 39-bus | Single Feasible Projection | 521.2022 | 456.8420 | 1.0000 | 0.0000 |
| IEEE RTS 24-bus | Feasible Quantile Projection | 647.6314 | 534.0655 | 0.9410 | 0.0000 |
| IEEE RTS 24-bus | Payment-Certified N-1 Verifier | 684.0717 | 575.1825 | 0.9410 | 0.0000 |
| IEEE RTS 24-bus | Risk-Constrained Convex Verifier | 818.4998 | 717.0665 | 0.9414 | 0.0000 |
| IEEE RTS 24-bus | Single Feasible Projection | 819.1245 | 717.7308 | 0.9414 | 0.0000 |

## Complete nonlinear AC post-contingency validation

| network | counterfactual_method | maximum_apparent_line_loading | maximum_voltage_violation_pu | minimum_voltage_pu | maximum_voltage_pu | evaluated_outages | locked_days |
| --- | --- | --- | --- | --- | --- | --- | --- |
| IEEE 14-bus | Feasible Quantile Projection | 0.01815 | 0.00000 | 0.97334 | 1.06000 | 19 | 54 |
| IEEE 14-bus | Payment-Certified N-1 Verifier | 0.01815 | 0.00000 | 0.97334 | 1.06000 | 19 | 54 |
| IEEE 14-bus | Risk-Constrained Convex Verifier | 0.01815 | 0.00000 | 0.97334 | 1.06000 | 19 | 54 |
| IEEE 14-bus | Single Feasible Projection | 0.01815 | 0.00000 | 0.97334 | 1.06000 | 19 | 54 |
| IEEE 9-bus | Feasible Quantile Projection | 0.87625 | 0.00000 | 0.94328 | 1.10000 | 6 | 54 |
| IEEE 9-bus | Payment-Certified N-1 Verifier | 0.87625 | 0.00000 | 0.94328 | 1.10000 | 6 | 54 |
| IEEE 9-bus | Risk-Constrained Convex Verifier | 0.88156 | 0.00000 | 0.94328 | 1.10000 | 6 | 54 |
| IEEE 9-bus | Single Feasible Projection | 0.88156 | 0.00000 | 0.94328 | 1.10000 | 6 | 54 |

## Complete spatial-assignment and power-scale robustness

| peak_dc_penetration | counterfactual_method | mean_absolute_error_usd | median_absolute_error_usd | maximum_absolute_error_usd | mean_overpayment_usd | maximum_line_loading | maximum_lmp_spread_usd_per_mwh | assignments | locked_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.0300 | Feasible Quantile Projection | 84.3359 | 29.9028 | 756.6081 | 71.8436 | 1.0000 | 0.1442 | 24 | 54 |
| 0.0300 | Risk-Constrained Convex Verifier | 100.2201 | 33.5644 | 765.8542 | 87.9297 | 1.0000 | 0.1442 | 24 | 54 |
| 0.0300 | Single Feasible Projection | 100.2705 | 33.5644 | 765.8542 | 87.9836 | 1.0000 | 0.1442 | 24 | 54 |
| 0.0300 | Trace-Anchored Reference | 32.3196 | 11.1524 | 235.6536 | 28.6144 | 1.0000 | 0.1442 | 24 | 54 |
| 0.0600 | Feasible Quantile Projection | 169.7153 | 59.9659 | 1526.1267 | 144.6566 | 1.0000 | 0.1442 | 24 | 54 |
| 0.0600 | Risk-Constrained Convex Verifier | 201.5092 | 67.3604 | 1544.6190 | 176.8469 | 1.0000 | 0.1442 | 24 | 54 |
| 0.0600 | Single Feasible Projection | 201.6099 | 67.3604 | 1544.6190 | 176.9546 | 1.0000 | 0.1442 | 24 | 54 |
| 0.0600 | Trace-Anchored Reference | 65.6832 | 22.5838 | 484.2177 | 58.1915 | 1.0000 | 0.1442 | 24 | 54 |
| 0.0900 | Feasible Quantile Projection | 249.2167 | 89.4642 | 2313.9429 | 211.5020 | 1.0000 | 16.9626 | 24 | 54 |
| 0.0900 | Risk-Constrained Convex Verifier | 296.9506 | 98.9517 | 2343.2309 | 259.8484 | 1.0000 | 20.1363 | 24 | 54 |
| 0.0900 | Single Feasible Projection | 297.1017 | 98.9517 | 2343.2309 | 260.0100 | 1.0000 | 20.1363 | 24 | 54 |
| 0.0900 | Trace-Anchored Reference | 100.5972 | 34.0619 | 1593.6164 | 85.1134 | 1.0000 | 0.1442 | 24 | 54 |

## Continuous-horizon space-time market validation

| counterfactual_method | mean_event_only_error_usd | mean_full_cycle_error_usd | mean_recovery_adjustment_usd | mean_post_event_rebound_mwh | maximum_absolute_cycle_energy_residual_mwh | maximum_baseline_projection_l1_mw | space_time_only_participant_ir_rate | bilateral_contract_activation_rate | bilateral_individual_rationality_rate | minimum_participant_contract_utility_usd | minimum_operator_contract_utility_usd | maximum_budget_balance_residual_usd | maximum_bilateral_budget_balance_residual_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Feasible Quantile Projection | 11.655725 | 0.053170 | -9.995124 | 0.112061 | 0.000003 | 0.000005 | 0.018519 | 1.000000 | 1.000000 | 1.842918 | 1.842918 | 0.000000 | 0.000000 |
| Payment-Certified N-1 Verifier | 8.091153 | 0.084761 | -6.209876 | 0.098505 | 0.000002 | 0.000006 | 0.018519 | 1.000000 | 1.000000 | 1.842918 | 1.842918 | 0.000000 | 0.000000 |
| Risk-Constrained Convex Verifier | 11.186565 | 0.241926 | -0.240426 | 0.095461 | 0.000002 | 0.000005 | 0.018519 | 1.000000 | 1.000000 | 1.842918 | 1.842918 | 0.000000 | 0.000000 |
| Single Feasible Projection | 10.763272 | 0.084761 | -8.881995 | 0.098505 | 0.000002 | 0.000005 | 0.018519 | 1.000000 | 1.000000 | 1.842918 | 1.842918 | 0.000000 | 0.000000 |

## Dependence-robust paired tests

- High-5-of-10 | nrmse: comparator-minus-proposed mean difference 3.8694, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- High-5-of-10 | false_response_ratio: comparator-minus-proposed mean difference 0.7732, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- High-5-of-10 | credit_f1: comparator-minus-proposed mean difference 0.2974, two-sided exact block-sign p=2.289e-05, Holm-adjusted p=0.0001373 (18 nonoverlapping blocks).
- Metadata Gradient Boosting | nrmse: comparator-minus-proposed mean difference 1.7879, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Metadata Gradient Boosting | false_response_ratio: comparator-minus-proposed mean difference 0.6924, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Metadata Gradient Boosting | credit_f1: comparator-minus-proposed mean difference 0.1768, two-sided exact block-sign p=0.005585, Holm-adjusted p=0.02234 (18 nonoverlapping blocks).
- Ex-post Metadata Gradient Boosting | nrmse: comparator-minus-proposed mean difference 1.7786, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Ex-post Metadata Gradient Boosting | false_response_ratio: comparator-minus-proposed mean difference 0.6910, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Ex-post Metadata Gradient Boosting | credit_f1: comparator-minus-proposed mean difference 0.1738, two-sided exact block-sign p=0.008575, Holm-adjusted p=0.02573 (18 nonoverlapping blocks).
- Ex-post Quantile Gradient Boosting | nrmse: comparator-minus-proposed mean difference 0.5995, two-sided exact block-sign p=0.0001907, Holm-adjusted p=0.0005722 (18 nonoverlapping blocks).
- Ex-post Quantile Gradient Boosting | false_response_ratio: comparator-minus-proposed mean difference 0.3455, two-sided exact block-sign p=3.052e-05, Holm-adjusted p=9.155e-05 (18 nonoverlapping blocks).
- Ex-post Quantile Gradient Boosting | credit_f1: comparator-minus-proposed mean difference -0.0904, two-sided exact block-sign p=0.06455, Holm-adjusted p=0.1291 (18 nonoverlapping blocks).
- Synthetic Control | nrmse: comparator-minus-proposed mean difference 2.2070, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Synthetic Control | false_response_ratio: comparator-minus-proposed mean difference 0.7235, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Synthetic Control | credit_f1: comparator-minus-proposed mean difference 0.2350, two-sided exact block-sign p=0.0009384, Holm-adjusted p=0.004692 (18 nonoverlapping blocks).
- Feasible Quantile Projection | nrmse: comparator-minus-proposed mean difference -0.0236, two-sided exact block-sign p=0.2838, Holm-adjusted p=0.5469 (18 nonoverlapping blocks).
- Feasible Quantile Projection | false_response_ratio: comparator-minus-proposed mean difference 0.0485, two-sided exact block-sign p=0.009247, Holm-adjusted p=0.01849 (18 nonoverlapping blocks).
- Feasible Quantile Projection | credit_f1: comparator-minus-proposed mean difference -0.0668, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Single Feasible Projection | nrmse: comparator-minus-proposed mean difference 0.0002, two-sided exact block-sign p=0.2734, Holm-adjusted p=0.5469 (18 nonoverlapping blocks).
- Single Feasible Projection | false_response_ratio: comparator-minus-proposed mean difference 0.0004, two-sided exact block-sign p=0.08838, Holm-adjusted p=0.08838 (18 nonoverlapping blocks).
- Single Feasible Projection | credit_f1: comparator-minus-proposed mean difference -0.0003, two-sided exact block-sign p=0.2954, Holm-adjusted p=0.2954 (18 nonoverlapping blocks).

## Scope and limitations

- BurstGPT exposes workload tokens but not facility power; token traces are scaled to an explicitly documented hyperscale capacity target.
- MIT SuperCloud provides measured GPU energy for its own workload, which is independently aggregated and scaled; it is not claimed to be a co-located trace from the same operator.
- All 24 mappings of the four measured regional traces to the four declared IEEE-118 connection buses and three predeclared power penetrations are evaluated, but these public traces are not claimed to be co-located utility and facility measurements.
- The final workload credit is constrained by a predeclared two-sided band around the selected single feasible projection; the upper side certifies false-credit noninferiority and the lower side bounds additional under-credit by the declared tolerance.
- The complete N-1 panel certifies preventive feasibility for every finite non-islanding line outage in the lossless continuous DC model; it is not an AC voltage, transient-stability, or island-balancing certificate.
- The nonlinear AC outage panel solves a separate corrective post-contingency optimum for every non-islanding IEEE-9 and IEEE-14 line outage; it is not a simultaneous preventive AC security-constrained OPF or a transient-stability certificate.
- The shared-active-plan preventive AC panel fixes non-reference active generation across every finite non-islanding IEEE-9 outage, with reactive-power, voltage, and reference-generator loss recourse; it is not a transient-stability or intertemporal unit-commitment certificate.
- The event-gate information panel removes post-gate arrivals before optimization and uses the locked execution trace only for scoring; its complete-ledger comparator quantifies information cost rather than defining a deployable gate policy.
- The cross-network AC panel is a corrective power-flow diagnostic over native-case admissible outages; voltage and loading diagnostics are reported without being promoted to a preventive AC security certificate.
