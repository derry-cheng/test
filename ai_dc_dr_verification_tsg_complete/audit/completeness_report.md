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
- [x] experiment_15:experiments/exp15_interval_certificate/results/final/interval_certified_counterfactual_profiles.npz: exists and non-empty
- [x] experiment_15:experiments/exp15_interval_certificate/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_15:experiments/exp15_interval_certificate/figures/fig21_interval_payment_certificate.png: exists and non-empty
- [x] experiment_16:experiments/exp16_ledger_capacity_provenance/results/final/ledger_provenance_summary.csv: exists and non-empty
- [x] experiment_16:experiments/exp16_ledger_capacity_provenance/results/final/capacity_reconciliation.csv: exists and non-empty
- [x] experiment_16:experiments/exp16_ledger_capacity_provenance/results/final/ledger_provenance_certificate.json: exists and non-empty
- [x] experiment_16:experiments/exp16_ledger_capacity_provenance/results/final/source_hashes.json: exists and non-empty
- [x] experiment_16:experiments/exp16_ledger_capacity_provenance/results/final/experiment_metadata.json: exists and non-empty
- [x] experiment_16:experiments/exp16_ledger_capacity_provenance/figures/fig22_ledger_capacity_provenance.png: exists and non-empty
- [x] experiment_17:experiments/exp17_decision_time_information/results/final/decision_time_comparison.csv: exists and non-empty
- [x] experiment_17:experiments/exp17_decision_time_information/results/final/decision_time_summary.csv: exists and non-empty
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
- [x] all_png_figures_decodable_and_high_resolution: fig15_ac_opf_validation.png=4195x1253; fig15b_ac_n1_contingency_validation.png=4069x1221; fig15c_preventive_ac_n1_validation.png=4069x1221; fig16_spatial_scale_robustness.png=4261x1253; fig18_rolling_market_validation.png=3493x2309; fig19_real_trace_replay.png=4133x1221; fig20_job_level_fidelity.png=4064x1221; fig21_interval_payment_certificate.png=3365x1221; fig22_ledger_capacity_provenance.png=4005x1189; fig23_decision_time_information.png=3813x1157; fig24_preventive_ac_cross_network.png=3877x1189; fig1_manipulation_phase_diagram.png=3042x1189; fig2_response_and_migration.png=3045x1125; fig3_baseline_verification_performance.png=4261x1205; fig4_tuning_and_ablation.png=3429x2277; fig4b_intervention_robustness.png=3493x1253; fig5_settlement_value_alignment.png=4039x1221; fig6_network_loading_heatmap.png=2975x1317; fig6b_settlement_factor_decomposition.png=3077x1221; fig7_spatial_response_case.png=2917x1957; fig8_ieee118_data_center_topology.png=2597x2213; fig9_cross_network_robustness.png=4347x1253; fig10_binding_constraint_stress.png=3619x1157; fig11_exact_value_allocation.png=4100x1221; fig12_eight_participant_scaling.png=4005x1221; fig12b_exact_20_participant_scaling.png=3973x1189; fig13_n1_security_validation.png=4069x1221; fig14_payment_certificate.png=4037x1205; fig0_framework.png=1800x797; fig17_cross_layer_robustness.png=4101x1189; fig_method_detail.png=1800x643
- [x] model_formula_citation_traceability: 28/28 required source keys in bibliography, formula-source matrix, and complete formulation
- [x] official_ieee_journal_template: manuscript uses the vendored official IEEEtran journal class
- [x] maximum_two_sources_per_citation_group: 41 in-text citation groups checked
- [x] complete_manuscript_bibliography: 32 verified bibliography entries; 32 unique in-text citations; uncited=[]; missing=[]
- [x] sha256:data/raw/burstgpt/BurstGPT_without_fails_1.csv: a4d068a7113ec0290e74063a1b3447dc6001a30e4298eb313581b71006dda1f4
- [x] sha256:data/raw/burstgpt/BurstGPT_without_fails_2.csv: 56193aa9b2bb26128ded43d2d29a960df6bf5af062bcfc9b005f3fcaa4e6e501
- [x] sha256:data/raw/mit_supercloud/scheduler_data.csv: 80c0b5bbe1c99b3920aa088bbc583fab01379d948c3ad7bcfa9ce524b0e9c092
- [x] sha256:data/raw/mit_supercloud/dcgm_verified_full.csv: 1b0a31722ef297745d9741ec0e68eeda8e40e2e3838fefaf61f1cac792c509c4
- [x] sha256:data/raw/pglib/pglib_opf_case118_ieee.m: b1af0833849040c04babc3700631cff0d9afa66b79c5d3e13ae79bdf516cec78
- [x] full_burstgpt_rows: 5188507
- [x] full_measured_gpu_jobs: 68664
- [x] heldout_power_conversion_scenarios_complete: 21,919 held-out jobs; measured-to-predicted energy factors=0.734154, 0.995724, 1.278023
- [x] complete_source_to_evaluation_data_flow: 5 source/join/split stages; calibration 66769 train + 28413 held out
- [x] processed_data_finite_nonnegative: (11616, 4, 3)
- [x] processed_data_nonempty: 89968.421 MWh
- [x] trace_observed_counterfactual_complete: (11616, 4)
- [x] locked_days_have_complete_history_and_future_coverage: days 45--114; 6 future days available for the 512-slot deadline
- [x] workload_conservation: max gap=1.776e-15 MWh
- [x] data_center_capacity: violation=0.000e+00 MW
- [x] deadline_feasibility: violation=0.000e+00 MWh
- [x] sced_power_balance: gap=0.000e+00 MW
- [x] sced_line_limits: max loading=1.000000 pu
- [x] complete_exp1_grid: 56/56
- [x] strategic_threshold_theory_matches_optimizer: 56/56 price-probability cells
- [x] locked_test_set_complete: 648/648 outcomes
- [x] two_sided_credit_band_certificate: 54/54 locked days satisfy the predeclared lower and upper physical credit band
- [x] decision_time_information_boundary_panel: 108/108 rows; post-gate arrivals are excluded from the event-gate decision
- [x] cross_network_ac_n1_admissibility_panel: 1698 AC outcomes over four public networks; native-case AC admissibility and validation-only scaling recorded
- [x] closest_literature_baseline_panel: 216/216 exact same-ledger comparator outcomes covering incentive-compatible, non-wire, proactive-shift, and frequency-regulation mechanisms
- [x] cross_experiment_locked_day_identity: 10/10 main panels use the identical locked days 61--114; mismatches=[]
- [x] dependence_robust_exact_block_tests: 18 pre-declared 3-day blocks, exact sign randomization, attainable-p audit, and Holm family-wise correction
- [x] tail_risk_counterfactual_estimator_comparison: tail-risk feasible counterfactual improves credit F1 against the single feasible projection, while its nRMSE difference is retained and nonsignificant over 18 exact temporal blocks
- [x] closest_feasible_baseline_comparison: risk verifier has no greater mean nRMSE and significantly lower false-credit exposure than the complete-ledger feasible-quantile projection
- [x] matched_effect_sizes_with_dependence_robust_intervals: false-credit improvement over feasible quantile has a positive three-day moving-block 95% interval, while all single-projection effects are contained in their dependence-aware intervals
- [x] complete_independent_intervention_panel: 864/864 rows; all matched interventions are evaluated without a comparator-derived cap
- [x] independent_pointwise_risk_envelope: locked test false-credit is compared to the feasible-quantile reference, while the LP cap and risk budget are anchored to the independent Metadata projection rho=0.3 candidate
- [x] risk_constrained_validation_dominance: convex verifier has no larger validation MSE and satisfies both total and daily-tail CVaR false-credit budgets
- [x] nested_daily_risk_reserve_selection: 16 reserve-fold cells; selected reserve=1.00
- [x] exact_pointwise_risk_envelope_selection: 6 globally solved envelope projections; selected weight=3
- [x] matched_post_event_information_protocol: statistical, single-projection, and convex verifiers share the full ledger and never observe execution truth
- [x] complete_predeclared_projection_validation: 7 pre-declared validation candidates
- [x] convex_projection_simplex: 7 coefficients; sum=1.000000000000
- [x] contiguous_blocked_validation: 4 held-out temporal folds
- [x] independent_full_constraint_certificates: 162 day-variant schedules certified
- [x] exact_sparse_complexity_scaling: log-log nonzero slope=1.0025
- [x] complete_settlement_factorial_panel: 3510/3510 rows; 65/65 complete cells
- [x] paired_settlement_factor_decomposition: 702 locked day-baseline rows and 52 one-factor paired summaries separate signed netting, locational pricing, and exact valuation
- [x] independent_high_resolution_value_evaluator: 10-segment settlement versus 80-segment evaluation; trace-reference max non-circular error=11.129670 USD/day
- [x] complete_settlement_mechanism_block_tests: 52 paired mechanism tests; Holm correction within each baseline-method family
- [x] global_polyhedral_value_certificate: 5616 interval-baseline certificates; maximum subgradient-inequality violation 2.029e-11 USD
- [x] complete_cross_network_panel: 6480/6480 rows; 120/120 complete cells across 4 networks
- [x] cross_network_paired_mechanism_inference: 24 paired exact block tests; positive estimated-baseline linear-minus-exact effect in 9/12 cells; minimum effect -0.058248 USD/day; sign-mixed end-to-end effects are retained, while the trace-anchored reference must remain nonnegative in every cell
- [x] complete_cross_network_resolution_convergence: 4 complete 54-day resolution levels; highest two mean effects=-0.014411, -0.010558 USD/day; final step=0.003853 versus initial step=0.010797 USD/day, and every 95% interval contains zero
- [x] native_rating_congestion_identification: 3/12 network-loading cells exhibit endogenous congestion
- [x] native_ratings_and_predeclared_sites: all thermal-rating factors equal 1.0; fixed-site specifications invariant in 4 networks
- [x] nodal_price_effect_identified: at least one cross-network cell has a nonzero uniform-versus-nodal error contrast
- [x] complete_exact_value_allocation_panel: 1728/1728 participant-day outcomes
- [x] exact_shapley_budget_balance: maximum absolute participant-sum minus grand-coalition value=2.274e-13 USD
- [x] complete_exact_eight_participant_scaling: 3456/3456 participant-interval outcomes; all 256 coalitions enumerated per interval
- [x] exact_group_symmetric_20_participant_scaling: 1080/1080 site-day-size outcomes; exact count-state summation through 20 participants
- [x] allocation_mechanism_identification: non-efficient marginal allocation rules exhibit a nonzero budget residual
- [x] complete_binding_constraint_panel: 810/810 rows; 15/15 complete cells; max capacity binding=0.138
- [x] complete_n1_security_panel: 2592/2592 interval-mechanism outcomes; all 37 non-islanding line outages enforced
- [x] n1_mechanism_identification: trace-reference N-1 exact MAE=0.903 USD versus base-case exact MAE=192.693 USD and N-1 linear MAE=2.298 USD
- [x] scenario_robust_exact_n1_payment_noninferiority_certificate: 54/54 lexicographically solved daily certificates across three held-out conversion scenarios; maximum cap violation=0.000e+00 USD
- [x] complete_independent_payment_model_transfer_evaluation: 648 method-day-scenario outcomes scored with the independent 40-segment N-1 evaluator; accuracy is reported as model-transfer evidence and is not part of Proposition 4
- [x] independent_endpoint_certificate_uses_selected_single_reference: 216/216 endpoint rows compare the payment-certified profile with the preselected single feasible reference; the quantile profile remains external
- [x] independent_nondegenerate_payment_candidate_hull: six first-stage projection candidates plus an external matched feasible-quantile comparator; the selected single projection is the contractual reference and the risk verifier is an external target with minimum maximum-distance 14.027 MW; 34 distinct daily optimal weight vectors
- [x] validation_only_payment_target_selection: seven workload-feasible candidates ranked on 384 independent validation N-1 payment cells; the selected target and DC scale are frozen before locked test evaluation
- [x] complete_nonlinear_ac_opf_panel: 864/864 converged network-day-method outcomes with AC voltage and apparent-power limits enforced
- [x] complete_nonlinear_ac_n1_panel: 5400/5400 converged method-day-outage AC OPFs across all 6 IEEE-9 and 19 IEEE-14 non-islanding line outages
- [x] complete_shared_active_plan_preventive_ac_n1_panel: 3888/3888 converged penetration-method-day-outage cells across four matched counterfactuals; all six IEEE-9 outages share the intact-state non-reference active dispatch exactly
- [x] complete_spatial_scale_factorial_panel: 15552/15552 outcomes cover all 24 regional assignments, 3 penetrations, 54 locked days, and 4 methods
- [x] complete_continuous_horizon_market_validation: 216/216 method-day outcomes use real future arrivals, lexicographic projection, complete-cycle energy accounting, exact site budget balance, and an individually rational bilateral outside option
- [x] exp16_source_hashes_match_current_inputs: Experiment 16 source hashes match the current scheduler, DCGM, and processed workload files
- [x] immutable_ledger_provenance_and_capacity_reconciliation: 71,128 joined jobs, canonical digest fdf49ad75d30..., raw-to-join energy conserved, and the pre-split committed capacity covers the observed regional envelope as a reconciliation

