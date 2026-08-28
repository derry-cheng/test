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
a nine-method comparison, including separate tail-risk counterfactual and
settlement-safe credit outputs.
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
