# Regression tests

Run from the project root with:

```bash
PYTHONPATH=src python tests/run_tests.py
```

The tests cover the submit-time ledger schema, the exclusion of execution
telemetry from the submission digest, requested-GPU parsing, and the typed
job-to-network conservation certificate.
