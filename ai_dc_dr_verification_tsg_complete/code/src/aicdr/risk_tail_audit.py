"""Tail-focused audit for the joint total/CVaR risk module."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .utils import write_json


def _cvar(values: np.ndarray, level: float) -> float:
    threshold = float(np.quantile(values, level, method="linear"))
    return float(values[values >= threshold].mean())


def run_exp28_risk_tail_audit(root: Path, cfg: dict[str, Any], logger: logging.Logger) -> None:
    """Report paired held-out tail metrics with a fixed circular block bootstrap."""
    folder = root / "experiments/exp28_risk_tail_audit"
    final = folder / "results/final"
    figures = folder / "figures"
    final.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    source = root / "experiments/exp2_baseline_verification/results/final/risk_module_ablation_daily.csv"
    if not source.exists():
        raise FileNotFoundError(f"Risk ablation daily ledger is missing: {source}")
    frame = pd.read_csv(source)
    test = frame.loc[frame["split"].eq("test")].copy()
    methods = ["total+CVaR ensemble", "total-budget-only ensemble"]
    if any(not test["ablation"].eq(method).any() for method in methods):
        raise RuntimeError("The held-out risk ablation does not contain both declared modules")
    pivot = test.pivot(index="day", columns="ablation", values="false_response_mwh").sort_index()
    oracle = test[test["ablation"].eq(methods[0])].set_index("day")["oracle_response_mwh"].sort_index()
    ratios = pd.DataFrame({method: pivot[method] / oracle.clip(lower=1e-12) for method in methods})
    level = float(cfg["experiments"].get("risk_cvar_level", 0.75))
    rows = []
    for method in methods:
        values = ratios[method].to_numpy(dtype=float)
        false_mwh = pivot[method].to_numpy(dtype=float)
        rows.append(
            {
                "ablation": method,
                "locked_test_days": int(len(values)),
                "false_credit_ratio_mean": float(values.mean()),
                "false_credit_ratio_cvar": _cvar(values, level),
                "false_credit_ratio_q90": float(np.quantile(values, 0.90)),
                "false_credit_mwh_mean": float(false_mwh.mean()),
                "false_credit_mwh_q90": float(np.quantile(false_mwh, 0.90)),
                "cvar_level": level,
            }
        )
    summary = pd.DataFrame(rows)
    summary.to_csv(final / "risk_tail_audit.csv", index=False)

    replications = int(cfg["experiments"].get("bootstrap_replications", 5000))
    block = int(cfg["experiments"].get("block_length_days", 3))
    if replications <= 0 or block <= 0 or len(ratios) % block:
        raise ValueError("Tail bootstrap requires a positive block and an integral locked-day panel")
    rng = np.random.default_rng(int(cfg["project"]["seed"]))
    joint = ratios[methods[0]].to_numpy(dtype=float)
    total = ratios[methods[1]].to_numpy(dtype=float)
    joint_mwh = pivot[methods[0]].to_numpy(dtype=float)
    total_mwh = pivot[methods[1]].to_numpy(dtype=float)
    draw_count = len(joint) // block
    bootstrap_rows: list[dict[str, Any]] = []
    for metric_name in ("false_credit_ratio_mean", "false_credit_ratio_cvar", "false_credit_ratio_q90", "false_credit_mwh_mean"):
        differences = np.empty(replications, dtype=float)
        for repetition in range(replications):
            starts = rng.integers(0, len(joint), size=draw_count)
            indices = np.concatenate([(start + np.arange(block, dtype=int)) % len(joint) for start in starts])
            if metric_name == "false_credit_ratio_mean":
                value_joint = float(joint[indices].mean())
                value_total = float(total[indices].mean())
            elif metric_name == "false_credit_ratio_cvar":
                value_joint = _cvar(joint[indices], level)
                value_total = _cvar(total[indices], level)
            elif metric_name == "false_credit_ratio_q90":
                value_joint = float(np.quantile(joint[indices], 0.90))
                value_total = float(np.quantile(total[indices], 0.90))
            else:
                value_joint = float(joint_mwh[indices].mean())
                value_total = float(total_mwh[indices].mean())
            differences[repetition] = value_joint - value_total
        bootstrap_rows.append(
            {
                "metric": metric_name,
                "joint_minus_total_mean": float(differences.mean()),
                "ci_2.5": float(np.quantile(differences, 0.025)),
                "ci_97.5": float(np.quantile(differences, 0.975)),
                "bootstrap_replications": replications,
                "block_length_days": block,
            }
        )
    bootstrap = pd.DataFrame(bootstrap_rows)
    bootstrap.to_csv(final / "risk_tail_paired_bootstrap.csv", index=False)
    selected = summary.loc[summary["ablation"].eq(methods[0])].iloc[0]
    metadata = {
        "experiment": "held-out tail-risk audit for the total-plus-CVaR module",
        "source_file": str(source.relative_to(root)),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "locked_test_days": int(len(ratios)),
        "risk_cvar_metric": "daily_false_credit_ratio",
        "risk_cvar_level": level,
        "joint_module": methods[0],
        "comparison_module": methods[1],
        "joint_mean_false_credit_ratio": float(selected["false_credit_ratio_mean"]),
        "joint_cvar_false_credit_ratio": float(selected["false_credit_ratio_cvar"]),
        "joint_q90_false_credit_ratio": float(selected["false_credit_ratio_q90"]),
        "paired_bootstrap": "circular contiguous blocks over the 54 locked days; no post-hoc module selection",
        "files": {"summary": "risk_tail_audit.csv", "bootstrap": "risk_tail_paired_bootstrap.csv", "figure": "fig_risk_tail_tradeoff.pdf"},
    }
    write_json(final / "experiment_metadata.json", metadata)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    metrics = ["false_credit_ratio_mean", "false_credit_ratio_cvar", "false_credit_ratio_q90"]
    labels = ["Mean", "CVaR$_{0.75}$", "90th percentile"]
    x = np.arange(len(metrics))
    width = 0.35
    joint_values = [float(summary.loc[summary["ablation"].eq(methods[0]), metric].iloc[0]) for metric in metrics]
    total_values = [float(summary.loc[summary["ablation"].eq(methods[1]), metric].iloc[0]) for metric in metrics]
    fig, ax = plt.subplots(figsize=(7.1, 3.45), constrained_layout=True)
    ax.bar(x - width / 2, joint_values, width, label="Total + CVaR", color="#0072B2")
    ax.bar(x + width / 2, total_values, width, label="Total budget only", color="#D55E00")
    ax.set_xticks(x, labels)
    ax.set_ylabel("False-credit ratio")
    ax.set_title("Held-out tail control under the paired risk ablation")
    ax.grid(axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False, fontsize=8)
    for suffix in ("png", "pdf"):
        fig.savefig(figures / f"fig_risk_tail_tradeoff.{suffix}", dpi=320, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    logger.info("Exp28 risk tail audit [100%%]: mean ratio joint=%.4f, paired bootstrap complete", float(selected["false_credit_ratio_mean"]))

