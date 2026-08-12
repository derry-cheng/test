# Full archive transport

The complete working tree for this study is stored in nine Git blobs under
`ai_dc_dr_verification_tsg_complete_FULL_ARCHIVE/`. The parts are ordered
`part-000` through `part-008`.

- Archive size: 72,568,844 bytes
- Archive SHA-256: `4529ad188138e61ebec81a684fd000b2ecbf2a1c91b285cf1c9759ac1a629c7e`

Reconstruct it after cloning:

```bash
mkdir -p /tmp/aicdr-full-archive
cat ai_dc_dr_verification_tsg_complete_FULL_ARCHIVE/part-* > /tmp/aicdr-full-archive/ai_dc_dr_verification_tsg_complete.tar.gz
sha256sum /tmp/aicdr-full-archive/ai_dc_dr_verification_tsg_complete.tar.gz
tar -xzf /tmp/aicdr-full-archive/ai_dc_dr_verification_tsg_complete.tar.gz
```

This archive is the complete source-of-truth snapshot for the current
revision. It includes the restored public raw inputs, revised manuscript,
source code, experiments, generated figures/results, audit records, tests,
license notices, and all other files available in the workspace.

The latest data stage and independent audit were run after restoration:
238/238 audit checks passed. The latest manuscript build has no unresolved
cross-references or overfull boxes and contains 12 letter-size pages. The
study remains a trace-driven benchmark and does not claim co-located
utility/facility telemetry.
