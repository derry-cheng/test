# Experiment 18: Cross-Network AC N--1 Admissibility Audit

This experiment evaluates the intact AC dispatch and corrective AC recourse
against every finite non-islanding line outage in RTS-24, IEEE-30, IEEE-39,
and IEEE-118. The day and event slot are fixed before the panel (`first locked
test day`, first declared event slot), while 3%, 6%, and 9% data-center
penetrations are all retained. Active-power displacement from the intact plan
is reported explicitly; this cross-network panel is a nonlinear AC feasibility
audit and does not silently promote corrective recourse to a preventive claim.
The power scale is fitted only from the validation traces.

The resulting CSVs and English visualization are stored under `results/` and
`figures/`; checkpoints make the complete outage panel restartable.
