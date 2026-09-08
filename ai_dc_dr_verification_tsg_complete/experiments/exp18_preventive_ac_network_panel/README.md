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
violation fails the stage. The declared native-load multiplier is 0.90,
matching the primary DC N--1 stress envelope; it is fixed before solving and
no line or voltage limit is relaxed. The fixed non-reference active plan uses
an explicit \(10^{-8}\)-MW bound; the certificate accepts only the declared
bound plus a (10^{-6})-MW solver-residual margin and records the post-solve
deviation. The power scale is fitted only from validation traces. The panel
therefore contains
\(2\times3\times6\times(32+35+24+177)=9{,}648\) outage outcomes (the exact
connected-outage counts and native-inadmissible screening counts are recorded
in the metadata).

The intact and contingency AC-OPF cells are evaluated in a bounded eight-worker
process pool. Parallel execution changes only wall-clock scheduling; each cell
receives an independent public case copy and the same hard constraints. A
schema-6 checkpoint permits restart after interruption without reusing
results from a different load multiplier, fixed-plan tolerance, or solver
protocol.

The panel records 9,648 admissible fixed-plan AC contingency solves and 144
intact reference dispatches. Native-inadmissible connected outages are screened
before workload injection and are reported explicitly in the metadata; they are
outside the declared AC admissibility scope. The resulting CSVs and English
visualization are stored under `results/` and `figures/`; checkpoints make the
complete outage panel restartable.
