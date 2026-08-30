# Experiment 22: Coupled job-to-network certificate

This audit reconstructs the regional power profile directly from the exact
job-indexed service vector saved by Experiment 19. It checks the aggregation
residual over every declared event slot and independently rechecks each stored
job-energy equality, committed GPU nameplate bound, and regional capacity row
before any network solve. It then evaluates the arithmetic event-window mean
with the secure DC security-constrained economic dispatch (SCED) model and all
finite non-islanding N–1 line contingencies. The
network-facing profile is therefore the same primal witness as the job-level
ledger, rather than a separately optimized aggregate schedule; the reported
network value is explicitly per representative event interval. In addition to
the raw witness, the audit replays two homogeneous transforms from Experiment
21: fixed-nameplate and capacity-proportional. Each transform scales the
indexed service vector and every associated resource cap before rebuilding the
regional profile, so job-to-network scale is tested rather than inferred from a
single tiny witness.

The coupled certificate is pinned to the public PYPOWER IEEE RTS-24 case
(`case24_ieee_rts`) and to four predeclared generator-bus locations.  This
explicit case rule keeps the N–1 replay identical in compact and full-data
checkouts; the PGLib IEEE-118 case remains available for the independent
cross-network and AC panels.
