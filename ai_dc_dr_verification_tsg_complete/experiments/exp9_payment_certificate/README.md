# Experiment 9: Scenario-Robust N-1 Payment Certificate

This experiment solves one global linear program for every locked test day. The
program selects a convex combination of six independently solved first-stage
workload-feasible projections and retains the validation-selected feasible
quantile projection only as an external transfer comparator. The contractual
reference is the validation-selected single feasible projection, whereas the
risk-constrained verifier is a separate validation-fitted
total-plus-daily-CVaR profile and is never silently substituted for the payment
cap. A lexicographic
pair of linear programs first minimizes target deviation and then maximizes the
worst fractional grid-cost margin without degrading that optimum. The resulting
daily N-1 baseline cost is constrained to be no larger than the selected single
projection in every held-out q01/q10/q50/q90/q99 conversion scenario.

Facility conversion uses a fixed/flexible decomposition. The benchmark scale is
calibrated on the held-out q99 flexible peak; fixed 6-MW/site demand is carried
separately, so the raw q99 factor is retained without clipping and can be
audited as an activation endpoint. The flexible-only capacity-safe factor in
Experiment 16 is a planning diagnostic, not a payment gate.

Run with:

```bash
PYTHONPATH=src:vendor python experiments/exp9_payment_certificate/run.py
```

Checkpoints are written under `results/intermediate`; complete tables, certified
profiles, metadata, and English vector/raster figures are written under
`results/final` and `figures`.
