# Experiment 20 — Independent Trace-Meter Replay

This panel scores the locked Experiment-2 profiles against the measured
MIT DCGM execution tensor temporalized on immutable job intervals. It is an
observational replay: the public releases contain no utility event label, so
the panel does not estimate a causal demand-response intervention or reuse an
event-response LP as measured truth. Three-day moving-block intervals preserve
the temporal dependence of the 54 locked days.

Run with `python run.py` from the project root after the Experiment-2 profile
archive and processed workload have been materialized. The summary, daily
panel, metadata, and publication-size figure are written under `results/final`
and `figures`.
