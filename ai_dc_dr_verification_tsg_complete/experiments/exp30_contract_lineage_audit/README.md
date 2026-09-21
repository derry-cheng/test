# Experiment 30: contract and settlement lineage audit

This release audit recomputes the declaration-energy scale over the overlap of
each fixed submit-time runtime block with the locked risk windows. It checks the
information boundary of the executable witness, verifies the finite network
replay inputs, and records the distinction between the declaration-only RTS-24
replay and the independent observed-meter scoring panel.

The network replay is a feasibility and signed-value certificate. It is not a
closed-meter payment record. A payable settlement requires a meter field for
both the baseline and counterfactual trajectories; the audit therefore reports
`closed_meter_payment_ready=false` for the current declaration-only replay.
