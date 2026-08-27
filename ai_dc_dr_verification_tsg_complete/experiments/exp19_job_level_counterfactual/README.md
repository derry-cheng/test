# Experiment 19: job-indexed executable counterfactual

This stage solves a global sparse linear program with one service variable for
every positive-energy scheduler job and every admissible release/deadline slot.
The job energy equality, native-region assignment, per-site nameplate capacity,
GPU-count-derived interval bound, and deterministic event tariff are all
enforced in the optimization model. Finite scheduler timelimits are retained
exactly; only the declared unlimited sentinel receives the precommitted
128-slot window. The measured-energy/nameplate calculation is an audit-only
feasibility precheck, and an infeasible declaration stops the run rather than
enlarging its deadline. The output is therefore an executable
preemptive batch-service counterfactual rather than a replay of an already
observed aggregate profile.

The experiment does not claim arbitrary nonpreemptive execution. The measured
contiguous runtime/GPU witness remains in Experiment 14; together the two
stages separate (i) task-level evidence for the observed ledger from (ii) an
indexed, globally optimized counterfactual for checkpointable batch work.

Run from the repository root with:

```bash
PYTHONPATH=src python experiments/exp19_job_level_counterfactual/run.py
```

The final directory contains the exact solver summary, slot profile, compressed
service vector, and machine-readable metadata used by the manuscript. The
downstream Experiment 21 audit reports both the capacity-proportional
homogeneous scale and the certified scale with the fixed per-GPU nameplate;
the latter is the deployment interpretation and neither scale is presented as
a re-optimised second LP.
