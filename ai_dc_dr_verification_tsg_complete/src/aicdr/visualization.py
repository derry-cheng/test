from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns


COLORS = {
    "blue": "#0072B2",
    "orange": "#E69F00",
    "green": "#009E73",
    "red": "#D55E00",
    "purple": "#CC79A7",
    "sky": "#56B4E9",
    "yellow": "#F0E442",
    "black": "#222222",
}


def configure_style(cfg: dict[str, Any]) -> None:
    sns.set_theme(style="whitegrid", context="paper", palette=cfg["visualization"]["palette"])
    mpl.rcParams.update(
        {
            "font.family": cfg["visualization"]["font_family"],
            "font.size": 11,
            "axes.titlesize": 12,
            "axes.labelsize": 11,
            "legend.fontsize": 9.5,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": cfg["visualization"]["dpi"],
            "savefig.dpi": cfg["visualization"]["dpi"],
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def save_figure(fig: plt.Figure, folder: Path, stem: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    temporary_paths: list[Path] = []
    try:
        for suffix in ("png", "pdf"):
            final_path = folder / f"{stem}.{suffix}"
            temporary_path = folder / f".{stem}.{suffix}.tmp"
            temporary_paths.append(temporary_path)
            fig.savefig(
                temporary_path,
                format=suffix,
                bbox_inches="tight",
                facecolor="white",
            )
            temporary_path.replace(final_path)
    finally:
        for temporary_path in temporary_paths:
            temporary_path.unlink(missing_ok=True)
        plt.close(fig)


def plot_exp8(
    daily: pd.DataFrame,
    interval_results: pd.DataFrame,
    folder: Path,
    cfg: dict[str, Any],
) -> None:
    """Plot security-aware settlement accuracy and contingency utilization."""
    configure_style(cfg)
    label_map = {
        "Base-case exact net value": "Base-case\nexact value",
        "N-1 signed linear": "N-1 linear",
        "N-1 exact net value": "N-1 exact value",
    }
    quality_map = {
        "Trace-Anchored Reference": "Trace reference",
        "Risk-Constrained Convex Verifier": "Workload verifier",
    }
    displayed = daily.assign(
        mechanism_label=daily["mechanism"].map(label_map),
        quality_label=daily["baseline_quality"].map(quality_map),
    )
    order = [label_map[key] for key in label_map]
    fig, axes = plt.subplots(
        1, 3, figsize=(12.6, 3.7), constrained_layout=True
    )
    sns.boxplot(
        data=displayed,
        x="mechanism_label",
        y="absolute_error_usd",
        hue="quality_label",
        order=order,
        showfliers=False,
        palette=[COLORS["blue"], COLORS["orange"]],
        ax=axes[0],
    )
    axes[0].set_title("(a) Security-aware payment error")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Daily absolute error ($)")
    axes[0].legend(title="Counterfactual", fontsize=7, title_fontsize=7)
    oracle = displayed[
        displayed["baseline_quality"] == "Trace-Anchored Reference"
    ]
    sns.ecdfplot(
        data=oracle,
        x="absolute_error_usd",
        hue="mechanism_label",
        hue_order=order,
        palette=[COLORS["red"], COLORS["green"], COLORS["blue"]],
        ax=axes[1],
    )
    axes[1].set_title("(b) Mechanism-isolation error distribution")
    axes[1].set_xlabel("Daily absolute error ($)")
    axes[1].set_ylabel("Empirical cumulative probability")
    axes[1].legend(
        title="Settlement",
        labels=["N-1 exact value", "N-1 linear", "Base-case exact value"],
        fontsize=7,
        title_fontsize=7,
    )
    loading = interval_results.drop_duplicates(
        ["day", "event_slot", "baseline_quality"]
    )
    loading_long = loading.melt(
        id_vars=["baseline_quality"],
        value_vars=["base_case_max_loading", "n1_base_case_max_loading"],
        var_name="dispatch",
        value_name="maximum_base_case_loading",
    )
    loading_long["dispatch"] = loading_long["dispatch"].map(
        {
            "base_case_max_loading": "Base-case dispatch",
            "n1_base_case_max_loading": "N-1 secure dispatch",
        }
    )
    sns.boxplot(
        data=loading_long,
        x="dispatch",
        y="maximum_base_case_loading",
        hue="baseline_quality",
        showfliers=False,
        palette=[COLORS["blue"], COLORS["orange"]],
        ax=axes[2],
    )
    axes[2].axhline(1.0, color=COLORS["red"], linestyle="--", linewidth=1)
    axes[2].set_ylim(0.68, 1.02)
    axes[2].set_title("(c) Security-constrained network loading")
    axes[2].set_xlabel("")
    axes[2].set_ylabel("Maximum base-case loading (p.u.)")
    axes[2].text(
        0.03,
        0.87,
        "37 non-islanding outages enforced\n"
        "Max post-contingency loading: 1.000 p.u.",
        transform=axes[2].transAxes,
        va="top",
        fontsize=6.5,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 1.5},
    )
    axes[2].legend(
        title="Counterfactual",
        labels=["Trace reference", "Workload verifier"],
        fontsize=7,
        title_fontsize=7,
    )
    save_figure(fig, folder, "fig13_n1_security_validation")


def plot_exp9(
    certificates: pd.DataFrame,
    scenario_certificates: pd.DataFrame,
    daily: pd.DataFrame,
    folder: Path,
    cfg: dict[str, Any],
) -> None:
    """Plot robust payment certificates and independently evaluated outcomes."""
    configure_style(cfg)
    order = [
        "Feasible Quantile Projection",
        "Single Feasible Projection",
        "Risk-Constrained Convex Verifier",
        "Payment-Certified N-1 Verifier",
    ]
    labels = {
        "Feasible Quantile Projection": "Feasible\nquantile",
        "Single Feasible Projection": "Single\nprojection",
        "Risk-Constrained Convex Verifier": "Risk-constrained\nverifier",
        "Payment-Certified N-1 Verifier": "Payment-certified\nverifier",
    }
    shown = daily.copy()
    shown["method_label"] = shown["counterfactual_method"].map(labels)
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.65), constrained_layout=True)
    sns.boxplot(
        data=shown,
        x="method_label",
        y="absolute_error_usd",
        order=[labels[value] for value in order],
        showfliers=False,
        color=COLORS["sky"],
        ax=axes[0],
    )
    axes[0].set_title("(a) Independent payment accuracy")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Daily absolute error ($)")
    sns.boxplot(
        data=shown,
        x="method_label",
        y="overpayment_usd",
        order=[labels[value] for value in order],
        showfliers=False,
        color=COLORS["orange"],
        ax=axes[1],
    )
    axes[1].set_title("(b) Overpayment against realized value")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Daily overpayment ($)")
    sns.scatterplot(
        data=scenario_certificates,
        x="reference_n1_baseline_cost_usd",
        y="certified_n1_baseline_cost_usd",
        hue="conversion_scenario",
        palette="viridis",
        s=24,
        alpha=0.72,
        edgecolor="white",
        linewidth=0.25,
        ax=axes[2],
    )
    lower = float(
        min(
            scenario_certificates["reference_n1_baseline_cost_usd"].min(),
            scenario_certificates["certified_n1_baseline_cost_usd"].min(),
        )
    )
    upper = float(
        max(
            scenario_certificates["reference_n1_baseline_cost_usd"].max(),
            scenario_certificates["certified_n1_baseline_cost_usd"].max(),
        )
    )
    axes[2].plot([lower, upper], [lower, upper], "--", color=COLORS["red"], linewidth=1)
    axes[2].set_title("(c) Robust daily payment certificates")
    axes[2].set_xlabel("Reference N-1 baseline cost ($)")
    axes[2].set_ylabel("Certified N-1 baseline cost ($)")
    axes[2].text(
        0.04,
        0.96,
        "All held-out conversion scenarios",
        transform=axes[2].transAxes,
        va="top",
        fontsize=7,
    )
    axes[2].legend(
        title="Energy-ratio quantile", fontsize=6.5, title_fontsize=6.5
    )
    save_figure(fig, folder, "fig14_payment_certificate")


def plot_exp13_real_trace_replay(
    daily: pd.DataFrame,
    trace: pd.DataFrame,
    folder: Path,
    cfg: dict[str, Any],
) -> None:
    """Visualize the observational replay against the measured execution trace."""
    configure_style(cfg)
    order = [
        "Batch-only minimum-cost schedule",
        "Batch-only trace-constrained verifier",
    ]
    labels = {
        "Batch-only minimum-cost schedule": "Batch minimum-cost",
        "Batch-only trace-constrained verifier": "Batch trace-constrained",
    }
    shown = daily.copy()
    shown["method_label"] = shown["method"].map(labels).fillna(shown["method"])
    fig, axes = plt.subplots(1, 3, figsize=(12.8, 3.7), constrained_layout=True)
    sns.boxplot(
        data=shown,
        x="method_label",
        y="mae_mw",
        order=[labels.get(value, value) for value in order],
        showfliers=False,
        color=COLORS["sky"],
        ax=axes[0],
    )
    axes[0].set_title("(a) Observational replay error")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Daily mean absolute error (MW)")
    axes[0].tick_params(axis="x", rotation=18)
    sns.ecdfplot(
        data=shown,
        x="energy_abs_mwh",
        hue="method_label",
        hue_order=[labels.get(value, value) for value in order],
        palette=[COLORS["purple"], COLORS["blue"]],
        ax=axes[1],
    )
    axes[1].set_title("(b) Absolute energy mismatch")
    axes[1].set_xlabel("Daily absolute energy mismatch (MWh)")
    axes[1].set_ylabel("Empirical cumulative probability")
    handles, legend_labels = axes[1].get_legend_handles_labels()
    if handles:
        axes[1].legend(
            handles,
            legend_labels,
            title="Verifier",
            fontsize=7,
            title_fontsize=7,
        )
    representative_day = int(trace["day"].min())
    representative = trace[trace["day"] == representative_day].sort_values("slot")
    axes[2].plot(
        representative["slot"],
        representative["observed_total_mw"],
        color=COLORS["black"],
        linewidth=1.6,
        label="Measured execution",
    )
    axes[2].plot(
        representative["slot"],
        representative["trace_constrained_total_mw"],
        color=COLORS["blue"],
        linewidth=1.1,
        label="Trace-constrained verifier",
    )
    axes[2].set_title("(c) Locked-day trace overlay")
    axes[2].set_xlabel("15-minute slot")
    axes[2].set_ylabel("Four-site total power (MW)")
    axes[2].legend(fontsize=7)
    save_figure(fig, folder, "fig19_real_trace_replay")


