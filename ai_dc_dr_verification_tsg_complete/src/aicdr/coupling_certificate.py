"""Exact bridge from job-indexed service to secure network settlement."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .optimization import build_n1_security_factors, solve_n1_sced
from .utils import write_json


def run_exp22_coupled_job_network_certificate(
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger,
) -> None:
    """Replay the exact Exp19 primal through the N--1 settlement model.

    The certificate has one source of truth: the saved job service vector
    ``u_{j,t}``.  The regional profile used by the network is reconstructed
    from that vector and compared with the Exp19 aggregate before any SCED is
    solved.  Thus a network value cannot be attached to a separately optimized
    aggregate trajectory.  The network replay is intentionally restricted to
    the declared event slots to keep the audit small and deterministic.
    """
    source = (
        root
        / "experiments/exp19_job_level_counterfactual/results/final/"
        "job_level_counterfactual_solution.npz"
    )
    if not source.exists():
        raise FileNotFoundError(
            "Exp19 exact job-level solution is required before the coupled certificate"
        )
    out = root / "experiments/exp22_coupled_job_network_certificate/results/final"
    out.mkdir(parents=True, exist_ok=True)

    data = np.load(source, allow_pickle=False)
    service = np.asarray(data["service_mwh"], dtype=float)
    starts = np.asarray(data["submit_slot"], dtype=np.int64)
    ends = np.asarray(data["deadline_slot"], dtype=np.int64)
    regions = np.asarray(data["region"], dtype=np.int64)
    saved_counterfactual = np.asarray(data["counterfactual_mwh"], dtype=float)
    saved_native = np.asarray(data["native_mwh"], dtype=float)
    if not (len(starts) == len(ends) == len(regions)):
        raise ValueError("Exp19 job arrays have inconsistent lengths")
    if np.any(ends <= starts) or np.any(regions < 0):
        raise ValueError("Exp19 job release/deadline or region labels are invalid")
    n_jobs = len(starts)
    n_regions, n_slots = saved_counterfactual.shape
    offsets = np.concatenate([[0], np.cumsum(ends - starts, dtype=np.int64)])
    if int(offsets[-1]) != len(service):
        raise ValueError(
            "Exp19 service vector length does not equal the declared job windows"
        )
    slots = np.concatenate(
        [np.arange(int(start), int(end), dtype=np.int64) for start, end in zip(starts, ends)]
    )
    variable_regions = np.repeat(regions, ends - starts)
    if np.any(slots < 0) or np.any(slots >= n_slots):
        raise ValueError("Exp19 job windows exceed the saved network horizon")
    reconstructed = np.bincount(
        variable_regions * n_slots + slots,
        weights=service,
        minlength=n_regions * n_slots,
    ).reshape(n_regions, n_slots)
    aggregation_residual = reconstructed - saved_counterfactual
    max_aggregation_residual = float(np.max(np.abs(aggregation_residual)))
    if max_aggregation_residual > 1.0e-12:
        raise RuntimeError(
            "The saved Exp19 regional profile is not the aggregation of its job witness: "
            f"max residual {max_aggregation_residual:.3e} MWh"
        )

    # Use the same public IEEE-118 network family as the compact audit path.
    # Full-data runs substitute the declared PGLib case through Exp2's input
    # loader; this certificate records which path was available.
    network_path = root / cfg["data"]["pglib_case"]
    if network_path.exists():
        from .optimization import parse_pglib_case

        system = parse_pglib_case(network_path)
        network_source = str(network_path.relative_to(root))
    else:
        from pypower.case118 import case118
        from .optimization import power_system_from_ppc

        system = power_system_from_ppc(case118())
        network_source = "vendored PYPOWER case118 (compact checkout fallback)"
    security = build_n1_security_factors(system)
    dc_buses = np.asarray(cfg["project"]["data_center_buses"], dtype=int) - 1
    if dc_buses.shape != (n_regions,) or np.any(dc_buses < 0) or np.any(dc_buses >= len(system.bus)):
        raise ValueError("Configured network data-center buses do not match the job regions")
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    native_multiplier = float(cfg["experiments"].get("n1_load_multiplier", 0.9))
    base_load = np.asarray(system.bus[:, 2], dtype=float) * native_multiplier
    event_slots = set(map(int, cfg["market"]["event_slots"]))
    selected_slots = [
        slot for slot in range(n_slots)
        if slot % int(cfg["project"]["slots_per_day"]) in event_slots
    ]
    network_segments = int(
        cfg["experiments"].get(
            "coupled_network_generator_segments",
            cfg["experiments"].get("payment_certificate_generator_segments", 4),
        )
    )
    workers = int(cfg["experiments"].get("coupled_network_parallel_workers", 1))
    if network_segments <= 0 or not 1 <= workers <= 20:
        raise ValueError("coupled network segments/workers are outside the declared limits")
    # The full job trace is first aggregated exactly over the declared event
    # slots.  The secure network model is then solved for this event-window
    # mean profile; this is a declared linear time aggregation, not an
    # outcome-selected slot or a post-solution clipping rule.  It keeps the
    # certificate bounded while preserving the exact job-to-profile equality
    # across every underlying slot.
    native_event_profile = saved_native[:, selected_slots].mean(axis=1)
    counterfactual_event_profile = reconstructed[:, selected_slots].mean(axis=1)
    native_load = base_load.copy()
    counterfactual_load = base_load.copy()
    native_load[dc_buses] += native_event_profile / dt_h
    counterfactual_load[dc_buses] += counterfactual_event_profile / dt_h
    native_result = solve_n1_sced(
        system,
        native_load,
        network_segments,
        security_factors=security,
    )
    counterfactual_result = solve_n1_sced(
        system,
        counterfactual_load,
        network_segments,
        security_factors=security,
    )
    rows = [
        {
            "slot": "event_window_mean",
            "event_slot_count": len(selected_slots),
            "native_profile_mwh": float(native_event_profile.sum()),
            "counterfactual_profile_mwh": float(counterfactual_event_profile.sum()),
            "aggregation_residual_mwh": float(np.abs(aggregation_residual[:, selected_slots]).sum()),
            "native_secure_cost_usd_per_interval": float(native_result.objective * dt_h),
            "counterfactual_secure_cost_usd_per_interval": float(counterfactual_result.objective * dt_h),
            "secure_net_value_usd_per_interval": float((native_result.objective - counterfactual_result.objective) * dt_h),
            "native_max_base_loading": float(native_result.max_loading),
            "counterfactual_max_base_loading": float(counterfactual_result.max_loading),
            "native_max_postcontingency_loading": float(native_result.max_post_contingency_loading),
            "counterfactual_max_postcontingency_loading": float(counterfactual_result.max_post_contingency_loading),
            "credible_contingencies": int(counterfactual_result.credible_contingencies),
            "solver_success": bool(native_result.success and counterfactual_result.success),
        }
    ]
    frame = pd.DataFrame(rows)
    frame.to_csv(out / "coupled_network_event_replay.csv", index=False)
    event_native = float(saved_native[:, selected_slots].sum())
    event_counterfactual = float(reconstructed[:, selected_slots].sum())
    summary = pd.DataFrame(
        [
            {"metric": "positive_energy_jobs", "value": n_jobs, "unit": "jobs"},
            {"metric": "service_variables", "value": len(service), "unit": "variables"},
            {"metric": "event_slots_replayed", "value": len(selected_slots), "unit": "slots"},
            {"metric": "maximum_job_to_aggregate_residual_mwh", "value": max_aggregation_residual, "unit": "MWh"},
            {"metric": "event_native_job_profile_mwh", "value": event_native, "unit": "MWh"},
            {"metric": "event_counterfactual_job_profile_mwh", "value": event_counterfactual, "unit": "MWh"},
            {"metric": "event_secure_network_value_usd_per_interval", "value": float(frame["secure_net_value_usd_per_interval"].sum()), "unit": "USD/interval"},
            {"metric": "maximum_counterfactual_base_loading", "value": float(frame["counterfactual_max_base_loading"].max()), "unit": "ratio"},
            {"metric": "maximum_counterfactual_postcontingency_loading", "value": float(frame["counterfactual_max_postcontingency_loading"].max()), "unit": "ratio"},
            {"metric": "all_network_solves_successful", "value": int(frame["solver_success"].all()), "unit": "boolean"},
        ]
    )
    summary.to_csv(out / "coupled_network_summary.csv", index=False)
    metadata = {
        "experiment": "exact job-to-network coupling certificate",
        "source_solution": str(source.relative_to(root)),
        "aggregation_equation": "p[r,t] = sum_{j:region_j=r, t in window_j} u[j,t]",
        "network_load_equation": "L_t = L_base * 0.90 + B p_t / Delta t",
        "network_value_model": "secure DC SCED with every finite non-islanding N-1 branch contingency",
        "network_generator_segments": network_segments,
        "network_parallel_workers": workers,
        "network_time_aggregation": "arithmetic mean of every declared event slot; network value is reported per representative interval",
        "network_source": network_source,
        "data_center_buses_one_based": (dc_buses + 1).tolist(),
        "event_slots": sorted(event_slots),
        "replayed_event_slot_count": len(selected_slots),
        "maximum_job_to_aggregate_residual_mwh": max_aggregation_residual,
        "network_profile_is_same_job_witness": True,
        "post_solution_profile_reoptimization": False,
        "all_network_solves_successful": bool(frame["solver_success"].all()),
    }
    write_json(out / "experiment_metadata.json", metadata)
    logger.info(
        "Experiment 22 complete: %d job variables aggregated with max residual %.3e MWh; event network value %.6f USD",
        len(service),
        max_aggregation_residual,
        float(frame["secure_net_value_usd_per_interval"].sum()),
    )
