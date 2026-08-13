# Experiment 5: Cross-network robustness

This experiment evaluates the settlement mechanisms on the IEEE RTS 24-bus, IEEE
39-bus, PGLib IEEE 118-bus, and IEEE 300-bus systems at the pre-declared native
load multipliers 0.90, 0.98, and 1.02. All mechanisms use the same event-specific price scale. Peak
data-center penetration is fixed at 6% of native system load and distributed over
four fixed, pre-declared buses. Every public thermal rating is retained exactly.
Neither site placement nor line rating depends on workload outcomes, nodal prices,
or settlement errors. The panel therefore separates endogenous congestion evidence
from uncongested boundary cases without constructing a favorable bottleneck.
For each network/loading/baseline cell, a pre-declared paired block test compares
nodal linear net settlement with exact nodal net value; Holm correction is applied
over the twelve network-loading hypotheses within each baseline-quality family.
The trace-anchored layer isolates the convex grid-value mechanism at matched load
endpoints. The end-to-end layer retains counterfactual estimation error and tests
strict improvement with exact paired temporal-block inference without attributing
estimator error to the settlement rule. A complete 54-day boundary-cell convergence panel
repeats the RTS-24, 0.98-load evaluation at 10/40, 20/80, 40/160, and 80/320
settlement/evaluation cost segments. This verifies that a locally affine dispatch
region converges toward a zero linear-versus-exact gap rather than being hidden by
an arbitrary favorable discretization.

Run with `./run_all.sh --stage exp5`. Checkpoints, final CSV panels, and English
PNG/PDF figures are written inside this directory.