def plot_exp14_job_level_fidelity(
    slot_profile: pd.DataFrame,
    summary: pd.DataFrame,
    folder: Path,
    cfg: dict[str, Any],
) -> None:
    """Visualize exact job-flow feasibility and aggregate fidelity."""
    configure_style(cfg)
    fig, axes = plt.subplots(1, 3, figsize=(12.6, 3.7), constrained_layout=True)
    sns.lineplot(
        data=slot_profile,
        x="slot",
        y="target_mwh",
        hue="region",
        palette="colorblind",
        linewidth=1.0,
        ax=axes[0],
    )
    axes[0].set_title("(a) Measured batch energy target")
    axes[0].set_xlabel("15-minute slot")
    axes[0].set_ylabel("Target energy (MWh)")
    axes[0].legend(title="Region", fontsize=7, title_fontsize=7)
    sns.lineplot(
        data=slot_profile,
        x="slot",
        y="absolute_residual_mwh",
        hue="region",
        palette="colorblind",
        linewidth=1.0,
        ax=axes[1],
    )
    axes[1].set_title("(b) Exact flow residual")
    axes[1].set_xlabel("15-minute slot")
    axes[1].set_ylabel("Absolute residual (MWh)")
    axes[1].legend(title="Region", fontsize=7, title_fontsize=7)
    bars = summary.set_index("metric")["value"]
    names = ["Jobs", "Flow residual", "Deadline residual", "Capacity slack"]
    values = [
        float(bars.get("jobs", 0.0)),
        float(bars.get("maximum_slot_residual_mwh", 0.0)),
        float(bars.get("maximum_job_completion_residual_mwh", 0.0)),
        float(bars.get("minimum_capacity_slack_mwh", 0.0)),
    ]
    axes[2].bar(names, values, color=[COLORS["blue"], COLORS["green"], COLORS["orange"], COLORS["purple"]])
    axes[2].set_title("(c) Job-level feasibility certificate")
    axes[2].set_ylabel("Value (native units)")
    axes[2].tick_params(axis="x", rotation=22)
    save_figure(fig, folder, "fig20_job_level_fidelity")


def plot_exp15_interval_certificate(
    endpoints: pd.DataFrame,
    folder: Path,
    cfg: dict[str, Any],
    intervals: pd.DataFrame | None = None,
) -> None:
    """Visualize endpoint costs and the workload-hull payment interval."""
    configure_style(cfg)
    shown = endpoints.copy()
    ncols = 3 if intervals is not None and not intervals.empty else 2
    fig, axes = plt.subplots(
        1,
        ncols,
        figsize=(13.0 if ncols == 3 else 10.4, 3.7),
        constrained_layout=True,
    )
    sns.scatterplot(
        data=shown,
        x="reference_cost_usd",
        y="certified_cost_usd",
        hue="endpoint",
        style="method",
        palette="colorblind",
        s=35,
        alpha=0.8,
        ax=axes[0],
    )
    lower = min(float(shown["reference_cost_usd"].min()), float(shown["certified_cost_usd"].min()))
    upper = max(float(shown["reference_cost_usd"].max()), float(shown["certified_cost_usd"].max()))
    axes[0].plot([lower, upper], [lower, upper], "--", color=COLORS["red"], linewidth=1)
    axes[0].set_title("(a) Endpoint N-1 cost certificate")
    axes[0].set_xlabel("Reference cost ($)")
    axes[0].set_ylabel("Certified cost ($)")
    axes[0].legend(fontsize=6.5, title_fontsize=6.5)
    margin = shown.groupby(["method", "endpoint"], as_index=False)["margin_usd"].mean()
    sns.barplot(data=margin, x="endpoint", y="margin_usd", hue="method", palette="colorblind", ax=axes[1])
    axes[1].axhline(0, color=COLORS["black"], linewidth=0.8)
    axes[1].set_title("(b) Endpoint payment-cap margin")
    axes[1].set_xlabel("Held-out conversion interval endpoint")
    axes[1].set_ylabel("Reference minus certified cost ($)")
    axes[1].legend(fontsize=6.5, title_fontsize=6.5)
    if ncols == 3:
        sns.boxplot(
            data=intervals,
            x="endpoint",
            y="payment_interval_width_usd",
            color=COLORS["sky"],
            width=0.55,
            fliersize=2,
            ax=axes[2],
        )
        axes[2].set_title("(c) Workload-hull payment uncertainty")
        axes[2].set_xlabel("Held-out conversion endpoint")
        axes[2].set_ylabel("Interval width ($/day)")
    save_figure(fig, folder, "fig21_interval_payment_certificate")


def plot_exp16_ledger_capacity(
    summary: dict[str, Any],
    capacity: pd.DataFrame,
    folder: Path,
    cfg: dict[str, Any],
) -> None:
    """Plot source provenance, raw-to-joined conservation, and capacity envelope."""
    configure_style(cfg)
    fig, axes = plt.subplots(1, 3, figsize=(12.4, 3.6), constrained_layout=True)

    integrity = pd.DataFrame(
        {
            "check": [
                "Release ≤ execution start",
                "Execution start < end",
                "Positive energy join",
                "Raw-to-join energy",
                "No synthetic rows",
                "No imputation",
            ],
            "value": [
                float(summary["integrity_conditions"]["release_before_start"]),
                float(summary["integrity_conditions"]["start_before_end"]),
                float(summary["integrity_conditions"]["positive_energy_join_only"]),
                float(summary["integrity_conditions"]["raw_to_join_energy_conservation"]),
                float(summary["integrity_conditions"]["no_synthetic_rows"]),
                float(summary["integrity_conditions"]["no_imputation"]),
            ],
        }
    )
    axes[0].barh(integrity["check"], integrity["value"], color=COLORS["green"])
    axes[0].set_xlim(0, 1.05)
    axes[0].set_xlabel("Verified condition (1 = pass)")
    axes[0].set_title("(a) Ledger integrity certificate")
    axes[0].tick_params(axis="y", labelsize=8)

    energy_values = [
        summary["positive_dcgm_energy_j"],
        summary["retained_join_energy_j"],
        summary["joined_energy_sum_j"],
    ]
    bars = axes[1].bar(
        ["Positive DCGM", "Retained IDs", "Joined ledger"],
        energy_values,
        color=[COLORS["blue"], COLORS["sky"], COLORS["orange"]],
    )
    axes[1].set_title("(b) Independent energy conservation")
    axes[1].set_ylabel("Energy (J)")
    axes[1].tick_params(axis="x", labelsize=8)
    axes[1].ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    axes[1].bar_label(bars, fmt="%.2e", padding=2, fontsize=7)

    displayed = capacity.copy()
    x = np.arange(len(displayed))
    width = 0.20
    axes[2].bar(x - width, displayed["scaled_benchmark_p95_mw"], width, label="Scaled benchmark P95", color=COLORS["sky"])
    axes[2].bar(x, displayed["scaled_benchmark_p99_mw"], width, label="Scaled benchmark P99", color=COLORS["orange"])
    axes[2].bar(x + width, displayed["scaled_benchmark_peak_mw"], width, label="Scaled benchmark peak", color=COLORS["red"])
    axes[2].axhline(
        float(displayed["configured_flexible_capacity_mw"].iloc[0]),
        color=COLORS["black"],
        linestyle="--",
        linewidth=1.0,
        label="Configured capacity",
    )
    axes[2].set_xticks(x, [f"Region {int(v)}" for v in displayed["region"]])
    axes[2].set_ylabel("Flexible power (MW)")
    axes[2].set_title("(c) Scaled benchmark envelope; raw replay reported separately")
    axes[2].legend(fontsize=7, loc="upper left")
    save_figure(fig, folder, "fig22_ledger_capacity_provenance")


