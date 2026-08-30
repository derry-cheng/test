# Experiment 11: Spatial and Power-Scale Robustness

This experiment evaluates every one of the \(4!=24\) assignments of the four
measured regional workload traces to the four declared IEEE 118-bus connection
points, together with two predeclared concentration controls (all traces at
bus 80, and a two-bus 80/116 split). The complete assignment set and controls
are crossed with three predeclared peak data-center penetrations and all 54
locked test days. No assignment is screened or selected from the outcomes.

The market payment uses the declared 10-segment security-constrained economic
dispatch objective. Realized value is evaluated independently with an
80-segment objective. The experiment compares the feasible quantile projection,
the selected single projection, the risk-constrained verifier, and the
trace-anchored mechanism-isolation reference.

The completed factorial contains 16,848 outcomes. Averaged over all 26
declared assignments and 54 locked days, the risk-constrained verifier and
the selected single projection have mean absolute payment errors of
$105.250, $211.555, and $315.490/day at 3%, 6%, and 9% peak penetration;
the feasible-quantile projection gives $81.613, $164.249, and $244.481/day.
The two concentration controls are retained in these aggregates rather than
treated as post-hoc exclusions. The maximum native-rating line loading is
1.000 p.u.; the maximum data-center LMP spread is $16.94/MWh in the complete
panel.

Run independently with:

```bash
python experiments/exp11_spatial_scale_robustness/run.py
```

Intermediate checkpoints are stored in `results/intermediate`. Complete tables
are written to `results/final`, and the English publication figure is written to
`figures`.
