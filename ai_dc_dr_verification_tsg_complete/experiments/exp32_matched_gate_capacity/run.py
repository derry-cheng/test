from __future__ import annotations
import os
for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[name] = "1"
import argparse
import logging
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code/src"))
sys.path.insert(0, str(ROOT / "vendor"))
from aicdr.matched_gate_capacity import run_exp32_matched_gate_capacity
from aicdr.utils import load_config
if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--part", choices=["all", "gate", "capacity"], default="all")
    args = parser.parse_args(); logging.basicConfig(level=logging.INFO)
    run_exp32_matched_gate_capacity(ROOT, load_config(ROOT / "configs/default.yaml"), logging.getLogger("exp32"), part=args.part)