def plot_exp10(
    results: pd.DataFrame,
    folder: Path,
    cfg: dict[str, Any],
) -> None:
    """Plot nonlinear AC OPF accuracy and physical feasibility."""
    configure_style(cfg)
    label_map = {
        "Feasible Quantile Projection": "Feasible quantile",
        "Single Feasible Projection": "Single projection",
        "Risk-Constrained Convex Verifier": "Risk verifier",
        "Payment-Certified N-1 Verifier": "Payment certificate",
    }
    shown = results.assign(
        method_label=results["counterfactual_method"].map(label_map)
    )
    order = list(label_map.values())
    fig, axes = plt.subplots(1, 3, figsize=(13.0, 3.8), constrained_layout=True)
    sns.barplot(
        data=shown,
        x="network",
        y="absolute_error_usd_per_h",
        hue="method_label",
        hue_order=order,
        errorbar=("ci", 95),
        palette=[
            COLORS["purple"],
            COLORS["orange"],
            COLORS["blue"],
            COLORS["green"],
        ],
        ax=axes[0],
    )
    axes[0].set_title("(a) Nonlinear AC value error")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Mean absolute error ($/h)")
    axes[0].tick_params(axis="x", rotation=20)
    axes[0].legend(title="Counterfactual", fontsize=6.5, title_fontsize=7)
    sns.boxplot(
        data=shown,
        x="network",
        y="maximum_apparent_line_loading",
        hue="method_label",
        hue_order=order,
        showfliers=False,
        palette=[
            COLORS["purple"],
            COLORS["orange"],
            COLORS["blue"],
            COLORS["green"],
        ],
        ax=axes[1],
    )
    axes[1].axhline(1.0, color=COLORS["red"], linestyle="--", linewidth=1)
    axes[1].set_title("(b) AC apparent-power loading")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Maximum branch loading (p.u.)")
    axes[1].tick_params(axis="x", rotation=20)
    axes[1].get_legend().remove()
    voltage = (
        shown.groupby(["network", "method_label"], as_index=False)[
            "maximum_voltage_violation_pu"
        ].max()
    )
    sns.barplot(
        data=voltage,
        x="network",
        y="maximum_voltage_violation_pu",
        hue="method_label",
        hue_order=order,
        palette=[
            COLORS["purple"],
            COLORS["orange"],
            COLORS["blue"],
            COLORS["green"],
        ],
        ax=axes[2],
    )
    axes[2].set_title("(c) AC voltage-limit certificate")
    axes[2].set_xlabel("")
    axes[2].set_ylabel("Maximum voltage violation (p.u.)")
    axes[2].tick_params(axis="x", rotation=20)
    axes[2].get_legend().remove()
    save_figure(fig, folder, "fig15_ac_opf_validation")


def plot_exp10_n1(
    results: pd.DataFrame,
    folder: Path,
    cfg: dict[str, Any],
) -> None:
    """Plot complete nonlinear AC post-contingency feasibility results."""
    configure_style(cfg)
    label_map = {
        "Feasible Quantile Projection": "Feasible quantile",
        "Single Feasible Projection": "Single projection",
        "Risk-Constrained Convex Verifier": "Risk verifier",
        "Payment-Certified N-1 Verifier": "Payment certificate",
    }
    shown = results.assign(
        method_label=results["counterfactual_method"].map(label_map)
    )
    order = list(label_map.values())
    palette = [
        COLORS["purple"],
        COLORS["orange"],
        COLORS["blue"],
        COLORS["green"],
    ]
    fig, axes = plt.subplots(
        1, 3, figsize=(12.6, 3.7), constrained_layout=True
    )
    sns.boxplot(
        data=shown,
        x="method_label",
        y="maximum_apparent_line_loading",
        order=order,
        palette=palette,
        showfliers=False,
        hue="method_label",
        legend=False,
        ax=axes[0],
    )
    axes[0].axhline(1.0, color=COLORS["red"], linestyle="--", linewidth=1)
    axes[0].set_title("(a) All non-islanding line outages")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Maximum AC branch loading (p.u.)")
    axes[0].tick_params(axis="x", rotation=15)
    voltage_long = shown.melt(
        id_vars=["method_label", "day", "outage"],
        value_vars=["minimum_voltage_pu", "maximum_voltage_pu"],
        var_name="voltage_bound",
        value_name="voltage_pu",
    )
    voltage_long["voltage_bound"] = voltage_long["voltage_bound"].map(
        {
            "minimum_voltage_pu": "Minimum",
            "maximum_voltage_pu": "Maximum",
        }
    )
    sns.boxplot(
        data=voltage_long,
        x="method_label",
        y="voltage_pu",
        hue="voltage_bound",
        order=order,
        palette=[COLORS["purple"], COLORS["sky"]],
        showfliers=False,
        ax=axes[1],
    )
    axes[1].set_title("(b) Post-contingency voltage envelope")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Bus-voltage magnitude (p.u.)")
    axes[1].tick_params(axis="x", rotation=15)
    axes[1].legend(title="", fontsize=7)
    sns.boxplot(
        data=shown,
        x="network",
        y="maximum_apparent_line_loading",
        hue="method_label",
        palette=palette,
        showfliers=False,
        ax=axes[2],
    )
    axes[2].axhline(1.0, color=COLORS["red"], linestyle="--", linewidth=1)
    axes[2].set_title("(c) Network-level outage envelope")
    axes[2].set_xlabel("")
    axes[2].set_ylabel("Maximum AC branch loading (p.u.)")
    axes[2].legend(
        title="Counterfactual", fontsize=6.5, title_fontsize=7
    )
    save_figure(fig, folder, "fig15b_ac_n1_contingency_validation")


def plot_exp10_preventive(
    results: pd.DataFrame,
    folder: Path,
    cfg: dict[str, Any],
) -> None:
    """Plot the shared-active-plan preventive AC contingency certificate."""
    configure_style(cfg)
    label_map = {
        "Feasible Quantile Projection": "Feasible quantile",
        "Single Feasible Projection": "Single projection",
        "Risk-Constrained Convex Verifier": "Risk verifier",
        "Payment-Certified N-1 Verifier": "Payment certificate",
    }
    shown = results.assign(
        method_label=results["counterfactual_method"].map(label_map),
        penetration_pct=100.0 * results["peak_dc_penetration"],
    )
    palette = [
        COLORS["purple"],
        COLORS["orange"],
        COLORS["blue"],
        COLORS["green"],
    ]
    fig, axes = plt.subplots(
        1, 3, figsize=(12.6, 3.7), constrained_layout=True
    )
    sns.lineplot(
        data=shown,
        x="penetration_pct",
        y="maximum_apparent_line_loading",
        hue="method_label",
        palette=palette,
        estimator="max",
        errorbar=None,
        marker="o",
        ax=axes[0],
    )
    axes[0].axhline(1.0, color=COLORS["red"], linestyle="--", linewidth=1)
    axes[0].set_title("(a) Preventive outage loading envelope")
    axes[0].set_xlabel("Peak data-center penetration (%)")
    axes[0].set_ylabel("Maximum AC branch loading (p.u.)")
    axes[0].legend(title="Counterfactual", fontsize=6.3, title_fontsize=6.5)
    voltage = (
        shown.groupby(
            ["penetration_pct", "method_label"], as_index=False
        )["maximum_voltage_violation_pu"]
        .max()
    )
    sns.lineplot(
        data=voltage,
        x="penetration_pct",
        y="maximum_voltage_violation_pu",
        hue="method_label",
        palette=palette,
        marker="o",
        ax=axes[1],
    )
    axes[1].set_title("(b) Preventive voltage certificate")
    axes[1].set_xlabel("Peak data-center penetration (%)")
    axes[1].set_ylabel("Maximum voltage violation (p.u.)")
    axes[1].get_legend().remove()
    recourse = shown.assign(
        absolute_reference_loss_recourse_mw=np.abs(
            shown["reference_generator_loss_recourse_mw"]
        )
    )
    sns.boxplot(
        data=recourse,
        x="penetration_pct",
        y="absolute_reference_loss_recourse_mw",
        hue="method_label",
        palette=palette,
        showfliers=False,
        ax=axes[2],
    )
    axes[2].set_title("(c) AC-loss balancing recourse")
    axes[2].set_xlabel("Peak data-center penetration (%)")
    axes[2].set_ylabel("Reference-generator recourse (MW)")
    axes[2].legend(title="Counterfactual", fontsize=6.3, title_fontsize=6.5)
    save_figure(fig, folder, "fig15c_preventive_ac_n1_validation")


