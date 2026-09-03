from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "code/src"), str(ROOT / "vendor")]

from aicdr.experiments import run_exp1
from aicdr.utils import configure_logging, load_config

run_exp1(ROOT, load_config(ROOT / "configs/default.yaml"), configure_logging(ROOT / "logs/exp1.log"))
