# Exp26: End-to-end evidence-chain certificate

This compact certificate checks the immutable chain from submit-time job
declarations to an indexed service witness, regional aggregation, nodal mapping,
validation-frozen risk/payment profiles, and the complete RTS-24 outage replay.
It recomputes residuals from the Exp19 service vector and records SHA-256 hashes
for every upstream artifact. The aggregate risk profile and indexed job witness
remain separate ledgers with explicit roles; the certificate prevents silent
profile substitution and does not claim that their numerical trajectories are
identical. Payment scope is a relative N--1 baseline-cost cap. It is not an
absolute no-overpayment, revenue-adequacy, or incentive-compatibility result.

Outputs: `end_to_end_lineage.csv`, `profile_role_lineage.csv`,
`payment_relative_cap_audit.csv`, `realized_payment_audit.csv`, and the JSON
certificate in `results/final/`.
