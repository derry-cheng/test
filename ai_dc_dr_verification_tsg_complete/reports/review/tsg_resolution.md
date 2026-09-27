# TSG Review Resolution — Current Evidence

This report records concrete changes made in this revision and separates
implemented checks from issues the available evidence does not resolve.

## C1 — Decision-time information

The manuscript and Experiment 17 README now identify the slot-62 panel as an
information-boundary audit. Arrivals after the gate are masked before target
construction, and execution is used only after commitment for scoring. The
54-day gate result is retained separately from the complete-ledger comparator.
Because the public traces have no utility-event label, neither result estimates
a causal event response. The gate result is not presented as field performance.

## C2 — Risk fit and ablations

The former `single reference` ablation label was inaccurate: that row was the
validation-selected causal Pareto anchor, not the metadata-targeted single
projection in the baseline table. Code and audit now name it `causal Pareto
anchor`. The manuscript reports the anchor and total-budget-only ablation in
Table II. The joint fit improves all four locked means over the selected single
projection, but total-only has better means on all four metrics than joint
total-plus-CVaR. The existing tail audit also does not show a CVaR advantage.
Thus the data support a risk/accuracy frontier and do not support a claim that
the CVaR term improves predictive performance over total-only.

## C3 — Aggregate-to-executable bridge

Experiment 29 verifies every stored contiguous start against the exact
separable additive price objective. It reports 7,306,622 feasible start
candidates, zero start mismatches, and a maximum objective residual of
\(2.27\times10^{-13}\) USD. The profile bridge remains materially inexact:
total-profile nRMSE is 0.03023, flexible relative-L2 residual is 1.58055, and
maximum absolute residual is 3.220 MW. The source code, captions, abstract, and
results now state that this proves policy optimality for the declared objective,
not close tracking of the aggregate risk target. This issue remains unresolved
for any claim that the risk profile itself is exactly executable.

## C4 — Capacity scale and q99 eligibility

Experiments 9 and 15 now check flexible site nameplate after fixed/flexible
conversion and the declared benchmark-to-network scale. The checks fail closed
if any validation or locked profile, or either interval endpoint, exceeds the
committed 118-MW flexible capacity. Experiment 16 continues to report the
un-normalized benchmark capacity diagnostic independently. The manuscript and
protocol READMEs say that post-normalization eligibility is a property of the
declared network scenario; the public traces do not demonstrate a co-located
facility response.

## C5 — Novelty and baseline fairness

The Introduction now positions the work against recent TSG research on
compute-power coupling and cross-regional dispatchable capacity. The event-
reward translation had reused the strategic generator profile and achieved
numerical identity with it; the experiment code now isolates it as an oracle
self-check rather than a ranked baseline. The other literature mappings remain
equation-level translations, explicitly not faithful software reproductions.
The supported contribution is the typed ledger-to-settlement invariant and its
information boundary, not the standard LP, CVaR, SCED, or allocation primitives.

## Release status

The manuscript remains capped at ten pages; audit and regression checks are
required after regeneration. The repository target is below 4 GB, numerical
workers remain below 20, and only `main` is retained. Raw scheduler and DCGM
files are external inputs, so preprocessing from raw data requires their
separate restoration. Because prior iterations already inspected the 54-day
panel, any new model chosen after reviewing those results must be labeled
exploratory; this revision does not retune on the locked panel.
