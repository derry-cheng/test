# Experiment 17: Event-Gate Decision-Time Information

This experiment evaluates the workload-state verifier under the information
available at the first declared event interval. Every arrival after the event
gate (slot 60, one hour before the event window) is removed from both the
gate-consistent target construction and the optimization
input, and the terminal equality is relaxed only for work that is not yet due.
The complete-ledger verifier is reported as a separate information-rich
comparator. The deployable committed-ledger rolling-service mode projects the
gate-consistent target over the physical fixed-plus-flexible capacity envelope, so it
can serve committed jobs without reserving or paying for future arrivals. Its
DR price and target regularization are selected from a predeclared exact-LP grid
on the 16 validation days under a false-credit budget; the locked test days are
never used for this choice. A committed-ledger reference schedule is retained
as an eligibility control. An information-boundary reserve is calibrated on earlier validation days for capacity planning;
it is never inserted into payment eligibility before the corresponding jobs are
committed. After the event meter closes, gross forecast credit is converted to
the pointwise meter-capped payable quantity; gross false credit remains the
independent risk metric. The event-response rows are explicitly operating
replays because the public releases contain no utility event label. The
measured execution tensor is scored separately in
`decision_time_trace_replay.csv` and is never supplied to a decision.

Outputs are written to `results/intermediate/` and `results/final/`, with the
English visualization `figures/fig23_decision_time_information.png` and PDF.
