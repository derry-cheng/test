from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

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
