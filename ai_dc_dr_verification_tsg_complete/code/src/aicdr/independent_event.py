"""Compatibility entry point for the independent event replay.

Experiment 23 is implemented in :mod:`aicdr.declaration_event_replay`. The
stage is intentionally declaration-only: it re-enumerates the same submitted
jobs under a distinct predeclared tariff and binds its output to the Exp27
runtime-complete witness digest. Keeping this module as a one-function
adapter avoids a second, unreachable controlled-event implementation with a
different information boundary.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .declaration_event_replay import run_declaration_only_replay


def run_exp23_independent_event_replay(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
) -> None:
    """Run the canonical Exp23 declaration-only independent replay."""

    run_declaration_only_replay(
        root,
        cfg,
        logger,
        output_experiment="exp23_independent_event_replay",
    )
