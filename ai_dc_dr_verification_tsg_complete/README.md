# AI Data-Center Demand-Response Verification

This repository is the source-and-artifact package for the study
**“Security-Aware Workload-State Counterfactual Verification and Nodal Net-Value
Settlement for Spatially Coupled AI Data Centers.”** It uses every valid row
from the downloaded BurstGPT traces, the complete MIT SuperCloud
scheduler--DCGM join, its explicitly declared common 121-day tensor-window
subset, and multiple unmodified public transmission benchmarks.

## Reproduction status and command

The checked-in processed arrays, experiment outputs, manuscript, tests, and
audit report come from the locked study run. The two raw files that had been
truncated in the uploaded archive are retained in the verified publication
archive outside the Git working tree and match the sizes and SHA-256 hashes
declared in `data/processed/data_manifest.json`.

```bash
./run_all.sh --stage all --force-preprocess
```

This command performs the full 20-stage run after the public raw inputs have
been restored. The latest independent audit reports 243/243 checks passed;
long-running experiment stages remain resumable through `--resume`.

The unified command writes a timestamped-entry log during execution, continuously
checkpoints long experiments, and produces an auditable run manifest in
`artifacts/run_manifest.json`, including the final status and per-stage timings.
The reproducibility-critical results of the latest raw-data, provenance, audit,
and regression checks are summarized in `logs/current_validation.log` and
`logs/final_tests.log`; stage-specific records are retained under
`artifacts/stage_runs/`.
Individual stages are also available through
`--stage data|exp1|exp2|exp3|exp4|exp5|exp6|exp7|exp8|exp9|exp10|exp11|exp12|exp13|exp14|exp15|exp16|exp17|exp18|audit`.
To preserve the completed all-stage evidence, a standalone stage writes its
own latest record under `artifacts/stage_runs/` and never overwrites
`artifacts/run_manifest.json`.

The deterministic regression suite is run with
`PYTHONPATH=src:vendor python tests/run_tests.py`; the final checked workspace
passes all 29 tests. The latest locked audit reports 243/243 checks passed. The
suite covers workload-flow feasibility, SCED balance
and line limits, N--1 enumeration, endpoint certificates, provenance joins,
budget balance, and stage-manifest isolation.

## Study design

| Paper claim | Identification strategy | Experiment |
|---|---|---|
| Conventional DR baselines create an incentive to inflate event-window consumption | Ten-reference-day expected-profit equilibrium over the complete price × call-probability grid | `exp1_manipulation` |
| Statistical baselines can credit load shifting rather than physical system reduction | Locked 16-day validation / 54-day test evaluation against trace-anchored execution | `exp2_baseline_verification` |
| Workload telemetry improves verification beyond an equally informed statistical learner | Complete-ledger learner, independent single projection, total-plus-tail-risk convex ensemble, and a final exact pointwise risk-envelope LP | `exp2_baseline_verification` |
| Gross MW payments can diverge from grid value in a congested network | Full 12-estimator-plus-trace-reference × 5-settlement factorial; 10-segment market payments are scored by an independent 80-segment SCED evaluator, with paired day-level decomposition of signed netting, locational pricing, and exact value | `exp3_nodal_settlement` |
| Spatial migration can turn a local reduction into a remote rebound | Ex-post case selected by a pre-declared gross-minus-net offset rule | `exp4_case_study` |
| Value alignment generalizes across network size and loading without constructed congestion | IEEE RTS 24, IEEE 39, PGLib IEEE 118, and IEEE 300 × native-load multipliers 0.90/0.98/1.02 × five settlement mechanisms, retaining every public thermal rating | `exp5_network_robustness` |
| Deadline and capacity constraints matter when active | Complete 5-capacity × 3-deadline × 54-day stress panel | `exp6_physical_stress` |
| Multi-site value can be allocated exactly and without a budget residual | Primary four-site allocation plus complete 256-coalition enumeration for eight trace-derived contractual portfolios on every locked day and event interval | `exp7_value_allocation` |
| Base-case value remains valid when a line outage changes preventive redispatch | All 37 finite non-islanding single-line outages in IEEE RTS-24 are enforced simultaneously, with a separate 40-segment evaluator | `exp8_n1_security` |
| The verifier controls security-aware payment, not only credited MWh | Two lexicographically ordered daily LPs choose over six independent first-stage feasible projections plus the matched feasible-quantile comparator, embed every preventive N-1 dispatch row for held-out 10th/50th/90th-percentile power-conversion scenarios, and certify payment no larger than the same-scenario validation-selected single-projection cap; the quantile profile is retained as an external transfer comparator | `exp9_payment_certificate` |
| Findings transfer beyond the lossless DC approximation | Nonlinear AC OPF on four public networks; complete corrective IEEE-9/14 outage panels; and a complete IEEE-9 shared-active-plan preventive panel at 3%, 6%, and 9% penetration | `exp10_ac_validation` |
| Spatial placement and trace-to-power scaling do not determine the result | Complete \(4!\) regional-trace-to-bus assignment set × three predeclared peak penetrations × all locked days, evaluated with independent settlement and truth objectives | `exp11_spatial_scale_robustness` |
| Cross-day feasibility and delayed recovery do not rely on a zero-arrival buffer | A 1,216-slot continuous real-arrival horizon, two-stage lexicographic event-window embedding, endogenous recovery, complete-cycle nodal remuneration, and an individually rational budget-balanced bilateral contract | `exp12_rolling_market_validation` |
| Public execution replay is separated from causal counterfactual identification | All 54 locked days are replayed from immutable MIT scheduler/DCGM execution intervals; the trace-constrained batch flow is observational only | `exp13_real_trace_replay` |
| Aggregate divisible flow is checked against exact job-level feasibility | One global sparse release/deadline LP retains all 71,128 positive-energy joined jobs, reconstructs the measured profile, and reports machine-precision job and slot residuals | `exp14_job_level_fidelity` |
| Telemetry conversion uncertainty is audited beyond three finite quantiles | The locked payment profile is independently evaluated at held-out q01/q99 endpoints under all 37 non-islanding outages; convex value geometry gives a worst-case interval cost bound | `exp15_interval_certificate` |
| The job-level witness is bound to immutable source records and the study capacity covers the measured regional envelope | Canonical SHA-256 digest, one-to-one scheduler/DCGM join, raw-to-join energy conservation, temporal-order checks, and complete observed per-region capacity reconciliation | `exp16_ledger_capacity_provenance` |
| A deployment-time verifier cannot use future arrivals that are unavailable at the decision gate | The same exact workload LP is evaluated with all post-gate arrivals removed and compared with the complete-ledger information upper bound on every locked day | `exp17_decision_time_information` |
| AC network transfer is auditable without overclaiming a preventive AC certificate | Every declared native-case admissible outage is solved as an AC corrective diagnostic on RTS-24/30/39/118 at three validation-only penetrations; voltage and loading deviations are reported explicitly | `exp18_preventive_ac_network_panel` |

