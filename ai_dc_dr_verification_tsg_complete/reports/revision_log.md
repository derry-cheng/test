# Revision and verification log

The current release rebuilds the declaration, risk, executable, network, and
settlement evidence chain. The detailed point-by-point mapping is in
`reports/review/tsg_resolution.md`.

Exp2, Exp9, Exp17, Exp20, Exp22, Exp23, Exp24, Exp26, Exp27, Exp28, Exp29, and
Exp30 were regenerated after the causal-Pareto risk-contract and active-window
changes; the AC lineage panel is rerun from the current locked profiles. Exp27 replays 54 locked days over 5,184 full-day
cells with 37 finite N--1 contingencies per cell. Exp28 contains three risk
ablations and both ratio and absolute-MWh tail metrics. Exp29 independently
recomputes 7,306,622 finite declaration-feasible start candidates and verifies
the saved policy objective. Exp30 makes the declaration-only network replay and
closed-meter payment gate machine-checkable.

The locked risk profile is the validation-selected \(\rho=10\) causal Pareto
simplex fit. Its predeclared 10% MSE non-inferiority certificate is solved by
CVXPY/Clarabel and independently checked through KKT and primal residuals; the
release reference-lock diagnostic is disabled. The locked release reaches
0.902/0.780/26.506/0.536 for nRMSE/false/under-credit/\(F_1\), strictly
improving all four metrics over the single feasible projection. The CVaR-only
row is retained as an internal comparator rather than relabelled as the joint
fit. The complete seven-profile causal hull is separately certified
Pareto-efficient, so the table does not conflate a boundary point with
componentwise dominance over every internal frontier point. The
final release keeps the indexed service-variable count (13,198,247) distinct
from the candidate-start count (7,306,622), separates signed cycle settlement
from its cash-floor presentation, and labels the complete-ledger profile as an
ex-post comparator while the slot-62 profile is gate-causal. Exp9's unseen
transfer evaluator uses a day-level checkpoint; the independent panel uses a
ten-segment exact N--1 evaluator with eight date-level workers and is forced to
regenerate whenever its profile checksum changes. Exp10's
AC N--1 panel uses bounded workers and a row checkpoint. Exp24 applies the
validation-frozen Exp9 $q_{99}$ facility-to-network scale before its complete
864-cell, 31,968-outage RTS-24 replay. Exp26 reproduces the
active-window declaration scale, including carry-in jobs, before accepting the
upstream hashes. The long Exp9 interval and unseen-transfer checkpoints now use
same-directory atomic replacement, so an interrupted serialization cannot expose
a partial CSV to a concurrent audit. The final unified run passes all 395 audit
checks, regression tests, and the ten-page LaTeX build. All experiment outputs
are retained in their experiment-specific directories; generated caches and
temporary files are removed before release.
