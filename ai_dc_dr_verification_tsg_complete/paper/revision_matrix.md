# Current TSG Revision Status

This matrix supersedes earlier closure summaries. It records what the current
code and locked outputs support; an implemented certificate is not treated as
evidence for a stronger empirical claim.

| Issue | Change in this revision | Evidence and remaining limit |
|---|---|---|
| C1 — Complete-ledger results were too close to a deployable decision | The paper and Experiment 17 documentation define the slot-62 gate as an information-boundary audit. The gate masks post-gate arrivals; execution telemetry is opened only for scoring. | The locked gate panel is reported separately from the complete-ledger profile. Public data have no utility-event labels, so this panel cannot establish causal event response or field performance. |
| C2 — The two-axis risk module was not identifiable against its anchor or simpler fits | Renamed the ablation anchor to `causal Pareto anchor` throughout code, reports, and manuscript. Added the causal Pareto and total-only rows to the locked table, and describe each convex fit as a separate program. | The joint fit is better than the selected metadata single projection on four mean metrics, but the total-only fit is better than the joint fit on all four locked means. The current results do not establish incremental CVaR benefit. `risk_module_ablation.csv`, `risk_tail_audit.csv`, and `risk_tail_paired_bootstrap.csv` are controlling evidence. |
| C3 — Aggregate risk profile and executable job schedule were treated as one trajectory | The manuscript now states the finite start policy's actual optimization scope: it exactly minimizes its separable additive price objective. The aggregate tracking residual is reported as a separate certificate. | Exp. 29 replays 7,306,622 feasible starts with zero start mismatches and a $2.27\times10^{-13}$ USD objective residual, but flexible relative-L2 target residual is 1.581 (maximum absolute residual 3.220 MW). Exact policy optimality does not resolve the profile-to-witness mismatch. |
| C4 — Raw q99 capacity and payment eligibility used inconsistent scales | Added fail-closed flexible-nameplate checks after fixed/flexible conversion and benchmark-to-network normalization. Exp. 9 checks five scenarios on validation and locked profile hulls; Exp. 15 checks q01/q99 endpoints. The paper distinguishes this normalized scenario from source-scale capacity diagnostics. | `network_capacity_activation_audit.csv` and `endpoint_capacity_activation_audit.csv` must pass the unified audit. The benchmark trace does not identify a co-located facility, so this is not a physical-site validation. |
| C5 — Novelty and baseline coverage were overstated | The Introduction now compares the ledger-verification question with recent coupled compute-power and cross-regional dispatchable-capacity studies. The event-reward generator identity is removed from peer rankings and isolated as an oracle self-check. | Five equation-level translations remain transparently labelled as translations, not software reproductions. The work's defensible novelty is the typed declaration-to-settlement invariant and information boundary; it is not a new CVaR, LP, SCED, or Shapley primitive. |

## Reproducibility and release checks

The release target remains a ten-page IEEE TSG manuscript, a single `main`
branch, no more than 20 numerical workers, and a repository below 4 GB. This
revision increments Experiment 9's payment certificate schema to 11 and
Experiment 15's endpoint schema to 14. The audit requires both capacity
certificates and rejects stale schema-10 payment outputs. Raw scheduler and
DCGM sources remain external; full preprocessing cannot be reproduced from the
repository alone without those files.

The same 54-day panel has already informed earlier revisions. New profile
selection on that panel would be exploratory rather than a fresh confirmatory
test. No test-informed retuning is used in this revision.