## Locked test-set baseline results

| method | nrmse | false_response_ratio | false_response_mwh | credit_precision | credit_recall | credit_f1 | bias_mw |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Ex-post Metadata Gradient Boosting | 1.9681 | 0.8077 | 91.1074 | 0.1923 | 0.8098 | 0.2988 | 7.4287 |
| Ex-post Quantile Gradient Boosting | 1.8912 | 0.7821 | 87.2229 | 0.2179 | 0.8040 | 0.3235 | 7.1313 |
| Extra Trees | 2.1728 | 0.8282 | 100.9200 | 0.1718 | 0.7718 | 0.2629 | 8.8941 |
| Feasible Quantile Projection | 0.3537 | 0.1264 | 2.0262 | 0.8736 | 0.3929 | 0.4859 | -1.1114 |
| Gradient Boosting | 2.1915 | 0.8340 | 103.3778 | 0.1660 | 0.7423 | 0.2556 | 9.2177 |
| High-5-of-10 | 2.6529 | 0.8556 | 118.8203 | 0.1444 | 0.7476 | 0.2303 | 10.3626 |
| Metadata Gradient Boosting | 2.1234 | 0.8238 | 98.6813 | 0.1762 | 0.8032 | 0.2752 | 8.3354 |
| Ridge | 1.8452 | 0.7880 | 90.5822 | 0.2120 | 0.8968 | 0.3208 | 9.0821 |
| Risk-Constrained Convex Verifier | 0.3484 | 0.1163 | 1.9106 | 0.8837 | 0.3896 | 0.4828 | -1.1575 |
| Single Feasible Projection | 0.3498 | 0.1222 | 1.9568 | 0.8778 | 0.3920 | 0.4850 | -1.1167 |
| Synthetic Control | 1.8933 | 0.8188 | 88.1847 | 0.1812 | 0.6839 | 0.2701 | 6.0003 |
| Tail-Risk Feasible Counterfactual | 0.3532 | 0.1976 | 4.1801 | 0.8024 | 0.4504 | 0.5126 | -0.9571 |

## Projection candidate validation

| candidate_index | projection_weight | validation_score | validation_score_std | event_window_deviation_from_optimization_only_mw | validation_credit_precision | validation_credit_recall | validation_credit_f1 | mean_contiguous_fold_nrmse | max_contiguous_fold_nrmse | selected_single_projection | candidate_type | ensemble_weight | selected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.03000 | 0.48607 | 0.32650 | 6.10259 | 0.83186 | 0.31732 | 0.42987 | 0.53563 | 0.83219 | False | metadata projection | 0.33426 | True |
| 2 | 0.10000 | 0.48607 | 0.32650 | 6.10259 | 0.83186 | 0.31732 | 0.42987 | 0.53563 | 0.83219 | False | metadata projection | 0.33426 | True |
| 3 | 0.30000 | 0.48555 | 0.29380 | 5.85540 | 0.79981 | 0.37702 | 0.48422 | 0.53406 | 0.77795 | True | metadata projection | 0.19952 | True |
| 4 | 1.00000 | 0.76284 | 0.28749 | 8.43813 | 0.48545 | 0.53027 | 0.46604 | 0.82660 | 1.03700 | False | metadata projection | 0.04293 | True |
| 5 | 3.00000 | 1.28092 | 0.59736 | 11.81086 | 0.32504 | 0.61881 | 0.40270 | 1.31586 | 1.59029 | False | metadata projection | 0.07402 | True |
| 6 | 10.00000 | 1.77948 | 0.77885 | 15.99572 | 0.23610 | 0.68568 | 0.33621 | 1.73566 | 2.08394 | False | metadata projection | 0.01501 | True |
| 6 | 0.30000 | 0.48808 | nan | nan | nan | nan | 0.48256 | nan | 0.68054 | False | feasible quantile projection | 0.00000 | False |

