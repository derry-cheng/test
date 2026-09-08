# Experiment 26: End-to-end evidence-chain certificate

This cached-only certificate recomputes the indexed job-to-network residuals,
checks the runtime-complete common witness, and verifies the frozen risk,
relative payment, and complete RTS-24 outage artifacts. The declaration witness
and its N-1 settlement replay carry one digest and one submission index. The
aggregate risk and payment profiles remain explicitly labeled analysis views.

The certificate does not refit, select, clip, or re-optimize any upstream
profile. Outputs are written to `results/final/`: `end_to_end_lineage.csv`,
`profile_role_lineage.csv`, `payment_relative_cap_audit.csv`,
`realized_payment_audit.csv`, and the JSON certificate.
