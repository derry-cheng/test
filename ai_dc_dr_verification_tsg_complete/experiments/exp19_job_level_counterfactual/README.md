# Experiment 19: job-indexed executable counterfactual

This stage loads every valid scheduler submission in the predeclared 132-day
horizon, not only jobs that later receive positive DCGM energy. Each job has a
submit-time release, an allocation-runtime window plus the fixed 96-slot queue
allowance, a requested GPU count, and a training-calibrated energy entitlement.
The central calibration witness is an exact contiguous start-time model: every
job selects one admissible integer start under its GPU nameplate bound, with an
analytically determined final-interval remainder when the central entitlement
is shorter than a full nameplate interval. Experiment 27 freezes these starts
and certifies a separate runtime-complete upper-capacity block, together with a
central-energy realization on the same blocks. Regional capacity rows,
declared-energy equalities, and the deterministic event tariff are checked at
every slot. A binding row is handled by the exact binary model in Experiment
25; this stage never falls back to a preemptive flow or extends a window using
observed completion.

The 71,128 scheduler/DCGM matches are opened only after the 75,326-job
counterfactual is fixed, for independent native replay and coverage. The
measured contiguous runtime/GPU witness remains in Experiment 14 and is not
used to constrain the counterfactual starts.

Run from the repository root with:

```bash
PYTHONPATH=code/src:vendor python experiments/exp19_job_level_counterfactual/run.py
```

The final directory contains the exact solver summary, slot profile, compressed
service vector, and machine-readable metadata used by the manuscript. The
downstream Experiment 21 audit reports both the capacity-proportional
homogeneous scale and the certified scale with the fixed per-GPU nameplate;
the latter is the deployment interpretation and neither scale is presented as
a re-optimised second LP.