## Settlement results

| baseline_method | mechanism | payment_usd | realized_value_usd | absolute_error_usd | overpayment_ratio |
| --- | --- | --- | --- | --- | --- |
| Ex-post Metadata Gradient Boosting | Nodal exact net value | 2672.984 | 358.377 | 2327.400 | 0.816 |
| Ex-post Metadata Gradient Boosting | Nodal gross | 4412.629 | 358.377 | 4054.252 | 0.918 |
| Ex-post Metadata Gradient Boosting | Nodal signed linear | 2691.706 | 358.377 | 2345.978 | 0.821 |
| Ex-post Metadata Gradient Boosting | Uniform gross | 4412.924 | 358.377 | 4054.546 | 0.918 |
| Ex-post Metadata Gradient Boosting | Uniform signed net | 2692.002 | 358.377 | 2346.263 | 0.821 |
| Ex-post Quantile Gradient Boosting | Nodal exact net value | 2581.548 | 358.377 | 2269.608 | 0.778 |
| Ex-post Quantile Gradient Boosting | Nodal gross | 4264.026 | 358.377 | 3905.648 | 0.904 |
| Ex-post Quantile Gradient Boosting | Nodal signed linear | 2598.523 | 358.377 | 2284.652 | 0.780 |
| Ex-post Quantile Gradient Boosting | Uniform gross | 4264.305 | 358.377 | 3905.928 | 0.904 |
| Ex-post Quantile Gradient Boosting | Uniform signed net | 2598.805 | 358.377 | 2284.916 | 0.781 |
| Extra Trees | Nodal exact net value | 3132.654 | 358.377 | 2969.324 | 0.780 |
| Extra Trees | Nodal gross | 4778.493 | 358.377 | 4420.116 | 0.921 |
| Extra Trees | Nodal signed linear | 3155.592 | 358.377 | 2987.665 | 0.781 |
| Extra Trees | Uniform gross | 4778.792 | 358.377 | 4420.415 | 0.921 |
| Extra Trees | Uniform signed net | 3155.895 | 358.377 | 2987.892 | 0.781 |
| Feasible Quantile Projection | Nodal exact net value | 13.732 | 358.377 | 522.638 | 0.155 |
| Feasible Quantile Projection | Nodal gross | 586.802 | 358.377 | 635.464 | 0.425 |
| Feasible Quantile Projection | Nodal signed linear | 15.263 | 358.377 | 523.627 | 0.164 |
| Feasible Quantile Projection | Uniform gross | 587.295 | 358.377 | 635.948 | 0.425 |
| Feasible Quantile Projection | Uniform signed net | 15.104 | 358.377 | 523.457 | 0.203 |
| Gradient Boosting | Nodal exact net value | 3234.958 | 358.377 | 2932.252 | 0.783 |
| Gradient Boosting | Nodal gross | 4870.751 | 358.377 | 4512.373 | 0.922 |
| Gradient Boosting | Nodal signed linear | 3259.524 | 358.377 | 2952.959 | 0.786 |
| Gradient Boosting | Uniform gross | 4871.046 | 358.377 | 4512.669 | 0.922 |
| Gradient Boosting | Uniform signed net | 3259.823 | 358.377 | 2953.198 | 0.786 |
| High-5-of-10 | Nodal exact net value | 3590.326 | 358.377 | 3301.917 | 0.833 |
| High-5-of-10 | Nodal gross | 5480.032 | 358.377 | 5121.654 | 0.933 |
| High-5-of-10 | Nodal signed linear | 3622.704 | 358.377 | 3331.901 | 0.834 |
| High-5-of-10 | Uniform gross | 5480.380 | 358.377 | 5122.002 | 0.933 |
| High-5-of-10 | Uniform signed net | 3623.063 | 358.377 | 3332.212 | 0.834 |
| Metadata Gradient Boosting | Nodal exact net value | 2957.110 | 358.377 | 2645.570 | 0.825 |
| Metadata Gradient Boosting | Nodal gross | 4704.778 | 358.377 | 4346.401 | 0.921 |
| Metadata Gradient Boosting | Nodal signed linear | 2976.658 | 358.377 | 2665.093 | 0.830 |
| Metadata Gradient Boosting | Uniform gross | 4705.084 | 358.377 | 4346.707 | 0.921 |
| Metadata Gradient Boosting | Uniform signed net | 2976.965 | 358.377 | 2665.386 | 0.830 |
| Ridge | Nodal exact net value | 3190.214 | 358.377 | 2881.296 | 0.830 |
| Ridge | Nodal gross | 4471.852 | 358.377 | 4113.475 | 0.922 |
| Ridge | Nodal signed linear | 3217.048 | 358.377 | 2907.937 | 0.836 |
| Ridge | Uniform gross | 4472.107 | 358.377 | 4113.730 | 0.922 |
| Ridge | Uniform signed net | 3217.301 | 358.377 | 2908.180 | 0.836 |
| Risk-Constrained Convex Verifier | Nodal exact net value | 3.256 | 358.377 | 522.499 | 0.138 |
| Risk-Constrained Convex Verifier | Nodal gross | 574.199 | 358.377 | 631.137 | 0.421 |
| Risk-Constrained Convex Verifier | Nodal signed linear | 5.338 | 358.377 | 523.840 | 0.148 |
| Risk-Constrained Convex Verifier | Uniform gross | 574.668 | 358.377 | 631.598 | 0.421 |
| Risk-Constrained Convex Verifier | Uniform signed net | 4.965 | 358.377 | 523.458 | 0.186 |
| Single Feasible Projection | Nodal exact net value | 11.780 | 358.377 | 522.729 | 0.151 |
| Single Feasible Projection | Nodal gross | 582.724 | 358.377 | 635.418 | 0.421 |
| Single Feasible Projection | Nodal signed linear | 13.863 | 358.377 | 524.070 | 0.160 |
| Single Feasible Projection | Uniform gross | 583.208 | 358.377 | 635.892 | 0.421 |
| Single Feasible Projection | Uniform signed net | 13.504 | 358.377 | 523.701 | 0.199 |
| Synthetic Control | Nodal exact net value | 2226.651 | 358.377 | 2023.345 | 0.727 |
| Synthetic Control | Nodal gross | 4196.238 | 358.377 | 3837.861 | 0.903 |
| Synthetic Control | Nodal signed linear | 2242.720 | 358.377 | 2035.707 | 0.729 |
| Synthetic Control | Uniform gross | 4196.518 | 358.377 | 3838.141 | 0.903 |
| Synthetic Control | Uniform signed net | 2243.012 | 358.377 | 2035.917 | 0.729 |
| Tail-Risk Feasible Counterfactual | Nodal exact net value | 60.393 | 358.377 | 472.729 | 0.221 |
| Tail-Risk Feasible Counterfactual | Nodal gross | 750.861 | 358.377 | 728.716 | 0.466 |
| Tail-Risk Feasible Counterfactual | Nodal signed linear | 61.906 | 358.377 | 473.617 | 0.215 |
| Tail-Risk Feasible Counterfactual | Uniform gross | 751.052 | 358.377 | 728.897 | 0.466 |
| Tail-Risk Feasible Counterfactual | Uniform signed net | 61.974 | 358.377 | 473.652 | 0.215 |
| Trace-Anchored Reference | Nodal exact net value | 356.354 | 358.377 | 2.344 | 0.000 |
| Trace-Anchored Reference | Nodal gross | 1099.661 | 358.377 | 741.699 | 0.594 |
| Trace-Anchored Reference | Nodal signed linear | 362.102 | 358.377 | 6.004 | 0.022 |
| Trace-Anchored Reference | Uniform gross | 1099.684 | 358.377 | 741.722 | 0.594 |
| Trace-Anchored Reference | Uniform signed net | 362.112 | 358.377 | 6.011 | 0.059 |

## Paired settlement-factor decomposition

