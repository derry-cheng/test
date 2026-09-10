# Executable code boundary

The maintained implementation is under `code/src/aicdr/`. `run_all.py` is the
single orchestration entry point, while each `experiments/exp*/run.py` is a
standalone stage wrapper. The manuscript source is under `paper/`. Tests live under `tests/`; no generated result or
raw-data file belongs in this directory.

The job-indexed Exp19 stage uses an exact contiguous fixed-rate start-time
witness: one binary start is selected per submitted job, with an exact
terminal-slot remainder for the calibrated central entitlement. Exp27 freezes
the same declaration index and certifies a full declared-runtime GPU-nameplate
block plus the central-energy profile on identical starts. Typed energy,
contiguity, GPU-capacity, site-capacity, and region-to-bus residual checks
precede settlement. The binding-capacity stress panel uses the same sparse
binary start-time MILP; the coupled network certificate is solved by the global
sparse HiGHS LP with no heuristic post-processing. Worker counts are configured
explicitly and validated to remain at or below 20.
