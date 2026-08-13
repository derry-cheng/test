from pathlib import Path
from aicdr.experiments import run_exp2
from aicdr.utils import configure_logging, load_config

ROOT = Path(__file__).resolve().parents[2]
run_exp2(ROOT, load_config(ROOT / "configs/default.yaml"), configure_logging(ROOT / "logs/exp2.log"))

