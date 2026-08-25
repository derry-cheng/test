"""Re-run the job-level counterfactual through the repository entry point."""

from __future__ import annotations

import subprocess
from pathlib import Path


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    subprocess.run(
        ["bash", str(root / "run_all.sh"), "--stage", "exp19"],
        cwd=root,
        check=True,
    )
