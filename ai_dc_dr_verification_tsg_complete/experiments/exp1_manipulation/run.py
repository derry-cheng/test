from pathlib import Path
from aicdr.experiments import run_exp1
from aicdr.utils import configure_logging, load_config

ROOT = Path(__file__).resolve().parents[2]
run_exp1(ROOT, load_config(ROOT / "configs/default.yaml"), configure_logging(ROOT / "logs/exp1.log"))

