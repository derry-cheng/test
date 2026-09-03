# AI-DC Demand-Response Verification

This repository contains the reproducible source, locked experiment manifests, and IEEE TSG manuscript for the AI data-center demand-response verification study. The implementation separates three evidence chains: submit-time job constraints, independent measured execution traces, and AC network validation.

## Repository layout

`code/src/aicdr/` contains the data, optimization, experiment, audit, and plotting modules. Each directory under `experiments/` owns its runner, README, figures, and final results. `configs/default.yaml` is the single frozen configuration entry point. `paper/` contains the LaTeX source, figures, and supporting formulation notes; `reports/` contains review/revision records; `results/` indexes final experiment outputs. The large BurstGPT and MIT SuperCloud releases are kept outside version control; the small public PGLib IEEE-118 case is retained under `data/raw/pglib/` for network reproducibility. All configured paths and provenance requirements are recorded in `data/processed/data_manifest.json`.

## Reproduction

From this directory, create an environment and install the minimum runtime
dependencies:

```text
python -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=code/src:vendor .venv/bin/python run_all.py --config configs/default.yaml --stage audit
```

After restoring the raw files named in `configs/default.yaml`, the complete
entry point is:

```text
./run_all.sh --stage all --force-preprocess
```

Every long experiment writes an intermediate checkpoint and can be resumed;
standalone stages write under `artifacts/stage_runs/` and do not overwrite the
canonical all-stage manifest. The deterministic regression suite is run with
`PYTHONPATH=code/src:vendor python tests/run_tests.py`.
The entry points clamp BLAS/HiGHS numerical backends to one thread per worker;
configured worker pools are checked against the 20-core ceiling.

The full data pipeline requires the raw files named in `configs/default.yaml`. Job-level counterfactual optimization fails closed if any declared job requires more service slots than its submit-time window; the indexed witness is an exact contiguous fixed-rate start-time model with one selected start per submitted job. The preventive AC panel uses six predeclared day/slot snapshots, all 3/6/9% penetrations, and records every native-case-admissible connected finite outage result in a schema-versioned checkpoint before finalization; native-inadmissible connected outages are counted in the metadata and excluded by the pre-registered model-domain rule. Experiment 22 validates the typed job-to-region-to-bus coupling before network settlement, Experiment 23 supplies an independently parameterized controlled-event replay with a nonzero predeclared service floor, and Experiment 24 evaluates all 37 finite non-islanding RTS-24 outages in every frozen-profile cell. The independent trace-meter replay is runnable once the processed workload and Exp2 committed profiles are present:

```text
PYTHONPATH=code/src:vendor .venv/bin/python experiments/exp20_trace_meter_replay/run.py
```

For manuscript compilation, run LaTeX from `paper/` so the experiment figures resolve relative to the source file. The generated PDF is checked for page count, unresolved references, and figure readability before release.

## Data and audit scope

The complete scheduler population contains 75,326 submissions and the
post-event scheduler--DCGM join contains 71,128 positive-energy jobs. The
common 121-day tensor window retains 68,664 jobs for the locked statistical
panels; the remaining jobs are retained by the complete ledger stages. Source
row counts, hashes, joins, temporal coverage, calibration, scaling, and all
split rules are recorded in `data/processed/data_manifest.json` and
`data/processed/data_flow_audit.csv`. The large workload and telemetry inputs
are intentionally excluded from version control; the tracked PGLib case is a
public network benchmark rather than private telemetry. Public traces do not expose facility geography, so the
four-region placement and trace-to-power conversion are declared benchmark
scenarios; all 24 region-to-bus permutations plus two predeclared concentration
controls are evaluated in Experiment 11.

Calibration labels require a matched positive DCGM energy measurement, but that
label join is confined to the conversion fit. Within the matched labels, the
first 40 complete days train the model, the next 16 complete days form the
frozen calibration-validation window, and the remaining 41,154 records are
locked for generalization auditing; no positive-energy filter, immutable-ID
modulo rule, or locked-day outcome selects the Exp19 submission population.

The compiled paper is `paper/main.pdf`. Supporting formulation, source
boundaries, implementation alignment, and the revision matrix are kept beside
the LaTeX source. Experiments 1--25 each own a README, final results,
checkpoint, and figures, while the audit module checks the expected output
inventory and the numerical certificates. Experiment 21 reports both the
capacity-proportional homogeneous scale and the fixed-nameplate scale; it does
not pretend that a scaled witness is a second re-optimised LP. Experiment 22
reconstructs the network profile from the exact Experiment 19 job--slot
witness, checks typed zero residuals before dispatch, and reports a
deterministic event-window-mean N--1 replay on the explicitly pinned public
IEEE RTS-24 case. Experiment 24 then freezes the profiles and covers all finite
non-islanding outages without screening or post-solution reoptimization. The
larger IEEE-118/PGLib case is reserved for the separate cross-network and AC
panels.

## Reproducibility boundaries

The region labels in the processed traces are feature-stratified scenario labels; they do not claim physical data-center geography. Event-response panels that use an LP-generated intervention are labelled mechanism-isolation analyses. Decision-time and trace-meter panels score predictions against an independently observed execution tensor and do not attach utility-event labels to that observational target.
