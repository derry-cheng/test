# Revision and verification log

The current release rebuilds the declaration, risk, executable, network, and
settlement evidence chain. The detailed point-by-point mapping is in
`reports/review/tsg_resolution.md`.

Exp27 was regenerated after the signed-ledger change and replays 54 locked days
over 5,184 full-day cells with 37 finite N--1 contingencies per cell. Exp26 was
then rerun against the regenerated witness. Exp28 was rebuilt with three risk
ablations and both ratio and absolute-MWh tail metrics. Exp29 independently
recomputes 7,306,622 finite declaration-feasible start candidates and verifies
the saved policy objective.

The final release keeps the indexed service-variable count (13,198,247) distinct
from the candidate-start count (7,306,622), separates signed cycle settlement
from its cash-floor presentation, and labels the complete-ledger profile as an
ex-post comparator while the slot-62 profile is gate-causal. All experiment
outputs are retained in their experiment-specific directories; stale Python
caches, unrelated analyses, and temporary files are removed before release.
