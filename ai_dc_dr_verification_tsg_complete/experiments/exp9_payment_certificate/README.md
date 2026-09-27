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
projection in every calibration-validation q01/q10/q50/q90/q99 conversion
scenario; locked days are an independent certificate replay.

Facility conversion uses a fixed/flexible decomposition. The benchmark scale is
calibrated on the calibration-validation q99 flexible peak, and fixed 6-MW/site
demand is carried separately. Each q01/q10/q50/q90/q99 profile is checked
against the 118-MW flexible nameplate after the declared network normalization;
the split-level results are saved in
`network_capacity_activation_audit.csv`. This is a normalized network scenario
check, not evidence that the public trace is a co-located facility measurement.
Experiment 16's raw flexible-only capacity-safe factor remains a separate
pre-network planning diagnostic.

Run with:

```bash
PYTHONPATH=code/src:vendor python experiments/exp9_payment_certificate/run.py
```

Checkpoints are written under `results/intermediate`; complete tables, certified
profiles, metadata, and English vector/raster figures are written under
`results/final` and `figures`. A resumed run is accepted only when the current
Experiment-2 profile checksum appears in both the locked evaluator rows and the
unseen-transfer rows; changing the risk profile therefore forces a complete
payment replay rather than a row-count-only reuse.