## Data integrity and identification scope

Raw-file paths remain under `data/raw`; expected hashes, row counts, preprocessing rules, held-out
DCGM power-calibration performance, held-out per-job energy-ratio quantiles,
temporal coverage, and scaling constants are recorded in
`data/processed/data_manifest.json`. The immutable scheduler--DCGM join contains
71,128 positive-energy jobs. The common 121-day tensor window retains 68,664 of
them for Experiments 1--13; the remaining 2,464 jobs remain in the full-horizon
job-level witness used by Experiments 14 and 16. This distinction is recorded as
separate rows in `data/processed/data_flow_audit.csv` and as separate manifest
fields. MIT scheduler submission timestamps
define queue arrivals, while independently measured DCGM execution defines the
counterfactual scoring truth. BurstGPT request service remains trace-observed. The
joint grid-coupled setting is a documented trace-driven benchmark: public traces do
not expose real data-center geography, so four-region placement and hyperscale
conversion are experimental scenario parameters rather than field measurements.
The 118-MW flexible nameplate is committed before the validation/test split.
Experiment 16 reconciles it post hoc with the maximum observed regional
MIT/DCGM batch envelope and stores the exact quantiles, peak values, source
hashes, and canonical joined-ledger digest; locked outcomes do not select the
nameplate.

## Repository structure

Each of the eighteen experiments has its own `run.py`, `results/intermediate`, `results/final`, and
`figures` directory. Figures are emitted as journal-quality English PNG and vector
PDF files; the manuscript's framework and method-detail diagrams are maintained
as editable Draw.io sources plus SVG/PDF exports. `audit/result_audit.json` independently checks raw-file hashes, complete
panels, primal workload constraints, SCED balance/line limits, matched information
sets, exact dependence-aware tests, native branch ratings, Shapley budget balance,
and the expected output inventory.

The compiled paper and locked result artifacts are `manuscript/main.pdf`, with source in
`manuscript/main.tex`. See also `manuscript/paper_outline_zh.md`, `manuscript/model_formulation.md`,
`manuscript/formula_source_matrix.md`, `manuscript/theoretical_results.md`, and
`manuscript/implementation_alignment.md` for the full equation/source/paper-to-code
mapping and `DATA.md` for data provenance and limitations. The source directory
contains only the final PDF and reproducible manuscript sources; the PDF was
rebuilt from `manuscript/main.tex` with BibTeX and `latexmk` after the final
sample-definition and cross-reference corrections.