def plot_cross_layer_robustness(
    conversion_certificates: pd.DataFrame,
    preventive_ac: pd.DataFrame,
    spatial_scale: pd.DataFrame,
    folder: Path,
    cfg: dict[str, Any],
) -> None:
    """Combine the three principal robustness certificates for the paper."""
    configure_style(cfg)
    labels = {
        "Feasible Quantile Projection": "Feasible quantile",
        "Single Feasible Projection": "Single projection",
        "Risk-Constrained Convex Verifier": "Risk verifier",
        "Payment-Certified N-1 Verifier": "Payment certificate",
    }
    fig, axes = plt.subplots(
        1, 3, figsize=(12.7, 3.6), constrained_layout=True
    )
    sns.scatterplot(
        data=conversion_certificates,
        x="reference_n1_baseline_cost_usd",
        y="certified_n1_baseline_cost_usd",
        hue="conversion_scenario",
        palette="viridis",
        s=22,
        alpha=0.72,
        edgecolor="white",
        linewidth=0.2,
        ax=axes[0],
    )
    lower = float(
        min(
            conversion_certificates[
                "reference_n1_baseline_cost_usd"
            ].min(),
            conversion_certificates[
                "certified_n1_baseline_cost_usd"
            ].min(),
        )
    )
    upper = float(
        max(
            conversion_certificates[
                "reference_n1_baseline_cost_usd"
            ].max(),
            conversion_certificates[
                "certified_n1_baseline_cost_usd"
            ].max(),
        )
    )
    axes[0].plot(
        [lower, upper],
        [lower, upper],
        "--",
        color=COLORS["red"],
        linewidth=1,
    )
    axes[0].set_title("(a) Conversion-robust N-1 cost cap")
    axes[0].set_xlabel("Reference daily N-1 cost ($)")
    axes[0].set_ylabel("Certified daily N-1 cost ($)")
    axes[0].legend(
        title="Energy-ratio quantile", fontsize=6.2, title_fontsize=6.4
    )
    preventive = preventive_ac.assign(
        method_label=preventive_ac["counterfactual_method"].map(labels),
        penetration_pct=100.0 * preventive_ac["peak_dc_penetration"],
    )
    sns.lineplot(
        data=preventive,
        x="penetration_pct",
        y="maximum_apparent_line_loading",
        hue="method_label",
        estimator="max",
        errorbar=None,
        marker="o",
        palette=[
            COLORS["purple"],
            COLORS["orange"],
            COLORS["blue"],
            COLORS["green"],
        ],
        ax=axes[1],
    )
    axes[1].axhline(
        1.0, color=COLORS["red"], linestyle="--", linewidth=1
    )
    axes[1].set_title("(b) Shared-plan preventive AC envelope")
    axes[1].set_xlabel("Peak data-center penetration (%)")
    axes[1].set_ylabel("Maximum outage loading (p.u.)")
    axes[1].legend(
        title="Counterfactual", fontsize=6.0, title_fontsize=6.2
    )
    spatial = spatial_scale.assign(
        method_label=spatial_scale["counterfactual_method"].map(labels),
        penetration_pct=100.0 * spatial_scale["peak_dc_penetration"],
    )
    spatial = spatial[
        spatial["counterfactual_method"].isin(
            [
                "Feasible Quantile Projection",
                "Single Feasible Projection",
                "Risk-Constrained Convex Verifier",
            ]
        )
    ]
    sns.lineplot(
        data=spatial,
        x="penetration_pct",
        y="absolute_error_usd",
        hue="method_label",
        estimator="mean",
        errorbar=None,
        marker="o",
        palette=[COLORS["purple"], COLORS["orange"], COLORS["blue"]],
        ax=axes[2],
    )
    axes[2].set_title("(c) Complete spatial-scale transfer")
    axes[2].set_xlabel("Peak data-center penetration (%)")
    axes[2].set_ylabel("Mean absolute payment error ($/day)")
    axes[2].legend(
        title="Counterfactual", fontsize=6.0, title_fontsize=6.2
    )
    save_figure(fig, folder, "fig17_cross_layer_robustness")


def plot_exp12(
    results: pd.DataFrame,
    summary: pd.DataFrame,
    folder: Path,
    cfg: dict[str, Any],
) -> None:
    """Plot continuous-horizon feasibility and recovery-aware remuneration."""
    configure_style(cfg)
    labels = {
        "Feasible Quantile Projection": "Feasible\nquantile",
        "Single Feasible Projection": "Single\nprojection",
        "Risk-Constrained Convex Verifier": "Risk\nverifier",
        "Payment-Certified N-1 Verifier": "Payment\ncertificate",
    }
    shown = results.assign(
        method_label=results["counterfactual_method"].map(labels)
    )
    order = list(labels.values())
    fig, axes_grid = plt.subplots(
        2, 2, figsize=(10.8, 7.1), constrained_layout=True
    )
    axes = axes_grid.ravel()
    error_long = shown.melt(
        id_vars=["method_label", "day"],
        value_vars=[
            "event_only_absolute_error_usd",
            "full_cycle_absolute_error_usd",
        ],
        var_name="accounting_window",
        value_name="absolute_error_usd",
    )
    error_long["accounting_window"] = error_long[
        "accounting_window"
    ].map(
        {
            "event_only_absolute_error_usd": "Event window only",
            "full_cycle_absolute_error_usd": "Complete response cycle",
        }
    )
    sns.barplot(
        data=error_long,
        x="method_label",
        y="absolute_error_usd",
        hue="accounting_window",
        order=order,
        errorbar=("ci", 95),
        palette=[COLORS["orange"], COLORS["blue"]],
        ax=axes[0],
    )
    axes[0].set_title("(a) Recovery-aware payment accuracy")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Mean absolute error ($/event)")
    axes[0].legend(title="", fontsize=6.7)
    sns.boxplot(
        data=shown,
        x="method_label",
        y="recovery_adjustment_usd",
        order=order,
        hue="method_label",
        palette=[
            COLORS["purple"],
            COLORS["orange"],
            COLORS["blue"],
            COLORS["green"],
        ],
        legend=False,
        showfliers=False,
        ax=axes[1],
    )
    axes[1].axhline(0.0, color=COLORS["black"], linewidth=0.8)
    axes[1].set_title("(b) Pre-event and recovery adjustment")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Full-cycle minus event-only payment ($)")
    contract = summary.assign(
        method_label=summary["counterfactual_method"].map(labels),
        activation_percent=(
            100.0 * summary["bilateral_contract_activation_rate"]
        ),
    )
    sns.barplot(
        data=contract,
        x="method_label",
        y="activation_percent",
        order=order,
        color=COLORS["green"],
        ax=axes[2],
    )
    axes[2].set_ylim(0, 105)
    axes[2].set_title("(c) Individually rational contract activation")
    axes[2].set_xlabel("")
    axes[2].set_ylabel("Eligible locked days (%)")
    feasibility = summary.assign(
        method_label=summary["counterfactual_method"].map(labels),
        log_energy_residual=np.log10(
            np.maximum(
                summary[
                    "maximum_absolute_cycle_energy_residual_mwh"
                ].to_numpy(),
                1e-14,
            )
        ),
    )
    sns.scatterplot(
        data=feasibility,
        x="maximum_baseline_projection_l1_mw",
        y="log_energy_residual",
        hue="method_label",
        style="method_label",
        s=75,
        palette=[
            COLORS["purple"],
            COLORS["orange"],
            COLORS["blue"],
            COLORS["green"],
        ],
        ax=axes[3],
    )
    axes[3].set_title("(d) Continuous-horizon certificates")
    axes[3].set_xlabel("Maximum day-profile projection L1 (MW)")
    axes[3].set_ylabel(r"$\log_{10}$ maximum energy residual (MWh)")
    axes[3].legend(title="Counterfactual", fontsize=6.1, title_fontsize=6.3)
    save_figure(fig, folder, "fig18_rolling_market_validation")


def plot_exp11(
    results: pd.DataFrame,
    mapping_summary: pd.DataFrame,
    folder: Path,
    cfg: dict[str, Any],
) -> None:
    """Plot the complete spatial-assignment and penetration experiment."""
    configure_style(cfg)
    label_map = {
        "Feasible Quantile Projection": "Feasible quantile",
        "Single Feasible Projection": "Single projection",
        "Risk-Constrained Convex Verifier": "Risk verifier",
        "Trace-Anchored Reference": "Trace reference",
    }
    palette = [
        COLORS["purple"],
        COLORS["orange"],
        COLORS["blue"],
        COLORS["green"],
    ]
    shown = results.assign(
        method_label=results["counterfactual_method"].map(label_map),
        penetration_label=(
            100.0 * results["peak_dc_penetration"]
        ).map(lambda value: f"{value:.0f}%"),
    )
    mapped = mapping_summary.assign(
        method_label=mapping_summary["counterfactual_method"].map(label_map),
        penetration_label=(
            100.0 * mapping_summary["peak_dc_penetration"]
        ).map(lambda value: f"{value:.0f}%"),
    )
    order = list(label_map.values())
    penetration_order = [
        f"{100.0 * value:.0f}%"
        for value in sorted(results["peak_dc_penetration"].unique())
    ]
    fig, axes = plt.subplots(
        1, 3, figsize=(13.2, 3.8), constrained_layout=True
    )
    sns.barplot(
        data=shown,
        x="penetration_label",
        y="absolute_error_usd",
        hue="method_label",
        order=penetration_order,
        hue_order=order,
        errorbar=("ci", 95),
        palette=palette,
        ax=axes[0],
    )
    axes[0].set_title("(a) Error across all 24 assignments")
    axes[0].set_xlabel("Peak data-center penetration")
    axes[0].set_ylabel("Mean absolute error ($/interval)")
    axes[0].legend(
        title="Counterfactual",
        fontsize=6.5,
        title_fontsize=7,
    )
    risk_mappings = mapped[
        mapped["counterfactual_method"]
        == "Risk-Constrained Convex Verifier"
    ]
    sns.boxplot(
        data=risk_mappings,
        x="penetration_label",
        y="mean_absolute_error_usd",
        order=penetration_order,
        color=COLORS["sky"],
        showfliers=True,
        ax=axes[1],
    )
    sns.stripplot(
        data=risk_mappings,
        x="penetration_label",
        y="mean_absolute_error_usd",
        order=penetration_order,
        color=COLORS["black"],
        size=3,
        alpha=0.65,
        ax=axes[1],
    )
    axes[1].set_title("(b) Mapping-to-mapping dispersion")
    axes[1].set_xlabel("Peak data-center penetration")
    axes[1].set_ylabel("Risk-verifier daily mean error ($)")
    risk = shown[
        shown["counterfactual_method"]
        == "Risk-Constrained Convex Verifier"
    ]
    sns.scatterplot(
        data=risk,
        x="data_center_lmp_spread_usd_per_mwh",
        y="absolute_error_usd",
        hue="penetration_label",
        hue_order=penetration_order,
        palette="viridis",
        alpha=0.42,
        s=18,
        linewidth=0,
        ax=axes[2],
    )
    axes[2].set_title("(c) Congestion heterogeneity and error")
    axes[2].set_xlabel("Data-center LMP spread ($/MWh)")
    axes[2].set_ylabel("Absolute error ($/interval)")
    axes[2].legend(
        title="Peak penetration",
        fontsize=7,
        title_fontsize=7,
    )
    save_figure(fig, folder, "fig16_spatial_scale_robustness")