| baseline_method | factor | mean_error_reduction_usd | median_error_reduction_usd | paired_days | block_length_days | blocks | observed_mean_difference | extreme_assignments | total_sign_assignments | minimum_attainable_two_sided_p | two_sided_exact_p_value | block_sum_lag1_autocorrelation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Risk-Constrained Convex Verifier | gross_to_signed_error_reduction_usd | 107.2970 | -29.7934 | 54 | 3 | 18 | 107.2970 | 47242 | 262144 | 0.0000 | 0.1802 | -0.6880 |
| Risk-Constrained Convex Verifier | uniform_to_nodal_error_reduction_usd | -0.3825 | -0.0011 | 54 | 3 | 18 | -0.3825 | 131388 | 262144 | 0.0000 | 0.5012 | -0.0323 |
| Risk-Constrained Convex Verifier | linear_to_exact_error_reduction_usd | 1.3409 | -0.0000 | 54 | 3 | 18 | 1.3409 | 94928 | 262144 | 0.0000 | 0.3621 | -0.0849 |
| Risk-Constrained Convex Verifier | uniform_gross_to_exact_error_reduction_usd | 109.0984 | -29.7938 | 54 | 3 | 18 | 109.0984 | 47148 | 262144 | 0.0000 | 0.1799 | -0.6814 |
| Trace-Anchored Reference | gross_to_signed_error_reduction_usd | 735.6949 | 641.3881 | 54 | 3 | 18 | 735.6949 | 2 | 262144 | 0.0000 | 0.0000 | -0.1241 |
| Trace-Anchored Reference | uniform_to_nodal_error_reduction_usd | 0.0062 | 0.0009 | 54 | 3 | 18 | 0.0062 | 93172 | 262144 | 0.0000 | 0.3554 | 0.3781 |
| Trace-Anchored Reference | linear_to_exact_error_reduction_usd | 3.6605 | -0.1039 | 54 | 3 | 18 | 3.6605 | 11458 | 262144 | 0.0000 | 0.0437 | -0.2163 |
| Trace-Anchored Reference | uniform_gross_to_exact_error_reduction_usd | 739.3781 | 642.1057 | 54 | 3 | 18 | 739.3781 | 2 | 262144 | 0.0000 | 0.0000 | -0.1286 |

## Cross-network robustness

