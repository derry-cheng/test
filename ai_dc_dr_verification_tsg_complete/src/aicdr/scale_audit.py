"""Exact scale-consistency audit for the job-level certificate."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def run_exp21_scale_consistency(root: Path, cfg: dict[str, Any], logger: logging.Logger) -> None:
    """Report network-proportional and fixed-nameplate scale certificates.

    Uniform scaling is an exact witness only when every declared resource cap
    is scaled with it.  The study therefore reports both a fixed-nameplate
    reference scale and a larger capacity-proportional network stress scale;
    Exp22 replays each as a homogeneous transform of the same indexed witness.
    No profile is repaired by clipping or by a heuristic post-processing rule.
    """
    source = root / "experiments/exp19_job_level_counterfactual/results/final/job_level_counterfactual_solution.npz"
    if not source.exists():
        raise FileNotFoundError("Exp19 exact primal is required before Exp21 scale audit")
    out = root / "experiments/exp21_scale_consistency/results/final"
    out.mkdir(parents=True, exist_ok=True)
    data = np.load(source)
    native = np.asarray(data["native_mwh"], dtype=float)
    counterfactual = np.asarray(data["counterfactual_mwh"], dtype=float)
    source_scale = float(data["source_scale_factor"]) if "source_scale_factor" in data.files else 1.0
    if source_scale <= 0.0:
        raise ValueError("Exp19 source_scale_factor must be positive")
    native_raw, counterfactual_raw = native / source_scale, counterfactual / source_scale
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    capacity_mw = float(cfg["project"]["flexible_capacity_mw"])
    manifest = json.loads((root / cfg["data"]["processed_dir"] / "data_manifest.json").read_text())
    declared = float(manifest["processing"]["batch_hyperscale_multiplier"])
    raw_peak_mw = float(max(native_raw.max(), counterfactual_raw.max()) / dt_h)
    capacity_safe = capacity_mw / max(raw_peak_mw, 1e-12)
    fixed_gpu_cap_mw = float(
        cfg["experiments"].get("job_level_declared_per_gpu_power_cap_mw", 1.0e-3)
    )
    starts = np.asarray(data["submit_slot"], dtype=np.int64)
    ends = np.asarray(data["deadline_slot"], dtype=np.int64)
    gpu_key = "requested_gpus" if "requested_gpus" in data.files else "measured_gpus"
    gpus = np.asarray(data[gpu_key], dtype=float)
    counts = np.maximum(0, ends - starts)
    service = np.asarray(data["service_mwh"], dtype=float)
    variable_cap = np.repeat(gpus * fixed_gpu_cap_mw * dt_h, counts)
    positive_service = service > 1.0e-15
    fixed_nameplate_scale = float(
        np.min(variable_cap[positive_service] / service[positive_service])
    )
    capacity_scale = min(declared, capacity_safe)
    fixed_scale = min(capacity_scale, fixed_nameplate_scale)
    # ``capacity_profile`` is a network-capacity stress scenario whose GPU
    # nameplate is scaled proportionally. ``deployable_profile`` respects the
    # fixed 0.001 MW/GPU declaration and is the contractual certificate.
    capacity_native, capacity_cf = native_raw * capacity_scale, counterfactual_raw * capacity_scale
    native_s, cf_s = native_raw * fixed_scale, counterfactual_raw * fixed_scale
    cap_mwh = capacity_mw * dt_h
    slack = cap_mwh - cf_s
    capacity_slack = cap_mwh - capacity_cf
    slots_per_day = int(cfg["project"]["slots_per_day"])
    events = set(map(int, cfg["market"]["event_slots"]))
    event_idx = np.array([i for i in range(cf_s.shape[1]) if i % slots_per_day in events], dtype=int)
    rows = pd.DataFrame([
        {"metric": "source_exp19_scale_factor", "value": source_scale, "unit": "x"},
        {"metric": "declared_batch_hyperscale_multiplier", "value": declared, "unit": "x"},
        {"metric": "capacity_safe_scale_factor", "value": capacity_safe, "unit": "x"},
        {"metric": "capacity_proportional_network_scale_factor", "value": capacity_scale, "unit": "x"},
        {"metric": "fixed_gpu_nameplate_scale_factor", "value": fixed_nameplate_scale, "unit": "x"},
        {"metric": "fixed_nameplate_certified_scale_factor", "value": fixed_scale, "unit": "x"},
        {"metric": "certified_scale_factor", "value": fixed_scale, "unit": "x"},
        {"metric": "raw_peak_mw", "value": raw_peak_mw, "unit": "MW"},
        {"metric": "capacity_proportional_network_peak_mw", "value": float(max(capacity_native.max(), capacity_cf.max()) / dt_h), "unit": "MW"},
        {"metric": "certified_peak_mw", "value": float(max(native_s.max(), cf_s.max()) / dt_h), "unit": "MW"},
        {"metric": "minimum_capacity_slack_mwh", "value": float(slack.min()), "unit": "MWh"},
        {"metric": "capacity_proportional_minimum_capacity_slack_mwh", "value": float(capacity_slack.min()), "unit": "MWh"},
        {"metric": "event_native_mwh", "value": float(native_s[:, event_idx].sum()), "unit": "MWh"},
        {"metric": "event_counterfactual_mwh", "value": float(cf_s[:, event_idx].sum()), "unit": "MWh"},
        {"metric": "event_gross_reduction_mwh", "value": float(np.clip(native_s[:, event_idx]-cf_s[:, event_idx], 0, None).sum()), "unit": "MWh"},
        {"metric": "event_rebound_mwh", "value": float(np.clip(cf_s[:, event_idx]-native_s[:, event_idx], 0, None).sum()), "unit": "MWh"},
        {"metric": "capacity_proportional_event_native_mwh", "value": float(capacity_native[:, event_idx].sum()), "unit": "MWh"},
        {"metric": "capacity_proportional_event_counterfactual_mwh", "value": float(capacity_cf[:, event_idx].sum()), "unit": "MWh"},
        {"metric": "capacity_proportional_event_gross_reduction_mwh", "value": float(np.clip(capacity_native[:, event_idx]-capacity_cf[:, event_idx], 0, None).sum()), "unit": "MWh"},
        {"metric": "homogeneous_resource_scaling_for_coupling", "value": 1.0, "unit": "boolean"},
    ])
    rows.to_csv(out / "scale_consistency_summary.csv", index=False)
    profile = []
    for r in range(native.shape[0]):
        for s in range(native.shape[1]):
            profile.append({"region": r, "slot": s, "native_mwh": native_s[r,s], "counterfactual_mwh": cf_s[r,s], "capacity_slack_mwh": slack[r,s]})
    pd.DataFrame(profile).to_csv(out / "scale_consistency_profile.csv", index=False)
    capacity_profile = []
    for r in range(native.shape[0]):
        for s in range(native.shape[1]):
            capacity_profile.append({
                "region": r,
                "slot": s,
                "native_mwh": float(capacity_native[r, s]),
                "counterfactual_mwh": float(capacity_cf[r, s]),
                "capacity_slack_mwh": float(capacity_slack[r, s]),
            })
    pd.DataFrame(capacity_profile).to_csv(out / "capacity_proportional_profile.csv", index=False)
    (out / "experiment_metadata.json").write_text(json.dumps({
        "experiment": "exact homogeneous scale-consistency certificate",
        "source": str(source.relative_to(root)),
        "proof_basis": "fixed-nameplate scaling preserves release/deadline support, job-energy equalities, nonnegativity, and the declared GPU upper bounds; the larger network-capacity profile is a proportional stress scenario",
        "source_scale": source_scale,
        "declared_scale": declared,
        "capacity_safe_scale": capacity_safe,
        "capacity_proportional_network_scale": capacity_scale,
        "fixed_gpu_nameplate_scale": fixed_nameplate_scale,
        "fixed_nameplate_certified_scale": fixed_scale,
        "certified_scale": fixed_scale,
        "capacity_proportional_profile_is_stress_scenario": True,
        "homogeneous_scale_replay_scales_all_resource_caps": True,
        "deployable_profile_respects_fixed_gpu_nameplate": True,
        "scale_semantics": (
            "The scale factors are reference transforms. Exp22 scales the job "
            "service, declared job energy, GPU cap, site capacity, and network "
            "load together before rechecking the typed coupling invariant."
        ),
        "resource_count_source": "submit-time requested_gpus" if gpu_key == "requested_gpus" else "legacy measured_gpus",
        "capacity_mw": capacity_mw, "re_solved": False,
    }, indent=2), encoding="utf-8")
    logger.info(
        "Experiment 21 complete: deployable fixed-nameplate scale %.3fx; "
        "network-proportional stress scale %.3fx (capacity-safe %.3fx)",
        fixed_scale,
        capacity_scale,
        capacity_safe,
    )
