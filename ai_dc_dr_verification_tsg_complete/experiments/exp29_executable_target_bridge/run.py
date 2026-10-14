"""Run this experiment through the unified, thread-limited entry point."""
from pathlib import Path
import os
import runpy
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "code/src"), str(ROOT / "vendor")]
if __name__ == "__main__":
    os.chdir(ROOT)
    sys.argv = [str(ROOT / "run_all.py"), "--stage", "exp29", *sys.argv[1:]]
    runpy.run_path(str(ROOT / "run_all.py"), run_name="__main__")
