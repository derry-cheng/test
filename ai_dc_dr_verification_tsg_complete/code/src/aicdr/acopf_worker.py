"""Isolated PYPOWER AC-OPF worker used only after in-process restarts fail.

The worker has no experiment logic and receives a serialized case/options pair.
Running the numerical solve in a clean interpreter prevents solver state from
one public network from affecting a later certificate cell.
"""

from __future__ import annotations

import pickle
import sys

from pypower.runopf import runopf


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m aicdr.acopf_worker INPUT OUTPUT")
    with open(sys.argv[1], "rb") as handle:
        payload = pickle.load(handle)
    result = runopf(payload["case"], payload["options"])
    with open(sys.argv[2], "wb") as handle:
        pickle.dump(result, handle, protocol=pickle.HIGHEST_PROTOCOL)


if __name__ == "__main__":
    main()
