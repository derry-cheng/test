# Final results index

Each experiment owns its immutable output directory at
`experiments/exp*/results/final/`. Keeping results beside the runner preserves
the data lineage and prevents figures from being detached from the exact
configuration used to produce them. The top-level `results/` directory is an
index only; generated checkpoints and raw releases are not copied here.

The revised closure stages are:

- `exp19_job_level_counterfactual`: 12,293,445-variable indexed witness.
- `exp22_coupled_job_network_certificate`: typed job/aggregation/mapping
  certificate before settlement.
- `exp23_independent_event_replay`: independently generated controlled-event
  response replay.
- `exp24_all_outage_security_panel`: all 37 finite RTS-24 outages in every
  frozen-profile cell.
