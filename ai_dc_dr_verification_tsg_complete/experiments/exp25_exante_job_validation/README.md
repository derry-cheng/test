# Experiment 25: Submit-time job validation

This stage validates the information boundary used by the indexed job model. It
loads the scheduler-only submission ledger and joins it to the DCGM execution
ledger only after the decision inputs are frozen. The central service quantity,
the physical requested-GPU nameplate, and the declared runtime are reported
separately. No observed energy, completion time, or allocation telemetry is
used to construct an Exp19 release, deadline, objective, or service equality.

The final directory contains a scalar certificate and a job-type stratified
coverage table. The results are an ex-ante declaration audit, not a second
counterfactual schedule.
