# Experiment 9: Scenario-Robust N-1 Payment Certificate

This experiment solves one global linear program for every locked test day. The
program selects a convex combination of six independently solved first-stage
workload-feasible projections and retains the validation-selected feasible
quantile projection only as an external transfer comparator. The contractual
reference is the validation-selected single feasible projection. The program
embeds the primal constraints of the all-contingency preventive N-1 dispatch for
every settlement interval. The risk-constrained verifier is an external
approximation target, not a selectable candidate. A lexicographic pair of
linear programs first minimizes target deviation and then maximizes the worst
fractional grid-cost margin without degrading that optimum. The resulting daily
N-1 baseline cost is constrained to be no larger than the selected single
projection in every held-out conversion scenario.

Run with:

```bash
PYTHONPATH=src:vendor python experiments/exp9_payment_certificate/run.py
```

Checkpoints are written under `results/intermediate`; complete tables, certified
profiles, metadata, and English vector/raster figures are written under
`results/final` and `figures`.
