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
SciPy trust-constr and independently checked through KKT and primal residuals;
the locked fit's stationarity residual is below \(10^{-9}\), and the release
reference-lock diagnostic is disabled. The locked release reaches
0.902/0.780/26.506/0.536 for nRMSE/false/under-credit/\(F_1\), improving the
four means over the selected single feasible projection. This does not amount
to componentwise dominance: the validation-selected causal Pareto anchor has
better nRMSE, under-credit, and \(F_1\), while the total-budget-only ablation
has better locked means on all four metrics than the joint total-plus-CVaR fit.
The reported evidence therefore supports a trade-off, not universal
superiority. The complete seven-profile causal hull is separately certified
Pareto-efficient. The
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
a partial CSV to a concurrent audit. The final audit count is recorded in the
regenerated audit artifact rather than hard-coded here. Regression tests and
the ten-page LaTeX build are run against the final staged outputs. Experiment
outputs remain in their experiment-specific directories; disposable caches and
temporary files are excluded from the release.

Final release verification (2026-09-27) regenerated Experiments 2, 9, 10, 15,
17, 20, 23, 26, and 27 against the current locked profile and witness hashes.
Experiment 27 completed 5,184 network-settlement cells, after which Exp26
rechecked 75,326 jobs and 13,198,247 indexed variables with zero bridge
residual. The independent event replay was then regenerated against the new
witness digest. The unified audit passed all 402 checks, and the regression
suite passed. The IEEEtran manuscript rebuilt to exactly ten pages; rendered
pages were inspected for clipping, overlap, and table/figure layout. The
repository is 112 MB, with one local branch (`main`) and a worker cap of eight.
Exp10's Python-level AC case construction was GIL-bound under threads, so its
corrective and intact-plan preventive cases now use bounded process workers;
sampled process results match the prior implementation to numerical precision.
The large BurstGPT and MIT SuperCloud CSVs remain outside version control; the
manifest-checked downloader in `code/scripts/download_public_inputs.py` restores
them for full preprocessing. This final session consumed the locked processed
assets and reran the dependent experiment stages and audit.
