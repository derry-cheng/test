# Interval-Robust Payment Certificate

This experiment independently audits the locked payment profile with the
40-segment N-1 dispatch model at both held-out energy-conversion interval
endpoints (q01 and q99) against the validation-selected single feasible
projection. The feasible-quantile profile remains an external transfer
comparator. Convexity of each optimal dispatch value makes the two endpoints an
exact worst-case cost audit over the closed interval. The finite q10/q50/q90
payment guarantee remains the pointwise contract; the endpoint result is
reported as a worst-case interval bound, not as an unproved pointwise ordering
of two value functions at every interior factor.

The run writes `interval_endpoint_certificates.csv` for the two independent
40-segment endpoint replays and `payment_value_interval_certificates.csv` for
the two validation-frozen workload endpoints. The latter is a contractual
uncertainty interval; it does not use an oracle profile for selection or
coverage claims. Summaries, certified profiles, metadata, checkpoints, and
English figures are kept under this directory.
