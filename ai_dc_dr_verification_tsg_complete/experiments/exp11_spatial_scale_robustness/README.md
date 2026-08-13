# Experiment 11: Spatial and Power-Scale Robustness

This experiment evaluates every one of the \(4!=24\) assignments of the four
measured regional workload traces to the four declared IEEE 118-bus connection
points. The complete assignment set is crossed with three predeclared peak
data-center penetrations and all 54 locked test days. No assignment is screened
or selected from the outcomes.

The market payment uses the declared 10-segment security-constrained economic
dispatch objective. Realized value is evaluated independently with an
80-segment objective. The experiment compares the feasible quantile projection,
the selected single projection, the risk-constrained verifier, and the
trace-anchored mechanism-isolation reference.

The completed factorial contains 15,552 outcomes. At 3%, 6%, and 9% peak
penetration, the risk-constrained verifier has mean absolute payment errors of
$103.80, $208.89, and $315.38/day, compared with $106.05, $213.47, and
$322.39/day for the closest feasible-quantile projection. Its mapping-level
mean error is lower in all 72 mapping--scale cells. The maximum native-rating
line loading is 1.000 p.u., and the maximum data-center LMP spread is
$13.03/MWh.

Run independently with:

```bash
python experiments/exp11_spatial_scale_robustness/run.py
```

Intermediate checkpoints are stored in `results/intermediate`. Complete tables
are written to `results/final`, and the English publication figure is written to
`figures`.
