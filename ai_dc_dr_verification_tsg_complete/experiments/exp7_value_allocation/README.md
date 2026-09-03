# Experiment 7: Exact Multi-Participant Value Allocation

This experiment enumerates all \(2^4=16\) coalitions of the four data centers
for every event interval and locked test day. It compares nodal-linear,
standalone, leave-one-out, and exact Shapley allocations. The exact allocation
uses no permutation sampling and is audited for grand-coalition budget balance.
The allocation formula and efficiency property follow Shapley (1953), cited as
`shapley1953value` in `paper/references.bib`. The signed SCED
characteristic function is defined and proved for this study in
`paper/theoretical_results.md`; it is not attributed to the original
Shapley result.

The scalability panel additionally decomposes each of the four sites into
inference and batch contractual portfolios using energy shares fixed from
pre-test public arrivals. It enumerates all \(2^8=256\) coalitions on IEEE
RTS-24 for every one of the 54 locked days and all eight event intervals. This
panel is exact and uses no permutation sampling.

A second exact scaling panel covers 4, 8, 12, 16, and 20 contractual
participants on every locked day. Contract slices are exchangeable only within
the same electrical site, allowing labeled coalitions to be summed with exact
binomial multiplicities over count states. At 20 participants this evaluates
1,296 exact states in place of 1,048,576 separately labeled coalitions; it is
an algebraic reduction, not an estimator.

Run from the project root:

```bash
./run_all.sh --stage exp7
```
