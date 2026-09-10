from __future__ import annotations

import logging
from pathlib import Path

from aicdr.experiments import run_exp10
from aicdr.utils import load_config


ROOT = Path(__file__).resolve().parents[2]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_exp10(
        ROOT,
        load_config(ROOT / "configs/default.yaml"),
        logging.getLogger("exp10"),
        resume=True,
    )
