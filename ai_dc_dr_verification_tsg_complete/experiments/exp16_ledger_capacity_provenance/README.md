# Experiment 16: Ledger Provenance and Capacity Reconciliation

This experiment joins immutable scheduler submissions to DCGM execution,
checks one-to-one identity and energy conservation, and fits the submit-time
energy conversion label on a chronological, training-only positive-energy
join. The positive DCGM join is a calibration-label requirement; it does not
filter the complete scheduler population used by the Exp19 counterfactual. The
experiment also reconciles the committed 118-MW nameplate with the observed
trace envelope.

`workload_power_calibration_sensitivity.csv` evaluates calibration-validation
measured-to-predicted energy ratios at quantiles 0.01, 0.10, 0.50, 0.90, and
0.99. The direct ratios are reported even when they exceed the committed
capacity; the current flexible-only `capacity_safe_scale_factor` is 0.890086.
It is the predeclared clipped conversion used for capacity planning and never
produces a peak above 118 MW. The raw q99 endpoint remains un-clipped in the
separate fixed/flexible payment-network model of Experiments 9 and 15.
This calibration audit is separate from network-placement permutations and
does not use test outcomes to choose the scale.
