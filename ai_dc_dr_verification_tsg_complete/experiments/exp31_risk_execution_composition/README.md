# Exp31: composable risk contracts and validation-only active-tail frontier

This revision is a new, explicitly retrospective method-development experiment.
The previously published locked outcomes motivated the design; they are not a
fresh external validation set. The new choices below are fixed before computing
any new locked-profile metrics. Original Exp2/27 profiles and results are immutable.

## Frozen protocol

- Reuse the seven cached declaration-only candidates, validation days 45–60,
  and the existing locked days 61–114. No new candidate is chosen using test data.
- Keep the 10% validation MSE neighborhood of the causal Pareto reference.
  Replace its sufficient triangle-inequality row with the actual convex squared
  error constraint. A thin QR factorization reduces the exact conic norm; it
  does not approximate or change the constraint.
- Use the normalized MSE plus total-exposure preference (weight 1). A separate
  old-objective control retains total weight 1 and tail weight .5, removing only
  the hard risk rows, to isolate constraint activity from preference effects.
- Fit the exact-MSE total-only solution first. Set a validation total budget to
  1.10 times its exposure, and find the minimum feasible top-m tail under this
  total budget and the same accuracy neighborhood. Freeze tail budgets at
  25%, 50%, and 75% of the interval between the minimum tail and total-only tail.
  The 50% midpoint is the designated primary active-tail contract. The objective
  remains the same as total-only, with zero soft tail weight. Both endpoints and
  every failure are retained. This evaluates an actual binding tail contract,
  not a universal performance-improvement claim.
- The tail is the mean of the largest ceil(.25 H) daily exposures, counting
  each observation once even under bootstrap ties. Effective levels are saved.
- Fit and persist all weights, budgets, and source hashes before opening locked
  profile values in the runner. Only then score the full panel. Paired 3-day
  circular block-bootstrap intervals (5,000 draws, fixed project seed) are
  exploratory, unadjusted intervals; they are not confirmatory superiority tests.

## Risk-to-execution audit

Replay every original Exp27 runtime-complete profile, without changing starts,
energy, or nameplate semantics. Express target, model-defined reference, and
model-generated event meter using the *same* archived upper-nameplate affine
scale. This is a scale-aligned mechanism-isolation audit, not independent physical
meter evidence. The scale was set over the old locked block; it is therefore an
ex-post audit only. Report original and executed total/tail exposure, exact MSE,
residual-to-risk upper bounds, and explicit pass/fail for the carried scaled
validation contract. Mean total-risk budget is multiplied by H_test/H_validation;
this is an audit threshold, not an out-of-sample guarantee.

For fixed target b, execution x, reference r and meter m, define
F_d(b)=dt sum_event [b-max(m,r)]+ and delta_d=dt sum_event |x-b|.
Then F_d(x)<=F_d(b)+delta_d, sum F(x)<=sum F(b)+sum delta,
and T_m(F(x))<=T_m(F(b))+T_m(delta). The exact MSE is checked separately;
its sufficient bound is (RMSE(b,r)+RMSE(x-b))^2.

The payable quantity q=min([x-m]+,[b-m]+) has false credit bounded pointwise
by the target's false credit, hence preserves both risk bounds whenever the
target passes them on that same reference/meter/sample set. It does not preserve
executable-profile accuracy or identify a no-event physical counterfactual.
Uncapped executable-risk failure is never relabeled as a successful bridge.
Exp32 supplies the complementary directly risk-constrained runtime MILP.

## Reproduce

PYTHONPATH=code/src:vendor python experiments/exp31_risk_execution_composition/run.py

CVXPY with CLARABEL is required. The runner sets BLAS numerical backends to one
thread and runs serially. All solver outcomes carry independently recomputed
primal, stationarity and complementarity checks; the acceptance tolerance is
1e-5 in the explicit normalized conic formulation.
