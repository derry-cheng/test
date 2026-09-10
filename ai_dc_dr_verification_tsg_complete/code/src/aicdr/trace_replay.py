"""Independent meter replay for the locked workload-verification panel.

This module deliberately has no dependency on the event-response optimizer.
It scores the profiles already committed by Experiment 2 against the measured
DCGM/BurstGPT execution tensor.  The resulting panel is observational: it
cannot identify a causal demand-response event because the public traces do
not contain an intervention label.
"""

from __future__ import annotations

import json
import hashlib
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


TRUTH_SOURCE = "independent_trace_observed_meter"


def _daily_metrics(prediction: np.ndarray, truth: np.ndarray, event_slots: np.ndarray) -> dict[str, float]:
    error = np.asarray(prediction, dtype=float)[:, event_slots] - np.asarray(truth, dtype=float)[:, event_slots]
    denominator = max(float(np.mean(truth[:, event_slots])), 1.0e-9)
    return {
        "mae_mw": float(np.mean(np.abs(error))),
        "rmse_mw": float(np.sqrt(np.mean(error**2))),
        "nrmse": float(np.sqrt(np.mean(error**2)) / denominator),
        "bias_mw": float(np.mean(error)),
        "max_abs_error_mw": float(np.max(np.abs(error))),
    }


