# Reproducibility supplement

This supplement records operating conventions and the audit map for the revised manuscript. It is not a substitute for the model, proof, or principal results in `main.tex`. Exact numerical values and failures remain in their experiment CSVs.

## Data populations and measurement boundaries

The full scheduler population contains 75,326 valid submissions. Independent DCGM replay has 71,128 positive-energy execution matches; 68,662 have valid intervals in the common 121-day aggregate tensor. The submit-time energy-label fit has 71,141 positive scheduler/DCGM pairs, including 13 label-only pairs without valid measured intervals. These 13 cannot enter an execution decision or measured interval replay.

The GPU-power fit uses 44,391 training jobs, 9,637 calibration-validation jobs, and 41,154 locked jobs in its own task-level partition. Those counts are not interchangeable with the day-level workload panel. Workload scaling uses the first 40 complete days. Aggregate validation uses days 45–60 and scoring uses days 61–114.

Runtime/nameplate energy, calibrated central energy, and observed GPU energy have different meanings. Full-runtime energy is declared slots times requested GPUs times 0.001 MW/GPU times 0.25 hours. Central energy is a training-calibrated declaration estimate, not measurement. DCGM energy is observed only after commitment. The full runtime/nameplate and central totals are approximately 1,972.115 and 0.570 MWh; their ratio does not compare nameplate with a measured aggregate. Utility-scale benchmark normalization is separately declared.

## Runtime and rolling-window conventions

Finite Slurm timelimits are converted to complete 15-minute slots. An unlimited sentinel uses 128 slots; a separate precommitted 96-slot queue allowance determines the service endpoint. Timelimit is not a submit-to-completion deadline. Every full-runtime witness job occupies exactly its declared number of contiguous fixed-rate slots in its fixed scenario region.

The aggregate preemptive envelope permits deferral classes of 0, 4, and 512 slots. Its rolling window starts a maximum deadline plus one day before the event and ends a maximum deadline after it. Due work and event-day arrivals must finish, while later unexpired arrivals remain in the state. Future complete-ledger records are permissible only in the explicitly ex-post comparator. The gate protocol masks records unavailable at commitment.

The original runtime bridge enumerates 7,306,622 starts for 75,326 jobs. Its per-job optimality argument is exact only when all chosen blocks together satisfy every capacity row. The original observed peak utilization is 0.444%, so this large case does not validate congested coupling. Experiment 32 uses the same full-runtime semantics in a separate small coupled MILP panel. Experiment 25's calibrated service with a partial final slot remains a distinct model.

## Ledger integrity and information

Canonical scheduler records contain job ID, submission time, timelimit, requested GPUs, class, and scheduler state. SHA-256 detects changes in this tuple; it does not attest that a region, runtime, or energy claim was true when submitted. Execution start/end and DCGM fields form a separate post-event ledger. Region mapping, tariffs, conversion constants, and model settings must also be bound to the protocol manifest when certifying a complete decision.

The original complete-window scale and maximum slot-price normalization are ex-post. Positive scaling cancels from that price heuristic, which therefore avoids high target-load slots rather than enforcing target tracking. Experiment 31's common-affine-scale audit is explicitly retrospective. It checks total, tail, and accuracy transfer separately and preserves the failed execution certificate. Credit intersection has a narrower monotonicity guarantee on the same reference, meter, and sample set.

## Risk and inference conventions

The original simplex contains six metadata-targeted feasible projections and a validation-selected causal Pareto projection. The complete-ledger feasible-quantile comparator is external to this risk fit, although it is included in the separate payment hull. Four contiguous leave-block-out validation folds are not rolling-origin folds: training for an earlier validation block may contain later validation observations, but never locked observations.

All empirical tails use exactly the worst ceil(0.25 H) days, counting each observation once. At 54 days this is 14 days, an effective tail level of 0.74074. This same operator is applied under bootstrap ties. Experiment 28's 5,000 three-day block-bootstrap intervals are unadjusted exploratory percentile intervals; the separate block-sign tests have Holm-adjusted p-values. The provided block-length sensitivity and serial dependence should inform interpretation.

Experiment 31's exact-MSE/binding-tail frontier was designed after inspection of the old locked results. Candidate budgets are determined from validation and frozen before newly computing locked metrics, but the data are not a fresh holdout. The active-tail row has zero soft tail-objective weight, allowing its constraint effect to be separated from a preference effect.

## Network, payment, and coalition scopes

DC settlement uses standard lossless dispatch with native thermal ratings and every finite non-islanding single-line outage in the stated case. Islanding exclusions reflect the connected PTDF representation and must be reported. AC numerical unknowns are never proof of physical infeasibility. The revised common-denominator AC panel retains every topology-admissible method/outage/snapshot/penetration cell and reports solver status separately from certificate limits.

A finite-scenario dispatch-value cap is not a guarantee for an entire transfer that also contains a meter-backed capacity term, a linear space–time component, or a positive cash floor. The signed ledger retains negative-value intervals. The continuous-segment audit holds the realized counterfactual fixed: a joint LP finds the minimum and convexity gives the endpoint maximum. It does not prove endpoint sufficiency when realized load changes simultaneously with conversion.

Shapley allocation enumerates all 16 coalitions for four sites and 256 for eight portfolios. Exchangeable slices reduce larger contracts to count states through 20 participants. Efficiency allocates an already defined signed value; it cannot establish physical feasibility or causal credit.

## Audit index

- Experiments 1–2: manipulation incentives, aggregate verification, method comparisons, and ablations
- Experiments 3–9: signed settlement, network transfer, physical stress, participant allocation, N–1 dispatch, and finite-scenario value caps
- Experiments 10–12: AC/spatial transfer and complete-cycle remuneration
- Experiments 13–16: independent measured replay, indexed intervals, conversion intervals, and scale reconciliation
- Experiments 17–25: information gate, fixed-plan AC, declaration feasibility, independent meter/event replay, complete DC outage coverage, and calibrated-service stress
- Experiments 26–30: release lineage, runtime-complete witness, corrected held-out risk tails, saved-policy recomputation, and payment activation
- Experiment 31: risk-to-execution composition, exact-MSE binding-tail frontier, and explicit failed/passed predicates
- Experiment 32: matched-gate methods and full-runtime capacity stress

## Publication aliases

Joint risk means the original total-plus-tail risk verifier. Total-only and tail-only refer to its independently solved ablations. Causal Pareto anchor is the validation reference; single projection is the separate metadata-targeted comparator. Value-certified verifier means the network dispatch-value cap previously called PaymentSafe. Historical file names are retained for reproducibility and do not change these publication meanings.
