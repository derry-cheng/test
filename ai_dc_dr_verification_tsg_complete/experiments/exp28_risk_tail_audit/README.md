# Experiment 28: held-out risk-tail audit

This stage compares the selected total-plus-daily-CVaR risk contract with the
total-budget-only and CVaR-only ablations on the locked 54-day panel. It reports
mean, empirical 0.75-CVaR, and 90th-percentile false-credit ratios and absolute
MWh exposures together with paired circular three-day bootstrap intervals. The
audit is a validation of the tail claim; it does not refit the risk model or
use locked outcomes to select a profile.

The final directory contains `risk_tail_audit.csv`,
`risk_tail_paired_bootstrap.csv`, the experiment metadata, and the publication
figure `fig_risk_tail_tradeoff.pdf`/`.png`.

Finite-sample tail convention: each point estimate and each resample averages
exactly the largest `m = ceil((1 - level) * n)` values. At level 0.75 and 54 days,
`m = 14` (effective tail level 40/54). Repeated cutoff values never enlarge the
tail. This matches the fitted risk contract's integer-tail epigraph.

The intervals are unadjusted exploratory 95% percentile intervals, not
Holm-adjusted or simultaneous confidence intervals. Exp2's exact block-sign
p-values have their own explicitly declared Holm families. The observed
`joint_minus_comparator_point_estimate` is reported separately from the
`bootstrap_mean_difference`; the legacy `joint_minus_comparator_mean` column
is retained as an alias for the bootstrap mean, not the observed effect.
Metadata binds the input ledger and audit implementation hashes. No profile
is refitted or selected from these locked results.