def plot_exp1(results: pd.DataFrame, folder: Path, cfg: dict[str, Any]) -> None:
    configure_style(cfg)
    pivot_false = results.pivot(index="event_probability", columns="dr_price", values="false_response_ratio")
    pivot_inflation = results.pivot(index="event_probability", columns="dr_price", values="baseline_inflation_mwh")
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.6), constrained_layout=True)
    sns.heatmap(pivot_inflation, cmap="YlOrRd", ax=axes[0], cbar_kws={"label": "Baseline inflation (MWh)"})
    probability_order = list(pivot_inflation.index)
    price_order = list(pivot_inflation.columns)
    profitable = results[results["theory_profitable"].astype(bool)]
    boundary = (
        results[results["boundary_indifference"].astype(bool)]
        if "boundary_indifference" in results
        else results.iloc[0:0]
    )
    axes[0].scatter(
        [price_order.index(value) + 0.5 for value in profitable["dr_price"]],
        [
            probability_order.index(value) + 0.5
            for value in profitable["event_probability"]
        ],
        marker="o",
        s=13,
        color="black",
        label="Strictly profitable",
    )
    axes[0].scatter(
        [price_order.index(value) + 0.5 for value in boundary["dr_price"]],
        [
            probability_order.index(value) + 0.5
            for value in boundary["event_probability"]
        ],
        marker="o",
        s=28,
        facecolors="none",
        edgecolors="black",
        linewidths=0.9,
        label="Indifference boundary",
    )
    axes[0].set_title("(a) Strategic baseline inflation")
    axes[0].set_xlabel("DR payment ($/MWh)")
    axes[0].set_ylabel("Event probability")
    axes[0].legend(loc="upper left", fontsize=6.8, frameon=True)
    sns.heatmap(pivot_false, cmap="mako", vmin=0, vmax=max(1.0, pivot_false.max().max()), ax=axes[1], cbar_kws={"label": "False response ratio"})
    axes[1].set_title("(b) Paid response not backed by physical reduction")
    axes[1].set_xlabel("DR payment ($/MWh)")
    axes[1].set_ylabel("Event probability")
    save_figure(fig, folder, "fig1_manipulation_phase_diagram")

    fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.4), constrained_layout=True)
    response = results.drop_duplicates("dr_price")
    sns.lineplot(data=response, x="dr_price", y="actual_reduction_mwh", marker="o", color=COLORS["blue"], ax=axes[0])
    axes[0].set_title("(a) Event-period load reduction")
    axes[0].set_xlabel("DR payment ($/MWh)")
    axes[0].set_ylabel("Reduction against honest operation (MWh)")
    sns.lineplot(data=results, x="event_probability", y="reference_migration_mwh", hue="dr_price", marker="s", palette="viridis", ax=axes[1])
    axes[1].set_title("(b) Strategic reference-period migration")
    axes[1].set_xlabel("Event probability")
    axes[1].set_ylabel("Migrated workload (MWh)")
    axes[1].legend(title="DR payment", ncol=2, fontsize=6.5, title_fontsize=7)
    save_figure(fig, folder, "fig2_response_and_migration")


def plot_exp2(
    metrics: pd.DataFrame,
    tuning: pd.DataFrame,
    ablation: pd.DataFrame,
    robustness: pd.DataFrame,
    folder: Path,
    cfg: dict[str, Any],
) -> None:
    configure_style(cfg)
    order = [
        "High-5-of-10", "Ridge", "Gradient Boosting", "Extra Trees",
        "Metadata Gradient Boosting", "Ex-post Metadata Gradient Boosting",
        "Ex-post Quantile Gradient Boosting", "Synthetic Control",
        "Feasible Quantile Projection",
        "Tail-Risk Feasible Counterfactual",
        "Single Feasible Projection", "Risk-Constrained Convex Verifier",
    ]
    method_labels = {
        "High-5-of-10": "High-5",
        "Ridge": "Ridge",
        "Gradient Boosting": "GB",
        "Extra Trees": "Extra Trees",
        "Metadata Gradient Boosting": "Online Meta-GB",
        "Ex-post Metadata Gradient Boosting": "Ex-post Meta-GB",
        "Ex-post Quantile Gradient Boosting": "Ex-post QGB",
        "Synthetic Control": "Synthetic\nControl",
        "Feasible Quantile Projection": "Feasible\nQuantile",
        "Tail-Risk Feasible Counterfactual": "Tail-Risk\nCounterfactual",
        "Single Feasible Projection": "Single Projection",
        "Risk-Constrained Convex Verifier": "Risk-Safe\nVerifier",
    }
    displayed_metrics = metrics.assign(
        display_method=metrics["method"].map(method_labels)
    )
    display_order = [method_labels[method] for method in order]
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 3.65), constrained_layout=True)
    sns.boxplot(data=displayed_metrics, x="display_method", y="nrmse", order=display_order, color=COLORS["sky"], showfliers=False, ax=axes[0])
    sns.stripplot(data=displayed_metrics, x="display_method", y="nrmse", order=display_order, color=COLORS["black"], alpha=0.45, size=2.5, ax=axes[0])
    axes[0].set_title("(a) Counterfactual baseline error")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Normalized RMSE")
    axes[0].tick_params(axis="x", rotation=24)
    sns.boxplot(data=displayed_metrics, x="display_method", y="false_response_ratio", order=display_order, color=COLORS["orange"], showfliers=False, ax=axes[1])
    sns.stripplot(data=displayed_metrics, x="display_method", y="false_response_ratio", order=display_order, color=COLORS["black"], alpha=0.45, size=2.5, ax=axes[1])
    axes[1].set_title("(b) False response exposure")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("False response ratio")
    axes[1].tick_params(axis="x", rotation=24)
    sns.boxplot(data=displayed_metrics, x="display_method", y="bias_mw", order=display_order, color=COLORS["green"], showfliers=False, ax=axes[2])
    axes[2].axhline(0, color="black", lw=0.8)
    axes[2].set_title("(c) Event-window bias")
    axes[2].set_xlabel("")
    axes[2].set_ylabel("Bias (MW)")
    axes[2].tick_params(axis="x", rotation=24)
    save_figure(fig, folder, "fig3_baseline_verification_performance")

    fig, axes_grid = plt.subplots(2, 2, figsize=(10.6, 7.0), constrained_layout=True)
    axes = axes_grid.ravel()
    displayed_tuning = tuning.copy()
    displayed_tuning["candidate_label"] = np.where(
        displayed_tuning["candidate_type"].eq("feasible quantile projection"),
        "Feasible\nquantile",
        displayed_tuning["projection_weight"].map(
            lambda value: rf"$\rho={float(value):g}$"
        ),
    )
    sns.barplot(
        data=displayed_tuning,
        x="candidate_label",
        y="ensemble_weight",
        color=COLORS["blue"],
        ax=axes[0],
    )
    axes[0].set_title("(a) Validation-fitted convex weights")
    axes[0].set_ylabel("Simplex coefficient")
    axes[0].set_xlabel("Feasible candidate")
    axes[0].set_ylim(0, max(0.65, float(tuning["ensemble_weight"].max()) * 1.12))
    axes[0].tick_params(axis="x", rotation=18)
    ablation_labels = {
        "Ex-post statistical": "Statistical",
        "Conservation only": "Release +\nconservation",
        "Release + conservation": "Release +\nconservation",
        "+ Release/deadlines": "+ deadlines",
        "+ Deadline constraints": "+ deadlines",
        "Full single projection": "Single\nprojection",
        "Full convex verifier": "Convex\nverifier",
        "Tail-risk convex ensemble": "Tail-risk\nensemble",
        "Full risk-envelope verifier": "Risk-safe\nverifier",
    }
    displayed_ablation = ablation.assign(
        display_variant=ablation["variant"].map(ablation_labels)
    )
    sns.barplot(data=displayed_ablation, x="display_variant", y="false_response_ratio", color=COLORS["purple"], ax=axes[1])
    axes[1].set_title("(b) Constraint-set ablation")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("False response ratio")
    axes[1].tick_params(axis="x", rotation=0)
    robust_order = list(robustness["scenario"].drop_duplicates())
    robust_labels = {
        "Optimization only": "Physics only",
        "Convex feasible ensemble": "Full verifier",
        "Deadline +50%": "Deadline 1.5×",
        "Waiting cost -50%": "Wait cost 0.5×",
        "No site capacity": "No capacity",
        "Missing batch metadata": "No batch data",
    }
    displayed_robustness = robustness.assign(
        display_scenario=robustness["scenario"].map(
            lambda value: robust_labels.get(value, value)
        )
    )
    display_robust_order = [
        robust_labels.get(item, item) for item in robust_order
    ]
    sns.boxplot(data=displayed_robustness, x="display_scenario", y="nrmse", order=display_robust_order, color=COLORS["green"], showfliers=False, ax=axes[2])
    axes[2].set_title("(c) Specification robustness")
    axes[2].set_xlabel("")
    axes[2].set_ylabel("Normalized RMSE")
    axes[2].tick_params(axis="x", rotation=18)
    frontier = tuning[
        np.isfinite(tuning["validation_credit_recall"])
        & np.isfinite(tuning["validation_credit_precision"])
    ].copy()
    axes[3].plot(
        frontier["validation_credit_recall"],
        frontier["validation_credit_precision"],
        marker="o", color=COLORS["blue"], lw=1.2,
    )
    coincident_labels: dict[tuple[float, float], list[str]] = {}
    for _, row in frontier.iterrows():
        coordinate = (
            round(float(row["validation_credit_recall"]), 6),
            round(float(row["validation_credit_precision"]), 6),
        )
        coincident_labels.setdefault(coordinate, []).append(
            f"{row['projection_weight']:g}"
        )
    for (recall, precision), weights in coincident_labels.items():
        if precision > 0.85 and recall < 0.52:
            offset = (-72, 8)
        elif precision > 0.85:
            offset = (8, 8)
        else:
            offset = (5, 7)
        axes[3].annotate(
            "w=" + ",".join(weights),
            (recall, precision),
            xytext=offset, textcoords="offset points", fontsize=7,
        )
    axes[3].set_xlim(0, 1)
    axes[3].set_ylim(0, 1)
    axes[3].set_title("(d) Validation precision-recall frontier")
    axes[3].set_xlabel("Credit recall")
    axes[3].set_ylabel("Credit precision")
    save_figure(fig, folder, "fig4_tuning_and_ablation")


