# Experiment 22: Coupled job-to-network certificate

This audit reconstructs the regional power profile directly from the exact
job-indexed service vector saved by Experiment 19. It checks the aggregation
residual over every declared event slot, then evaluates the arithmetic
event-window mean with the secure DC security-constrained economic dispatch
(SCED) model and all finite non-islanding N–1 line contingencies. The
network-facing profile is therefore the same primal witness as the job-level
ledger, rather than a separately optimized aggregate schedule; the reported
network value is explicitly per representative event interval.

The compact checkout uses the vendored public PYPOWER IEEE-118 case when the
declared PGLib raw case is unavailable.  A full-data run records the declared
PGLib path in `experiment_metadata.json`.
