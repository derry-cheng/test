# Full archive transport

The complete working tree for this study is stored in nine Git blobs under
`ai_dc_dr_verification_tsg_complete_FULL_ARCHIVE/`. The parts are ordered
`part-000` through `part-008`.

- Archive size: 72,569,839 bytes
- Archive SHA-256: `8022d8abb982e1b1861df5fa88efc1c38b84dcaf7e4cfa02fe1966814b0d42e2`

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
238/238 audit checks passed. The study remains a trace-driven benchmark and
does not claim co-located utility/facility telemetry.
