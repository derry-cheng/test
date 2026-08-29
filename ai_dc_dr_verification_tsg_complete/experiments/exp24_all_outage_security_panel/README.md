# Experiment 24 — full finite N−1 frozen-profile security panel

This panel freezes the locked-test workload profiles before network evaluation
and solves the continuous DC security-constrained dispatch with every finite
non-islanding RTS-24 line outage. It does not screen outages using an AC
admissibility test, rank contingencies, or re-optimize the workload profile
after seeing a network result. The profile-to-bus map and the 0.90 native-load
multiplier are predeclared in `configs/default.yaml`.

The replay contains 54 locked days × 8 event slots × 2 frozen profiles, with
37 finite non-islanding outages represented in each cell. Results and the
machine-readable certificate are under `results/final/`.
