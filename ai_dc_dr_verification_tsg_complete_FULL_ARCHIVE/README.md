# Complete workspace archive transport

The full reproducibility snapshot is stored as ordered Git blobs under this
directory. The previous nine truncated transport parts were replaced.

- Archive size: 64,601,281 bytes
- Archive SHA-256: `cd274cea3e64bcd7215eafc61d42aebd8e75072e5029941e52f30351fe1bbb7e`
- Parts: `part-0000` through `part-0157`
- Part size: 409,600 bytes except the final part

After cloning the branch, reconstruct the archive with:

```bash
mkdir -p /tmp/aicdr_archive_parts
cp ai_dc_dr_verification_tsg_complete_FULL_ARCHIVE/part-* /tmp/aicdr_archive_parts/
cat /tmp/aicdr_archive_parts/part-* > /tmp/ai_dc_dr_verification_tsg_complete.tar.gz
sha256sum /tmp/ai_dc_dr_verification_tsg_complete.tar.gz
tar -xzf /tmp/ai_dc_dr_verification_tsg_complete.tar.gz
```

The extracted directory contains the source code, complete public raw inputs,
processed data, all experiment outputs, manuscript sources and PDF, figures,
tests, audit certificates, license notices, and the current validation log.
Temporary render caches and failed historical run logs are excluded.
