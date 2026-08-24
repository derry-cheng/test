# Experiment 18: Cross-Network Preventive AC N--1 Certificate

This experiment evaluates a fixed active plan against every finite
non-islanding line outage in RTS-24, IEEE-30, IEEE-39, and IEEE-118. The day
and event slot are fixed before the panel (`first locked test day`, first
declared event slot), while 3%, 6%, and 9% data-center penetrations are all
retained. Non-reference generator active outputs are copied from the intact AC
dispatch for every outage; only the reference generator, reactive outputs, and
voltages can recourse. Four data-center regions use a pre-registered public-bus
mapping for each network; the mapping is fixed before any outage is solved.
Apparent-power and voltage limits are checked on the same fixed plan, and any
violation fails the stage. The power scale is fitted only from validation
traces.

The resulting CSVs and English visualization are stored under `results/` and
`figures/`; checkpoints make the complete outage panel restartable.
