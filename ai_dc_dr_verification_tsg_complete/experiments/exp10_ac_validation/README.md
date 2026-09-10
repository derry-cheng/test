# Experiment 10: Nonlinear AC Validation

This experiment evaluates every locked day on IEEE RTS-24, IEEE-30, IEEE-39,
and IEEE-118 with a nonlinear AC optimal power flow. The evaluated interval is the maximum realized
data-center demand within the eight declared event intervals of each day. Native
active and reactive loads, voltage bounds, generator reactive-power limits, and
apparent-power branch ratings are retained.

A second complete panel evaluates all 6 finite non-islanding IEEE-9 outages
and all 19 finite non-islanding IEEE-14 outages for each counterfactual and
locked day. Each outage is solved as
a nonlinear post-contingency AC optimal power flow with corrective redispatch;
no loading-based contingency screening is used.

A third complete panel evaluates a shared preventive active-power plan on
IEEE-9. For each locked day, counterfactual, and 3%, 6%, or 9% peak
data-center penetration, the intact-case active outputs of all non-reference
generators are equality-fixed in every one of the six non-islanding outages.
Only reference-generator loss compensation, reactive generation, and voltage
are contingency recourse. All panels compare the feasible-quantile, single-
projection, risk-constrained, and payment-certified counterfactuals. The
preventive panel therefore contains 3,888 outage cells and
does not use loading-based screening.

Run with:

```bash
PYTHONPATH=code/src:vendor python experiments/exp10_ac_validation/run.py
```

The run checkpoints the base-case network-day cells, the corrective
method-day-outage panel, and the shared-active-plan preventive panel, and emits
full tables plus English PNG/PDF visualizations.

After a profile refit, the run compares every upstream method array and the
AC peak-trace normalization maximum before resuming. Rows whose numeric input
is bytewise identical are carried forward with the current combined profile
digest; changed RiskSafe rows are re-solved. The resulting reuse and refit
lineage is stored in `results/final/ac_profile_refit_reuse_manifest.json` and
is checked by the repository audit.
