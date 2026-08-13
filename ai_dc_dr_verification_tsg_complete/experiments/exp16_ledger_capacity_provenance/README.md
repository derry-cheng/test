# Experiment 16: Ledger Provenance and Capacity Reconciliation

This experiment joins immutable scheduler submissions to DCGM execution,
checks one-to-one identity and energy conservation, and freezes the resulting
positive-energy ledger before the validation/test split. It also reconciles
the committed 118-MW nameplate with the observed trace envelope.

`workload_power_calibration_sensitivity.csv` evaluates held-out
measured-to-predicted energy ratios at quantiles 0.01, 0.10, 0.50, 0.90, and
0.99. The direct ratios are reported even when they exceed the committed
capacity; `capacity_safe_scale_factor` is the predeclared clipped conversion
used for the capacity-safe region and never produces a peak above 118 MW.
This calibration audit is separate from network-placement permutations and
does not use test outcomes to choose the scale.
