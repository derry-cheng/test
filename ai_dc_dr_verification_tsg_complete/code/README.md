# Executable code boundary

The canonical implementation is the `src/aicdr/` package. It contains data
loading, sparse workload optimization, network valuation, experiment runners,
typed coupling checks, and the release audit. The `tests/` directory contains
deterministic regression tests; `configs/` contains the frozen protocol. This
directory intentionally contains documentation only, so generated solver
outputs remain isolated under `experiments/` and release reports remain under
`reports/`.

The end-to-end evidence-chain check is implemented in
`src/aicdr/end_to_end_certificate.py` and is exposed as pipeline stage
`exp26`. It consumes locked upstream artifacts, recomputes residuals, and
does not refit or select parameters.
