# AI-DC Demand-Response Verification

This repository contains the reproducible source, locked experiment manifests, and IEEE TSG manuscript for the AI data-center demand-response verification study. The implementation separates three evidence chains: submit-time job constraints, independent measured execution traces, and AC network validation.

## Repository layout

`code/src/aicdr/` contains the data, optimization, experiment, audit, and plotting modules. Each directory under `experiments/` owns its runner, protocol README, and final results; stages that require long execution or publication figures additionally retain `results/intermediate/` checkpoints or a `figures/` subdirectory. `configs/default.yaml` is the single frozen configuration entry point. `paper/` contains the LaTeX source, figures, and supporting formulation notes; `reports/` contains review/revision records; `results/` indexes final experiment outputs. The large BurstGPT and MIT SuperCloud releases are kept outside version control; the small public PGLib IEEE-118 case is retained under `data/raw/pglib/` for network reproducibility. All configured paths and provenance requirements are recorded in `data/processed/data_manifest.json`.

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

The full data pipeline requires the raw files named in `configs/default.yaml`. Job-level counterfactual optimization fails closed if any declared job requires more service slots than its submit-time window; the indexed witness is an exact contiguous fixed-rate start-time model with one selected start per submitted job. The preventive AC panel uses six predeclared day/slot snapshots, all 3/6/9% penetrations, and records every native-case-admissible connected finite outage result in a schema-versioned checkpoint before finalization; native-inadmissible connected outages are counted in the metadata and excluded by the pre-registered model-domain rule. Experiment 22 validates the typed job-to-region-to-bus coupling before network settlement, Experiment 23 supplies an independently parameterized declaration-only replay with a distinct predeclared tariff and no future-arrival or execution-telemetry input, and Experiment 24 evaluates all 37 finite non-islanding RTS-24 outages in every frozen-profile cell. The independent trace-meter replay is runnable once the processed workload and Exp2 committed profiles are present:

```text
PYTHONPATH=code/src:vendor .venv/bin/python experiments/exp20_trace_meter_replay/run.py
```

For manuscript compilation, run LaTeX from `paper/` so the experiment figures resolve relative to the source file. The generated PDF is checked for page count, unresolved references, and figure readability before release.

## Data and audit scope

The complete scheduler population contains 75,326 submissions and the
post-event scheduler--DCGM join contains 71,128 positive-energy jobs. The
common 121-day tensor window retains 68,662 jobs for the locked statistical
panels; the remaining jobs are retained by the complete ledger stages. Source
row counts, hashes, joins, temporal coverage, calibration, scaling, and all
split rules are recorded in `data/processed/data_manifest.json` and
`data/processed/data_flow_audit.csv`. The large workload and telemetry inputs
are intentionally excluded from version control; the tracked PGLib case is a
public network benchmark with no private telemetry. Public traces do not expose facility geography, so the
four-region placement and trace-to-power conversion are declared benchmark
scenarios; all 24 region-to-bus permutations plus two predeclared concentration
controls are evaluated in Experiment 11.

The submit-time calibration label join contains 71,141 positive scheduler/DCGM records; the full execution replay contains 71,128 after applying valid measured start/end intervals. The 13-record difference is label-only and cannot enter the counterfactual or locked eligibility sets.

Calibration labels require a matched positive DCGM energy measurement, but that
label join is confined to the conversion fit. Within the matched labels, the
first 40 complete days train the model, the next 16 complete days form the
frozen calibration-validation window, and the remaining 41,154 records are
locked for generalization auditing; no positive-energy filter, immutable-ID
modulo rule, or locked-day outcome selects the Exp19 submission population.

The compiled paper is `paper/main.pdf`. Supporting formulation, source
boundaries, implementation alignment, and the revision matrix are kept beside
the LaTeX source. Experiments 1--28 each own a protocol README and final
results; long-running stages add checkpoints and visualization-producing
stages add figures. The audit module checks the expected output inventory and
numerical certificates. Experiment 21 reports both the
capacity-proportional homogeneous scale and the fixed-nameplate scale; it does
not treat a scaled witness as a second re-optimised LP. Experiment 22 retains
the aggregate indexed coupling certificate and checks typed zero residuals
before dispatch. Experiment 27 then forms the runtime-complete declaration
witness, exports a typed baseline/counterfactual coupling certificate, and
reuses its digest for the common RTS-24 N--1 valuation and settlement replay.
The digest covers both indexed service vectors, their contiguous start blocks,
and the regional profiles; Experiment 26 reconstructs and re-hashes those
arrays before accepting the lineage.
Experiment 28 audits the held-out total-plus-CVaR tail against the
total-budget-only ablation. Experiment 24 independently freezes its profiles and
evaluates all 37 finite RTS-24 DC N--1 outages per cell; native-inadmissible
outages are screened before workload injection and reported by network. The
larger IEEE-118/PGLib case is reserved for the separate cross-network and AC
panels. Experiment 26 is a cached-only end-to-end lineage certificate: it
recomputes indexed coupling residuals, verifies the common witness and
settlement hashes, and records the explicit role separation before the release
audit.

## Reproducibility boundaries

The region labels in the processed traces are feature-stratified scenario labels; they do not claim physical data-center geography. Declaration arrivals and regions are fixed before the execution trace is opened. Event-response panels that use an LP-generated intervention are labelled mechanism-isolation analyses. Decision-time and trace-meter panels score predictions against an independently observed execution tensor and do not attach utility-event labels to that observational target.
