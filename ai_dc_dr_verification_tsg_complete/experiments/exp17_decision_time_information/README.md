# Experiment 17: Event-Gate Decision-Time Information

This experiment evaluates the workload-state verifier under the information
available at the first declared event interval. Every arrival after the event
gate is removed from the optimization input, and the terminal equality is
relaxed only for work that is not yet due. The complete-ledger verifier is
reported as a separate information-rich comparator. The locked execution trace
is used only for scoring; it is never supplied to either decision.

Outputs are written to `results/intermediate/` and `results/final/`, with the
English visualization `figures/fig23_decision_time_information.png` and PDF.