def plot_intervention_robustness(
    results: pd.DataFrame,
    folder: Path,
    cfg: dict[str, Any],
) -> None:
    configure_style(cfg)
    method_order = [
        "Feasible Quantile Projection",
        "Single Feasible Projection",
        "Tail-Risk Feasible Counterfactual",
        "Risk-Constrained Convex Verifier",
    ]
    labels = {
        "Feasible Quantile Projection": "Feasible quantile",
        "Single Feasible Projection": "Single projection",
        "Tail-Risk Feasible Counterfactual": "Tail-risk counterfactual",
        "Risk-Constrained Convex Verifier": "Risk-safe verifier",
    }
    shown = results.assign(
        display_method=results["method"].map(labels)
    )
    hue_order = [labels[value] for value in method_order]
    fig, axes = plt.subplots(
        1, 2, figsize=(10.8, 3.8), constrained_layout=True
    )
    sns.barplot(
        data=shown,
        x="intervention",
        y="false_response_mwh",
        hue="display_method",
        hue_order=hue_order,
        errorbar=("ci", 95),
        ax=axes[0],
    )
    axes[0].set_title("(a) False credit under independent interventions")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("False response (MWh)")
    axes[0].tick_params(axis="x", rotation=20)
    axes[0].legend(
        title="Method", fontsize=6.5, title_fontsize=7
    )
    sns.barplot(
        data=shown,
        x="intervention",
        y="credit_f1",
        hue="display_method",
        hue_order=hue_order,
        errorbar=("ci", 95),
        ax=axes[1],
    )
    axes[1].set_title("(b) Credit identification")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Credit F1")
    axes[1].tick_params(axis="x", rotation=20)
    axes[1].legend_.remove()
    save_figure(fig, folder, "fig4b_intervention_robustness")


def plot_exp3(settlement: pd.DataFrame, line_loading: pd.DataFrame, folder: Path, cfg: dict[str, Any]) -> None:
    configure_style(cfg)
    order = [
        "Uniform gross",
        "Nodal gross",
        "Uniform signed net",
        "Nodal signed linear",
        "Nodal exact net value",
    ]
    fig, axes = plt.subplots(1, 3, figsize=(12.0, 3.7), constrained_layout=True)
    error = settlement.assign(abs_error=lambda x: x["payment_error_usd"].abs()).pivot_table(
        index="baseline_method", columns="mechanism", values="abs_error", aggfunc="mean"
    ).reindex(columns=order)
    over = settlement.pivot_table(index="baseline_method", columns="mechanism", values="overpayment_ratio", aggfunc="mean").reindex(columns=order)
    sns.heatmap(error, cmap="YlOrRd", ax=axes[0], cbar_kws={"label": "Mean absolute error ($)"})
    axes[0].set_title("(a) Baseline × settlement error")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Baseline method")
    sns.heatmap(over, cmap="rocket_r", vmin=0, vmax=1, ax=axes[1], cbar_kws={"label": "Overpayment ratio"})
    axes[1].set_title("(b) Overpayment exposure")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("")
    proposed = settlement[
        settlement["baseline_method"]
        == "Risk-Constrained Convex Verifier"
    ]
    sns.scatterplot(data=proposed, x="realized_grid_value_usd", y="payment_usd", hue="mechanism", style="mechanism", ax=axes[2], s=36)
    lower = min(proposed["realized_grid_value_usd"].min(), proposed["payment_usd"].min(), -1)
    upper = max(proposed["realized_grid_value_usd"].max(), proposed["payment_usd"].max(), 1)
    margin = 0.04 * (upper - lower)
    lower, upper = lower - margin, upper + margin
    axes[2].plot([lower, upper], [lower, upper], "--", color="black", lw=0.9, label="Perfect settlement")
    axes[2].set_xlim(lower, upper)
    axes[2].set_ylim(lower, upper)
    axes[2].set_title("(c) Proposed baseline: value alignment")
    axes[2].set_xlabel("Realized grid value ($)")
    axes[2].set_ylabel("Payment ($)")
    save_figure(fig, folder, "fig5_settlement_value_alignment")

    pivot = line_loading.pivot(index="interval", columns="line", values="loading_percent")
    busiest = pivot.max().sort_values(ascending=False).head(20).index
    fig, ax = plt.subplots(figsize=(9.2, 4.0), constrained_layout=True)
    sns.heatmap(pivot[busiest].T, cmap="rocket_r", vmin=40, vmax=max(100, float(pivot[busiest].max().max())), cbar_kws={"label": "Line loading (%)"}, ax=ax)
    ax.set_title("Network loading during the demand-response event")
    ax.set_xlabel("15-minute event interval")
    ax.set_ylabel("PGLib branch index")
    save_figure(fig, folder, "fig6_network_loading_heatmap")


def plot_settlement_factor_decomposition(
    factors: pd.DataFrame,
    folder: Path,
    cfg: dict[str, Any],
) -> None:
    """Visualize paired one-factor settlement-mechanism contrasts."""
    configure_style(cfg)
    selected = factors[
        factors["baseline_method"].isin(
            [
                "Trace-Anchored Reference",
                "Risk-Constrained Convex Verifier",
            ]
        )
    ].copy()
    factor_map = {
        "gross_to_signed_error_reduction_usd": "Signed netting",
        "uniform_to_nodal_error_reduction_usd": "Locational pricing",
        "linear_to_exact_error_reduction_usd": "Exact grid value",
    }
    quality_map = {
        "Trace-Anchored Reference": "Trace reference",
        "Risk-Constrained Convex Verifier": "Risk verifier",
    }
    long = selected.melt(
        id_vars=["day", "baseline_method"],
        value_vars=list(factor_map),
        var_name="factor",
        value_name="paired_error_reduction_usd",
    )
    long["factor"] = long["factor"].map(factor_map)
    long["counterfactual"] = long["baseline_method"].map(quality_map)
    order = list(factor_map.values())
    fig, axes = plt.subplots(
        1, 2, figsize=(9.5, 3.7), constrained_layout=True
    )
    sns.boxplot(
        data=long,
        x="factor",
        y="paired_error_reduction_usd",
        hue="counterfactual",
        order=order,
        showfliers=False,
        palette=[COLORS["green"], COLORS["blue"]],
        ax=axes[0],
    )
    axes[0].axhline(0.0, color=COLORS["black"], linewidth=0.8)
    axes[0].set_title("(a) Paired one-factor error reduction")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Comparator MAE - upgraded MAE ($/day)")
    axes[0].tick_params(axis="x", rotation=15)
    axes[0].legend(
        title="Counterfactual", fontsize=7, title_fontsize=7
    )
    risk = long[long["counterfactual"] == "Risk verifier"]
    sns.ecdfplot(
        data=risk,
        x="paired_error_reduction_usd",
        hue="factor",
        hue_order=order,
        palette=[COLORS["orange"], COLORS["purple"], COLORS["blue"]],
        ax=axes[1],
    )
    axes[1].axvline(0.0, color=COLORS["black"], linewidth=0.8)
    axes[1].set_title("(b) Locked-day effect distributions")
    axes[1].set_xlabel("Paired error reduction ($/day)")
    axes[1].set_ylabel("Empirical cumulative probability")
    axes[1].legend(
        title="Settlement factor",
        labels=list(reversed(order)),
        fontsize=7,
        title_fontsize=7,
    )
    save_figure(fig, folder, "fig6b_settlement_factor_decomposition")