| network | load_multiplier | baseline_quality | mechanism | mean_absolute_error_usd | median_normalized_error | mean_overpayment_usd | congestion_share |
| --- | --- | --- | --- | --- | --- | --- | --- |
| IEEE 300-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal exact net value | 1930.899 | 1.000 | 304.945 | 0.000 |
| IEEE 300-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal gross | 2329.194 | 0.950 | 1559.317 | 0.000 |
| IEEE 300-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal signed linear | 1931.005 | 1.000 | 305.185 | 0.000 |
| IEEE 300-bus | 0.900 | Risk-Constrained Convex Verifier | Uniform gross | 2329.194 | 0.950 | 1559.317 | 0.000 |
| IEEE 300-bus | 0.900 | Risk-Constrained Convex Verifier | Uniform signed net | 1931.005 | 1.000 | 305.185 | 0.000 |
| IEEE 300-bus | 0.900 | Trace-Anchored Reference | Nodal exact net value | 5.607 | 0.002 | 5.192 | 0.000 |
| IEEE 300-bus | 0.900 | Trace-Anchored Reference | Nodal gross | 2750.609 | 1.385 | 2750.609 | 0.000 |
| IEEE 300-bus | 0.900 | Trace-Anchored Reference | Nodal signed linear | 9.333 | 0.002 | 9.201 | 0.000 |
| IEEE 300-bus | 0.900 | Trace-Anchored Reference | Uniform gross | 2750.609 | 1.385 | 2750.609 | 0.000 |
| IEEE 300-bus | 0.900 | Trace-Anchored Reference | Uniform signed net | 9.333 | 0.002 | 9.201 | 0.000 |
| IEEE 300-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal exact net value | 2190.475 | 1.000 | 345.560 | 0.000 |
| IEEE 300-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal gross | 2644.423 | 0.949 | 1771.869 | 0.000 |
| IEEE 300-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal signed linear | 2190.442 | 1.000 | 345.605 | 0.000 |
| IEEE 300-bus | 0.980 | Risk-Constrained Convex Verifier | Uniform gross | 2644.423 | 0.949 | 1771.869 | 0.000 |
| IEEE 300-bus | 0.980 | Risk-Constrained Convex Verifier | Uniform signed net | 2190.442 | 1.000 | 345.605 | 0.000 |
| IEEE 300-bus | 0.980 | Trace-Anchored Reference | Nodal exact net value | 11.607 | 0.006 | 11.281 | 0.000 |
| IEEE 300-bus | 0.980 | Trace-Anchored Reference | Nodal gross | 3130.354 | 1.393 | 3130.354 | 0.000 |
| IEEE 300-bus | 0.980 | Trace-Anchored Reference | Nodal signed linear | 14.333 | 0.006 | 14.096 | 0.000 |
| IEEE 300-bus | 0.980 | Trace-Anchored Reference | Uniform gross | 3130.354 | 1.393 | 3130.354 | 0.000 |
| IEEE 300-bus | 0.980 | Trace-Anchored Reference | Uniform signed net | 14.333 | 0.006 | 14.096 | 0.000 |
| IEEE 300-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal exact net value | 2312.435 | 1.000 | 363.912 | 0.000 |
| IEEE 300-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal gross | 2788.483 | 0.950 | 1866.217 | 0.000 |
| IEEE 300-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal signed linear | 2312.498 | 1.000 | 364.059 | 0.000 |
| IEEE 300-bus | 1.020 | Risk-Constrained Convex Verifier | Uniform gross | 2788.483 | 0.950 | 1866.217 | 0.000 |
| IEEE 300-bus | 1.020 | Risk-Constrained Convex Verifier | Uniform signed net | 2312.498 | 1.000 | 364.059 | 0.000 |
| IEEE 300-bus | 1.020 | Trace-Anchored Reference | Nodal exact net value | 7.046 | 0.002 | 6.811 | 0.000 |
| IEEE 300-bus | 1.020 | Trace-Anchored Reference | Nodal gross | 3295.971 | 1.385 | 3295.971 | 0.000 |
| IEEE 300-bus | 1.020 | Trace-Anchored Reference | Nodal signed linear | 10.349 | 0.003 | 10.335 | 0.000 |
| IEEE 300-bus | 1.020 | Trace-Anchored Reference | Uniform gross | 3295.971 | 1.385 | 3295.971 | 0.000 |
| IEEE 300-bus | 1.020 | Trace-Anchored Reference | Uniform signed net | 10.349 | 0.003 | 10.335 | 0.000 |
| IEEE 39-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal exact net value | 159.167 | 1.000 | 25.501 | 0.000 |
| IEEE 39-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal gross | 192.502 | 0.950 | 129.152 | 0.000 |
| IEEE 39-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal signed linear | 159.292 | 1.000 | 25.629 | 0.000 |
| IEEE 39-bus | 0.900 | Risk-Constrained Convex Verifier | Uniform gross | 192.502 | 0.950 | 129.152 | 0.000 |
| IEEE 39-bus | 0.900 | Risk-Constrained Convex Verifier | Uniform signed net | 159.292 | 1.000 | 25.629 | 0.000 |
| IEEE 39-bus | 0.900 | Trace-Anchored Reference | Nodal exact net value | 1.039 | 0.004 | 0.163 | 0.000 |
| IEEE 39-bus | 0.900 | Trace-Anchored Reference | Nodal gross | 225.987 | 1.374 | 225.961 | 0.000 |
| IEEE 39-bus | 0.900 | Trace-Anchored Reference | Nodal signed linear | 2.214 | 0.005 | 1.753 | 0.000 |
| IEEE 39-bus | 0.900 | Trace-Anchored Reference | Uniform gross | 225.987 | 1.374 | 225.961 | 0.000 |
| IEEE 39-bus | 0.900 | Trace-Anchored Reference | Uniform signed net | 2.214 | 0.005 | 1.753 | 0.000 |
| IEEE 39-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal exact net value | 194.749 | 1.000 | 31.644 | 0.000 |
| IEEE 39-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal gross | 236.960 | 0.949 | 160.025 | 0.000 |
| IEEE 39-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal signed linear | 194.733 | 1.000 | 31.671 | 0.000 |
| IEEE 39-bus | 0.980 | Risk-Constrained Convex Verifier | Uniform gross | 236.960 | 0.949 | 160.025 | 0.000 |
| IEEE 39-bus | 0.980 | Risk-Constrained Convex Verifier | Uniform signed net | 194.733 | 1.000 | 31.671 | 0.000 |
| IEEE 39-bus | 0.980 | Trace-Anchored Reference | Nodal exact net value | 1.302 | 0.007 | 1.086 | 0.000 |
| IEEE 39-bus | 0.980 | Trace-Anchored Reference | Nodal gross | 280.526 | 1.396 | 280.526 | 0.000 |
| IEEE 39-bus | 0.980 | Trace-Anchored Reference | Nodal signed linear | 3.226 | 0.007 | 3.148 | 0.000 |
| IEEE 39-bus | 0.980 | Trace-Anchored Reference | Uniform gross | 280.526 | 1.396 | 280.526 | 0.000 |
| IEEE 39-bus | 0.980 | Trace-Anchored Reference | Uniform signed net | 3.226 | 0.007 | 3.148 | 0.000 |
| IEEE 39-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal exact net value | 222.477 | 1.000 | 38.718 | 0.016 |
| IEEE 39-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal gross | 276.461 | 0.950 | 189.556 | 0.016 |
| IEEE 39-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal signed linear | 222.655 | 1.000 | 39.003 | 0.016 |
| IEEE 39-bus | 1.020 | Risk-Constrained Convex Verifier | Uniform gross | 274.720 | 0.950 | 187.816 | 0.016 |
| IEEE 39-bus | 1.020 | Risk-Constrained Convex Verifier | Uniform signed net | 221.966 | 1.000 | 38.268 | 0.016 |
| IEEE 39-bus | 1.020 | Trace-Anchored Reference | Nodal exact net value | 2.697 | 0.012 | 0.464 | 0.016 |
| IEEE 39-bus | 1.020 | Trace-Anchored Reference | Nodal gross | 320.302 | 1.381 | 319.864 | 0.016 |
| IEEE 39-bus | 1.020 | Trace-Anchored Reference | Nodal signed linear | 8.383 | 0.013 | 7.235 | 0.016 |
| IEEE 39-bus | 1.020 | Trace-Anchored Reference | Uniform gross | 320.107 | 1.381 | 319.669 | 0.016 |
| IEEE 39-bus | 1.020 | Trace-Anchored Reference | Uniform signed net | 8.312 | 0.013 | 7.164 | 0.016 |
| IEEE RTS 24-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal exact net value | 105.656 | 1.000 | 16.860 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal gross | 127.967 | 0.950 | 85.986 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal signed linear | 105.666 | 1.000 | 16.890 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Risk-Constrained Convex Verifier | Uniform gross | 127.967 | 0.950 | 85.986 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Risk-Constrained Convex Verifier | Uniform signed net | 105.666 | 1.000 | 16.890 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Trace-Anchored Reference | Nodal exact net value | 0.158 | 0.001 | 0.011 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Trace-Anchored Reference | Nodal gross | 150.977 | 1.381 | 150.970 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Trace-Anchored Reference | Nodal signed linear | 0.977 | 0.002 | 0.923 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Trace-Anchored Reference | Uniform gross | 150.977 | 1.381 | 150.970 | 0.000 |
| IEEE RTS 24-bus | 0.900 | Trace-Anchored Reference | Uniform signed net | 0.977 | 0.002 | 0.923 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal exact net value | 328.405 | 1.000 | 51.869 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal gross | 396.772 | 0.950 | 266.145 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal signed linear | 328.346 | 1.000 | 51.870 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Risk-Constrained Convex Verifier | Uniform gross | 396.772 | 0.950 | 266.145 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Risk-Constrained Convex Verifier | Uniform signed net | 328.346 | 1.000 | 51.870 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Trace-Anchored Reference | Nodal exact net value | 0.510 | 0.002 | 0.285 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Trace-Anchored Reference | Nodal gross | 469.193 | 1.393 | 469.181 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Trace-Anchored Reference | Nodal signed linear | 1.491 | 0.002 | 1.431 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Trace-Anchored Reference | Uniform gross | 469.193 | 1.393 | 469.181 | 0.000 |
| IEEE RTS 24-bus | 0.980 | Trace-Anchored Reference | Uniform signed net | 1.491 | 0.002 | 1.431 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal exact net value | 346.972 | 1.000 | 54.389 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal gross | 417.890 | 0.950 | 279.278 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal signed linear | 347.004 | 1.000 | 54.427 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Risk-Constrained Convex Verifier | Uniform gross | 417.890 | 0.950 | 279.278 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Risk-Constrained Convex Verifier | Uniform signed net | 347.004 | 1.000 | 54.427 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Trace-Anchored Reference | Nodal exact net value | 0.280 | 0.001 | 0.156 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Trace-Anchored Reference | Nodal gross | 492.958 | 1.383 | 492.958 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Trace-Anchored Reference | Nodal signed linear | 0.893 | 0.001 | 0.861 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Trace-Anchored Reference | Uniform gross | 492.958 | 1.383 | 492.958 | 0.000 |
| IEEE RTS 24-bus | 1.020 | Trace-Anchored Reference | Uniform signed net | 0.893 | 0.001 | 0.861 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal exact net value | 342.649 | 1.000 | 54.074 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal gross | 414.642 | 0.949 | 278.492 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Risk-Constrained Convex Verifier | Nodal signed linear | 342.664 | 1.000 | 54.091 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Risk-Constrained Convex Verifier | Uniform gross | 414.646 | 0.949 | 278.496 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Risk-Constrained Convex Verifier | Uniform signed net | 342.664 | 1.000 | 54.092 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Trace-Anchored Reference | Nodal exact net value | 2.970 | 0.009 | 2.822 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Trace-Anchored Reference | Nodal gross | 492.954 | 1.406 | 492.954 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Trace-Anchored Reference | Nodal signed linear | 3.368 | 0.010 | 3.245 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Trace-Anchored Reference | Uniform gross | 492.958 | 1.406 | 492.958 | 0.000 |
| PGLib IEEE 118-bus | 0.900 | Trace-Anchored Reference | Uniform signed net | 3.369 | 0.010 | 3.246 | 0.000 |
| PGLib IEEE 118-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal exact net value | 388.702 | 1.000 | 61.422 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal gross | 468.343 | 0.950 | 313.395 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Risk-Constrained Convex Verifier | Nodal signed linear | 388.771 | 1.000 | 61.498 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Risk-Constrained Convex Verifier | Uniform gross | 468.343 | 0.950 | 313.395 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Risk-Constrained Convex Verifier | Uniform signed net | 388.771 | 1.000 | 61.499 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Trace-Anchored Reference | Nodal exact net value | 2.182 | 0.006 | 0.813 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Trace-Anchored Reference | Nodal gross | 551.572 | 1.398 | 551.571 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Trace-Anchored Reference | Nodal signed linear | 2.898 | 0.005 | 2.261 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Trace-Anchored Reference | Uniform gross | 551.572 | 1.398 | 551.571 | 1.000 |
| PGLib IEEE 118-bus | 0.980 | Trace-Anchored Reference | Uniform signed net | 2.898 | 0.005 | 2.261 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal exact net value | 414.396 | 1.000 | 65.762 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal gross | 502.327 | 0.949 | 337.704 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Risk-Constrained Convex Verifier | Nodal signed linear | 414.488 | 1.000 | 65.885 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Risk-Constrained Convex Verifier | Uniform gross | 502.372 | 0.949 | 337.753 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Risk-Constrained Convex Verifier | Uniform signed net | 414.436 | 1.000 | 65.837 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Trace-Anchored Reference | Nodal exact net value | 3.003 | 0.007 | 2.858 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Trace-Anchored Reference | Nodal gross | 596.055 | 1.401 | 596.055 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Trace-Anchored Reference | Nodal signed linear | 3.956 | 0.007 | 3.917 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Trace-Anchored Reference | Uniform gross | 596.072 | 1.401 | 596.072 | 1.000 |
| PGLib IEEE 118-bus | 1.020 | Trace-Anchored Reference | Uniform signed net | 3.961 | 0.007 | 3.922 | 1.000 |

