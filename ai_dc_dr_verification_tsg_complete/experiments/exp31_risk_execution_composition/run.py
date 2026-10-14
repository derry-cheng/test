from pathlib import Path
import os
for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[key] = "1"
import sys
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "code/src"))
sys.path.insert(0, str(root / "vendor"))
from aicdr.utils import load_config, configure_logging
from aicdr.risk_execution_composition import run_exp31_risk_execution_composition
if __name__ == "__main__":
    run_exp31_risk_execution_composition(root, load_config(root / "configs/default.yaml"), configure_logging(root / "logs/exp31.log"))