def plot_case_study(
    timeseries: pd.DataFrame,
    network: dict[str, np.ndarray],
    dc_buses: list[int],
    folder: Path,
    cfg: dict[str, Any],
) -> None:
    configure_style(cfg)
    fig, axes = plt.subplots(2, 1, figsize=(9.0, 6.0), sharex=True, constrained_layout=True)
    sns.lineplot(data=timeseries, x="slot", y="oracle_baseline_mw", hue="data_center", ax=axes[0], lw=1.7)
    sns.lineplot(data=timeseries, x="slot", y="actual_mw", hue="data_center", ax=axes[0], lw=1.1, linestyle="--", legend=False)
    axes[0].set_title("(a) Counterfactual and event-period data-center power")
    axes[0].set_ylabel("Power (MW)")
    axes[0].set_xlabel("")
    sns.lineplot(data=timeseries, x="slot", y="nodal_response_mw", hue="data_center", ax=axes[1], lw=1.7)
    axes[1].axhline(0, color="black", lw=0.8)
    axes[1].set_title("(b) Positive reduction and destination-node rebound")
    axes[1].set_ylabel("Nodal response (MW)")
    axes[1].set_xlabel("15-minute interval")
    save_figure(fig, folder, "fig7_spatial_response_case")

    graph = nx.Graph()
    branches = network["branch"]
    for row in branches:
        graph.add_edge(int(row[0]), int(row[1]))
    pos = nx.spring_layout(graph, seed=int(cfg["project"]["seed"]), iterations=300, k=0.22)
    fig, ax = plt.subplots(figsize=(8.0, 6.8), constrained_layout=True)
    nx.draw_networkx_edges(graph, pos, width=0.45, alpha=0.38, edge_color="#777777", ax=ax)
    other = [node for node in graph.nodes if node not in set(dc_buses)]
    nx.draw_networkx_nodes(graph, pos, nodelist=other, node_size=16, node_color="#B8C2CC", alpha=0.75, ax=ax)
    nx.draw_networkx_nodes(graph, pos, nodelist=dc_buses, node_size=120, node_color=COLORS["red"], edgecolors="white", linewidths=0.8, ax=ax)
    nx.draw_networkx_labels(graph, pos, labels={node: f"DC@{node}" for node in dc_buses}, font_size=7, ax=ax)
    ax.set_title("Spatial placement of AI data centers in the PGLib IEEE 118-bus system")
    ax.axis("off")
    save_figure(fig, folder, "fig8_ieee118_data_center_topology")


def plot_exp5(
    results: pd.DataFrame,
    resolution_summary: pd.DataFrame,
    folder: Path,
    cfg: dict[str, Any],
) -> None:
    configure_style(cfg)
    summary = results.groupby(["network", "load_multiplier", "baseline_quality", "mechanism"], as_index=False).agg(
        absolute_error_usd=("absolute_error_usd", "mean"),
        normalized_error=("normalized_absolute_error", "median"),
    )
    endpoint = summary[
        summary["baseline_quality"]
        == "Risk-Constrained Convex Verifier"
    ].pivot_table(
        index=["network", "load_multiplier"], columns="mechanism", values="absolute_error_usd"
    )
    endpoint["linear_minus_exact_usd"] = (
        endpoint["Nodal signed linear"]
        - endpoint["Nodal exact net value"]
    )
    proposed = endpoint.reset_index()
    fig, axes = plt.subplots(1, 3, figsize=(13.0, 3.8), constrained_layout=True)
    pivot = proposed.pivot(
        index="network",
        columns="load_multiplier",
        values="linear_minus_exact_usd",
    )
    sns.heatmap(
        pivot,
        cmap="vlag",
        center=0.0,
        annot=True,
        fmt=".3f",
        ax=axes[0],
        cbar_kws={
            "label": "Nodal linear MAE - exact MAE ($/day)"
        },
    )
    axes[0].set_title("(a) Estimated-baseline mechanism gap")
    axes[0].set_xlabel("Native-load multiplier")
    axes[0].set_ylabel("")
    oracle_mechanisms = summary[
        summary["baseline_quality"] == "Trace-Anchored Reference"
    ]
    sns.pointplot(
        data=oracle_mechanisms, x="network", y="absolute_error_usd", hue="mechanism",
        markers="o", linestyles="-", errorbar=None, ax=axes[1],
    )
    axes[1].set_yscale("symlog", linthresh=1.0)
    axes[1].set_title("(b) Mechanism error under matched prices")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Mean absolute value error ($, symlog scale)")
    axes[1].tick_params(axis="x", rotation=18)
    axes[1].legend(title="Settlement", fontsize=6.5, title_fontsize=7)
    convergence = resolution_summary.sort_values("settlement_segments")
    axes[2].errorbar(
        convergence["settlement_segments"],
        convergence["mean_linear_minus_exact_error_usd_day"],
        yerr=1.96 * convergence["standard_error_usd_day"],
        color=COLORS["blue"],
        marker="o",
        linewidth=1.3,
        capsize=3,
    )
    axes[2].axhline(0.0, color=COLORS["red"], linestyle="--", linewidth=1)
    axes[2].set_xscale("log", base=2)
    axes[2].set_xticks(convergence["settlement_segments"])
    axes[2].set_xticklabels(convergence["settlement_segments"].astype(int))
    axes[2].set_title("(c) Resolution convergence at boundary cell")
    axes[2].set_xlabel("Settlement cost segments")
    axes[2].set_ylabel("Linear MAE - exact MAE ($/day)")
    save_figure(fig, folder, "fig9_cross_network_robustness")


def plot_exp6(summary: pd.DataFrame, folder: Path, cfg: dict[str, Any]) -> None:
    configure_style(cfg)
    fig, axes = plt.subplots(1, 3, figsize=(11.2, 3.5), constrained_layout=True)
    specifications = [
        ("false_response_ratio", "False response ratio", "(a) Verification robustness"),
        ("capacity_binding_share", "Capacity binding share", "(b) Active site constraints"),
        ("deadline_binding_share", "Deadline binding share", "(c) Active service constraints"),
    ]
    for ax, (metric, label, title) in zip(axes, specifications):
        pivot = summary.pivot(index="deadline_multiplier", columns="capacity_multiplier", values=metric)
        sns.heatmap(pivot, cmap="viridis", annot=True, fmt=".2f", ax=ax, cbar_kws={"label": label})
        ax.set_title(title)
        ax.set_xlabel("Capacity multiplier")
        ax.set_ylabel("Deadline multiplier")
    save_figure(fig, folder, "fig10_binding_constraint_stress")


def plot_exp7(
    results: pd.DataFrame,
    summary: pd.DataFrame,
    folder: Path,
    cfg: dict[str, Any],
) -> None:
    configure_style(cfg)
    endpoint = results[
        results["baseline_quality"]
        == "Risk-Constrained Convex Verifier"
    ].copy()
    methods = [
        "Nodal signed linear",
        "Standalone avoided cost",
        "Leave-one-out marginal",
        "Exact Shapley net value",
    ]
    fig, axes = plt.subplots(
        1, 3, figsize=(12.4, 3.7), constrained_layout=True
    )
    participant = (
        endpoint.groupby(["participant", "allocation_method"], as_index=False)[
            "participant_absolute_error_usd"
        ]
        .mean()
    )
    sns.barplot(
        data=participant,
        x="participant",
        y="participant_absolute_error_usd",
        hue="allocation_method",
        hue_order=methods,
        ax=axes[0],
    )
    axes[0].set_title("(a) Participant value-allocation error")
    axes[0].set_xlabel("Data-center participant")
    axes[0].set_ylabel("Mean absolute error ($)")
    axes[0].legend(
        title="Allocation", fontsize=6.2, title_fontsize=7, loc="upper left"
    )

    daily = endpoint.drop_duplicates(
        ["day", "allocation_method"]
    ).copy()
    daily["absolute_budget_residual_usd"] = daily[
        "budget_residual_usd"
    ].abs()
    sns.boxplot(
        data=daily,
        x="allocation_method",
        y="absolute_budget_residual_usd",
        order=methods,
        color=COLORS["green"],
        showfliers=False,
        ax=axes[1],
    )
    axes[1].set_yscale("log")
    axes[1].set_title("(b) Grand-coalition budget residual")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Absolute residual ($, log scale)")
    axes[1].tick_params(axis="x", rotation=27)

    allocation = endpoint[
        endpoint["allocation_method"] == "Exact Shapley net value"
    ]
    sns.scatterplot(
        data=allocation,
        x="oracle_shapley_value_usd",
        y="participant_payment_usd",
        hue="participant",
        palette="colorblind",
        s=28,
        alpha=0.75,
        ax=axes[2],
    )
    limits = [
        float(
            min(
                allocation["oracle_shapley_value_usd"].min(),
                allocation["participant_payment_usd"].min(),
            )
        ),
        float(
            max(
                allocation["oracle_shapley_value_usd"].max(),
                allocation["participant_payment_usd"].max(),
            )
        ),
    ]
    axes[2].plot(limits, limits, "--", color=COLORS["black"], lw=1)
    axes[2].set_title("(c) Exact allocation under estimated baseline")
    axes[2].set_xlabel("Trace-observed Shapley value ($)")
    axes[2].set_ylabel("Estimated Shapley payment ($)")
    axes[2].legend(title="Participant", fontsize=6.5, title_fontsize=7)
    save_figure(fig, folder, "fig11_exact_value_allocation")


