# Experiment 3 — Nodal Net-Value Settlement

Run with `python run.py` or `./run_all.sh --stage exp3`. All eight event intervals on
all 54 locked test days are evaluated by network-constrained SCED. Five mechanisms share
the same interval-specific price scale. Both layers preserve the PGLib
IEEE-118 topology, generator buses, capacities, and native ratings and use the
public PYPOWER IEEE-118 quadratic costs after an exact generator-bus alignment
check. Payments use 10 segments and realized value is independently re-solved
at 80-segment resolution, eliminating circular zero-error scoring. Trace-observed truth isolates the settlement
effect, while all estimated baselines quantify end-to-end performance. The proposed
net-value rule is bilateral: positive avoided cost earns a credit and negative
avoided cost creates a debit. Three-day exact paired block tests compare every
alternative mechanism with exact net value on the same locked days, with Holm
correction within each baseline-method family.
