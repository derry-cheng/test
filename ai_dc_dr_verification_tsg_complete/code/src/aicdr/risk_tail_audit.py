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


def _tail_count(sample_size: int, level: float) -> int:
    """Use the contract's integer tail mass, including in bootstrap samples."""
    if sample_size <= 0 or not np.isfinite(level) or not 0.0 <= level < 1.0:
        raise ValueError("CVaR requires a nonempty sample and 0 <= level < 1")
    return max(1, int(np.ceil((1.0 - level) * sample_size)))


def _cvar(values: np.ndarray, level: float) -> float:
    """Mean of exactly the largest m observations, m=ceil((1-level)*n).

    This is the integer-tail epigraph convention used by the fitted contract,
    not an average of all observations above an interpolated quantile. The
    distinction matters when resampling introduces ties at the cutoff.
    """
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or not np.isfinite(values).all():
        raise ValueError("CVaR requires a finite one-dimensional sample")
    tail_count = _tail_count(len(values), level)
    return float(np.sort(values)[-tail_count:].mean())


def _paired_locked_panel(
    frame: pd.DataFrame, methods: list[str], expected_days: int
) -> tuple[pd.DataFrame, pd.Series]:
    """Fail closed on an incomplete pairing or inconsistent truth denominator."""
    test = frame.loc[frame["split"].eq("test") & frame["ablation"].isin(methods)].copy()
    if test.duplicated(["day", "ablation"]).any():
        raise ValueError("Tail audit has duplicate day/method rows")
    pivot = test.pivot(index="day", columns="ablation", values="false_response_mwh").sort_index()
    if set(pivot.columns) != set(methods) or len(pivot) != expected_days:
        raise ValueError("Tail audit does not contain the complete declared locked panel")
    pivot = pivot.loc[:, methods]
    oracle = test.pivot(index="day", columns="ablation", values="oracle_response_mwh").sort_index()
    oracle = oracle.reindex(index=pivot.index, columns=methods)
    if not np.isfinite(pivot.to_numpy(dtype=float)).all() or not np.isfinite(oracle.to_numpy(dtype=float)).all():
        raise ValueError("Tail audit requires finite, fully paired day/method data")
    if (pivot.to_numpy(dtype=float) < 0.0).any() or (oracle.to_numpy(dtype=float) < 0.0).any():
        raise ValueError("Tail audit requires nonnegative false credit and oracle response")
    if not np.allclose(oracle.to_numpy(dtype=float), oracle[methods[0]].to_numpy(dtype=float)[:, None], rtol=0.0, atol=1e-10):
        raise ValueError("Tail audit oracle response differs across paired methods")
    return pivot, oracle[methods[0]]


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
    methods = [
        "total+CVaR ensemble",
        "total-budget-only ensemble",
        "CVaR-only ensemble",
    ]
    pivot, oracle = _paired_locked_panel(
        frame, methods, int(cfg["experiments"].get("test_days", 54))
    )
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
                "false_credit_mwh_cvar": _cvar(false_mwh, level),
                "false_credit_mwh_q90": float(np.quantile(false_mwh, 0.90)),
                "cvar_level": level,
                "cvar_tail_days": _tail_count(len(values), level),
                "cvar_convention": "mean_of_largest_m",
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
    joint_mwh = pivot[methods[0]].to_numpy(dtype=float)
    draw_count = len(joint) // block
    bootstrap_rows: list[dict[str, Any]] = []
    # The joint model is compared with both single-axis controls.  We report
    # absolute MWh and normalized ratio metrics because a ratio alone can hide
    # the system-level scale of the credited response.
    for comparator in methods[1:]:
        comparator_ratio = ratios[comparator].to_numpy(dtype=float)
        comparator_mwh = pivot[comparator].to_numpy(dtype=float)
        for metric_name in (
            "false_credit_ratio_mean",
            "false_credit_ratio_cvar",
            "false_credit_ratio_q90",
            "false_credit_mwh_mean",
            "false_credit_mwh_cvar",
            "false_credit_mwh_q90",
        ):
            differences = np.empty(replications, dtype=float)
            for repetition in range(replications):
                starts = rng.integers(0, len(joint), size=draw_count)
                indices = np.concatenate(
                    [(start + np.arange(block, dtype=int)) % len(joint) for start in starts]
                )
                if metric_name == "false_credit_ratio_mean":
                    value_joint = float(joint[indices].mean())
                    value_comparator = float(comparator_ratio[indices].mean())
                elif metric_name == "false_credit_ratio_cvar":
                    value_joint = _cvar(joint[indices], level)
                    value_comparator = _cvar(comparator_ratio[indices], level)
                elif metric_name == "false_credit_ratio_q90":
                    value_joint = float(np.quantile(joint[indices], 0.90))
                    value_comparator = float(np.quantile(comparator_ratio[indices], 0.90))
                elif metric_name == "false_credit_mwh_mean":
                    value_joint = float(joint_mwh[indices].mean())
                    value_comparator = float(comparator_mwh[indices].mean())
                elif metric_name == "false_credit_mwh_cvar":
                    value_joint = _cvar(joint_mwh[indices], level)
                    value_comparator = _cvar(comparator_mwh[indices], level)
                else:
                    value_joint = float(np.quantile(joint_mwh[indices], 0.90))
                    value_comparator = float(np.quantile(comparator_mwh[indices], 0.90))
                differences[repetition] = value_joint - value_comparator
            bootstrap_rows.append(
                {
                    "comparison": comparator,
                    "metric": metric_name,
                    "joint_minus_comparator_point_estimate": float(
                        summary.loc[summary["ablation"].eq(methods[0]), metric_name].iloc[0]
                        - summary.loc[summary["ablation"].eq(comparator), metric_name].iloc[0]
                    ),
                    # Retained for compatibility; this is a bootstrap mean,
                    # not the observed paired point estimate.
                    "joint_minus_comparator_mean": float(differences.mean()),
                    "bootstrap_mean_difference": float(differences.mean()),
                    "ci_2.5": float(np.quantile(differences, 0.025)),
                    "ci_97.5": float(np.quantile(differences, 0.975)),
                    "bootstrap_replications": replications,
                    "block_length_days": block,
                    "interval_type": "unadjusted_exploratory_percentile_95",
                    "multiplicity_adjusted": False,
                    "cvar_tail_days": _tail_count(len(joint), level),
                }
            )
    bootstrap = pd.DataFrame(bootstrap_rows)
    bootstrap.to_csv(final / "risk_tail_paired_bootstrap.csv", index=False)
    selected = summary.loc[summary["ablation"].eq(methods[0])].iloc[0]
    metadata = {
        "schema_version": 2,
        "experiment": "held-out tail-risk audit for the total-plus-CVaR module",
        "implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "bootstrap_seed": int(cfg["project"]["seed"]),
        "bootstrap_replications": replications,
        "block_length_days": block,
        "cvar_convention": "mean of exactly the largest m=ceil((1-level)*n) observations, including bootstrap ties",
        "cvar_tail_days": _tail_count(len(ratios), level),
        "confidence_interval": "unadjusted exploratory 95% percentile circular-block bootstrap interval",
        "multiplicity_adjusted": False,
        "holm_scope": "separate exact block-sign test families in Exp2; no Holm adjustment is applied to these percentile intervals",
        "point_estimate_column": "joint_minus_comparator_point_estimate",
        "bootstrap_mean_column": "bootstrap_mean_difference",
        "selection_boundary": "the previously locked Exp2 profiles are evaluated without refitting, retuning, or locked-test selection",
        "source_file": str(source.relative_to(root)),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "locked_test_days": int(len(ratios)),
        "risk_cvar_metric": "daily_false_credit_ratio and daily_false_credit_mwh",
        "risk_cvar_level": level,
        "joint_module": methods[0],
        "comparison_modules": methods[1:],
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

    metric_groups = [
        ("false_credit_ratio_mean", "false_credit_ratio_cvar", "false_credit_ratio_q90", "False-credit ratio"),
        ("false_credit_mwh_mean", "false_credit_mwh_cvar", "false_credit_mwh_q90", "False-credit energy (MWh)"),
    ]
    labels = ["Mean", f"CVaR$_{{{level:.2f}}}$", "90th percentile"]
    colors = {methods[0]: "#0072B2", methods[1]: "#D55E00", methods[2]: "#009E73"}
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 3.15), constrained_layout=True)
    x = np.arange(3)
    width = 0.24
    for ax, (mean_key, cvar_key, q90_key, ylabel) in zip(axes, metric_groups):
        metric_keys = [mean_key, cvar_key, q90_key]
        for index, method in enumerate(methods):
            values = [float(summary.loc[summary["ablation"].eq(method), key].iloc[0]) for key in metric_keys]
            ax.bar(x + (index - 1) * width, values, width, label=method.replace(" ensemble", ""), color=colors[method])
        ax.set_xticks(x, labels)
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", alpha=0.25)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    axes[0].set_title("Normalized scale")
    axes[1].set_title("Absolute scale")
    axes[1].legend(frameon=False, fontsize=7, loc="upper left")
    fig.suptitle("Held-out tail-risk audit across the paired ablations", fontsize=10)
    for suffix in ("png", "pdf"):
        fig.savefig(figures / f"fig_risk_tail_tradeoff.{suffix}", dpi=320, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    logger.info("Exp28 risk tail audit [100%%]: mean ratio joint=%.4f, paired bootstrap complete", float(selected["false_credit_ratio_mean"]))
