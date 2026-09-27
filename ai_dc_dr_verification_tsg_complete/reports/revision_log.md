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
ten-segment exact N--1 evaluator with four date-level workers and is forced to
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

## 2026-09-27 — verified-source rerun and critical-issue reconciliation

Restored the four untracked BurstGPT and MIT Supercloud CSV inputs using the
new `code/scripts/download_public_inputs.py` utility. Their sizes and SHA-256
values match `data/processed/data_manifest.json`; the tracked PGLib case also
passes the same check. Rebuilt the processed data from those inputs (92.315 s),
then reran Exp2 (341.900 s), Exp17 at the precommitted slot-62 gate (79.575 s),
Exp9 (3.754 s), Exp16 (2.251 s), Exp20 (1.117 s), Exp22 (2.207 s), Exp26
(4.875 s), Exp27 (18.175 s), Exp28 (5.737 s), Exp29 (11.128 s), and Exp30
(0.124 s). The runner exposed nine processors; numerical-library thread counts
were clamped to one and stages ran sequentially.

The reruns reproduce the locked evidence rather than selecting against the
test period. Exp2's joint total-plus-CVaR model remains behind the total-only
ablation on nRMSE, mean false credit, under-credit, F1, and absolute false-credit
CVaR. A paired three-day bootstrap gives a +0.134 MWh/day mean false-credit
difference (95% CI 0.016--0.287) and a +0.394 MWh/day absolute-CVaR difference
(95% CI -0.049--0.923). Exp17 retains slot-62 nRMSE 1.366, F1 0.080, and
recall 0.050. Exp29 confirms zero finite-start mismatches but retains flexible
relative-L2 target residual 1.581. Exp27 verifies zero network/service coupling
residual across the 5,184-cell common witness; Exp30 continues to report that
closed-meter payment is not ready. These results do not resolve C1--C5 and do
not justify a universal baseline-superiority claim.

After the revised evidence reconciliation, the independent audit passes
395/395 checks, `tests/run_tests.py` passes, the public-input check passes, and
the manuscript remains ten pages with no overfull boxes or unresolved
references. See `reports/review/tsg_resolution.md` and the
`latest_rerun` object in `reports/reproducibility/targeted_rerun_manifest.json`
for the point-by-point status and machine-readable provenance.
