# Experiment 18: Cross-Network Preventive AC N--1 Certificate

This experiment evaluates a fixed active plan against every finite
non-islanding line outage in RTS-24, IEEE-30, IEEE-39, and IEEE-118. Six
day/slot snapshots (three predeclared locked days crossed with the first and
last event slots) are fixed before the panel; no snapshot is selected from an
outage result. The 3%, 6%, and 9% data-center penetrations are all retained.
Non-reference generator active outputs are copied from the intact AC dispatch
for every outage; only the reference generator, reactive outputs, and voltages
can recourse. Four data-center regions use a pre-registered public-bus mapping
for each network; the mapping is fixed before any outage is solved.
Apparent-power and voltage limits are checked on the same fixed plan, and any
violation fails the stage. The declared native-load multiplier is 0.45; it is
fixed before solving to keep every public case in the stated AC model domain,
including the 9% IEEE-39 snapshot. The power scale is fitted only from
validation traces. The panel therefore contains
\(2\times3\times6\times(36+38+24+177)=9{,}900\) outage outcomes.

The resulting CSVs and English visualization are stored under `results/` and
`figures/`; checkpoints make the complete outage panel restartable.