## Binding-constraint stress test

| capacity_multiplier | deadline_multiplier | day | capacity_binding_share | deadline_binding_share | estimator_schema_version | mae_mw | rmse_mw | nrmse | nmae | normalization_mean_truth_mw | bias_mw | max_abs_error_mw | paid_response_mwh | oracle_response_mwh | false_response_mwh | false_response_ratio | underestimation_mwh | credit_precision | credit_recall | credit_f1 | net_system_response_mwh |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.5500 | 0.2500 | 87.5000 | 0.0411 | 0.9118 | 3.0000 | 3.2794 | 4.7593 | 0.3389 | 0.2341 | 14.3314 | -1.1075 | 15.9391 | 15.7160 | 28.1302 | 2.6455 | 0.1375 | 15.0597 | 0.8625 | 0.3941 | 0.4814 | 0.4159 |
| 0.5500 | 0.5000 | 87.5000 | 0.0411 | 0.9013 | 3.0000 | 3.2794 | 4.7593 | 0.3389 | 0.2341 | 14.3314 | -1.1075 | 15.9391 | 15.7160 | 28.1302 | 2.6455 | 0.1375 | 15.0597 | 0.8625 | 0.3941 | 0.4814 | 0.4159 |
| 0.5500 | 1.0000 | 87.5000 | 0.0411 | 0.8738 | 3.0000 | 3.2794 | 4.7593 | 0.3389 | 0.2341 | 14.3314 | -1.1075 | 15.9391 | 15.7160 | 28.1302 | 2.6455 | 0.1375 | 15.0597 | 0.8625 | 0.3941 | 0.4814 | 0.4159 |
| 0.7000 | 0.2500 | 87.5000 | 0.0280 | 0.9118 | 3.0000 | 3.2910 | 4.8252 | 0.3419 | 0.2345 | 14.3314 | -1.1421 | 16.6726 | 15.1220 | 28.1302 | 2.2274 | 0.1306 | 15.2356 | 0.8694 | 0.3920 | 0.4823 | 0.1395 |
| 0.7000 | 0.5000 | 87.5000 | 0.0280 | 0.9013 | 3.0000 | 3.2910 | 4.8252 | 0.3419 | 0.2345 | 14.3314 | -1.1421 | 16.6726 | 15.1220 | 28.1302 | 2.2274 | 0.1306 | 15.2356 | 0.8694 | 0.3920 | 0.4823 | 0.1395 |
| 0.7000 | 1.0000 | 87.5000 | 0.0280 | 0.8738 | 3.0000 | 3.2910 | 4.8252 | 0.3419 | 0.2345 | 14.3314 | -1.1421 | 16.6726 | 15.1220 | 28.1302 | 2.2274 | 0.1306 | 15.2356 | 0.8694 | 0.3920 | 0.4823 | 0.1395 |
| 0.8500 | 0.2500 | 87.5000 | 0.0203 | 0.9118 | 3.0000 | 3.2934 | 4.9605 | 0.3481 | 0.2347 | 14.3314 | -1.1421 | 17.6559 | 14.8673 | 28.1302 | 1.9727 | 0.1253 | 15.2356 | 0.8747 | 0.3920 | 0.4846 | 0.1395 |
| 0.8500 | 0.5000 | 87.5000 | 0.0203 | 0.9013 | 3.0000 | 3.2934 | 4.9605 | 0.3481 | 0.2347 | 14.3314 | -1.1421 | 17.6559 | 14.8673 | 28.1302 | 1.9727 | 0.1253 | 15.2356 | 0.8747 | 0.3920 | 0.4846 | 0.1395 |
| 0.8500 | 1.0000 | 87.5000 | 0.0203 | 0.8738 | 3.0000 | 3.2934 | 4.9605 | 0.3481 | 0.2347 | 14.3314 | -1.1421 | 17.6559 | 14.8673 | 28.1302 | 1.9727 | 0.1253 | 15.2356 | 0.8747 | 0.3920 | 0.4846 | 0.1395 |
| 1.0000 | 0.2500 | 87.5000 | 0.0151 | 0.9118 | 3.0000 | 3.3040 | 5.0521 | 0.3521 | 0.2351 | 14.3314 | -1.1419 | 18.1490 | 14.6872 | 28.1302 | 1.8343 | 0.1221 | 15.2773 | 0.8779 | 0.3911 | 0.4854 | 0.1410 |
| 1.0000 | 0.5000 | 87.5000 | 0.0151 | 0.9013 | 3.0000 | 3.3040 | 5.0521 | 0.3521 | 0.2351 | 14.3314 | -1.1419 | 18.1490 | 14.6872 | 28.1302 | 1.8343 | 0.1221 | 15.2773 | 0.8779 | 0.3911 | 0.4854 | 0.1410 |
| 1.0000 | 1.0000 | 87.5000 | 0.0151 | 0.8738 | 3.0000 | 3.3040 | 5.0521 | 0.3521 | 0.2351 | 14.3314 | -1.1419 | 18.1490 | 14.6872 | 28.1302 | 1.8343 | 0.1221 | 15.2773 | 0.8779 | 0.3911 | 0.4854 | 0.1410 |
| 1.2000 | 0.2500 | 87.5000 | 0.0105 | 0.9118 | 3.0000 | 3.3040 | 5.0689 | 0.3529 | 0.2351 | 14.3314 | -1.1419 | 18.5861 | 14.7965 | 28.1302 | 1.9436 | 0.1246 | 15.2773 | 0.8754 | 0.3911 | 0.4841 | 0.1410 |
| 1.2000 | 0.5000 | 87.5000 | 0.0105 | 0.9013 | 3.0000 | 3.3040 | 5.0689 | 0.3529 | 0.2351 | 14.3314 | -1.1419 | 18.5861 | 14.7965 | 28.1302 | 1.9436 | 0.1246 | 15.2773 | 0.8754 | 0.3911 | 0.4841 | 0.1410 |
| 1.2000 | 1.0000 | 87.5000 | 0.0105 | 0.8738 | 3.0000 | 3.3040 | 5.0689 | 0.3529 | 0.2351 | 14.3314 | -1.1419 | 18.5861 | 14.7965 | 28.1302 | 1.9436 | 0.1246 | 15.2773 | 0.8754 | 0.3911 | 0.4841 | 0.1410 |

## Exact multi-participant value allocation

| baseline_quality | allocation_method | mean_participant_absolute_error_usd | mean_absolute_budget_residual_usd | max_absolute_budget_residual_usd | mean_absolute_total_value_error_usd |
| --- | --- | --- | --- | --- | --- |
| Risk-Constrained Convex Verifier | Exact Shapley net value | 101.5774 | 0.0000 | 0.0000 | 353.9058 |
| Risk-Constrained Convex Verifier | Leave-one-out marginal | 100.9162 | 7.2806 | 60.9791 | 352.0092 |
| Risk-Constrained Convex Verifier | Nodal signed linear | 102.2336 | 2.8658 | 52.3508 | 353.7856 |
| Risk-Constrained Convex Verifier | Standalone avoided cost | 102.5962 | 7.3851 | 60.9791 | 357.3421 |
| Trace-Anchored Reference | Exact Shapley net value | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Trace-Anchored Reference | Leave-one-out marginal | 2.2738 | 7.2470 | 67.9922 | 7.2470 |
| Trace-Anchored Reference | Nodal signed linear | 4.3386 | 12.8193 | 162.5464 | 12.8193 |
| Trace-Anchored Reference | Standalone avoided cost | 2.3060 | 7.7982 | 70.3043 | 7.7982 |

## Complete N-1 security-aware settlement

| baseline_quality | mechanism | mean_absolute_error_usd | median_absolute_error_usd | mean_overpayment_usd | mean_payment_usd | mean_realized_n1_value_usd | maximum_post_contingency_loading |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Risk-Constrained Convex Verifier | Base-case exact net value | 207.5251 | 126.3627 | 156.7248 | 0.7926 | -105.1319 | 1.0000 |
| Risk-Constrained Convex Verifier | N-1 exact net value | 155.1437 | 113.2993 | 36.7303 | -186.8148 | -105.1319 | 1.0000 |
| Risk-Constrained Convex Verifier | N-1 signed linear | 155.0230 | 112.5041 | 37.3166 | -185.5218 | -105.1319 | 1.0000 |
| Trace-Anchored Reference | Base-case exact net value | 192.6935 | 98.5047 | 185.2088 | 72.5922 | -105.1319 | 1.0000 |
| Trace-Anchored Reference | N-1 exact net value | 0.9026 | 0.8219 | 0.0120 | -106.0104 | -105.1319 | 1.0000 |
| Trace-Anchored Reference | N-1 signed linear | 2.2985 | 0.6119 | 2.0779 | -103.2745 | -105.1319 | 1.0000 |

