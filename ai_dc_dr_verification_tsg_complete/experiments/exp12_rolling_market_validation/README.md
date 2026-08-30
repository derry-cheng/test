# Experiment 12: Continuous-Horizon Market Validation

This experiment replaces the zero-arrival completion buffer with a continuous
rolling horizon containing every processed workload arrival. Each locked day
is preceded by a maximum-deadline washout interval and followed by the full
512-slot batch deadline. The submitted eight-slot event trajectory is embedded
by a two-stage lexicographic linear program: the first stage minimizes event
L1 trajectory distance, and the second minimizes operating cost on the
first-stage optimal face. Pre-event and recovery operation are endogenous. No
penalty-weight tradeoff or outcome-dependent repair rule is used.

The market analysis compares event-window remuneration with signed nodal
remuneration over the complete response cycle. The latter includes
anticipatory shifting and post-event recovery. A separately solved continuous
no-event optimum defines both delivered capacity service and participant
opportunity cost. The predeclared DR capacity value and signed space-time
energy value form the operator value; a symmetric Nash contract with a
no-activation outside option then certifies bilateral individual rationality
and budget balance. Every estimator, including the payment-certified verifier,
is evaluated on all locked days. Site allocations, energy-conservation
residuals, both budget-balance residuals, bilateral utilities, and paired block
tests are reported.

The row-level field `full_cycle_absolute_value_residual_usd` is the absolute
difference between complete-cycle space-time remuneration and the independently
solved continuous no-event optimum. It is a settlement-accounting residual, not
a second forecast-accuracy score. A zero residual is expected (up to LP
precision) when the lexicographic cost stage selects the same minimum-cost face
as the no-event reference; event-window settlement error remains a separate
metric. The companion `no_event_objective_gap_usd` records the direct
second-stage objective difference to make that accounting identity auditable.

Run independently with:

```bash
python experiments/exp12_rolling_market_validation/run.py
```

Intermediate rolling profiles are checkpointed in `results/intermediate`.
Complete tables and profiles are written to `results/final`, and the English
publication figure is written to `figures`.
