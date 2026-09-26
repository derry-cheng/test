# TSG revision status and evidence record

This revision reconciles the manuscript and project summary with the locked artifacts. It updates wording, table references, settlement units, a trace-meter transcription, and the two-sided-credit derivation. It does not regenerate the locked experiment outputs: the raw BurstGPT and MIT Supercloud data are excluded from this checkout, so no rerun of the 54-day fitting/decision-time panels was possible in this session. All fitted model scores remain the existing, version-controlled results. I did rerun the paired three-day block bootstrap from the archived 54-day daily ablation ledger (5,000 resamples, seed 20260720); its 12 reported estimates and intervals match the checked-in output exactly.

## C1 — domain contribution and novelty

The Introduction frames the contribution around a power-system problem: connect declaration-feasible workload service to signed nodal value and N--1 settlement on one auditable ledger. Implementation primitives are not presented as a new optimizer. The claim is scoped to this coupling and its certificates. This clarifies the claimed contribution, but does not by itself establish novelty over prior spatially coupled data-center demand-response work; the literature positioning still requires expert review.

## C2 — decision-time evidence

The paper separates the complete-ledger mechanism-isolation comparison from the slot-62 committed-ledger evaluation and independent observational meter replay. The slot-62 score remains nRMSE 1.366 and F1 0.080 over 54 days, so current evidence does not establish strong event-time prediction. The text no longer treats the full-ledger score as an operational result. A model redesign and locked replay would be needed to improve this evidence; no test-period tuning is admissible.

## C3 — aggregate-to-job bridge

The claim now distinguishes exact optimization of the declared finite linear-price objective from tracking the aggregate target. The existing audit enumerates 7,306,622 starts, reports zero selected-start mismatches and an objective residual of 2.27e-13 USD, while total-load nRMSE is 0.03023, flexible relative-L2 residual is 1.581, and maximum absolute residual is 3.220 MW. This verifies the finite policy minimizer but does not establish close flexible-load target tracking. No new objective or experiment was run here.

## C4 — risk objective and internal comparisons

Table I includes the validation-selected Causal Pareto reference, separately from the rho=10 single feasible projection. The joint fit has locked metrics 0.9021/0.780/26.506/0.536 (nRMSE/false MWh/day/under-credit MWh/day/F1). The Causal Pareto reference scores 0.6914/1.895/17.024/0.699. The total-budget-only fit scores 0.8917/0.6455/26.3723/0.549 and false-credit CVaR 2.222 MWh/day, versus 2.607 for the joint fit. Thus the current data do not support dominance of the joint method over its internal reference or the total-only ablation, nor an empirical benefit from adding CVaR. The reproduced bootstrap gives joint-minus-total-only mean false credit of +0.134 MWh/day (95% interval 0.016--0.287) and a 75%-CVaR difference of +0.394 MWh/day (95% interval -0.049--0.923). The manuscript now reports these intervals and says explicitly that the tail-risk claim is not supported by this panel. Validation feasibility and KKT certificates are optimization evidence, not locked-test superiority. Resolving this critical issue requires a revised objective chosen on training/validation data and a fresh locked evaluation; the raw records needed for that run were unavailable here.

## C5 — settlement and power-system scope

The method and results distinguish declaration replay, signed network-value accounting, and meter-gated payment. The indexed N--1 replay is not labelled as a payable settlement. A closed meter remains a payment precondition. Trace-to-region placement is described as a benchmark scenario because the public data do not identify facility buses. The manuscript states MW, h, MWh, and USD roles in the settlement equations and retains negative debit cells in the signed ledger. The logged replay values are simulation evidence, not field settlement evidence.

## Secondary consistency checks

The paper compiles to ten US-letter pages with 31 references. The abstract is 255 words and expands AI, DR, GPU, CVaR, MSE, and nRMSE at first use. Tables and figures are cited and retain captions; the paper has three tables and three figures. The independent trace-meter MAE for the risk-constrained verifier is 6.879838 MW, displayed as 6.880 MW. The README and implementation-alignment note have been corrected to remove unsupported dominance language. The supporting credit-bound derivation now matches the paper's floor definition and epsilon=0 contract.

## Reproduction and repository state

No model training or optimization rerun was performed in this revision. The paired bootstrap recheck ran as a single-process calculation (about 13 s); the existing runner configuration uses at most 12 workers, within the stated 20-core cap. Other checks used manuscript compilation and source/result reconciliation. The branch inventory already contained only `main`, and the repository was approximately 340 MB, below the 4 GB ceiling. Existing directories already separate code, experiments, paper, reports, results, and data, so no result or dataset files were deleted.

Validation performed: three-pass LaTeX/BibTeX build; ten-page PDF check; no undefined references, citations, or overfull boxes in the final build log; metric comparison against the checked-in ablation and trace-meter summaries.
