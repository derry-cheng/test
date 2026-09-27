# Experiment 2 — Workload-Conserving Verification

Run with `python run.py` or `./run_all.sh --stage exp2`. Sixteen days fit a
simplex-constrained convex ensemble over six exact workload-feasible projections;
all candidate fits are retained. The validation program jointly constrains total
false-credit exposure and the 75% conditional value at risk of daily exposure.
A nested contiguous-fold ordering selects the reserve fraction before the locked
days are opened, and the selected value is recorded in both reserve audit files.
A second exact workload LP applies a pointwise event envelope defined by the
independently selected single feasible projection; this guarantees false-credit
MWh noninferiority without using execution truth. Fifty-four later days support
the locked comparison. The validation-selected causal Pareto anchor is distinct
from the metadata-targeted single projection used in the main external
comparison. The total-only, CVaR-only, and joint convex fits are reported
separately; locked means show that the total-only fit is better than the joint
fit on the four response metrics. The event-reward generator identity is
isolated in `oracle_identity_audit.csv` and excluded from baseline rankings
because it reuses its own generator truth. The settlement-safe credit output is
a separate contract profile.
The key statistical comparator, selected single projection, and convex verifier
receive the same complete submitted-job ledger at the same post-event decision
time. Four contiguous validation folds, moving-block intervals with four block
lengths, exact three-day block-sign randomization over 18 blocks with Holm correction, independent
constraint certificates, and sparse-complexity scaling are all written to final
CSV panels. `risk_truth_source_audit.csv` recomputes locked-test false credit
separately for the observed meter and the mechanism-isolation trajectory; both
rows are explicitly observational diagnostics and neither is a utility-event
treatment effect. Scoring truth is trace-observed execution and is never supplied
to a candidate method.
