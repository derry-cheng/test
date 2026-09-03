from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "code/src"), str(ROOT / "vendor")]

from aicdr.experiments import run_exp5
from aicdr.utils import configure_logging, load_config


if __name__ == "__main__":
    run_exp5(ROOT, load_config(ROOT / "configs/default.yaml"), configure_logging(ROOT / "logs/exp5.log"))
