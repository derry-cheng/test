# Full archive transport

The complete working tree for this study is stored in eight Git blobs under
`ai_dc_dr_verification_tsg_complete_FULL_ARCHIVE/`. The parts are ordered
`part-000` through `part-007`.

- Archive size: 64,922,829 bytes
- Archive SHA-256: `6a823fbba83bfe69065f748a659f464a7963ccaa3a73c2afcedebfb6350a6c23`

Reconstruct it after cloning:

```bash
mkdir -p /tmp/aicdr-full-archive
cat ai_dc_dr_verification_tsg_complete_FULL_ARCHIVE/part-* > /tmp/aicdr-full-archive/ai_dc_dr_verification_tsg_complete.tar.gz
sha256sum /tmp/aicdr-full-archive/ai_dc_dr_verification_tsg_complete.tar.gz
tar -xzf /tmp/aicdr-full-archive/ai_dc_dr_verification_tsg_complete.tar.gz
```

The archive is the source-of-truth snapshot for this revision. The browsable
directory in the repository is retained from the earlier Git commit, with the
revised manuscript, audit report, key source/test files, and package
documentation exposed directly. The archive includes the revised manuscript,
source code, experiments, generated figures/results, audit records, and all
files available in the workspace.

The archive status remains explicit: two raw CSV inputs available in the
workspace are shorter than the hashes declared by the locked data manifest.
The generated locked outputs are therefore preserved artifacts, not a fresh
raw-to-result reproduction, until the original complete CSVs are restored.