def plot_exp7_scaling(
    scaling: pd.DataFrame,
    folder: Path,
    cfg: dict[str, Any],
) -> None:
    """Visualize the complete exact eight-participant allocation panel."""
    configure_style(cfg)
    fig, axes = plt.subplots(
        1, 3, figsize=(12.4, 3.7), constrained_layout=True
    )
    sns.barplot(
        data=scaling,
        x="participant",
        y="exact_shapley_value_usd",
        hue="portfolio",
        errorbar=("ci", 95),
        ax=axes[0],
    )
    axes[0].axhline(0, color=COLORS["black"], lw=0.8)
    axes[0].set_title("(a) Eight-participant exact allocation")
    axes[0].set_xlabel("Contractual participant")
    axes[0].set_ylabel("Shapley value ($/interval)")
    axes[0].legend(
        title="Portfolio", fontsize=6.5, title_fontsize=7
    )

    daily = (
        scaling.drop_duplicates(["day", "slot"])
        .groupby("day", as_index=False)
        .agg(
            maximum_budget_residual_usd=(
                "budget_residual_usd",
                lambda values: float(np.max(np.abs(values))),
            ),
            solve_seconds=("day_solve_seconds", "first"),
        )
    )
    residual = np.maximum(
        daily["maximum_budget_residual_usd"].to_numpy(), 1e-14
    )
    axes[1].hist(
        residual,
        bins=16,
        color=COLORS["green"],
        edgecolor="white",
    )
    axes[1].set_xscale("log")
    axes[1].set_title("(b) Exact efficiency certificate")
    axes[1].set_xlabel("Maximum daily budget residual ($, log)")
    axes[1].set_ylabel("Locked days")

    axes[2].plot(
        daily["day"],
        daily["solve_seconds"],
        color=COLORS["blue"],
        marker="o",
        markersize=2.5,
        lw=1,
    )
    axes[2].set_title("(c) Complete coalition runtime")
    axes[2].set_xlabel("Locked day")
    axes[2].set_ylabel("2,048 coalition solves per day (s)")
    save_figure(fig, folder, "fig12_eight_participant_scaling")


def plot_exp7_grouped_scaling(
    scaling: pd.DataFrame,
    folder: Path,
    cfg: dict[str, Any],
) -> None:
    """Visualize exact count-state allocation through 20 participants."""
    configure_style(cfg)
    compact = scaling.drop_duplicates(["day", "participant_count"])
    summary = (
        compact.groupby("participant_count", as_index=False)
        .agg(
            mean_runtime=("solve_seconds", "mean"),
            states=("count_states_evaluated", "max"),
            avoided=("full_coalitions_avoided", "max"),
            maximum_residual=(
                "budget_residual_usd",
                lambda values: float(np.max(np.abs(values))),
            ),
        )
    )
    fig, axes = plt.subplots(1, 3, figsize=(12.3, 3.6), constrained_layout=True)
    axes[0].plot(
        summary["participant_count"],
        summary["states"],
        marker="o",
        color=COLORS["blue"],
        label="Exact count states",
    )
    axes[0].plot(
        summary["participant_count"],
        2.0 ** summary["participant_count"],
        marker="s",
        color=COLORS["red"],
        label="Uncompressed coalitions",
    )
    axes[0].set_yscale("log")
    axes[0].set_title("(a) Exact symmetry reduction")
    axes[0].set_xlabel("Contractual participants")
    axes[0].set_ylabel("Value-function evaluations (log)")
    axes[0].legend(fontsize=7)
    sns.boxplot(
        data=compact,
        x="participant_count",
        y="solve_seconds",
        color=COLORS["sky"],
        showfliers=False,
        ax=axes[1],
    )
    axes[1].set_title("(b) Locked-day runtime")
    axes[1].set_xlabel("Contractual participants")
    axes[1].set_ylabel("Exact allocation runtime (s)")
    residual = np.maximum(summary["maximum_residual"], 1e-15)
    axes[2].plot(
        summary["participant_count"],
        residual,
        marker="o",
        color=COLORS["green"],
    )
    axes[2].set_yscale("log")
    axes[2].set_title("(c) Budget-balance certificate")
    axes[2].set_xlabel("Contractual participants")
    axes[2].set_ylabel("Maximum residual ($, log)")
    save_figure(fig, folder, "fig12b_exact_20_participant_scaling")


def plot_exp17_decision_time(
    rows: pd.DataFrame,
    folder: Path,
    cfg: dict[str, Any],
) -> None:
    """Visualize the information-boundary replay without mixing protocols."""
    configure_style(cfg)
    summary = (
        rows.groupby("method", as_index=False)
        .agg(
            nrmse=("nrmse", "mean"),
            false_response_mwh=("false_response_mwh", "mean"),
            meter_capped_response_mwh=("meter_capped_response_mwh", "mean"),
            credit_recall=("credit_recall", "mean"),
        )
    )
    order = [
        "Decision-time truncated-ledger verifier",
        "Committed-ledger rolling-service verifier",
        "Committed-ledger reference schedule",
        "Complete-ledger risk-constrained verifier",
    ]
    labels = {
        order[0]: "Gate-causal\ncontract profile",
        order[1]: "Committed-ledger\nrolling response",
        order[2]: "Committed-ledger\nreference",
        order[3]: "Complete-ledger\nrisk",
    }
    summary["label"] = summary["method"].map(labels)
    summary["order"] = summary["method"].map({name: i for i, name in enumerate(order)})
    # Keep the plot valid if a future protocol adds a comparator: unknown
    # methods are shown after the declared protocol order instead of producing
    # NaN categorical labels or a colour-length mismatch.
    summary["order"] = summary["order"].fillna(len(order))
    summary["label"] = summary["label"].fillna(summary["method"].astype(str))
    summary = summary.sort_values(["order", "method"]).reset_index(drop=True)
    fig, axes = plt.subplots(1, 4, figsize=(15.8, 3.8), constrained_layout=True)
    palette = [COLORS["orange"], COLORS["green"], COLORS["sky"], COLORS["blue"], COLORS["red"]]
    colors = [palette[index % len(palette)] for index in range(len(summary))]
    for axis, metric, ylabel, title in zip(
        axes,
        ["nrmse", "false_response_mwh", "meter_capped_response_mwh", "credit_recall"],
        [
            "Event-window nRMSE",
            "Gross unsupported credit (MWh/day)",
            "Contract-capped payable (MWh/day)",
            "Credit recall",
        ],
        [
            "(a) Error under the information boundary",
            "(b) Gross false-credit exposure",
            "(c) Post-event payable response",
            "(d) Positive-credit recall",
        ],
    ):
        axis.bar(summary["label"], summary[metric], color=colors, edgecolor="white")
        axis.set_title(title)
        axis.set_ylabel(ylabel)
        axis.tick_params(axis="x", rotation=18, labelsize=7.5)
        for tick in axis.get_xticklabels():
            tick.set_horizontalalignment("right")
        if metric == "credit_recall":
            axis.set_ylim(0.0, 1.0)
    save_figure(fig, folder, "fig23_decision_time_information")


def plot_exp18_preventive_ac_panel(
    results: pd.DataFrame,
    folder: Path,
    cfg: dict[str, Any],
) -> None:
    """Plot the cross-network AC N-1 physical diagnostics."""
    configure_style(cfg)
    summary = (
        results.groupby(["network", "peak_dc_penetration", "method"], as_index=False)
        .agg(
            maximum_loading=("maximum_apparent_line_loading", "max"),
            maximum_voltage_violation=("maximum_voltage_violation_pu", "max"),
            outages=("outage", "nunique"),
            maximum_pg_deviation=("maximum_nonreference_active_plan_deviation_mw", "max"),
        )
    )
    proposed = summary[summary["method"] == "Payment-Certified N-1 Verifier"].copy()
    proposed["network_label"] = proposed["network"].str.replace("IEEE ", "", regex=False)
    fig, axes = plt.subplots(1, 3, figsize=(12.0, 3.6), constrained_layout=True)
    sns.lineplot(
        data=proposed,
        x="peak_dc_penetration",
        y="maximum_loading",
        hue="network_label",
        marker="o",
        ax=axes[0],
    )
    axes[0].axhline(1.0, color=COLORS["red"], ls="--", lw=0.9)
    axes[0].set_title("(a) AC N--1 apparent loading")
    axes[0].set_xlabel("Data-center peak penetration")
    axes[0].set_ylabel("Maximum loading (p.u.)")
    axes[0].legend(title="Network", fontsize=7, title_fontsize=8)
    sns.lineplot(
        data=proposed,
        x="peak_dc_penetration",
        y="maximum_voltage_violation",
        hue="network_label",
        marker="o",
        legend=False,
        ax=axes[1],
    )
    axes[1].set_title("(b) Voltage-limit deviation")
    axes[1].set_xlabel("Data-center peak penetration")
    axes[1].set_ylabel("Maximum violation (p.u.)")
    sns.lineplot(
        data=proposed,
        x="peak_dc_penetration",
        y="maximum_pg_deviation",
        hue="network_label",
        marker="o",
        legend=False,
        ax=axes[2],
    )
    axes[2].set_title("(c) Active recourse from intact plan")
    axes[2].set_xlabel("Data-center peak penetration")
    axes[2].set_ylabel("Non-reference $P_G$ deviation (MW)")
    save_figure(fig, folder, "fig24_preventive_ac_cross_network")
