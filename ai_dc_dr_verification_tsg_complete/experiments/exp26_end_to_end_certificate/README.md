# Experiment 26: End-to-end evidence-chain certificate

This cached-only certificate recomputes the indexed job-to-network residuals and
checks the frozen risk, relative payment, and complete RTS-24 outage artifacts.
It records SHA-256 source hashes and explicit roles for the aggregate risk
profile, payment-certified profile, and executable submitted-job witness. The
roles remain separate; no numerical identity or universal payment theorem is
asserted.

The certificate does not refit, select, clip, or re-optimize any upstream
profile. Outputs are written to `results/final/`: `end_to_end_lineage.csv`,
`profile_role_lineage.csv`, `payment_relative_cap_audit.csv`,
`realized_payment_audit.csv`, and the JSON certificate.
