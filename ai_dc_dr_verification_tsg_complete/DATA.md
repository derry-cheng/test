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
 relative clocks, the earliest eligible measured MIT job is shifted to time zero;
 every observed inter-arrival time and duration is preserved without repetition.
The complete positive-energy join contains 71,128 jobs. For the common 121-day
tensor used by Experiments 1--13, 68,664 jobs whose aligned execution starts
before the common horizon are retained; 2,464 later-starting jobs remain in the
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
are declared scenario factors and all 24 region-to-bus permutations are audited.

The exact hashes, row counts, empirical quantiles, inferred scale factors, missing
trace days, valid evaluation days, and held-out DCGM calibration diagnostics are
generated into `data/processed/data_manifest.json` by the data stage.
The accompanying `data/processed/data_flow_audit.csv` provides a row-level
source-to-join-to-split accounting table, including the disjoint calibration
training and held-out partitions and the final valid-slot count.
The calibration split is deterministic by immutable job ID. On the 21,919
held-out jobs with positive predicted energy, the measured-to-predicted energy
ratio has 10th, 50th, and 90th percentiles 0.734154, 0.995724, and 1.278023.
Experiment 9 embeds all three values in the same payment-certificate program;
they form a declared finite empirical uncertainty set, not a tuned continuous
distribution or a replacement for the measured scoring trace.

Experiment 19 uses a separate job-indexed counterfactual. Slurm `timelimit` is
an allocation run-time declaration, not a submission-to-completion deadline.
Finite declarations are converted to 15-minute runtime slots and combined with
a precommitted 96-slot queue allowance; the unlimited sentinel is mapped to a
precommitted 128-slot runtime before the same allowance is added. A fixed 0.001
MW/GPU nameplate provides the per-slot service bound. The observed scheduler
completion interval is retained only for the independent native replay and
never defines the counterfactual deadline or power cap. The resulting witness
contains 12,293,445 job--slot variables and is solved by an exact separable
continuous-knapsack decomposition whenever the declared regional capacity rows
are inactive, with a sparse LP fallback only when a row binds.

Experiment 23 adds a structurally distinct controlled event: after the same
slot-60 submission gate, an independently parameterized exact LP applies a
predeclared event tariff and a 5-MWh service floor without receiving any
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

Experiment 16 computes a canonical SHA-256 digest of the sorted joined
scheduler/DCGM rows, verifies release-before-execution ordering and exact raw-
to-join positive-energy conservation, and stores the source-file hashes. The
raw execution peaks are at most 0.008637 MW per region; after the train-fitted
batch scaling used for the benchmark, the regional peaks are 61.463, 97.836,
102.619, and 37.460 MW. The flexible nameplate of 118 MW is committed before
the validation/test split; Experiment 16 reconciles this predeclared value
against the scaled benchmark envelope and verifies that it covers every
observed region-slot. Locked outcomes do not select the nameplate.

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
arrivals after the pre-event commitment gate (slot 60, one hour before the
event window) before solving and uses the locked execution trace only for
scoring. Experiment 18 fixes the first locked day, first event slot, native-case
connected/finite-AC outage rule, and a generator-bus electrical-role mapping for
each public network before
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
