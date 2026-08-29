"""Run the indexed job-to-network coupling certificate directly."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "vendor"))

from aicdr.coupling_certificate import run_exp22_coupled_job_network_certificate
from aicdr.utils import load_config


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_exp22_coupled_job_network_certificate(
        ROOT,
        load_config(ROOT / "configs/default.yaml"),
        logging.getLogger("exp22"),
    )
