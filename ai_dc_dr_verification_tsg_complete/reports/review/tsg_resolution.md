# TSG revision resolution

This release maps each critical review point to a changed implementation, a
machine-readable certificate, and the corresponding manuscript statement.

## C1 — signed settlement ledger

`executable_witness.py` now writes `signed_settlement_usd` and
`cash_settlement_usd` as separate interval fields. Exp27 aggregates the signed
cycle before applying the optional cash floor. The regenerated ledger contains
1,168 negative settlement intervals, a signed cycle total of 161.036 USD, and a
separate cash-floor presentation of 277.806 USD. Exp26 independently checks both
pointwise identities and the signed-cycle total.

## C2 — risk target and executable policy

The risk-to-start mapping is explicitly an exact minimizer of a finite
declaration-feasible start objective. It is not described as exact equality to
the aggregate target. Exp29 recomputes all 7,306,622 candidates, finds zero
start mismatches and an objective residual below (2.3\times10^{-13}) USD, and
reports total-load nRMSE 0.0260 together with flexible-target nRMSE 3.144. The
residual definition and figure are included in the manuscript and retained in
the daily CSV.

## C3 — decision-time information boundary

The complete-ledger risk profile is labelled as an ex-post comparator. The
slot-62 gate profile is the deployable contract mode: post-gate arrivals and
execution truth are absent from its decision LP, its 3-MWh committed-service
constraint is fixed before scoring, and the information-boundary certificate
records these conditions for all 54 locked days. The results table now reports
both profiles rather than merging their claims.

## C4 — joint total/CVaR evidence

Exp28 now evaluates the joint, total-only, and CVaR-only fits on both normalized
false-credit ratios and absolute daily MWh. It reports means, empirical
CVaR\(_{0.75}\), 90th percentiles, and paired three-day block intervals. The
manuscript states that the joint fit is selected by simultaneous validation
constraints and does not claim held-out dominance where the intervals include
zero.

## C5 — theoretical and domain contribution

The paper adds a typed residual-to-value bound for a Lipschitz SCED value,
strengthening the job-to-region-to-bus coupling invariant. The continuous
conversion claim is restricted to the fixed-counterfactual affine segment
actually solved by Exp15; the five-scenario payment certificate remains finite
and explicit. A recent IEEE TSG computation--power coupling reference is added
to the related-work boundary. The contributions are stated as power-system
certificates rather than software components.

## Minor consistency and presentation corrections

The manuscript now distinguishes service-variable counts from candidate-start
counts, uses the signed/cash settlement names consistently, expands required
abbreviations on first use, removes a duplicate section declaration, updates the
tail-risk and bridge figures, and adds complete-ledger/gate rows to the
information-boundary table. Supporting formulation and implementation notes use
the same counts and claim boundaries. Generated artifacts remain under their
experiment-specific `results/final` and `figures` directories; human-readable
review records are kept under `reports/review`.
