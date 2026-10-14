from __future__ import annotations

import argparse
import logging
import os
import sys
import tempfile
from pathlib import Path

# Keep numerical backends from multiplying the declared experiment worker
# counts.  The paper's largest process pool remains below 20 workers, and a
# single BLAS/HiGHS thread per worker gives a deterministic workstation bound.
for _thread_env in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "BLIS_NUM_THREADS",
):
    os.environ[_thread_env] = "1"
# Bound aggregate worker CPU use even when a native backend ignores its
# thread environment variable. Child processes inherit this Linux CPU set.
if hasattr(os, "sched_getaffinity") and hasattr(os, "sched_setaffinity"):
    _allowed_cpus = sorted(os.sched_getaffinity(0))
    if len(_allowed_cpus) > 20:
        os.sched_setaffinity(0, _allowed_cpus[:20])

os.environ["HIGHS_NUM_THREADS"] = "1"
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "aicdr_matplotlib_cache"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "aicdr_cache"))

from aicdr.pipeline import run_pipeline
from aicdr.utils import configure_logging, load_config


def main() -> int:
    parser = argparse.ArgumentParser(description="Full reproducible AI data-center DR verification study")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--force-preprocess", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--stage",
        choices=[
            "all",
            "data",
            "exp1",
            "exp2",
            "exp3",
            "exp4",
            "exp5",
            "exp6",
            "exp7",
            "exp8",
            "exp9",
            "exp10",
            "exp11",
            "exp12",
            "exp13",
            "exp14",
            "exp15",
            "exp16",
            "exp17",
            "exp18",
            "exp19",
            "exp20",
            "exp21",
            "exp22",
            "exp23",
            "exp24",
            "exp25",
            "exp27",
            "exp28",
            "exp29",
            "exp30",
            "exp31",
            "exp32",
            "exp26",
            "audit",
        ],
        default="all",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    cfg = load_config(root / args.config)
    logger = configure_logging(root / "logs" / "full_run.log")
    logger.info("Unified run started; stage=%s, resume=%s", args.stage, args.resume)
    try:
        run_pipeline(root, cfg, args.stage, args.force_preprocess, args.resume, logger)
    except Exception:
        logger.exception("Pipeline failed")
        return 1
    logger.info("Unified run completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
