"""Run the exact homogeneous scale-consistency audit."""
from pathlib import Path
import logging
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code/src"))
from aicdr.scale_audit import run_exp21_scale_consistency
from aicdr.utils import load_config

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_exp21_scale_consistency(ROOT, load_config(ROOT / "configs/default.yaml"), logging.getLogger("exp21"))
