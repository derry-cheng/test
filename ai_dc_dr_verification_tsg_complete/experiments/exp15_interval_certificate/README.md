# Interval-Robust Payment Certificate

This experiment independently audits the locked payment profile with the
four-segment N-1 dispatch model at both calibration-validation energy-conversion
interval endpoints (q01 and q99) against the validation-selected single feasible
projection. Fixed facility demand is carried separately from flexible workload
in both endpoint solves. Each endpoint is checked against the 118-MW flexible
nameplate after the declared network normalization, with the values retained in
`endpoint_capacity_activation_audit.csv`; no conversion factor is clipped. This
certificate applies to the normalized network scenario and does not establish a
co-located facility measurement. The flexible-only capacity-safe factor from
Experiment 16 is retained as a pre-network planning diagnostic.
The standalone stage consumes the locked processed workload and Exp9 artifacts;
raw-source validation remains the responsibility of the explicit `data` or
`all` pipeline stages.
The feasible-quantile profile remains an external transfer comparator. Convexity
of each optimal dispatch value makes the two endpoints an exact worst-case cost
audit over the closed interval. The finite q10/q50/q90 payment guarantee
remains the pointwise contract; the endpoint result is reported as a worst-case
interval bound, not as an unproved pointwise ordering of two value functions at
every interior factor.

The run writes `interval_endpoint_certificates.csv` for the two independent
four-segment endpoint replays and `payment_value_interval_certificates.csv` for
the two validation-frozen workload endpoints. The latter is a contractual
uncertainty interval; it does not use an oracle profile for selection or
coverage claims. Summaries, certified profiles, metadata, checkpoints, and
English figures are kept under this directory.
