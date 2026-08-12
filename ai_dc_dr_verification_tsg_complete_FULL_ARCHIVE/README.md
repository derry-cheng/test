# Full archive transport

The complete working tree for this study is stored in eight Git blobs under
`ai_dc_dr_verification_tsg_complete_FULL_ARCHIVE/`. The parts are ordered
`part-000` through `part-007`.

- Archive size: 64,922,823 bytes
- Archive SHA-256: `4d8da8d85000b5674a5c7a5eda0fd7ddefe690e84f697d8a442254dc737fbe83`

Reconstruct it after cloning:

```bash
mkdir -p /tmp/aicdr-full-archive
cat ai_dc_dr_verification_tsg_complete_FULL_ARCHIVE/part-* > /tmp/aicdr-full-archive/ai_dc_dr_verification_tsg_complete.tar.gz
sha256sum /tmp/aicdr-full-archive/ai_dc_dr_verification_tsg_complete.tar.gz
tar -xzf /tmp/aicdr-full-archive/ai_dc_dr_verification_tsg_complete.tar.gz
```

The archive is the source-of-truth snapshot for this revision. The browsable
directory in the repository is retained from the earlier Git commit. The
archive includes the revised manuscript, source code, experiments, generated
figures/results, audit records, and all files available in the workspace.

The archive status remains explicit: two raw CSV inputs available in the
workspace are shorter than the hashes declared by the locked data manifest.
The generated locked outputs are therefore preserved artifacts, not a fresh
raw-to-result reproduction, until the original complete CSVs are restored.
