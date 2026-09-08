"""Declaration-only independent event replay for the common witness.

The replay changes only a predeclared event tariff and re-enumerates every
admissible contiguous start from the same submitted-job declarations.  It is
therefore independent of the statistical risk fit and of the Exp27 response
policy while retaining an auditable, executable event meter.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .executable_witness import _aggregate_blocks, _select_exact_starts
from .utils import write_json


def run_declaration_only_replay(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
    *,
    output_experiment: str = "exp23_independent_event_replay",
) -> None:
    """Re-evaluate the common witness under an independently declared tariff."""
    folder = root / "experiments" / output_experiment
    final = folder / "results/final"
    figures = folder / "figures"
    final.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    logger.info("Exp23 declaration-only independent event replay [0%%]")

    witness_path = root / "experiments/exp27_executable_common_witness/results/final/runtime_complete_witness.npz"
    witness_meta_path = root / "experiments/exp27_executable_common_witness/results/final/experiment_metadata.json"
    settlement_path = root / "experiments/exp27_executable_common_witness/results/final/common_witness_settlement.csv"
    test_profile_path = root / "experiments/exp2_baseline_verification/results/intermediate/test_profiles.npz"
    if not witness_path.exists() or not witness_meta_path.exists() or not settlement_path.exists():
        raise FileNotFoundError("Exp23 requires the completed Exp27 common witness")
    witness_meta = json.loads(witness_meta_path.read_text(encoding="utf-8"))
    witness = np.load(witness_path, allow_pickle=False)
    submit = np.asarray(witness["submit_slot"], dtype=np.int64)
    deadline = np.asarray(witness["deadline_slot"], dtype=np.int64)
    runtime = np.asarray(witness["runtime_slots"], dtype=np.int64)
    region = np.asarray(witness["region"], dtype=np.int64)
    gpus = np.asarray(witness["requested_gpus"], dtype=float)
    cap_mw = float(np.asarray(witness["per_gpu_power_cap_mw"], dtype=float).reshape(-1)[0])
    common_baseline = np.asarray(witness["baseline_mwh"], dtype=float)
    common_response = np.asarray(witness["counterfactual_mwh"], dtype=float)
    witness_digest = str(np.asarray(witness["witness_digest"]).reshape(-1)[0])
    if witness_meta.get("profile_identity_asserted") is not True:
        raise RuntimeError("Exp23 cannot score a witness without an identity certificate")
    if not test_profile_path.exists():
        raise FileNotFoundError(f"Locked day index is missing: {test_profile_path}")
    test_days = np.asarray(np.load(test_profile_path, allow_pickle=False)["days"], dtype=int)

    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    slots_per_day = int(cfg["project"]["slots_per_day"])
    queue_buffer = int(witness_meta["queue_buffer_slots"])
    horizon_slots = int(common_baseline.shape[1])
    event_slots = np.asarray(list(map(int, cfg["market"]["event_slots"])), dtype=int)
    event_slot_set = set(event_slots.tolist())
    event_mask = np.asarray([int(t % slots_per_day in event_slot_set) for t in range(horizon_slots + 1)], dtype=np.int8)
    event_prefix = np.concatenate([[0], np.cumsum(event_mask, dtype=np.int64)])
    waiting_cost = float(cfg["workload"]["waiting_cost_per_mwh_slot"][-1])
    independent_price = float(cfg["experiments"].get("independent_event_replay_price_per_mwh", 60.0))
    common_price = float(witness_meta["event_tariff_per_mwh"])
    if np.isclose(independent_price, common_price):
        raise ValueError("Independent replay tariff must differ from the common witness tariff")
    energy_per_slot = gpus * cap_mw * dt_h
    independent_baseline_starts, _ = _select_exact_starts(
        submit, runtime, queue_buffer, energy_per_slot, event_prefix,
        waiting_cost, independent_price, event_price_enabled=False,
    )
    independent_response_starts, _ = _select_exact_starts(
        submit, runtime, queue_buffer, energy_per_slot, event_prefix,
        waiting_cost, independent_price, event_price_enabled=True,
    )
    independent_baseline = _aggregate_blocks(
        independent_baseline_starts, runtime, region, gpus * cap_mw,
        common_baseline.shape[0], horizon_slots, dt_h,
    )
    independent_response = _aggregate_blocks(
        independent_response_starts, runtime, region, gpus * cap_mw,
        common_baseline.shape[0], horizon_slots, dt_h,
    )
    if np.max(np.abs(independent_baseline - common_baseline)) > 1e-12:
        raise RuntimeError("Independent replay changed the common declaration baseline")
    if np.max(np.abs(independent_response - common_response)) <= 1e-12:
        raise RuntimeError("Independent replay collapsed to the common event policy")
    settlement = pd.read_csv(settlement_path)
    if not settlement["counterfactual_witness_profile_sha256"].eq(witness_digest).all():
        raise RuntimeError("Exp23 settlement source is not the common witness")

    rows: list[dict[str, Any]] = []
    for day in test_days:
        day = int(day)
        start = day * slots_per_day
        stop = min(start + slots_per_day, horizon_slots)
        if start >= stop or int(event_slots.max()) + start >= horizon_slots:
            continue
        indices = np.asarray([start + int(slot) for slot in event_slots if start + int(slot) < stop], dtype=int)
        baseline = independent_baseline[:, indices]
        truth_response = independent_response[:, indices]
        assessed_response = common_response[:, indices]
        truth_reduction = np.maximum(baseline - truth_response, 0.0)
        assessed_reduction = np.maximum(baseline - assessed_response, 0.0)
        overlap = np.minimum(truth_reduction, assessed_reduction)
        true_total = float(truth_reduction.sum())
        assessed_total = float(assessed_reduction.sum())
        overlap_total = float(overlap.sum())
        false_response = float(np.maximum(assessed_reduction - truth_reduction, 0.0).sum())
        underpayment = float(np.maximum(truth_reduction - assessed_reduction, 0.0).sum())
        precision = overlap_total / max(assessed_total, 1e-12)
        recall = overlap_total / max(true_total, 1e-12)
        f1 = 2.0 * precision * recall / max(precision + recall, 1e-12)
        scale = max(float(np.mean(np.abs(truth_response))), 1e-12)
        nrmse = float(np.sqrt(np.mean((assessed_response - truth_response) ** 2)) / scale)
        rows.append(
            {
                "day": day,
                "truth_source": "independent declaration-only exact start policy",
                "assessed_source": "Exp27 common runtime-complete witness response",
                "truth_event_reduction_mwh": true_total,
                "assessed_event_reduction_mwh": assessed_total,
                "false_response_mwh": false_response,
                "underpayment_mwh": underpayment,
                "credit_precision": precision,
                "credit_recall": recall,
                "credit_f1": f1,
                "nrmse": nrmse,
                "common_witness_digest": witness_digest,
                "future_arrivals_used": False,
                "execution_telemetry_used": False,
            }
        )
    daily = pd.DataFrame(rows).sort_values("day").reset_index(drop=True)
    if len(daily) != len(test_days):
        raise RuntimeError("Independent replay did not cover every locked day")
    daily.to_csv(final / "independent_event_replay_daily.csv", index=False)
    summary = pd.DataFrame(
        [
            {
                "method": "Common runtime-complete witness",
                "locked_days": int(len(daily)),
                "nrmse": float(daily["nrmse"].mean()),
                "false_response_mwh": float(daily["false_response_mwh"].mean()),
                "underpayment_mwh": float(daily["underpayment_mwh"].mean()),
                "credit_precision": float(daily["credit_precision"].mean()),
                "credit_recall": float(daily["credit_recall"].mean()),
                "credit_f1": float(daily["credit_f1"].mean()),
                "truth_source": "independent declaration-only exact start policy",
            },
            {
                "method": "Independent declaration-only exact policy",
                "locked_days": int(len(daily)),
                "nrmse": 0.0,
                "false_response_mwh": 0.0,
                "underpayment_mwh": 0.0,
                "credit_precision": 1.0,
                "credit_recall": 1.0,
                "credit_f1": 1.0,
                "truth_source": "independent declaration-only exact start policy",
            },
        ]
    )
    summary.to_csv(final / "independent_event_replay_summary.csv", index=False)
    np.savez_compressed(
        final / "independent_event_profiles.npz",
        days=daily["day"].to_numpy(dtype=int),
        independent_baseline=np.asarray(
            [independent_baseline[:, int(day) * slots_per_day + event_slots] for day in daily["day"]]
        ),
        independent_response=np.asarray(
            [independent_response[:, int(day) * slots_per_day + event_slots] for day in daily["day"]]
        ),
        common_response=np.asarray(
            [common_response[:, int(day) * slots_per_day + event_slots] for day in daily["day"]]
        ),
    )
    protocol = pd.DataFrame(
        [
            {"criterion": "post_gate_or_future_arrivals_used", "value": 0, "required_value": 0, "evidence": "all starts use the frozen submission index"},
            {"criterion": "execution_telemetry_used", "value": 0, "required_value": 0, "evidence": "Exp23 reads only declaration fields and the common witness"},
            {"criterion": "independent_tariff_distinct", "value": int(not np.isclose(independent_price, common_price)), "required_value": 1, "evidence": f"independent tariff={independent_price:g}, common tariff={common_price:g} USD/MWh"},
            {"criterion": "same_submission_digest", "value": 1, "required_value": 1, "evidence": witness_digest},
            {"criterion": "same_declaration_baseline", "value": int(np.max(np.abs(independent_baseline - common_baseline)) <= 1e-12), "required_value": 1, "evidence": "exact earliest-start enumeration"},
            {"criterion": "distinct_event_trajectory", "value": int(np.max(np.abs(independent_response - common_response)) > 1e-12), "required_value": 1, "evidence": "pre-scoring profile comparison"},
        ]
    )
    protocol.to_csv(final / "independent_event_protocol_certificate.csv", index=False)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.1, 3.45), constrained_layout=True)
    metrics = ["credit_precision", "credit_recall", "credit_f1"]
    values = [float(daily[name].mean()) for name in metrics]
    bars = ax.bar(metrics, values, color=["#0072B2", "#009E73", "#D55E00"], width=0.58)
    ax.set_ylim(0.0, 1.05)
    ax.set_ylabel("Score against independent declaration replay")
    ax.set_title("Independent exact event replay on the common workload witness")
    ax.grid(axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2.0, value + 0.015, f"{value:.3f}", ha="center", va="bottom", fontsize=8)
    for suffix in ("png", "pdf"):
        fig.savefig(figures / f"fig26_independent_event_replay.{suffix}", dpi=320, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    independent_policy_difference_mw = float(
        np.max(np.abs(independent_response - common_response)) / max(dt_h, 1e-12)
    )
    positive_participant_energy = energy_per_slot[energy_per_slot > 0.0]
    metadata = {
        "experiment": "independent declaration-only event replay",
        "schema_version": 2,
        "locked_days": int(len(daily)),
        "truth_source": "independent declaration-only exact start policy",
        "assessment_source": "Exp27 runtime-complete common witness response",
        "event_intervention": True,
        "common_witness_digest": witness_digest,
        "event_slots": event_slots.tolist(),
        "independent_event_tariff_per_mwh": independent_price,
        "common_witness_event_tariff_per_mwh": common_price,
        "future_arrivals_used": False,
        "execution_telemetry_used": False,
        "causal_intervention_claim": False,
        "independent_policy": {
            "description": "exact enumeration of every contiguous declaration-feasible start under a distinct predeclared event tariff",
            "risk_oracle_reused": False,
            "tariff_pair_distinct_from_gate": bool(not np.isclose(independent_price, common_price)),
            "structurally_distinct_from_gate": bool(independent_policy_difference_mw > 1e-8),
            "minimum_participant_event_mwh": float(np.min(positive_participant_energy)) if len(positive_participant_energy) else 0.0,
            "maximum_response_difference_from_gate_mw": independent_policy_difference_mw,
        },
        "protocol_certificate_file": "independent_event_protocol_certificate.csv",
        "profile_identity_asserted": True,
        "replay_metrics": {
            "mean_nrmse": float(daily["nrmse"].mean()),
            "mean_false_response_mwh": float(daily["false_response_mwh"].mean()),
            "mean_underpayment_mwh": float(daily["underpayment_mwh"].mean()),
            "mean_credit_f1": float(daily["credit_f1"].mean()),
        },
        "files": {
            "daily": "independent_event_replay_daily.csv",
            "summary": "independent_event_replay_summary.csv",
            "profiles": "independent_event_profiles.npz",
            "protocol": "independent_event_protocol_certificate.csv",
            "figure": "fig26_independent_event_replay.pdf",
        },
        "source_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    write_json(final / "experiment_metadata.json", metadata)
    (folder / "README.md").write_text(
        """# Experiment 23: independent declaration-only event replay

The replay retains the Exp27 submission index and runtime-complete job model,
but changes a predeclared event tariff and enumerates all admissible contiguous
starts again. The assessment profile is therefore evaluated against an exact
policy that is independent of the statistical risk fit and of the Exp27 event
tariff. The saved digest certifies that both profiles use the same submitted
jobs. No execution telemetry or future arrivals enter the replay.
""",
        encoding="utf-8",
    )
    logger.info("Exp23 declaration-only independent event replay [100%%]: PASS; mean F1=%.4f", float(daily["credit_f1"].mean()))
