from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from aicdr.experiments import run_exp16
from aicdr.utils import load_config


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_exp16(
        ROOT,
        load_config(ROOT / "configs/default.yaml"),
        logging.getLogger("exp16"),
    )
