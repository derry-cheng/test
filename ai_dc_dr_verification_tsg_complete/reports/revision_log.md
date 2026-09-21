# Revision and verification log

The current release rebuilds the declaration, risk, executable, network, and
settlement evidence chain. The detailed point-by-point mapping is in
`reports/review/tsg_resolution.md`.

Exp2, Exp9, Exp17, Exp20, Exp22, Exp23, Exp24, Exp26, Exp27, Exp28, Exp29, and
Exp30 were regenerated after the risk-contract and active-window changes; the AC
lineage panel is rerun from the current locked profiles. Exp27 replays 54 locked days over 5,184 full-day
cells with 37 finite N--1 contingencies per cell. Exp28 contains three risk
ablations and both ratio and absolute-MWh tail metrics. Exp29 independently
recomputes 7,306,622 finite declaration-feasible start candidates and verifies
the saved policy objective. Exp30 makes the declaration-only network replay and
closed-meter payment gate machine-checkable.

The final release keeps the indexed service-variable count (13,198,247) distinct
from the candidate-start count (7,306,622), separates signed cycle settlement
from its cash-floor presentation, and labels the complete-ledger profile as an
ex-post comparator while the slot-62 profile is gate-causal. Exp9's high-memory
unseen transfer evaluator uses a day-level checkpoint and one worker; the payment
evaluator is forced to regenerate whenever its profile checksum changes. Exp10's
AC N--1 panel uses bounded workers and a row checkpoint. Exp26 reproduces the
active-window declaration scale, including carry-in jobs, before accepting the
upstream hashes. The long Exp9 interval and unseen-transfer checkpoints now use
same-directory atomic replacement, so an interrupted serialization cannot expose
a partial CSV to a concurrent audit. The final unified run passes all 390 audit
checks, regression tests, and the ten-page LaTeX build. All experiment outputs
are retained in their experiment-specific directories; generated caches and
temporary files are removed before release.