## Scenario-robust N-1 payment certificate

| conversion_scenario | conversion_scale_factor | counterfactual_method | mean_payment_usd | mean_realized_value_usd | mean_absolute_error_usd | mean_overpayment_usd | maximum_post_contingency_loading |
| --- | --- | --- | --- | --- | --- | --- | --- |
| q10 | 0.7342 | Feasible Quantile Projection | -135.2360 | -76.2536 | 113.8132 | 27.4154 | 1.0000 |
| q10 | 0.7342 | Payment-Certified N-1 Verifier | -136.1515 | -76.2536 | 114.3165 | 27.2093 | 1.0000 |
| q10 | 0.7342 | Risk-Constrained Convex Verifier | -136.7991 | -76.2536 | 113.7268 | 26.5907 | 1.0000 |
| q10 | 0.7342 | Single Feasible Projection | -135.5559 | -76.2536 | 113.7575 | 27.2276 | 1.0000 |
| q50 | 0.9957 | Feasible Quantile Projection | -183.8867 | -104.6624 | 154.6133 | 37.6945 | 1.0000 |
| q50 | 0.9957 | Payment-Certified N-1 Verifier | -185.1282 | -104.6624 | 155.2808 | 37.4075 | 1.0000 |
| q50 | 0.9957 | Risk-Constrained Convex Verifier | -186.0088 | -104.6624 | 154.4787 | 36.5662 | 1.0000 |
| q50 | 0.9957 | Single Feasible Projection | -184.3189 | -104.6624 | 154.5212 | 37.4324 | 1.0000 |
| q90 | 1.2780 | Feasible Quantile Projection | -236.6478 | -136.3066 | 198.6828 | 49.1708 | 1.0000 |
| q90 | 1.2780 | Payment-Certified N-1 Verifier | -238.2828 | -136.3066 | 199.5121 | 48.7680 | 1.0000 |
| q90 | 1.2780 | Risk-Constrained Convex Verifier | -239.4151 | -136.3066 | 198.4805 | 47.6860 | 1.0000 |
| q90 | 1.2780 | Single Feasible Projection | -237.2443 | -136.3066 | 198.5369 | 48.7996 | 1.0000 |

## Validation-frozen payment target selection

| candidate_index | candidate_name | mean_validation_payment_mae_usd | validation_cells | selected |
| --- | --- | --- | --- | --- |
| 3 | Projection rho=1 | 53.6311 | 384 | True |
| 4 | Projection rho=3 | 59.3470 | 384 | False |
| 6 | Feasible Quantile Projection | 64.6893 | 384 | False |
| 2 | Projection rho=0.3 | 65.1398 | 384 | False |
| 0 | Projection rho=0.03 | 70.3217 | 384 | False |
| 1 | Projection rho=0.1 | 70.3217 | 384 | False |
| 5 | Projection rho=10 | 78.1599 | 384 | False |

## Nonlinear AC out-of-model validation

| network | counterfactual_method | mean_absolute_error_usd_per_h | mean_overpayment_usd_per_h | maximum_apparent_line_loading | maximum_voltage_violation_pu |
| --- | --- | --- | --- | --- | --- |
| IEEE 118-bus | Feasible Quantile Projection | 938.3462 | 810.6601 | 0.0421 | 0.0000 |
| IEEE 118-bus | Payment-Certified N-1 Verifier | 899.3529 | 772.2511 | 0.0421 | 0.0000 |
| IEEE 118-bus | Risk-Constrained Convex Verifier | 895.5394 | 767.6414 | 0.0421 | 0.0000 |
| IEEE 118-bus | Single Feasible Projection | 902.8701 | 776.0207 | 0.0421 | 0.0000 |
| IEEE 30-bus | Feasible Quantile Projection | 4.1100 | 3.5483 | 1.0000 | 0.0000 |
| IEEE 30-bus | Payment-Certified N-1 Verifier | 3.9509 | 3.3908 | 1.0000 | 0.0000 |
| IEEE 30-bus | Risk-Constrained Convex Verifier | 3.9335 | 3.3700 | 1.0000 | 0.0000 |
| IEEE 30-bus | Single Feasible Projection | 3.9655 | 3.4064 | 1.0000 | 0.0000 |
| IEEE 39-bus | Feasible Quantile Projection | 505.0174 | 436.8159 | 1.0000 | 0.0000 |
| IEEE 39-bus | Payment-Certified N-1 Verifier | 483.6718 | 415.6597 | 1.0000 | 0.0000 |
| IEEE 39-bus | Risk-Constrained Convex Verifier | 481.4573 | 413.0352 | 1.0000 | 0.0000 |
| IEEE 39-bus | Single Feasible Projection | 485.5532 | 417.6724 | 1.0000 | 0.0000 |
| IEEE RTS 24-bus | Feasible Quantile Projection | 796.3916 | 688.8471 | 0.9396 | 0.0000 |
| IEEE RTS 24-bus | Payment-Certified N-1 Verifier | 763.3773 | 656.3919 | 0.9383 | 0.0000 |
| IEEE RTS 24-bus | Risk-Constrained Convex Verifier | 760.0764 | 652.3916 | 0.9383 | 0.0000 |
| IEEE RTS 24-bus | Single Feasible Projection | 766.3377 | 659.5632 | 0.9383 | 0.0000 |

## Complete nonlinear AC post-contingency validation

| network | counterfactual_method | maximum_apparent_line_loading | maximum_voltage_violation_pu | minimum_voltage_pu | maximum_voltage_pu | evaluated_outages | locked_days |
| --- | --- | --- | --- | --- | --- | --- | --- |
| IEEE 14-bus | Feasible Quantile Projection | 0.01815 | 0.00000 | 0.97323 | 1.06000 | 19 | 54 |
| IEEE 14-bus | Payment-Certified N-1 Verifier | 0.01814 | 0.00000 | 0.97323 | 1.06000 | 19 | 54 |
| IEEE 14-bus | Risk-Constrained Convex Verifier | 0.01814 | 0.00000 | 0.97325 | 1.06000 | 19 | 54 |
| IEEE 14-bus | Single Feasible Projection | 0.01814 | 0.00000 | 0.97323 | 1.06000 | 19 | 54 |
| IEEE 9-bus | Feasible Quantile Projection | 0.87707 | 0.00000 | 0.94321 | 1.10000 | 6 | 54 |
| IEEE 9-bus | Payment-Certified N-1 Verifier | 0.87749 | 0.00000 | 0.94319 | 1.10000 | 6 | 54 |
| IEEE 9-bus | Risk-Constrained Convex Verifier | 0.87703 | 0.00000 | 0.94322 | 1.10000 | 6 | 54 |
| IEEE 9-bus | Single Feasible Projection | 0.87749 | 0.00000 | 0.94319 | 1.10000 | 6 | 54 |

## Complete spatial-assignment and power-scale robustness

