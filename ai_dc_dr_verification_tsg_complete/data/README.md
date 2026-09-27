# Data layout

`processed/` contains the compact, versioned tensors and manifests needed for
the locked experiments. Public source CSVs belong under `raw/burstgpt/`,
`raw/mit_supercloud/`, and `raw/pglib/`; raw releases are intentionally ignored
by Git, while their URLs, checksums, and preprocessing decisions are recorded in
`processed/data_manifest.json`. No experiment reads a raw completion timestamp
to enlarge a submit-time counterfactual window.

Restore the four optional BurstGPT and MIT CSVs from their public releases and
verify every locked byte count and SHA-256 digest with:

```text
python code/scripts/download_public_inputs.py
```

The script writes only to the ignored `raw/` directories. The PGLib IEEE-118
case is already tracked and is verified by the same command. To validate an
existing local data restore without network access, run:

```text
python code/scripts/download_public_inputs.py --check-only
```
