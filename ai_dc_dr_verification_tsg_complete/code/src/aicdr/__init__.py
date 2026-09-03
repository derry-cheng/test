"""Reproducible experiments for verifiable demand response from spatially coupled AI data centers."""

# Standalone experiment wrappers import ``aicdr`` without going through the
# top-level ``run_all.py`` entry point.  Clamp numerical backends before any
# SciPy/HiGHS module is imported so a configured worker pool cannot silently
# multiply into an unbounded BLAS/solver thread pool.  The unified entry point
# sets the same variables explicitly; the standalone entry points use the same
# deterministic one-thread policy so an inherited environment cannot silently
# exceed the declared twenty-core envelope.
import os as _os

for _thread_env in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "BLIS_NUM_THREADS",
):
    _os.environ[_thread_env] = "1"
_os.environ["HIGHS_NUM_THREADS"] = "1"

__version__ = "0.1.0"
