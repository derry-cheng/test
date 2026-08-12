# Archive and repository status

The uploaded `ai_dc_dr_verification_tsg_complete.tar(1).gz` stream was
truncated and cannot by itself reproduce the study (`gzip: unexpected end of
file`). The workspace contains the source code, processed arrays, all 18
experiment directories, audit reports, tests, manuscript sources, editable
figures, and generated results. It also contains partial copies of the raw
inputs, but two large CSV files are truncated and fail the hashes recorded in
the manifest.

The expected raw-data sizes and SHA-256 hashes are retained in
`data/processed/data_manifest.json`. Until the original full CSV files are
restored, the generated results are a locked artifact snapshot rather than a
locally reproducible end-to-end run. The repository should also be treated as
a trace-driven benchmark, not as evidence from a co-located utility event. The
network placement and workload-to-power scaling are declared scenario
parameters, and the manuscript states this identification boundary explicitly.

Before publication, restore and hash-verify the original raw CSV files, verify
their redistribution permissions, and use Git LFS for the BurstGPT file that
exceeds GitHub's ordinary per-file limit.
