from __future__ import annotations

import logging
from pathlib import Path

from aicdr.experiments import run_exp8
from aicdr.utils import configure_logging, load_config


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    config = load_config(root / "configs/default.yaml")
    logger = configure_logging(root / "logs/exp8_n1_security.log")
    run_exp8(root, config, logger, resume=True)
