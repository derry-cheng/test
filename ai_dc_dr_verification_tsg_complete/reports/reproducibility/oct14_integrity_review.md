# Revision integrity review (2026-10-14)

This report concerns reproducibility, data lineage, and numerical certificates.
A passing integrity check does not imply that a method dominates every control,
that simulated response is observed utility response, or that an aggregate
risk certificate automatically applies to a nonpreemptive executable schedule.

## Baseline findings and repairs

1. The documented `tests/run_tests.py` smoke suite passed. The complete baseline
   pytest suite had **47 passes and one failure**: the Exp18 table contained
   9,612 rows while the metadata's survivor-domain formula implied 9,648.
   This disagreement exposed method-specific exclusions, not a harmless test
   tolerance. The revised AC protocol retains the complete 10,332-cell
   topology-connected domain with identical denominators for both methods.
   Numerical unknowns and converged limit violations remain explicit.
2. Exp28 used all observations above an interpolated quantile, whereas the
   risk-contract epigraph uses exactly `ceil((1-level)*n)` observations.
   Resampling ties enlarged the former tail. Both point estimates and
   bootstrap samples now use exactly the largest 14 of 54 observations.
3. Exp28 also referred to a stale input ledger. Its archived source hash was
   `533b81ccbd8d9e3060aab7459582e471f818a5aefaf8132f1921ce1217f63f9f`;
   the source present in the starting Git revision and this revision is
   `6ec152f318062280983fa42fb562131f2d536859e63301f84e9d5a0dbee6dab9`.
   The audit was regenerated from that unchanged current source. Point-estimate
   changes therefore include a provenance refresh and cannot all be attributed
   to the tie correction. New tests bind the ledger and implementation hashes.
4. Exp28's 95% circular three-day bootstrap intervals are **unadjusted
   exploratory percentile intervals**. The separate exact block-sign tests in
   Exp2 have their own metric-wise Holm families. Bootstrap intervals are not
   Holm-adjusted confidence intervals. The observed effect and bootstrap mean
   are now separate columns, preserving the old bootstrap-mean alias.
5. Exp9 retained a stale data-manifest digest. The old digest belongs to
   commit `7ad4dad4a00a4d262ef6a83a566e13f9edb9a374`. A recursive comparison
   found exactly one changed field:
   `mit_supercloud.common_trace_horizon_definition`, a provenance wording
   clarification. The entire power-calibration object and both Exp2 profile
   files are unchanged. The normal Exp9 resume path must revalidate/rebuild
   the final panel; merely replacing its digest is not an acceptable repair.
6. The historical 32-stage all-run manifest is preserved as historical.
   Targeted new work does not retroactively turn it into a 34-stage full run.
   The current audit accepts either a genuinely complete 34-stage run or an
   explicitly disclosed targeted revision alongside the old 32-stage record.

## Corrected Exp28 results

All values below use the existing locked source and fixed seed, not a newly
selected risk model.

| Method | Mean false credit (MWh/day) | Largest-14 tail mean (MWh/day) |
|---|---:|---:|
| Joint total+CVaR | 0.7802851301 | 2.6065343002 |
| Total-only | 0.6457487651 | 2.2230012198 |
| CVaR-only | 0.8166106887 | 2.7120779576 |

Joint minus total-only observed mean difference is 0.1345363651 MWh/day,
with exploratory percentile interval [0.0163972871, 0.2860054495]. Its tail
point difference is 0.3835330804 MWh/day, with interval
[-0.0087464947, 0.9018186466]. The joint model does not beat total-only here.
These intervals are not simultaneous/confirmatory superiority claims.

## Independence and claim boundaries

- Exp23 has a separately implemented selector and a distinct modeled tariff.
  It still shares the declaration model, some aggregation code, and the same
  public benchmark. It is not independently observed event delivery.
- Exp29 imports the Exp27 risk-aligned selector. It is an objective, saved-array,
  and profile-residual replay check, not an implementation-independent solver
  or an independent proof of target realization.
- Exp9's higher-resolution evaluator calls the same SCED implementation with
  a different piecewise cost resolution. This is model/resolution separation,
  not a separately implemented network solver.
- Exp31 transparently labels its redesign as retrospective exploratory method
  development on previously seen locked days. It freezes new validation fits
  before their scoring, but does not claim a fresh external validation set.
- The new audit checks that every stated executable-risk pass flag agrees with
  the actual executed budgets. A payment cap preserving modeled risk does not
  imply that uncapped execution preserves total risk, tail risk, or accuracy.
- Matched-gate comparisons must use the same eligible ledger, common modeled
  reference, response, pre-gate state, participation, and baseline definition.
  A zero modeled shortfall is not an observed default probability.

## Availability and size

The locked processed tensor, profile caches, original runtime witness, and
compact checkpoints are present. The four large optional BurstGPT/MIT raw CSVs
are absent as documented; their manifest declares 281,384,220 bytes in total.
Their bytes were not re-downloaded or re-hashed in this targeted review.
The tracked PGLib case is present (80,336 bytes), and its SHA-256 matches.

At the interim inventory, project files occupy about 122 MB and Git history
about 299 MB, comfortably below the requested 4 GB bound. Final figures and
new outputs may change that slightly. No data deletion was needed or performed
by this review. Ignored Python/pytest caches and LaTeX auxiliaries are ordinary
regenerable cleanup candidates. Retain locked sources, input hashes, public
source licenses, checkpoints needed for provenance, and the archived AC rows
used to distinguish reused certificates from fresh solves. Byte-identical
checkpoint/final pairs are intentional restart evidence, not automatic deletion
candidates.

## Verification record

- Original smoke suite: passed
- Original complete suite: 47 passed, 1 failed (Exp18 domain inconsistency)
- First revision-focused run: 31 passed (risk-tail ties/pairing, release lineage,
  Exp31 transfer/optimization, AC classification, runtime-capacity algebra)
- Final complete suite, release audit, Exp9 revalidation, and final PDF checks:
  recorded in `oct14_revision_manifest.json` after all concurrent stages finish

All numerical commands use one BLAS/OMP/MKL/HiGHS thread per process; this
review's tests run serially. No model choice is adapted to force a locked-test
win, and no failed or unknown scientific cell is removed to improve a table.
