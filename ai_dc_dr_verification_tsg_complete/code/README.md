# Executable code boundary

The maintained implementation is under `src/aicdr/`. `run_all.py` is the
single orchestration entry point, while each `experiments/exp*/run.py` is a
standalone stage wrapper. Tests live under `tests/`; no generated result or
raw-data file belongs in this directory.

The job-indexed stage uses an exact separable continuous-knapsack decomposition
followed by typed capacity, energy, and region-to-bus residual checks; the
coupled network certificate is solved by the global sparse HiGHS LP with no
heuristic post-processing. Worker counts are configured explicitly and
validated to remain at or below 20.
