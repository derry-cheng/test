# Archive and repository status

The uploaded `ai_dc_dr_verification_tsg_complete.tar(1).gz` stream was
truncated and cannot by itself reproduce the study (`gzip: unexpected end of
file`). The workspace has been completed with verified public raw inputs and
contains the source code, processed arrays, all 21 experiment directories,
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

The large raw inputs remain outside the Git working tree because they exceed
GitHub's ordinary per-file limit. Their public URLs, hashes, licenses, and the
checked-in transport reconstruction procedure are part of the publication
package. The locked processed tensor and compressed experiment checkpoints are
stored directly so tests do not depend on an LFS smudge step.
