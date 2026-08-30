# Data layout

`processed/` contains the compact, versioned tensors and manifests needed for
the locked experiments. Public source CSVs belong under `raw/burstgpt/`,
`raw/mit_supercloud/`, and `raw/pglib/`; raw releases are intentionally ignored
by Git, while their URLs, checksums, and preprocessing decisions are recorded in
`processed/data_manifest.json`. No experiment reads a raw completion timestamp
to enlarge a submit-time counterfactual window.
