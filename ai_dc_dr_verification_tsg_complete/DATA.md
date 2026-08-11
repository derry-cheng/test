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
assigned by a deterministic multiplicative hash of immutable row/job IDs because
neither dataset provides usable multi-site geography.

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

Experiment 16 computes a canonical SHA-256 digest of the sorted joined
scheduler/DCGM rows, verifies release-before-execution ordering and exact raw-
to-join positive-energy conservation, and stores the source-file hashes. The
complete observed regional batch envelope has peaks 70.637, 112.439, 117.936,
and 43.051 MW. The flexible nameplate of 118 MW is committed before the
validation/test split; Experiment 16 reconciles this predeclared value against
the observed envelope and verifies that it covers every observed region-slot.
Locked outcomes do not select the nameplate.

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
arrivals after the first declared event slot before solving and uses the locked
execution trace only for scoring. Experiment 18 fixes the first locked day,
first event slot, native-case connected/finite-AC outage rule, and
validation-only power scale before evaluating RTS-24, IEEE-30, IEEE-39, and
IEEE-118 AC contingencies. It reports corrective loading, voltage, and active
recourse diagnostics; it is not a preventive AC security-constrained OPF
certificate.
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
