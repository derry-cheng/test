# Archive and repository status

The uploaded `ai_dc_dr_verification_tsg_complete.tar(1).gz` stream was
truncated (`gzip: unexpected end of file`). The recoverable workspace has
since been completed with the original public raw inputs: the BurstGPT
release asset and the MIT SuperCloud S3 object were downloaded independently
and verified byte-for-byte against the hashes recorded in the manifest.
The workspace now contains the source code, complete raw and processed data,
all 18 experiment directories, audit reports, tests, manuscript sources,
editable figures, and generated results.

The expected raw-data sizes and SHA-256 hashes are retained in
`data/processed/data_manifest.json`; the latest independent audit passes all
237 checks. The repository should still be treated as a trace-driven
benchmark, not as evidence from a co-located utility event. The network
placement and workload-to-power scaling are declared scenario parameters, and
the manuscript states this identification boundary explicitly.

The source datasets remain subject to their upstream terms. The repository
uses Git LFS rules for large local files; the complete transport archive in
the companion GitHub branch contains the full available snapshot when a
regular Git blob is not suitable for the upstream file-size limit.
