# TSG revision status and evidence record

## Scope of this revision

The previously omitted public BurstGPT and MIT Supercloud inputs were restored from their official distribution endpoints and checked against the repository's byte-count and SHA-256 manifest. All four large CSV files match the locked hashes; the tracked PGLib case also matches. The data-preparation stage was rerun in 92.3 s, and the 54-day Exp2 and slot-62 Exp17 panels were regenerated in 341.9 s and 79.6 s, respectively. Exp9, Exp16, Exp20, Exp22, and Exp26--Exp30 were also replayed from their current checkpoints or inputs. The final machine audit passes 395/395 checks, the regression suite passes, and the manuscript rebuilds to ten pages with no overfull boxes. The reruns reproduce the locked evaluation design; they do not create a new test set or authorize test-period model selection.

The C1--C5 concerns below are recorded against the rerun evidence. A reproducible certificate is not treated as proof of predictive performance, and a network replay is not treated as a utility settlement. The results do not support a claim that the proposed model leads every baseline on every reported metric.

## C1 — Domain contribution and novelty

The power-system question is relevant: a data-center demand-response claim needs to connect pre-event workload declarations, feasible service, nodal value, and payment evidence. The revised manuscript keeps that question central and connects an executable workload ledger to signed nodal accounting. However, the principal optimization components—simplex-constrained convex fitting, exposure budgets, conditional value-at-risk, and finite start enumeration—are established tools. The current evidence does not isolate a new theoretical result or establish superiority over recent spatially coupled data-center demand-response methods. The contribution is therefore a potentially useful integration and verification design; a substantive novelty gap remains. Establishing C1 requires a sharper comparison against the closest power-system formulations and a result that changes what those formulations can certify, not additional implementation detail.

## C2 — Decision-time information and slot-62 evidence

The information-boundary protocol now fixes the commitment gate at slot 62, 30 minutes before the first event slot 64, and the regenerated panel uses only the committed ledger. The 54-day result remains weak: nRMSE is 1.366, F1 is 0.080, recall is approximately 0.050, and mean false response is 0.494 MWh/day. The information audit supports the timing claim, but these scores do not establish useful event-time response prediction. The complete-ledger result remains an ex-post diagnostic and cannot fill this gap. A new model would need to be chosen using training and validation data and evaluated once on an untouched holdout; the current locked test has not been used for further selection.

## C3 — Aggregate-to-job bridge

The independent finite-start audit reproduces the selected minimizer over 7,306,622 candidate starts, with zero start mismatches and a maximum objective-recomputation residual of (2.27\times10^{-13}) USD. That result establishes exact optimization for the declared finite linear-price objective. It does not establish that the chosen job schedule tracks the aggregate target: mean total-load nRMSE is 0.0302, while flexible-load relative-ℓ2 residual is 1.581 and maximum absolute residual is 3.220 MW. The bridge therefore remains an optimization certificate with a material tracking gap. Improving it requires a workload-feasibility model and a tracking objective whose trade-off is selected before locked evaluation; exact solution of the current objective cannot substitute for this evidence.

## C4 — Risk objective and internal baselines

The regenerated 54-day panel confirms that the joint total-plus-CVaR fit does not dominate its internal references. Its nRMSE, false credit, under-credit, and F1 are 0.9021, 0.7803 MWh/day, 26.506 MWh/day, and 0.5362. The total-budget-only ablation is better on all four measures: 0.8917, 0.6455 MWh/day, 26.372 MWh/day, and 0.5490. Its absolute false-credit CVaR is also lower (2.222 versus 2.607 MWh/day). In the paired three-day block bootstrap, joint-minus-total-only mean false credit is +0.134 MWh/day (95% CI 0.016--0.287); the absolute-CVaR difference is +0.394 MWh/day (95% CI -0.049--0.923). Thus the mean disadvantage is supported by this panel, while the CVaR difference remains uncertain; neither result supports an empirical benefit from the current tail term. The Causal Pareto reference also has lower nRMSE and under-credit and higher F1, but higher false credit, so the comparison is a trade-off rather than universal dominance. C4 remains unresolved. A defensible repair requires a training/validation redesign and a fresh locked evaluation, not a new threshold selected against these 54 days.

## C5 — Settlement and power-system scope

The rerun verifies the declared network coupling on RTS-24: the common witness covers 5,184 full-cycle cells, includes 37 finite N−1 outages per cell, and has zero service/network coupling residual. Exp30 still reports `closed_meter_payment_ready=false`; payment activation is therefore not established. The workload-to-region mapping is a benchmark assignment because the public trace does not provide facility-bus locations, and the data contain no utility intervention or field settlement. These results support a declaration-only network replay and an accounting audit. They do not support claims of observed grid-service delivery, field settlement, or transferable regional value. C5 remains unresolved at the level required for an operational TSG claim.

## Secondary consistency and reproducibility checks

The paper compiles to ten pages and contains 31 references. The final build has no overfull boxes, undefined citations, undefined labels, or duplicate labels; citation groups are limited to two sources per sentence, and the checked acronym expansions are present at first use. The project retains separate paper, code, experiment, report, and data directories. The new standard-library downloader restores the four excluded public CSV inputs and verifies their locked sizes and hashes. The project remains below the 4-GB limit. The code and experiments ran sequentially with numerical-library threads limited to one; the host exposed nine processors and the requested 20-core ceiling was not exceeded.

## Readiness decision

This revision improves reproducibility and corrects the evidence trail, but it does not resolve C1--C5. C2, C3, and C4 have direct quantitative gaps; C5 remains a scenario replay without meter-gated payment; C1 still needs a stronger novelty result. The manuscript should not be represented as meeting the TSG acceptance standard on this evidence. A full claim of across-the-board baseline superiority would conflict with the locked results and cannot be supported by wording changes.
