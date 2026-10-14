# TSG revision record — 14 October 2026

Baseline: `f98b6bee487df1f9a650b4a9d6787659c1db6473` in `derry-cheng/test`. This record uses the October 14 review numbering. The earlier numbering is archived under `archive/tsg_resolution_pre_oct14.md`.

## C1 — Risk-to-execution composition

Implemented residual-to-total-risk, top-m-tail and RMSE bounds, direct postexecution acceptance, a separate payable-credit intersection certificate, and a binary-start model jointly enforcing unchanged runtime, fixed power, all-slot capacity, total/tail scenario risk and exact lattice MSE. An independent exhaustive 80-start fixture agrees with the optimizer. Experiment 31 shows that the archived 75,326-job bridge does not satisfy the transported budgets; the result is retained. Experiment 32 demonstrates the integrated constraints on 64-job cohorts, including a minimum-MSE phase-I optimization when exact matching is infeasible. The mathematical interface is repaired, but a congested full-population execution claim remains unverified. A payment cap is not relabeled as execution accuracy.

## C2 — Incremental tail-risk value

Replaced the conservative triangle accuracy neighborhood with the exact convex MSE row and separated hard constraints from objective penalties. The original hard rows are independently shown inactive by removing them with the same objective. The new validation-defined midpoint tail constraint binds with positive dual value. Against the matched exact-MSE total-only control, retrospective locked false-credit mean/tail improve from 0.564553/1.943670 to 0.540289/1.860547 MWh; nRMSE/F1 improve from 0.948715/0.505982 to 0.945146/0.511344. The paired tail interval [-0.18180, 0.00608] includes zero. Improvement over every archived comparator is not supported. The fit is explicitly retrospective, with validation weights and hashes frozen before its new scoring pass; it is not new external validation. A days 115–120 extension would violate the unchanged 512-slot full-future-support eligibility rule and was not mislabeled as a matched holdout.

## C3 — Matched event-gate evidence

Added 910 rows covering 13 methods on the same 70 validation/locked days, slot 62 ledger, participants, modeled reference/response, service floor and scoring rule. No future arrivals or current execution telemetry enter fitting. Shared information arrays are independently rehashed. Joint, total-only, tail-only and unconstrained fits coincide with the selected single projection: this protocol does not show incremental risk-module advantage. The 3-MWh modeled payable floor is a construction property, not measured reliability. Real causal utility-event and closed-meter deployment evidence still require suitable data; no observational trace is presented as an intervention.

## C4 — Runtime-consistent coupled capacity

Added 24 finite all-slot coupled cases with the same 64-job cohorts,32 pending and 32 running jobs, unchanged power/runtime/deadlines and predeclared capacity levels. All 24 solve to zero gap, spanning 19–99% achieved peak utilization. The joint exact-MSE/risk diagnostic retains all 12 cells: four of six exact-match contracts are feasible; two are proven infeasible, with six minimum-MSE phase-I solves establishing the attainable errors. The scientific inference remains finite-cohort feasibility, not full-scale congested performance. An actual backend bug in combined LP/MILP execution was repaired using explicit one-thread initialization and an unchanged-model retry; failed infrastructure attempts remain under intermediate records, and the final combined run is verified.

## C5 — AC denominator and numerical outcomes

Removed every method-dependent outcome exclusion. The primary domain contains all 10,332 topology-connected cells for both methods:9,642 certified,690 numerical unknowns, zero converged limit violations. Unknown is not physical infeasibility or certified feasibility. The repair retained 9,576 checksum-bound original certificates and freshly solved 756 cells, including matched controls. IEEE30 outages 29/31 now retain all 36 proposed and 36 reference cells; reference has 30 certified and 6 unknown, rather than deleting all 36. Native screening is only a subgroup. A resumed finalization verifies the same complete domain; Exp 9 provenance refresh leaves all 34 input arrays and their three NPZ byte hashes unchanged. This protocol issue is fixed; blanket all-cell AC certification is not claimed.

## M1 — Format

Restored standard IEEE reference/table typography, a 182-word abstract,32 cited references and 10 compiled pages. Page count is achieved through restructuring and prose reduction, not the previous 6.3pt bibliography. All labels/references pass the release audit.

## M2 — Figures

Rebuilt both diagrams as editable draw.io/SVG plus vector PDF, with final-size 8.5pt body labels and no identified text/arrow collisions. Main result charts now display the exact-MSE risk comparison and coupled capacity evidence at readable size. The settlement table is unscaled 8pt. Final PDF pages are rendered and visually checked.

## M3 — Organization

Separated model definitions, proposed risk/execution/settlement methods, experimental settings and contribution-led results. Archived superseded design notes with explicit current-source pointers. Experiment identifiers remain reproducibility references rather than the narrative structure.

## M4 — Units, aggregation and result versions

Corrected the time-step factor and system-before-floor settlement aggregation to match implementation; signed value and positive cash presentation stay separate. Added saved-ledger unit/netting regressions. Unified method aliases and source-derived rounding; rebuilt Exp 28 from the actual unchanged daily source because its previous checksum was stale. The original Exp 9 manifest discrepancy was provenance wording only; legitimate resume revalidation refreshed its record while preserving all physical profile bytes.

## M5 — Originality and references

Reworked the closest-work comparison around workload commitment, risk/execution compatibility and signed network value, rather than presenting LP/CVaR/Shapley primitives as inventions. Corrected the Extra Trees citation and first-use expansions. The integrated formulation and independently tested admission conditions strengthen the technical contribution; top-journal acceptance or universal superiority cannot be certified by an engineering audit.

## Verification and publication status

The full deterministic suite passes 96 tests; the release audit passes 448/448 checks. The original smoke suite is also retained. The targeted command/provenance manifest is `reports/reproducibility/oct14_revision_manifest.json`; historical all-stage manifests are not rewritten as a fresh full rerun. The compact working project is approximately 127 MB and Git history 299 MB, below 4 GB. Maximum concurrent compute allocation was 20 CPU cores; AC reconstruction used at most 8 one-thread workers.

The current local revision is verified. This report records local scientific and software checks; remote commit and CI verification are reported separately after publication. C1–C4 now have explicit implementations and targeted evidence, but the remaining scientific boundaries above prevent declaring all claims fully established or the paper guaranteed TSG-ready.
