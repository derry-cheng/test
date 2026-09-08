# Experiment 28: held-out risk-tail audit

This stage compares the selected total-plus-daily-CVaR risk contract with the
total-budget-only ablation on the locked 54-day panel. It reports the mean,
empirical 0.75-CVaR, and 90th-percentile false-credit ratios together with a
paired circular three-day bootstrap interval. The audit is a validation of the
tail claim; it does not refit the risk model or use locked outcomes to select a
profile.

The final directory contains `risk_tail_audit.csv`,
`risk_tail_paired_bootstrap.csv`, the experiment metadata, and the publication
figure `fig_risk_tail_tradeoff.pdf`/`.png`.
