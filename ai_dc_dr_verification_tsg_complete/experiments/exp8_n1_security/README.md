# Experiment 8: N-1 Security-Aware Settlement

This experiment evaluates all 54 locked test days and all eight event intervals
on the public IEEE Reliability Test System 24-bus network. One linear program
simultaneously enforces the base-case limits and every finite non-islanding
single-line contingency constraint. The experiment uses all 37 credible
non-islanding outages; it performs no contingency screening, branch derating,
or outcome-conditioned selection.

The trace-anchored reference isolates the settlement mechanism, while the
risk-constrained workload verifier reports end-to-end performance. Base-case
exact value and N-1 linear settlement are compared with the proposed N-1 exact
net value against an independently re-solved 40-segment N-1 evaluator. Every
interval result, daily aggregation, paired block test, metadata record, and
English vector/raster figure is retained.

Run independently with:

```bash
./run_all.sh --stage exp8 --resume
```
