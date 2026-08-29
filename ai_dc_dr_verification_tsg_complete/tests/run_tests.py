"""Dependency-free runner for the project's assertion-style test suite."""

from __future__ import annotations

import inspect
import sys
import tempfile
import traceback
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "vendor"))

import test_core  # noqa: E402
import test_deadline_ledger  # noqa: E402


def main() -> int:
    tests = [
        (name, function)
        for module in (test_core, test_deadline_ledger)
        for name, function in inspect.getmembers(module, inspect.isfunction)
        if name.startswith("test_")
    ]
    failures = 0
    for name, function in tests:
        try:
            # Keep the runner dependency-free while supporting the two
            # filesystem-isolated regression tests that use pytest's
            # ``tmp_path`` convention.  A fresh directory is supplied only
            # when the test explicitly declares one positional parameter.
            parameters = inspect.signature(function).parameters
            if not parameters:
                function()
            elif len(parameters) == 1 and "tmp_path" in parameters:
                with tempfile.TemporaryDirectory(prefix="aicdr-test-") as path:
                    function(Path(path))
            else:
                raise TypeError(
                    f"unsupported test signature for {name}: {list(parameters)}"
                )
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
