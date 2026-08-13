# Exact Job-Level Fidelity

This experiment solves one sparse linear feasibility problem over every positive-energy scheduler/DCGM job retained by the immutable join. Each job receives exactly its measured energy between its scheduler release and observed completion deadline, while the reconstructed regional 15-minute profile is constrained to the measured aggregate target and the declared facility capacity.

The run produces the full job-flow solution, slot-level residuals, fidelity summary, metadata, checkpoints, and English figures. It uses no sampling, synthetic jobs, imputed deadlines, or heuristic scheduling.
