from pathlib import Path

from aicdr.trace_replay import run_trace_meter_replay
from aicdr.utils import configure_logging, load_config


ROOT = Path(__file__).resolve().parents[2]
run_trace_meter_replay(ROOT, load_config(ROOT / "configs/default.yaml"), configure_logging(ROOT / "logs/exp20.log"))
