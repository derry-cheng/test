from __future__ import annotations

import hashlib
import json
import logging
import os
import platform
import random
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import scipy
import sklearn
import yaml


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def configure_logging(path: Path) -> logging.Logger:
    path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("aicdr")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    file_handler = logging.FileHandler(path, mode="a", encoding="utf-8")
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def set_reproducible_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


def sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(chunk_size):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False, default=_json_default)


def _json_default(value: Any) -> Any:
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Unsupported type: {type(value)!r}")


def environment_manifest() -> dict[str, Any]:
    try:
        git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        git_commit = None
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "processor_count": os.cpu_count(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "git_commit": git_commit,
    }


def ensure_dirs(root: Path) -> None:
    for rel in [
        "data/processed",
        "logs",
        "artifacts",
        "experiments/exp1_manipulation/results/intermediate",
        "experiments/exp1_manipulation/results/final",
        "experiments/exp1_manipulation/figures",
        "experiments/exp2_baseline_verification/results/intermediate",
        "experiments/exp2_baseline_verification/results/final",
        "experiments/exp2_baseline_verification/figures",
        "experiments/exp3_nodal_settlement/results/intermediate",
        "experiments/exp3_nodal_settlement/results/final",
        "experiments/exp3_nodal_settlement/figures",
        "experiments/exp4_case_study/results/intermediate",
        "experiments/exp4_case_study/results/final",
        "experiments/exp4_case_study/figures",
        "experiments/exp5_network_robustness/results/intermediate",
        "experiments/exp5_network_robustness/results/final",
        "experiments/exp5_network_robustness/figures",
        "experiments/exp6_physical_stress/results/intermediate",
        "experiments/exp6_physical_stress/results/final",
        "experiments/exp6_physical_stress/figures",
        "experiments/exp7_value_allocation/results/intermediate",
        "experiments/exp7_value_allocation/results/final",
        "experiments/exp7_value_allocation/figures",
        "audit",
    ]:
        (root / rel).mkdir(parents=True, exist_ok=True)
