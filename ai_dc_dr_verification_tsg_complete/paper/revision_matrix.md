# TSG revision evidence map

Updated 14 October 2026. `main.tex` and its compiled `main.pdf` are the publication sources. The machine-readable experiment outputs govern numerical precision. Earlier design records are explicitly marked historical; they do not override the revised claims.

| Review issue | Revised treatment | Canonical evidence |
|---|---|---|
| C1 risk-to-execution composition | Positive normalized slot price is described as a load-avoidance heuristic. Daily L1, top-m-tail, and RMSE transport bounds are proved. Uncapped execution failure and capped-credit success remain separate. | Main Sections III.C and V.B; [Experiment 31](../experiments/exp31_risk_execution_composition/README.md) |
| C2 inactive tail constraints | Old-objective/no-hard-row control isolates the old slack constraints. Exact-MSE total-only and binding-tail frontier share the same hull and objective; exploratory uncertainty and retrospective status are explicit. | Main Sections III.B and V.A; Experiment 31 solver certificates and locked bootstrap CSVs |
| C3 decision-time population | Complete-ledger audits and the slot-62 protocol are distinguished. Main and old gate F1 values are not treated as a matched deterioration. | Main Sections II.A, IV, V.B; [Experiment 32](../experiments/exp32_matched_gate_capacity/README.md) |
| C4 runtime/nameplate capacity | Full-runtime separability is conditional on combined capacity feasibility. Calibrated-energy, measured-energy, and nameplate ledgers are separate; the older partial-slot stress does not validate the full-runtime model. | Main Sections III.C and V.B; Experiment 32 same-semantics stress |
| C5 AC denominator | Topology-only common outage domain retains numerical unknowns and converged violations. Native-screen status is a secondary subgroup, not a locked-outcome filter. DC and AC scopes remain separate. | Main Section V.C; [Experiment 18](../experiments/exp18_preventive_ac_network_panel/README.md) |
| M1 abstract and hierarchy | Abstract is within 150–200 words. Results lead with scientific questions and principal findings. | Main abstract and Section V |
| M2 model/method organization | System definitions are separated from runtime MILP, risk fit, and implementation conventions. | Main Sections II–IV; [reproducibility supplement](revision_supplement.md) |
| M3 readable IEEE layout | Standard 10pt IEEEtran body and 8pt references/tables; no bibliography compression or table resize. Editable vector diagrams use native-size 8.5pt labels. | Main PDF; figures/*.drawio, *.svg; figure builder scripts |
| M4 names, units, and precision | One publication alias per method; three decimal places in main tables; both credit columns in MWh/day. The missing interval factor in local capacity cash is restored. | Main Tables I–II and settlement formula |
| M5 citations and mathematics | Extra-trees citation is attached to the estimator sentence; close network-remuneration and CVaR works are contrasted. The unfounded universal absence claim is removed. | Main Introduction and Section III.A; references.bib |

The revision does not claim a fresh unseen holdout, causal utility-event identification, semantic authentication of declarations, or a universal method ranking. A failed composition test is preserved as evidence rather than counted as a passed end-to-end certificate.
