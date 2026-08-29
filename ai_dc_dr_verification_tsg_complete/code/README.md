# Executable code boundary

The maintained implementation is under `src/aicdr/`. `run_all.py` is the
single orchestration entry point, while each `experiments/exp*/run.py` is a
standalone stage wrapper. Tests live under `tests/`; no generated result or
raw-data file belongs in this directory.

The job-indexed stage uses a certified exact continuous-knapsack decomposition
when regional capacity rows are inactive and switches to a sparse HiGHS LP only
when those rows bind. Worker counts are configured explicitly and validated to
remain at or below 20.
