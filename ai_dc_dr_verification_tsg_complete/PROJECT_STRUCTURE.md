# Project structure

This repository separates implementation, experiments, artifacts, and the manuscript so that a locked result can be traced without mixing source code and generated files.

- `code/src/aicdr/`: reusable data, optimization, certificate, replay, and audit modules.
- `code/scripts/`: small reproducibility utilities, including the hash-checked public-input downloader.
- `configs/`: frozen study configuration and predeclared capacity commitments.
- `data/processed/`: compact, hashed intermediate arrays and manifests derived from the source data.
- `data/raw/`: source-data notices/licenses and optional source files restored for a full preprocessing run.
- `experiments/exp*/`: one directory per experiment, with `run.py`, `README.md`, `results/intermediate/`, `results/final/`, and `figures/`. Experiment 29 recomputes the archived target bridge; Experiment 31 checks risk composition and the exact-convex active-tail fit; Experiment 32 contains matched-gate and coupled runtime-capacity panels.
- `results/`: cross-experiment exports that are not owned by one experiment.
- `audit/`: machine-readable and human-readable completeness reports.
- `paper/`: LaTeX source, bibliography, figures, and the compiled manuscript.
- `reports/review/`: claim-by-claim TSG review resolution.
- `reports/reproducibility/`: targeted rerun manifests and release provenance.
- `reports/`: revision log and reproducibility notes.
- `artifacts/`: stage manifests and execution metadata.
- `tests/`: deterministic certificate and invariant tests.

Generated Python caches and temporary atomic-writer files are excluded from version control. The compact checkout remains below the project size limit; the large raw CSVs are intentionally represented by their source notices and hashes in `data/processed/data_manifest.json`.

The October 14 revision retains superseded review reports under `reports/review/archive/`, with an explicit historical label. New code and outputs do not rewrite the original frozen statistical profiles.
