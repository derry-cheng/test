# Archive and repository status

The uploaded `ai_dc_dr_verification_tsg_complete.tar(1).gz` stream was
truncated and cannot by itself reproduce the study (`gzip: unexpected end of
file`). The workspace has been completed with verified public raw inputs and
contains the source code, processed arrays, all 28 experiment directories,
audit reports, tests, manuscript sources, editable figures, and generated
results.

The expected raw-data sizes and SHA-256 hashes are retained in
`data/processed/data_manifest.json`; the verified archive raw files match them. The
complete positive-energy scheduler--DCGM join contains 71,128 jobs, while the
common 121-day tensor window used by Experiments 1--13 contains 68,664. The
remaining 2,464 jobs are retained by the full-horizon Experiments 14 and 16.
The repository should also be treated as
a trace-driven benchmark, not as evidence from a co-located utility event. The
network placement and workload-to-power scaling are declared scenario
parameters, and the manuscript states this identification boundary explicitly.
Experiment 19 now enumerates 13,198,247 admissible contiguous starts over all
75,326 scheduler submissions; 71,128 execution matches are opened only for
post-event scoring. Experiment 21 separates the fixed-nameplate deployable scale from its
capacity-proportional stress profile; Experiment 22 replays the exact indexed
job witness through N--1 settlement on the predeclared public PYPOWER RTS-24
case after a zero-residual job-to-network aggregation check. Experiment 23
adds a structurally distinct controlled event replay with a separate
tariff-bearing LP and predeclared service floor, and
Experiment 24 evaluates every finite non-islanding RTS-24 outage for frozen
profiles. Experiment 25 validates the submit-time declaration boundary and
binding-capacity stress cohort without using execution telemetry in the
counterfactual. Experiment 27 adds the declaration-only runtime-complete
common witness, its typed job/aggregation/GPU/capacity certificate, and the
RTS-24 settlement replay; Experiment 28 audits the held-out risk tail. The
tracked
PGLib IEEE-118 file supports the separate cross-network/AC panels.

The large raw inputs remain outside the Git working tree because they exceed
GitHub's ordinary per-file limit. Their public URLs, hashes, licenses, and the
checked-in transport reconstruction procedure are part of the publication
package. The locked processed tensor and compressed experiment checkpoints are
stored directly so tests do not depend on an LFS smudge step.
