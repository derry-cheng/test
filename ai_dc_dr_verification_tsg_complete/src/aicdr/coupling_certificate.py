"""Exact bridge from job-indexed service to secure network settlement."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .optimization import (
    build_n1_security_factors,
    power_system_from_ppc,
    solve_n1_sced,
)
from .coupling_invariant import (
    assert_valid_certificate,
    validate_job_network_coupling,
)
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
    execution_match = np.asarray(
        data["execution_match"] if "execution_match" in data.files else np.ones(len(starts)),
        dtype=bool,
    )
    if "declared_job_energy_mwh" not in data.files or "requested_gpus" not in data.files or "per_gpu_power_cap_mw" not in data.files:
        raise ValueError(
            "Exp19 witness must include declared job energies, requested GPUs, and "
            "the committed GPU nameplate for an independent feasibility recheck"
        )
    job_energy = np.asarray(data["declared_job_energy_mwh"], dtype=float)
    requested_gpus = np.asarray(data["requested_gpus"], dtype=float)
    per_gpu_power_cap_mw = float(
        np.asarray(data["per_gpu_power_cap_mw"], dtype=float).reshape(-1)[0]
    )
    if not (len(starts) == len(ends) == len(regions)):
        raise ValueError("Exp19 job arrays have inconsistent lengths")
    if not (len(job_energy) == len(requested_gpus) == len(starts)):
        raise ValueError("Exp19 job energy/GPU arrays have inconsistent lengths")
    if np.any(ends <= starts) or np.any(regions < 0):
        raise ValueError("Exp19 job release/deadline or region labels are invalid")
    if (
        not np.isfinite(service).all()
        or not np.isfinite(job_energy).all()
        or not np.isfinite(requested_gpus).all()
        or per_gpu_power_cap_mw <= 0.0
    ):
        raise ValueError("Exp19 witness contains non-finite job-level quantities")
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
    dt_h = float(cfg["project"]["interval_minutes"]) / 60.0
    # Recheck the indexed primal independently of the Exp19 summary.  The
    # network certificate must not trust a saved aggregate profile or a solver
    # status without verifying each job equality, GPU nameplate bound, and
    # regional capacity row from the stored service vector itself.
    job_service = np.add.reduceat(service, offsets[:-1])
    job_energy_residual = job_service - job_energy
    gpu_upper = np.repeat(
        requested_gpus * per_gpu_power_cap_mw * dt_h,
        ends - starts,
    )
    gpu_bound_slack = gpu_upper - service
    minimum_gpu_bound_slack = float(np.min(gpu_bound_slack, initial=np.inf))
    maximum_gpu_bound_violation = float(
        max(0.0, float(np.max(service - gpu_upper, initial=-np.inf)))
    )
    reconstructed_capacity = np.bincount(
        variable_regions * n_slots + slots,
        weights=service,
        minlength=n_regions * n_slots,
    ).reshape(n_regions, n_slots)
    site_capacity_mwh = float(cfg["project"]["flexible_capacity_mw"]) * dt_h
    minimum_site_capacity_slack = float(
        np.min(site_capacity_mwh - reconstructed_capacity)
    )
    maximum_job_energy_residual = float(np.max(np.abs(job_energy_residual)))
    coupling_certificate = validate_job_network_coupling(
        service_mwh=service,
        job_energy_mwh=job_energy,
        submit_slot=starts,
        deadline_slot=ends,
        region=regions,
        aggregate_mwh=saved_counterfactual,
        dt_h=dt_h,
        requested_gpus=requested_gpus,
        per_gpu_power_cap_mw=per_gpu_power_cap_mw,
        site_capacity_mw=float(cfg["project"]["flexible_capacity_mw"]),
    )
    assert_valid_certificate(coupling_certificate)
    # Keep the named residuals used by the existing report, but source them
    # from the typed certificate so the network bridge and the audit use the
    # same numerical contract.
    maximum_job_energy_residual = coupling_certificate.max_job_energy_residual_mwh
    maximum_gpu_bound_violation = coupling_certificate.maximum_gpu_bound_violation_mwh
    minimum_gpu_bound_slack = coupling_certificate.minimum_gpu_bound_slack_mwh
    minimum_site_capacity_slack = coupling_certificate.minimum_site_capacity_slack_mwh
    reconstructed = np.bincount(
        variable_regions * n_slots + slots,
        weights=service,
        minlength=n_regions * n_slots,
    ).reshape(n_regions, n_slots)
    aggregation_residual = reconstructed - saved_counterfactual
    max_aggregation_residual = coupling_certificate.max_aggregation_residual_mwh

    # The indexed coupling certificate uses the same public RTS-24 benchmark
    # as the independently validated N--1 settlement panel.  IEEE-118 is
    # retained for the cross-network and AC panels.  Silently switching cases
    # based on raw-file availability would make the certificate non-reproducible;
    # the case is therefore explicit and immutable here.
    coupled_case = str(
        cfg["experiments"].get("coupled_network_case", "PYPOWER case24_ieee_rts")
    )
    if coupled_case != "PYPOWER case24_ieee_rts":
        raise ValueError(
            "coupled_network_case must be the predeclared PYPOWER case24_ieee_rts"
        )
    from pypower.case24_ieee_rts import case24_ieee_rts

    system = power_system_from_ppc(case24_ieee_rts())
    network_source = "PYPOWER case24_ieee_rts (public RTS-24 benchmark)"
    security = build_n1_security_factors(system)
    dc_buses = np.asarray(
        cfg["experiments"].get("coupled_network_buses_one_based", [3, 8, 15, 21]),
        dtype=int,
    ) - 1
    if (
        dc_buses.shape != (n_regions,)
        or np.any(dc_buses < 0)
        or np.any(dc_buses >= len(system.bus))
    ):
        raise ValueError("Configured network data-center buses do not match the job regions")
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
    mapping = np.zeros((len(system.bus), n_regions), dtype=float)
    mapping[dc_buses, np.arange(n_regions)] = 1.0
    # The profile passed to the mapping certificate retains every slot.  The
    # network solve below uses the declared event-window mean only after this
    # dimension-preserving check has completed.
    network_profile_mw = mapping @ (reconstructed / dt_h)
    mapped_certificate = validate_job_network_coupling(
        service_mwh=service,
        job_energy_mwh=job_energy,
        submit_slot=starts,
        deadline_slot=ends,
        region=regions,
        aggregate_mwh=saved_counterfactual,
        dt_h=dt_h,
        requested_gpus=requested_gpus,
        per_gpu_power_cap_mw=per_gpu_power_cap_mw,
        site_capacity_mw=float(cfg["project"]["flexible_capacity_mw"]),
        network_profile_mw=network_profile_mw,
        network_mapping=mapping,
    )
    assert_valid_certificate(mapped_certificate)
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
            "scenario": "raw_job_witness",
            "scale_factor": 1.0,
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
            "maximum_job_energy_residual_mwh": maximum_job_energy_residual,
            "maximum_gpu_bound_violation_mwh": maximum_gpu_bound_violation,
            "minimum_gpu_bound_slack_mwh": minimum_gpu_bound_slack,
            "minimum_site_capacity_slack_mwh": minimum_site_capacity_slack,
            "solver_success": bool(native_result.success and counterfactual_result.success),
            "coupling_certificate_valid": bool(mapped_certificate.valid),
            "network_mapping_residual_mw": float(mapped_certificate.max_network_mapping_residual_mw),
        }
    ]

    # The raw MIT witness is intentionally tiny relative to the declared
    # benchmark nameplate.  Exp21 supplies two predeclared homogeneous scale
    # factors; replaying the *same* indexed service vector at those scales
    # closes the job-to-network scale gap without inventing a second aggregate
    # trajectory.  Every physical quantity in the certificate is scaled: job
    # energy, service, GPU nameplate, site capacity, and the network profile.
    scale_path = (
        root
        / "experiments/exp21_scale_consistency/results/final/"
        "scale_consistency_summary.csv"
    )
    if not scale_path.exists():
        raise FileNotFoundError(
            "Exp21 scale-consistency summary is required before the coupled replay"
        )
    scale_frame = pd.read_csv(scale_path)
    scale_values = {
        "fixed_nameplate_homogeneous": float(
            scale_frame.loc[
                scale_frame["metric"].astype(str)
                == "fixed_nameplate_certified_scale_factor",
                "value",
            ].iloc[0]
        ),
        "capacity_proportional_homogeneous": float(
            scale_frame.loc[
                scale_frame["metric"].astype(str)
                == "capacity_proportional_network_scale_factor",
                "value",
            ].iloc[0]
        ),
    }
    scaled_rows: list[dict[str, Any]] = []
    for scenario, scale_factor in scale_values.items():
        if not np.isfinite(scale_factor) or scale_factor <= 0.0:
            raise RuntimeError(f"Invalid Exp21 scale factor for {scenario}")
        scaled_service = service * scale_factor
        scaled_job_energy = job_energy * scale_factor
        scaled_aggregate = saved_counterfactual * scale_factor
        scaled_reconstructed = np.bincount(
            variable_regions * n_slots + slots,
            weights=scaled_service,
            minlength=n_regions * n_slots,
        ).reshape(n_regions, n_slots)
        scaled_certificate = validate_job_network_coupling(
            service_mwh=scaled_service,
            job_energy_mwh=scaled_job_energy,
            submit_slot=starts,
            deadline_slot=ends,
            region=regions,
            aggregate_mwh=scaled_aggregate,
            dt_h=dt_h,
            requested_gpus=requested_gpus,
            per_gpu_power_cap_mw=per_gpu_power_cap_mw * scale_factor,
            site_capacity_mw=float(cfg["project"]["flexible_capacity_mw"]) * scale_factor,
            network_profile_mw=mapping @ (scaled_aggregate / dt_h),
            network_mapping=mapping,
        )
        assert_valid_certificate(scaled_certificate)
        scaled_native_event = (saved_native * scale_factor)[:, selected_slots].mean(axis=1)
        scaled_counterfactual_event = scaled_aggregate[:, selected_slots].mean(axis=1)
        scaled_native_load = base_load.copy()
        scaled_counterfactual_load = base_load.copy()
        scaled_native_load[dc_buses] += scaled_native_event / dt_h
        scaled_counterfactual_load[dc_buses] += scaled_counterfactual_event / dt_h
        scaled_native_result = solve_n1_sced(
            system, scaled_native_load, network_segments, security_factors=security
        )
        scaled_counterfactual_result = solve_n1_sced(
            system,
            scaled_counterfactual_load,
            network_segments,
            security_factors=security,
        )
        scaled_rows.append(
            {
                "scenario": scenario,
                "scale_factor": float(scale_factor),
                "slot": "event_window_mean",
                "event_slot_count": len(selected_slots),
                "native_profile_mwh": float((saved_native * scale_factor)[:, selected_slots].sum()),
                "counterfactual_profile_mwh": float(scaled_aggregate[:, selected_slots].sum()),
                "aggregation_residual_mwh": float(
                    np.abs(
                        (scaled_reconstructed - scaled_aggregate)[:, selected_slots]
                    ).sum()
                ),
                "native_secure_cost_usd_per_interval": float(scaled_native_result.objective * dt_h),
                "counterfactual_secure_cost_usd_per_interval": float(scaled_counterfactual_result.objective * dt_h),
                "secure_net_value_usd_per_interval": float(
                    (scaled_native_result.objective - scaled_counterfactual_result.objective) * dt_h
                ),
                "native_max_base_loading": float(scaled_native_result.max_loading),
                "counterfactual_max_base_loading": float(scaled_counterfactual_result.max_loading),
                "native_max_postcontingency_loading": float(scaled_native_result.max_post_contingency_loading),
                "counterfactual_max_postcontingency_loading": float(scaled_counterfactual_result.max_post_contingency_loading),
                "credible_contingencies": int(scaled_counterfactual_result.credible_contingencies),
                "maximum_job_energy_residual_mwh": scaled_certificate.max_job_energy_residual_mwh,
                "maximum_gpu_bound_violation_mwh": scaled_certificate.maximum_gpu_bound_violation_mwh,
                "minimum_gpu_bound_slack_mwh": scaled_certificate.minimum_gpu_bound_slack_mwh,
                "minimum_site_capacity_slack_mwh": scaled_certificate.minimum_site_capacity_slack_mwh,
                "solver_success": bool(
                    scaled_native_result.success and scaled_counterfactual_result.success
                ),
                "coupling_certificate_valid": bool(scaled_certificate.valid),
                "network_mapping_residual_mw": float(
                    scaled_certificate.max_network_mapping_residual_mw
                ),
            }
        )
    rows.extend(scaled_rows)
    frame = pd.DataFrame(rows)
    frame.to_csv(out / "coupled_network_event_replay.csv", index=False)
    frame[frame["scenario"] != "raw_job_witness"].to_csv(
        out / "coupled_network_scale_replay.csv", index=False
    )
    event_native = float(saved_native[:, selected_slots].sum())
    event_counterfactual = float(reconstructed[:, selected_slots].sum())
    summary = pd.DataFrame(
        [
            {"metric": "submitted_jobs", "value": n_jobs, "unit": "jobs"},
            {"metric": "execution_matched_jobs", "value": int(execution_match.sum()), "unit": "jobs"},
            {"metric": "service_variables", "value": len(service), "unit": "variables"},
            {"metric": "event_slots_replayed", "value": len(selected_slots), "unit": "slots"},
            {"metric": "maximum_job_to_aggregate_residual_mwh", "value": max_aggregation_residual, "unit": "MWh"},
            {"metric": "maximum_job_energy_recheck_residual_mwh", "value": maximum_job_energy_residual, "unit": "MWh"},
            {"metric": "maximum_gpu_bound_violation_mwh", "value": maximum_gpu_bound_violation, "unit": "MWh"},
            {"metric": "minimum_gpu_bound_slack_mwh", "value": minimum_gpu_bound_slack, "unit": "MWh"},
            {"metric": "minimum_site_capacity_slack_mwh", "value": minimum_site_capacity_slack, "unit": "MWh"},
            {"metric": "event_native_job_profile_mwh", "value": event_native, "unit": "MWh"},
            {"metric": "event_counterfactual_job_profile_mwh", "value": event_counterfactual, "unit": "MWh"},
            {"metric": "event_secure_network_value_usd_per_interval", "value": float(rows[0]["secure_net_value_usd_per_interval"]), "unit": "USD/interval"},
            {"metric": "homogeneous_scaled_scenario_count", "value": len(scaled_rows), "unit": "scenarios"},
            {"metric": "maximum_homogeneous_scaled_network_value_usd_per_interval", "value": float(max(row["secure_net_value_usd_per_interval"] for row in scaled_rows)), "unit": "USD/interval"},
            {"metric": "maximum_counterfactual_base_loading", "value": float(frame["counterfactual_max_base_loading"].max()), "unit": "ratio"},
            {"metric": "maximum_counterfactual_postcontingency_loading", "value": float(frame["counterfactual_max_postcontingency_loading"].max()), "unit": "ratio"},
            {"metric": "all_network_solves_successful", "value": int(frame["solver_success"].all()), "unit": "boolean"},
        ]
    )
    summary.to_csv(out / "coupled_network_summary.csv", index=False)
    metadata = {
        "experiment": "exact job-to-network coupling certificate",
        "source_solution": str(source.relative_to(root)),
        "submitted_jobs": n_jobs,
        "execution_matched_jobs": int(execution_match.sum()),
        "execution_ledger_role": "post-event scoring only",
        "aggregation_equation": "p[r,t] = sum_{j:region_j=r, t in window_j} u[j,t]",
        "network_load_equation": (
            f"L_t = L_base * {native_multiplier:.6g} + B p_t / Delta t"
        ),
        "network_load_multiplier": native_multiplier,
        "network_value_model": "secure DC SCED with every finite non-islanding N-1 branch contingency",
        "network_case": "IEEE RTS-24 (PYPOWER case24_ieee_rts)",
        "network_generator_segments": network_segments,
        "network_parallel_workers": workers,
        "network_time_aggregation": "arithmetic mean of every declared event slot; network value is reported per representative interval",
        "scale_replay_file": "coupled_network_scale_replay.csv",
        "scale_replay_definition": (
            "The raw indexed witness and two predeclared homogeneous transforms "
            "(fixed-nameplate and capacity-proportional) are replayed through the "
            "same RTS-24 N-1 evaluator. Each transform scales service, declared "
            "job energy, GPU cap, site capacity, and network load together."
        ),
        "scale_factors": {
            "raw_job_witness": 1.0,
            **{key: float(value) for key, value in scale_values.items()},
        },
        "raw_witness_is_not_118mw": True,
        "capacity_proportional_network_stress_is_same_job_witness": True,
        "network_source": network_source,
        "data_center_buses_one_based": (dc_buses + 1).tolist(),
        "event_slots": sorted(event_slots),
        "replayed_event_slot_count": len(selected_slots),
        "maximum_job_to_aggregate_residual_mwh": max_aggregation_residual,
        "independent_job_feasibility_recheck": True,
        "maximum_job_energy_recheck_residual_mwh": maximum_job_energy_residual,
        "maximum_gpu_bound_violation_mwh": maximum_gpu_bound_violation,
        "minimum_gpu_bound_slack_mwh": minimum_gpu_bound_slack,
        "minimum_site_capacity_slack_mwh": minimum_site_capacity_slack,
        "network_profile_is_same_job_witness": True,
        "post_solution_profile_reoptimization": False,
        "all_network_solves_successful": bool(frame["solver_success"].all()),
        "coupling_invariant_certificate": coupling_certificate.to_dict(),
        "network_mapping_certificate": mapped_certificate.to_dict(),
    }
    write_json(out / "experiment_metadata.json", metadata)
    write_json(
        out / "coupling_invariant_certificate.json",
        {
            "certificate": coupling_certificate.to_dict(),
            "network_mapping_certificate": mapped_certificate.to_dict(),
            "mapping_one_hot_bus_indices_zero_based": dc_buses.tolist(),
        },
    )
    logger.info(
        "Experiment 22 complete: %d job variables aggregated with max residual %.3e MWh; event network value %.6f USD",
        len(service),
        max_aggregation_residual,
        float(frame["secure_net_value_usd_per_interval"].sum()),
    )
