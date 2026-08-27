"""Exact scale-consistency audit for the job-level certificate."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def run_exp21_scale_consistency(root: Path, cfg: dict[str, Any], logger: logging.Logger) -> None:
    """Construct a capacity-safe witness by uniform scaling of a feasible primal.

    Every job-energy equality and GPU upper bound is homogeneous in the same
    scale. Consequently, scaling the stored feasible primal is an exact
    certificate, not a heuristic schedule repair and does not require another
    multi-million-variable LP solve.
    """
    source = root / "experiments/exp19_job_level_counterfactual/results/final/job_level_counterfactual_solution.npz"
    if not source.exists():
        raise FileNotFoundError("Exp19 exact primal is required before Exp21 scale audit")
    out = root / "experiments/exp21_scale_consistency/results/final"
    out.mkdir(parents=True, exist_ok=True)
    data = np.load(source)
    native = np.asarray(data["native_mwh"], dtype=float)
    counterfactual = np.asarray(data["counterfactual_mwh"], dtype=float)
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    capacity_mw = float(cfg["project"]["flexible_capacity_mw"])
    manifest = json.loads((root / cfg["data"]["processed_dir"] / "data_manifest.json").read_text())
    declared = float(manifest["processing"]["batch_hyperscale_multiplier"])
    raw_peak_mw = float(max(native.max(), counterfactual.max()) / dt_h)
    capacity_safe = capacity_mw / max(raw_peak_mw, 1e-12)
    scale = min(declared, capacity_safe)
    native_s, cf_s = native * scale, counterfactual * scale
    cap_mwh = capacity_mw * dt_h
    slack = cap_mwh - cf_s
    slots_per_day = int(cfg["project"]["slots_per_day"])
    events = set(map(int, cfg["market"]["event_slots"]))
    event_idx = np.array([i for i in range(cf_s.shape[1]) if i % slots_per_day in events], dtype=int)
    rows = pd.DataFrame([
        {"metric": "declared_batch_hyperscale_multiplier", "value": declared, "unit": "x"},
        {"metric": "capacity_safe_scale_factor", "value": capacity_safe, "unit": "x"},
        {"metric": "certified_scale_factor", "value": scale, "unit": "x"},
        {"metric": "raw_peak_mw", "value": raw_peak_mw, "unit": "MW"},
        {"metric": "certified_peak_mw", "value": float(max(native_s.max(), cf_s.max()) / dt_h), "unit": "MW"},
        {"metric": "minimum_capacity_slack_mwh", "value": float(slack.min()), "unit": "MWh"},
        {"metric": "event_native_mwh", "value": float(native_s[:, event_idx].sum()), "unit": "MWh"},
        {"metric": "event_counterfactual_mwh", "value": float(cf_s[:, event_idx].sum()), "unit": "MWh"},
        {"metric": "event_gross_reduction_mwh", "value": float(np.clip(native_s[:, event_idx]-cf_s[:, event_idx], 0, None).sum()), "unit": "MWh"},
        {"metric": "event_rebound_mwh", "value": float(np.clip(cf_s[:, event_idx]-native_s[:, event_idx], 0, None).sum()), "unit": "MWh"},
    ])
    rows.to_csv(out / "scale_consistency_summary.csv", index=False)
    profile = []
    for r in range(native.shape[0]):
        for s in range(native.shape[1]):
            profile.append({"region": r, "slot": s, "native_mwh": native_s[r,s], "counterfactual_mwh": cf_s[r,s], "capacity_slack_mwh": slack[r,s]})
    pd.DataFrame(profile).to_csv(out / "scale_consistency_profile.csv", index=False)
    (out / "experiment_metadata.json").write_text(json.dumps({
        "experiment": "exact homogeneous scale-consistency certificate",
        "source": str(source.relative_to(root)),
        "proof_basis": "uniform scaling preserves release/deadline support, job-energy equalities, nonnegativity, and proportional GPU upper bounds",
        "declared_scale": declared, "capacity_safe_scale": capacity_safe, "certified_scale": scale,
        "capacity_mw": capacity_mw, "re_solved": False,
    }, indent=2), encoding="utf-8")
    logger.info("Experiment 21 complete: certified scale %.3fx (capacity-safe %.3fx)", scale, capacity_safe)
