# Data Provenance and Processing

## Inputs

1. **[BurstGPT](https://github.com/HPMLL/BurstGPT)**: two no-failure request traces. All valid rows are processed; request
   timestamps and token counts define 15-minute inference arrivals. Conversation
   requests are treated as non-deferrable real-time inference and other API requests
   as short-deadline elastic inference.
2. **[MIT SuperCloud scheduler + DCGM](https://dcc.mit.edu/data/)**: scheduler jobs are one-to-one joined to DCGM
   measurements by immutable job ID. Measured joules are allocated to 15-minute
   intervals in exact proportion to temporal overlap. No average-power proxy replaces
   a job when measured energy is available. Because the two releases use independent
 relative clocks, a precommitted scheduler-clock origin is fixed before any execution
 join; execution timestamps do not define the causal arrival origin or membership.
The complete positive-energy join contains 71,128 jobs. For the common 121-day
tensor used by Experiments 1--13, 68,662 jobs with valid intervals
in the common horizon are retained; 2,466 jobs outside that horizon remain in the
full-horizon job-level witness of Experiments 14 and 16. The two counts are not
alternative versions of the same sample and are reported separately in the
manifest and data-flow audit.
3. **Public transmission benchmarks**: IEEE RTS 24-bus, IEEE 39-bus, PGLib
   IEEE 118-bus, and IEEE 300-bus cases retain their buses, online generators,
   branches, published thermal ratings, and generation costs. No branch rating is
   reduced to manufacture congestion.

## Transformations

The public traces provide temporal demand rather than a common hyperscale facility
measurement. BurstGPT token volume and measured GPU energy are therefore separately
scaled so their empirical 99th-percentile aggregate powers equal the declared
scenario targets in `configs/default.yaml`. The original observations, ordering,
burstiness, job durations, energy, and class mix are preserved. Four regions are
assigned by a deterministic feature-stratified round-robin rule over workload
class, GPU count, runtime, submission time, and energy; identifiers only break
exact ties. Neither dataset provides usable multi-site geography, so the labels
are declared scenario factors and all 24 region-to-bus permutations plus two
predeclared concentration controls are audited.

The exact hashes, row counts, empirical quantiles, inferred scale factors, missing
trace days, valid evaluation days, and calibration-validation/locked DCGM diagnostics are
generated into `data/processed/data_manifest.json` by the data stage.
The accompanying `data/processed/data_flow_audit.csv` provides a row-level
source-to-join-to-split accounting table, including the disjoint calibration
training, calibration-validation, and locked partitions and the final valid-slot count.
The calibration split is chronological: scheduler/DCGM observations whose
submit and execution times fall in the first 40 complete days train the
conversion model; the next 16 complete days are calibration-validation; and
the remaining matched records are locked evaluation observations. The
calibration-validation measured-to-predicted energy ratio has 1st, 10th, 50th,
90th, and 99th percentiles 0.582671, 0.687118, 0.969849, 1.349061, and
5.320913. Experiment 9 embeds these five values in the same payment-certificate
program; they form a declared finite empirical uncertainty set, not a tuned
continuous distribution or a replacement for the measured scoring trace. The
locked partition is a generalization audit and is never used for scaling or
selection. A matched positive DCGM measurement supplies the calibration label,
whereas chronological submit/end timestamps determine split membership; no
such label filter defines the full Exp19 submission population.

Experiment 19 uses a separate job-indexed counterfactual. Slurm `timelimit` is
an allocation run-time declaration, not a submission-to-completion deadline.
Finite declarations are converted to 15-minute runtime slots and combined with
a precommitted 96-slot queue allowance; the unlimited sentinel is mapped to a
precommitted 128-slot runtime before the same allowance is added. A fixed 0.001
MW/GPU nameplate provides the per-slot service bound. The observed scheduler
completion interval is retained only for the independent native replay and
never defines the counterfactual deadline or power cap. The indexed model
enumerates 13,198,247 admissible job--slot starts. Experiment 19 uses the
calibrated central entitlement with an analytically determined remainder in its
final occupied interval; Experiment 27 freezes those starts and certifies the
runtime-complete GPU-nameplate upper block and the central-energy realization
on the same blocks. Experiment 25 solves the same declaration-bound start-time
model with a binding regional capacity row; no arbitrary pausing or post-event
completion time is substituted for the executable witness.


The training-only submit-time energy-label join contains 71,141 positive scheduler/DCGM
records because it requires valid scheduler submit/end, runtime, and GPU fields but
not a valid measured execution interval; the full execution replay applies that
additional interval filter and therefore contains 71,128 jobs. The 13-record
label-only difference cannot enter any counterfactual or locked eligibility set.

Experiment 23 adds a structurally distinct controlled event: after the same
slot-62 submission gate, an independently parameterized exact LP applies a
predeclared event tariff and a 3-MWh service floor without receiving any
verifier target, risk envelope, or locked outcome. It is a mechanism-isolation
certificate, not a field treatment estimate.

Experiment 22 reconstructs the regional network profile directly from the
stored Experiment 19 job--slot service vector. A typed certificate checks job
energy, job-to-region aggregation, region-to-bus mapping, GPU nameplate, and
regional-capacity residuals before solving the secure network model. The
reported network value is an arithmetic-mean event-window replay on the
predeclared public PYPOWER IEEE RTS-24 case (four fixed generator-bus
locations) and is not based on a second aggregate optimization. Experiment 24
then freezes the two locked profiles and evaluates all 37 finite non-islanding
RTS-24 outages in all 864 day/slot/profile cells. The public PGLib IEEE-118
case supplies the independent cross-network/AC benchmark.

Experiment 27 uses the same immutable submission digest but defines a separate
declaration-only runtime entitlement from each requested GPU count, nameplate,
and allocation runtime. It exports a typed baseline/counterfactual service
certificate before the common RTS-24 settlement replay; no measured execution
field or fitted aggregate entitlement enters that witness. Experiment 28 audits
the held-out total-plus-CVaR tail against the total-budget-only ablation with a
paired block bootstrap.

Experiment 16 computes a canonical SHA-256 digest of the sorted joined
scheduler/DCGM rows, verifies release-before-execution ordering and exact raw-
to-join positive-energy conservation, and stores the source-file hashes. The
raw execution peaks are at most 0.008637 MW per region; after the train-fitted
batch scaling used for the benchmark, the regional peaks are 43.808, 62.537,
103.197, and 132.571 MW. The flexible nameplate of 118 MW is committed before
the validation/test split. Experiment 16 reports the raw execution envelope and
the scaled benchmark excess explicitly; its capacity-safe conversion factor is
the separate planning diagnostic used when a physical 118-MW bound is required.
The payment certificate applies conversion uncertainty only to the flexible
component after a fixed/flexible decomposition, so its raw $q_{99}$ endpoint
is activation-eligible in the declared payment network model even when the
independent capacity diagnostic clips that factor. Locked outcomes do not
select the nameplate.

The locked-day selector requires both the declared 40-day historical
information set and the complete 512-slot future deadline window. The final 16
validation and 54 test days are consecutive within that support. Experiment 12
reads every real arrival in a 1,216-slot window around each locked day; it does
not append zero arrivals, repeat the trace, or wrap the end of the dataset.

## Boundaries of inference

This is a trace-driven counterfactual systems experiment. It does not claim that the
three public datasets came from the same operator, nor that the IEEE benchmark is an
observed utility territory. Conclusions concern mechanism validity under measured
workload shapes and an auditable network benchmark; external validity to a particular
operator requires confidential co-located telemetry.

The deployment information boundary is explicit: Experiment 17 removes all
arrivals after the pre-event commitment gate (slot 62, 30 minutes before the
event window) before solving and uses the locked execution trace only for
scoring. Experiment 18 fixes three locked days crossed with the first and last
event slots (six snapshots), the native-case connected/finite-AC outage rule,
and a generator-bus electrical-role mapping for each public network before
evaluating RTS-24, IEEE-30, IEEE-39, and IEEE-118 AC contingencies at the same
0.90 native-load multiplier used by the primary preventive DC panel. It freezes
the intact AC-OPF non-reference active plan and enforces apparent-power and
voltage limits for every contingency; the reference generator and reactive
variables are the only recourse.

# Data construction and independent counterfactual protocol

The benchmark uses every valid BurstGPT row and every MIT job that has both a
scheduler record and positive DCGM energy. For MIT jobs, total measured energy is
placed into the controllable queue at `time_submit`; the independent no-event truth
allocates that same measured energy over `[time_start, time_end]`. Thus, the verifier
does not generate the trajectory used to score itself.

BurstGPT has no facility-power or geographic channel. Token energy is scaled to the
declared hyperscale scenario, and immutable row identifiers determine four balanced
experimental regions. MIT, BurstGPT, and the power-system benchmarks are not claimed
to be co-located operator telemetry. The study is therefore a full-data,
trace-driven joint benchmark rather than a field trial.
