"""Dependency-free runner for the project's assertion-style test suite."""

from __future__ import annotations

import inspect
import sys
import traceback
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "vendor"))

import test_core  # noqa: E402


def main() -> int:
    tests = [
        (name, function)
        for name, function in inspect.getmembers(test_core, inspect.isfunction)
        if name.startswith("test_")
    ]
    failures = 0
    for name, function in tests:
        try:
            function()
            print(f"PASS {name}", flush=True)
        except Exception:
            failures += 1
            print(f"FAIL {name}", flush=True)
            traceback.print_exc()
    print(
        f"{len(tests) - failures}/{len(tests)} tests passed",
        flush=True,
    )
    return int(failures > 0)


if __name__ == "__main__":
    raise SystemExit(main())
