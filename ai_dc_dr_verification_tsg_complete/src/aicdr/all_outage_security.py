"""Full finite N-1 replay for frozen workload profiles."""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .optimization import build_n1_security_factors, power_system_from_ppc, solve_n1_sced
from .progress import progress as tqdm
from .utils import write_json


def run_exp24_all_outage_security_panel(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
) -> None:
    """Replay frozen locked-test profiles against every finite RTS-24 outage.

    The workload profile is fixed before the network solve.  No AC admissibility
    screen, outage ranking, or post-solution profile adjustment is applied.  A
    cell therefore contains one complete DC N-1 SCED with all finite
    non-islanding branch contingencies represented in the security factors.
    """

    folder = root / "experiments/exp24_all_outage_security_panel"
    final = folder / "results/final"
    figures = folder / "figures"
    final.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    source = root / "experiments/exp2_baseline_verification/results/intermediate/test_profiles.npz"
    if not source.exists():
        raise FileNotFoundError(f"Locked profile panel is missing: {source}")
    stored = np.load(source, allow_pickle=False)
    days = np.asarray(stored["days"], dtype=int)
    methods = [str(value) for value in stored["methods"].tolist()]
    selected_methods = ["Risk-Constrained Convex Verifier", "Single Feasible Projection"]
    missing = [name for name in selected_methods if name not in methods]
    if missing:
        raise ValueError(f"Exp2 profile panel is missing required methods: {missing}")
    profiles = np.asarray(
        stored["baselines"][:, [methods.index(name) for name in selected_methods]],
        dtype=float,
    )
    # Keep this panel on the predeclared RTS-24 security benchmark.  Exp2's
    # workload profiles may use IEEE-118 for other panels, but silently using
    # that topology here would change the contingency count and invalidate the
    # headline all-outage comparison.
    from pypower.case24_ieee_rts import case24_ieee_rts

    system = power_system_from_ppc(case24_ieee_rts())
    security = build_n1_security_factors(system)
    event_slots = list(map(int, cfg["market"]["event_slots"]))
    fixed_load_mw = float(cfg["project"]["fixed_facility_load_mw"])
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    buses = np.asarray(
        cfg["experiments"].get("coupled_network_buses_one_based", [3, 8, 15, 21]),
        dtype=int,
    ) - 1
    if len(buses) != profiles.shape[2] or np.any(buses < 0) or np.any(buses >= len(system.bus)):
        raise ValueError("Configured network data-center buses do not match profile regions")
    workers = int(cfg["experiments"].get("all_outage_panel_workers", 4))
    if not 1 <= workers <= 20:
        raise ValueError("all_outage_panel_workers must be between 1 and 20")
    base_load = np.asarray(system.bus[:, 2], dtype=float) * float(
        cfg["experiments"].get("n1_load_multiplier", 0.9)
    )

    tasks = [
        (local_day, int(day), method_index, method, int(slot))
        for local_day, day in enumerate(days)
        for method_index, method in enumerate(selected_methods)
        for slot in event_slots
    ]

    def solve_one(task: tuple[int, int, int, str, int]) -> dict[str, Any]:
        local_day, day, method_index, method, slot = task
        load = base_load.copy()
        flexible_mw = np.maximum(profiles[local_day, method_index, :, slot] - fixed_load_mw, 0.0)
        load[buses] += flexible_mw
        solved = solve_n1_sced(
            system,
            load,
            int(cfg["market"]["generator_segments"]),
            security_factors=security,
        )
        return {
            "day": day,
            "slot": slot,
            "method": method,
            "flexible_profile_mw": float(flexible_mw.sum()),
            "secure_cost_usd_per_interval": float(solved.objective * dt_h),
            "max_base_loading": float(solved.max_loading),
            "max_postcontingency_loading": float(solved.max_post_contingency_loading),
            "credible_contingencies": int(solved.credible_contingencies),
            "evaluated_finite_nonislanding_outages": int(solved.credible_contingencies),
            "solver_success": bool(solved.success),
            "post_solution_profile_reoptimization": False,
        }

    logger.info(
        "Experiment 24 full N-1 replay: %d cells, %d workers, %d outages/cell",
        len(tasks),
        workers,
        int(security[3]),
    )
    rows: list[dict[str, Any]] = []
    progress = tqdm(total=len(tasks), desc="Exp24 all finite N-1 cells")
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for row in executor.map(solve_one, tasks):
            rows.append(row)
            progress.update(1)
    progress.close()
    frame = pd.DataFrame(rows).sort_values(["day", "method", "slot"]).reset_index(drop=True)
    frame.to_csv(final / "all_outage_security_replay.csv", index=False)
    summary = (
        frame.groupby("method", as_index=False)
        .agg(
            locked_days=("day", "nunique"),
            replay_cells=("slot", "size"),
            secure_cost_usd_per_interval=("secure_cost_usd_per_interval", "mean"),
            max_base_loading=("max_base_loading", "max"),
            max_postcontingency_loading=("max_postcontingency_loading", "max"),
            minimum_contingencies=("credible_contingencies", "min"),
            maximum_contingencies=("credible_contingencies", "max"),
            all_cells_successful=("solver_success", "all"),
        )
    )
    summary.to_csv(final / "all_outage_security_summary.csv", index=False)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.1, 3.8), constrained_layout=True)
    groups = [
        frame.loc[frame["method"] == method, "max_postcontingency_loading"].to_numpy()
        for method in selected_methods
    ]
    ax.boxplot(groups, labels=["Risk-constrained\nverifier", "Single feasible\nprojection"], patch_artist=True,
               boxprops={"facecolor": "#D9EAF7", "edgecolor": "#0072B2"},
               medianprops={"color": "#D55E00", "linewidth": 1.5})
    ax.axhline(1.0, color="#333333", linestyle="--", linewidth=1.0, label="N−1 limit")
    ax.set_ylabel("Maximum post-contingency loading (p.u.)")
    ax.set_title("Frozen profiles under every finite RTS-24 N−1 outage")
    ax.grid(axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False, fontsize=8)
    for suffix in ("png", "pdf"):
        fig.savefig(figures / f"fig27_all_outage_security.{suffix}", dpi=320, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    metadata = {
        "experiment": "full finite N-1 frozen-profile security replay",
        "network_case": "IEEE RTS-24 (PYPOWER case24_ieee_rts)",
        "network_source": "PYPOWER case24_ieee_rts (public RTS-24 benchmark)",
        "profile_source": "Exp2 locked-test profiles frozen before network replay",
        "evaluated_methods": selected_methods,
        "locked_days": int(len(days)),
        "event_slots": event_slots,
        "replay_cells": int(len(frame)),
        "credible_contingencies_per_cell": int(security[3]),
        "all_finite_nonislanding_outages_evaluated": True,
        "ac_admissibility_screen": False,
        "outage_ranking_or_screening": False,
        "post_solution_profile_reoptimization": False,
        "workers": workers,
        "maximum_postcontingency_loading": float(frame["max_postcontingency_loading"].max()),
        "all_solver_cells_successful": bool(frame["solver_success"].all()),
        "figure": "fig27_all_outage_security.pdf",
    }
    write_json(final / "experiment_metadata.json", metadata)
    logger.info(
        "Experiment 24 complete: %d cells and %d finite non-islanding outages per cell",
        len(frame),
        int(security[3]),
    )