| peak_dc_penetration | counterfactual_method | mean_absolute_error_usd | median_absolute_error_usd | maximum_absolute_error_usd | mean_overpayment_usd | maximum_line_loading | maximum_lmp_spread_usd_per_mwh | assignments | locked_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.0300 | Feasible Quantile Projection | 95.4758 | 34.9222 | 678.0849 | 82.4117 | 0.9651 | 0.0000 | 24 | 54 |
| 0.0300 | Risk-Constrained Convex Verifier | 91.2617 | 33.0945 | 623.9904 | 78.1622 | 0.9647 | 0.0000 | 24 | 54 |
| 0.0300 | Single Feasible Projection | 92.0088 | 33.0945 | 628.6517 | 79.0130 | 0.9665 | 0.0000 | 24 | 54 |
| 0.0300 | Trace-Anchored Reference | 0.2294 | 0.1091 | 1.8853 | 0.1339 | 0.9043 | 0.0000 | 24 | 54 |
| 0.0600 | Feasible Quantile Projection | 191.8167 | 70.0673 | 1365.5703 | 165.6007 | 1.0000 | 0.0021 | 24 | 54 |
| 0.0600 | Risk-Constrained Convex Verifier | 183.2457 | 66.4304 | 1254.6608 | 156.9514 | 1.0000 | 0.0021 | 24 | 54 |
| 0.0600 | Single Feasible Projection | 184.7498 | 66.4304 | 1264.2063 | 158.6660 | 1.0000 | 0.0021 | 24 | 54 |
| 0.0600 | Trace-Anchored Reference | 0.6996 | 0.1361 | 6.5057 | 0.2253 | 0.9930 | 0.0000 | 24 | 54 |
| 0.0900 | Feasible Quantile Projection | 289.1879 | 105.2141 | 2067.4782 | 249.7440 | 1.0000 | 4.0645 | 24 | 54 |
| 0.0900 | Risk-Constrained Convex Verifier | 276.2540 | 99.8524 | 1899.6093 | 236.6907 | 1.0000 | 3.8822 | 24 | 54 |
| 0.0900 | Single Feasible Projection | 278.5421 | 99.8524 | 1914.0068 | 239.2952 | 1.0000 | 4.0645 | 24 | 54 |
| 0.0900 | Trace-Anchored Reference | 1.3764 | 0.3015 | 12.7399 | 0.3797 | 1.0000 | 0.0021 | 24 | 54 |

## Continuous-horizon space-time market validation

| counterfactual_method | mean_event_only_error_usd | mean_full_cycle_error_usd | mean_recovery_adjustment_usd | mean_post_event_rebound_mwh | maximum_absolute_cycle_energy_residual_mwh | maximum_baseline_projection_l1_mw | space_time_only_participant_ir_rate | bilateral_contract_activation_rate | bilateral_individual_rationality_rate | minimum_participant_contract_utility_usd | minimum_operator_contract_utility_usd | maximum_budget_balance_residual_usd | maximum_bilateral_budget_balance_residual_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Feasible Quantile Projection | 11.655725 | 0.053170 | -9.995124 | 0.112061 | 0.000003 | 0.000005 | 0.018519 | 1.000000 | 1.000000 | 1.842918 | 1.842918 | 0.000000 | 0.000000 |
| Payment-Certified N-1 Verifier | 8.091153 | 0.084761 | -6.209876 | 0.098505 | 0.000002 | 0.000006 | 0.018519 | 1.000000 | 1.000000 | 1.842918 | 1.842918 | 0.000000 | 0.000000 |
| Risk-Constrained Convex Verifier | 11.186565 | 0.241926 | -0.240426 | 0.095461 | 0.000002 | 0.000005 | 0.018519 | 1.000000 | 1.000000 | 1.842918 | 1.842918 | 0.000000 | 0.000000 |
| Single Feasible Projection | 10.763272 | 0.084761 | -8.881995 | 0.098505 | 0.000002 | 0.000005 | 0.018519 | 1.000000 | 1.000000 | 1.842918 | 1.842918 | 0.000000 | 0.000000 |

## Dependence-robust paired tests

- High-5-of-10 | nrmse: comparator-minus-proposed mean difference 2.3045, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- High-5-of-10 | false_response_ratio: comparator-minus-proposed mean difference 0.7393, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- High-5-of-10 | credit_f1: comparator-minus-proposed mean difference 0.2525, two-sided exact block-sign p=1.526e-05, Holm-adjusted p=0.0001068 (18 nonoverlapping blocks).
- Metadata Gradient Boosting | nrmse: comparator-minus-proposed mean difference 1.7749, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Metadata Gradient Boosting | false_response_ratio: comparator-minus-proposed mean difference 0.7075, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Metadata Gradient Boosting | credit_f1: comparator-minus-proposed mean difference 0.2076, two-sided exact block-sign p=0.000885, Holm-adjusted p=0.00531 (18 nonoverlapping blocks).
- Ex-post Metadata Gradient Boosting | nrmse: comparator-minus-proposed mean difference 1.6197, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Ex-post Metadata Gradient Boosting | false_response_ratio: comparator-minus-proposed mean difference 0.6914, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Ex-post Metadata Gradient Boosting | credit_f1: comparator-minus-proposed mean difference 0.1840, two-sided exact block-sign p=0.00502, Holm-adjusted p=0.02008 (18 nonoverlapping blocks).
- Ex-post Quantile Gradient Boosting | nrmse: comparator-minus-proposed mean difference 1.5428, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Ex-post Quantile Gradient Boosting | false_response_ratio: comparator-minus-proposed mean difference 0.6658, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Ex-post Quantile Gradient Boosting | credit_f1: comparator-minus-proposed mean difference 0.1592, two-sided exact block-sign p=0.0241, Holm-adjusted p=0.0723 (18 nonoverlapping blocks).
- Synthetic Control | nrmse: comparator-minus-proposed mean difference 1.5449, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Synthetic Control | false_response_ratio: comparator-minus-proposed mean difference 0.7025, two-sided exact block-sign p=7.629e-06, Holm-adjusted p=5.341e-05 (18 nonoverlapping blocks).
- Synthetic Control | credit_f1: comparator-minus-proposed mean difference 0.2126, two-sided exact block-sign p=0.0008926, Holm-adjusted p=0.00531 (18 nonoverlapping blocks).
- Feasible Quantile Projection | nrmse: comparator-minus-proposed mean difference 0.0053, two-sided exact block-sign p=0.004051, Holm-adjusted p=0.008102 (18 nonoverlapping blocks).
- Feasible Quantile Projection | false_response_ratio: comparator-minus-proposed mean difference 0.0102, two-sided exact block-sign p=0.0625, Holm-adjusted p=0.125 (18 nonoverlapping blocks).
- Feasible Quantile Projection | credit_f1: comparator-minus-proposed mean difference -0.0032, two-sided exact block-sign p=0.1493, Holm-adjusted p=0.1493 (18 nonoverlapping blocks).
- Single Feasible Projection | nrmse: comparator-minus-proposed mean difference 0.0014, two-sided exact block-sign p=0.01357, Holm-adjusted p=0.01357 (18 nonoverlapping blocks).
- Single Feasible Projection | false_response_ratio: comparator-minus-proposed mean difference 0.0059, two-sided exact block-sign p=0.3395, Holm-adjusted p=0.3395 (18 nonoverlapping blocks).
- Single Feasible Projection | credit_f1: comparator-minus-proposed mean difference -0.0022, two-sided exact block-sign p=0.05859, Holm-adjusted p=0.1172 (18 nonoverlapping blocks).

## Scope and limitations

- BurstGPT exposes workload tokens but not facility power; token traces are scaled to an explicitly documented hyperscale capacity target.
- MIT SuperCloud provides measured GPU energy for its own workload, which is independently aggregated and scaled; it is not claimed to be a co-located trace from the same operator.
- The network tests use public IEEE RTS-24, IEEE-14, IEEE-30, IEEE-39, IEEE-118, and IEEE-300 benchmark cases, not confidential utility topology or market telemetry.
- All 24 mappings of the four measured regional traces to the four declared IEEE-118 connection buses and three predeclared power penetrations are evaluated, but these public traces are not claimed to be co-located utility and facility measurements.
- The final workload credit is constrained by a predeclared two-sided band around the selected single feasible projection; the upper side certifies false-credit noninferiority and the lower side bounds additional under-credit by the declared tolerance.
- The complete N-1 panel certifies preventive feasibility for every finite non-islanding line outage in the lossless continuous DC model; it is not an AC voltage, transient-stability, or island-balancing certificate.
- The nonlinear AC outage panel solves a separate corrective post-contingency optimum for every non-islanding IEEE-9 and IEEE-14 line outage; it is not a simultaneous preventive AC security-constrained OPF or a transient-stability certificate.
- The shared-active-plan preventive AC panel fixes non-reference active generation across every finite non-islanding IEEE-9 outage, with reactive-power, voltage, and reference-generator loss recourse; it is not a transient-stability or intertemporal unit-commitment certificate.
- The event-gate information panel removes post-gate arrivals before optimization and uses the locked execution trace only for scoring; its complete-ledger comparator quantifies information cost rather than defining a deployable gate policy.
- The cross-network AC panel is a corrective power-flow diagnostic over native-case admissible outages; voltage and loading diagnostics are reported without being promoted to a preventive AC security certificate.
