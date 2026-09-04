# Final results index

Each experiment owns its immutable output directory at
`experiments/exp*/results/final/`. Keeping results beside the runner preserves
the data lineage and prevents figures from being detached from the exact
configuration used to produce them. The top-level `results/` directory is an
index only; generated checkpoints and raw releases are not copied here.

The revised closure stages are:

- `exp19_job_level_counterfactual`: exact contiguous indexed witness selected
  from 13,198,247 admissible starts over 75,326 submissions.
- `exp20_trace_meter_replay`: independent 54-day observed-meter replay.
- `exp21_scale_consistency`: fixed-nameplate and capacity-proportional
  homogeneous transforms of the same indexed witness.
- `exp22_coupled_job_network_certificate`: typed job/aggregation/mapping
  certificate before settlement, including both scale replays.
- `exp23_independent_event_replay`: independently generated controlled-event
  response replay.
- `exp24_all_outage_security_panel`: all 37 finite RTS-24 outages in every
  frozen-profile cell.
- `exp25_exante_job_validation`: independent submit-time declaration and
  binding-capacity stress certificate for the complete submitted population.
- `exp26_end_to_end_certificate`: cached-only recomputation of indexed
  coupling residuals, source hashes, risk/payment role separation, and the
  complete outage replay.
