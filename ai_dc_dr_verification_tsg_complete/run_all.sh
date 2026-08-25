#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$ROOT/src:$ROOT/vendor:${PYTHONPATH:-}"
export PYTHONDONTWRITEBYTECODE=1
export MPLCONFIGDIR="${TMPDIR:-/tmp}/aicdr_matplotlib_cache"
mkdir -p "$MPLCONFIGDIR"
cd "$ROOT"
python run_all.py --config configs/default.yaml "$@"