def _moving_block_ci(values: np.ndarray, block_length: int, replications: int, seed: int) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or len(values) == 0:
        raise ValueError("CI input must be a nonempty one-dimensional array")
    length = int(max(1, block_length))
    blocks = [values[start : start + length] for start in range(0, len(values), length)]
    blocks = [block for block in blocks if len(block) == length]
    if not blocks:
        blocks = [values]
    rng = np.random.default_rng(int(seed))
    draws = np.empty(int(replications), dtype=float)
    for index in range(len(draws)):
        selected = rng.integers(0, len(blocks), size=len(blocks))
        draws[index] = np.concatenate([blocks[i] for i in selected]).mean()
    return float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def _write_figure(summary: pd.DataFrame, output: Path) -> None:
    """Write a compact, publication-size uncertainty plot."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    order = summary.sort_values("mean_mae_mw").reset_index(drop=True)
    labels = order["method"].str.replace("Risk-Constrained Convex Verifier", "Risk-constrained verifier")
    fig, ax = plt.subplots(figsize=(7.2, 3.8), constrained_layout=True)
    y = np.arange(len(order))
    # Rounding can make an interval endpoint numerically cross its mean.
    # Clip each directional error at zero before passing it to Matplotlib.
    xerr = np.vstack(
        [
            np.maximum(order["mean_mae_mw"].to_numpy() - order["mae_ci_low_mw"].to_numpy(), 0.0),
            np.maximum(order["mae_ci_high_mw"].to_numpy() - order["mean_mae_mw"].to_numpy(), 0.0),
        ]
    )
    ax.errorbar(
        order["mean_mae_mw"],
        y,
        xerr=xerr,
        fmt="o",
        color="#0072B2",
        ecolor="#222222",
        elinewidth=1.0,
        capsize=2.5,
        markersize=4.5,
    )
    ax.set_yticks(y, labels, fontsize=8.5)
    ax.set_xlabel("Event-window MAE against measured execution (MW)")
    ax.set_title("Locked trace-meter replay (54 days; 95% block intervals)")
    ax.grid(axis="x", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    output.mkdir(parents=True, exist_ok=True)
    for suffix in ("png", "pdf"):
        fig.savefig(output / f"fig25_trace_meter_replay.{suffix}", dpi=320, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def run_trace_meter_replay(root: Path, cfg: dict[str, Any], logger: logging.Logger | None = None) -> None:
    """Score committed Experiment-2 profiles against the independent meter tensor."""
    folder = root / "experiments/exp20_trace_meter_replay"
    final = folder / "results/final"
    figures = folder / "figures"
    final.mkdir(parents=True, exist_ok=True)
    profiles_path = root / "experiments/exp2_baseline_verification/results/intermediate/test_profiles.npz"
    workload_path = root / cfg["data"]["processed_dir"] / "workload_15min.npz"
    if not profiles_path.exists():
        raise FileNotFoundError(f"Committed Experiment-2 profiles are missing: {profiles_path}")
    if not workload_path.exists():
        raise FileNotFoundError(f"Processed workload is missing: {workload_path}")

    with np.load(profiles_path, allow_pickle=False) as stored:
        required = {"days", "methods", "baselines"}
        if not required.issubset(stored.files):
            raise RuntimeError(f"Experiment-2 profile archive lacks {sorted(required - set(stored.files))}")
        days = stored["days"].astype(int)
        methods = [str(value) for value in stored["methods"].tolist()]
        profiles = np.asarray(stored["baselines"], dtype=float)
    with np.load(workload_path, allow_pickle=False) as workload:
        observed = np.asarray(workload["observed_counterfactual_mw"], dtype=float)
        slots_per_day = int(cfg["project"]["slots_per_day"])
        observed_days = observed[: (len(observed) // slots_per_day) * slots_per_day].reshape(-1, slots_per_day, observed.shape[1]).transpose(0, 2, 1)

    if profiles.ndim != 4 or profiles.shape[0] != len(days) or profiles.shape[1] != len(methods):
        raise RuntimeError(f"Unexpected committed profile shape {profiles.shape}")
    if np.any(days < 0) or np.any(days >= len(observed_days)):
        raise RuntimeError("A locked Experiment-2 day is outside the measured workload tensor")
    event_slots = np.asarray(cfg["market"]["event_slots"], dtype=int)
    if np.any(event_slots < 0) or np.any(event_slots >= slots_per_day):
        raise ValueError("Configured event slots are outside the daily meter tensor")

    rows: list[dict[str, Any]] = []
    for day_index, day in enumerate(days):
        truth = observed_days[int(day)]
        for method_index, method in enumerate(methods):
            metrics = _daily_metrics(profiles[day_index, method_index], truth, event_slots)
            rows.append(
                {
                    "day": int(day),
                    "method": method,
                    "truth_source": TRUTH_SOURCE,
                    "event_intervention": False,
                    **metrics,
                }
            )
    daily = pd.DataFrame(rows).sort_values(["day", "method"]).reset_index(drop=True)
    daily.to_csv(final / "trace_meter_replay_daily.csv", index=False)

    summary_rows: list[dict[str, Any]] = []
    block_length = int(cfg["experiments"].get("block_length_days", 3))
    replications = min(5000, int(cfg["experiments"].get("bootstrap_replications", 5000)))
    seed = int(cfg["project"]["seed"]) + 20_000
    for method in methods:
        subset = daily[daily["method"] == method].sort_values("day")
        low, high = _moving_block_ci(subset["mae_mw"].to_numpy(), block_length, replications, seed + methods.index(method))
        summary_rows.append(
            {
                "method": method,
                "n_days": int(len(subset)),
                "mean_mae_mw": float(subset["mae_mw"].mean()),
                "median_mae_mw": float(subset["mae_mw"].median()),
                "std_mae_mw": float(subset["mae_mw"].std(ddof=1)),
                "mae_ci_low_mw": low,
                "mae_ci_high_mw": high,
                "mean_rmse_mw": float(subset["rmse_mw"].mean()),
                "mean_nrmse": float(subset["nrmse"].mean()),
                "mean_bias_mw": float(subset["bias_mw"].mean()),
                "truth_source": TRUTH_SOURCE,
                "event_intervention": False,
            }
        )
    summary = pd.DataFrame(summary_rows).sort_values("mean_mae_mw").reset_index(drop=True)
    summary.to_csv(final / "trace_meter_replay_summary.csv", index=False)
    _write_figure(summary, figures)
    metadata = {
        "experiment": "independent trace-meter replay of locked verifier profiles",
        "target_source": "processed observed_counterfactual_mw derived from measured MIT DCGM execution intervals",
        "truth_source": TRUTH_SOURCE,
        "event_intervention": False,
        "causal_interpretation": "none; this panel verifies observational trace alignment only",
        "locked_days": days.tolist(),
        "event_slots": event_slots.tolist(),
        "block_length_days": block_length,
        "bootstrap_replications": replications,
        "profiles_file": str(profiles_path.relative_to(root)),
        "profiles_checksum": hashlib.sha256(profiles_path.read_bytes()).hexdigest(),
        "daily_file": "trace_meter_replay_daily.csv",
        "summary_file": "trace_meter_replay_summary.csv",
        "figure": "fig25_trace_meter_replay.pdf",
    }
    (final / "experiment_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    if logger:
        logger.info("Experiment 20 complete: %d methods over %d locked days", len(methods), len(days))
