# Experiment 24 — full finite N−1 frozen-profile security panel

This panel freezes the locked-test workload profiles before network evaluation
and solves the continuous DC security-constrained dispatch (DC N-1 SCED) with
all 37 finite non-islanding RTS-24 line outages. The outage set is defined by
the DC RTS-24 topology; no AC admissibility filter, contingency ranking, or
post-result workload re-optimization is used. The profile-to-bus map and the
0.90 native-load multiplier are predeclared in `configs/default.yaml`.

The replay contains 54 locked days × 8 event slots × 2 frozen profiles, hence
864 optimization cells and 31,968 sample-contingency evaluations (37 finite
non-islanding outages per cell). Results and the machine-readable certificate
are under `results/final/`.
