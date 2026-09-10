"""Run the job-level counterfactual directly from this experiment directory."""

from __future__ import annotations

import logging
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code/src"))

from aicdr.experiments import run_exp19
from aicdr.utils import load_config


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_exp19(
        ROOT,
        load_config(ROOT / "configs/default.yaml"),
        logging.getLogger("exp19"),
        resume=True,
    )
