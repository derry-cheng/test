# Experiment 18: Common-domain fixed-plan AC N-1 audit

The primary denominator is fixed from topology before any AC result is scored.
It includes every connected single active-branch outage in RTS-24, IEEE-30,
IEEE-39, and IEEE-118: respectively 37, 38, 35, and 177 outages. Both methods,
all three relative workload scale multipliers (3%, 6%, 9%), and all six locked
day/slot snapshots are retained, giving **10,332 declared cells**. These are
six operating snapshots, not 10,332 independent operating days.

Each cell freezes non-reference active generation to its method's intact AC
OPF dispatch with a 1e-8 MW bound. Reference-generation losses, reactive outputs,
and voltages may recourse. The native-load multiplier remains 0.90, the
power factor remains 0.95, the four regional bus locations are unchanged, and
the workload scale is the checksum-bound Exp9 scale. Neither profiles nor
physical constraints are changed to obtain a desired result.

## Complete outcome ledger

- `certified`: solver reports convergence and the explicit apparent-loading,
  voltage, and fixed-active-plan checks pass with their original 1e-6 residual
  margins
- `converged_limit_violation`: a converged candidate fails at least one of
  those checks; it remains in the denominator
- `numerical_unknown`: the nonlinear solver/restarts do not produce a usable
  converged candidate, or the intact dispatch is unresolved; it remains in
  the denominator and is **not** called physically infeasible

None of these labels proves global nonlinear AC infeasibility. The primary
certification fraction is certified cells divided by all declared cells for
that network, penetration, and method. Accounting coverage includes all three
categories; it is distinct from a physical certification rate.

The native no-workload solve is now only a diagnostic subgroup shared by both
methods. `native_connected_outage_diagnostics.csv` retains every native outage,
and `native_screened_common_domain_summary.csv` reports the secondary subgroup.
Native solver failures cannot remove cells from the primary denominator. No
method/outage is removed after a locked-workload failure.

## Reproduction and archived evidence

From the project root:

```
PYTHONPATH=code/src:vendor python code/scripts/run_ac_common_domain_audit.py --reuse-legacy --workers 8
```

`--reuse-legacy` verifies the original successful CSV and the three frozen
profile-file hashes against `results/intermediate/schema12_reuse_manifest.json`.
It preserves 9,576 original successful certificates and reconstructs 756 cells:
all 720 previously omitted cells plus the 36 existing proposed-method cells
on IEEE30 outages 29 and 31, so both methods receive the same fresh diagnostic
protocol on those two previously method-filtered outages. Reused rows are
explicitly marked `retained_schema12_certificate`; no fresh solve or new
independent residual audit is claimed for them. The original intact result
arrays were not archived, a limitation of the retained evidence.

Omit `--reuse-legacy` to recompute every contingency. Use `--resume` to continue
from the schema-13 checkpoint, which binds the complete protocol and profile
hashes. The execution uses at most eight worker processes and one BLAS thread
per worker; the final repair run uses eight workers. Hash-bound intact-dispatch
and native-diagnostic caches avoid repeating completed stages after interruption. Every fresh case receives the same
MIPS/default, safeguarded PIPS, and power-flow-initialized restart budget.
Retries change initialization only, never load, dispatch bounds, or limits.

Primary outputs are `common_domain_manifest.csv`,
`preventive_ac_cross_network_results.csv`,
`preventive_ac_cross_network_summary.csv`, and `experiment_metadata.json`.
`reconstructed_cells.csv` isolates fresh evidence and
`solver_attempt_diagnostics.csv` records the retained cells’ numerical starts,
convergence status, iteration count, and available feasibility/KKT residuals.
The new coverage figure displays unresolved cells explicitly. Schema-12 files
are historical source evidence only and are not the current denominator.
