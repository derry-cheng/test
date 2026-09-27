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
0.99. The raw q90/q99 benchmark factors exceed the 118-MW flexible nameplate;
the diagnostic capacity-safe multiplier is 1.161610 and yields a 118-MW peak
on the pre-network benchmark envelope. It is a planning diagnostic, not the
network activation gate. Experiments 9 and 15 retain raw q01/q99 conversion
factors and check the resulting normalized network scenario separately.
This calibration audit is separate from network-placement permutations and
does not use test outcomes to choose the scale.
