"""Run the full finite N-1 frozen-profile panel directly."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "vendor"))

from aicdr.all_outage_security import run_exp24_all_outage_security_panel
from aicdr.utils import load_config


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_exp24_all_outage_security_panel(
        ROOT,
        load_config(ROOT / "configs/default.yaml"),
        logging.getLogger("exp24"),
    )
