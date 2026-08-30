# Experiment index

Each `exp*/` directory is a self-contained stage with a `run.py`, a short
protocol README, publication figures, and separated `results/final/` and
`results/intermediate/` directories. The unified runner is `run_all.py`; direct
stage runs must set BLAS/OpenMP thread counts explicitly. Final tables and
figures are generated from the locked configuration and are not copied into the
top-level results index.

The closure stages are arranged as follows: Exp. 2 establishes the matched-ledger
risk profile; Exp. 9 and 15 certify payment conversion and interval endpoints;
Exp. 17 and 23 test the information boundary; Exp. 19, 21, and 22 preserve one
indexed workload witness through scale and network valuation; Exp. 20 and 24
provide independent replay and N--1 checks; Exp. 25 audits submit-time
declarations and binding capacity.
