"""Typed, dimension-preserving certificates for the job/network bridge.

The settlement model must consume the same committed service vector as the
job-level LP.  This module keeps that statement executable instead of leaving
it as an aggregation identity in the manuscript.  All checks are in physical
units (MWh or MW); callers may serialize the returned certificate without
serializing the large primal vector itself.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class CouplingInvariantCertificate:
    """Residuals and bounds for one indexed workload/network witness."""

    version: str
    jobs: int
    service_variables: int
    regions: int
    slots: int
    dt_h: float
    max_job_energy_residual_mwh: float
    max_aggregation_residual_mwh: float
    max_network_mapping_residual_mw: float
    minimum_service_mwh: float
    minimum_gpu_bound_slack_mwh: float
    maximum_gpu_bound_violation_mwh: float
    minimum_site_capacity_slack_mwh: float
    valid: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_job_network_coupling(
    *,
    service_mwh: np.ndarray,
    job_energy_mwh: np.ndarray,
    submit_slot: np.ndarray,
    deadline_slot: np.ndarray,
    region: np.ndarray,
    aggregate_mwh: np.ndarray,
    dt_h: float,
    requested_gpus: np.ndarray | None = None,
    measured_gpus: np.ndarray | None = None,
    per_gpu_power_cap_mw: float | None = None,
    site_capacity_mw: float | np.ndarray | None = None,
    network_profile_mw: np.ndarray | None = None,
    network_mapping: np.ndarray | None = None,
) -> CouplingInvariantCertificate:
    """Check indexed conservation, requested-resource bounds, aggregation, and mapping.

    ``service_mwh`` is concatenated in job-window order.  ``aggregate_mwh`` is
    the exact regional profile sent to the network, and an optional
    ``network_mapping`` checks the final unit conversion explicitly.  The
    function raises on malformed dimensions or windows; numerical violations
    are reported in the certificate and leave the caller to decide whether to
    fail closed.
    """

    # ``measured_gpus`` was used by an early diagnostic API.  Keep it as an
    # explicit compatibility alias, but never combine it with the submit-time
    # resource declaration: the indexed certificate is bounded by the
    # requested GPU count.  Reject contradictory aliases instead of silently
    # choosing one.
    if requested_gpus is not None and measured_gpus is not None:
        if not np.array_equal(
            np.asarray(requested_gpus).reshape(-1),
            np.asarray(measured_gpus).reshape(-1),
        ):
            raise ValueError("requested_gpus and measured_gpus disagree")
    if requested_gpus is None and measured_gpus is not None:
        requested_gpus = measured_gpus

    service = np.asarray(service_mwh, dtype=float).reshape(-1)
    energy = np.asarray(job_energy_mwh, dtype=float).reshape(-1)
    starts = np.asarray(submit_slot, dtype=np.int64).reshape(-1)
    ends = np.asarray(deadline_slot, dtype=np.int64).reshape(-1)
    regions = np.asarray(region, dtype=np.int64).reshape(-1)
    aggregate = np.asarray(aggregate_mwh, dtype=float)
    if not np.isfinite(float(dt_h)) or float(dt_h) <= 0.0:
        raise ValueError("dt_h must be a finite positive value")
    if not (len(energy) == len(starts) == len(ends) == len(regions)):
        raise ValueError("job arrays have inconsistent lengths")
    if aggregate.ndim != 2:
        raise ValueError("aggregate_mwh must have shape (regions, slots)")
    if np.any(ends <= starts) or np.any(starts < 0) or np.any(regions < 0):
        raise ValueError("job windows and region labels must be nonnegative and nonempty")
    widths = ends - starts
    offsets = np.concatenate(([0], np.cumsum(widths, dtype=np.int64)))
    if int(offsets[-1]) != len(service):
        raise ValueError("service vector length does not match job windows")
    if aggregate.shape[0] != (0 if len(regions) == 0 else int(regions.max()) + 1):
        raise ValueError("aggregate region dimension does not match region labels")
    if len(service) and not np.isfinite(service).all():
        raise ValueError("service vector contains non-finite values")
    if not np.isfinite(energy).all() or not np.isfinite(aggregate).all():
        raise ValueError("job energy or aggregate profile contains non-finite values")

    # Every job equality is checked from the primitive vector.  This avoids
    # trusting a summary CSV or a precomputed aggregate residual.
    job_service = np.add.reduceat(service, offsets[:-1]) if len(energy) else np.empty(0)
    job_residual = job_service - energy
    slots = np.concatenate(
        [np.arange(int(start), int(end), dtype=np.int64) for start, end in zip(starts, ends)]
    ) if len(energy) else np.empty(0, dtype=np.int64)
    variable_regions = np.repeat(regions, widths)
    if len(slots) and np.any(slots >= aggregate.shape[1]):
        raise ValueError("job windows exceed aggregate horizon")
    reconstructed = np.bincount(
        variable_regions * aggregate.shape[1] + slots,
        weights=service,
        minlength=aggregate.size,
    ).reshape(aggregate.shape)
    aggregation_residual = reconstructed - aggregate

    minimum_gpu_slack = 0.0
    maximum_gpu_violation = 0.0
    if requested_gpus is not None or per_gpu_power_cap_mw is not None:
        if requested_gpus is None or per_gpu_power_cap_mw is None:
            raise ValueError("requested_gpus and per_gpu_power_cap_mw must be supplied together")
        gpus = np.asarray(requested_gpus, dtype=float).reshape(-1)
        if len(gpus) != len(energy) or np.any(gpus <= 0.0) or float(per_gpu_power_cap_mw) <= 0.0:
            raise ValueError("GPU counts and per-GPU cap are invalid")
        upper = np.repeat(gpus * float(per_gpu_power_cap_mw) * float(dt_h), widths)
        slack = upper - service
        minimum_gpu_slack = float(np.min(slack)) if len(slack) else 0.0
        maximum_gpu_violation = float(max(0.0, float(np.max(-slack, initial=0.0))))

    minimum_capacity_slack = 0.0
    if site_capacity_mw is not None:
        capacity = np.asarray(site_capacity_mw, dtype=float)
        if capacity.ndim == 0:
            capacity_mwh = np.full(aggregate.shape, float(capacity) * float(dt_h))
        elif capacity.ndim == 1 and len(capacity) == aggregate.shape[0]:
            capacity_mwh = capacity[:, None] * float(dt_h)
        elif capacity.shape == aggregate.shape:
            capacity_mwh = capacity * float(dt_h)
        else:
            raise ValueError("site_capacity_mw must be scalar, regional, or regional-slot shaped")
        minimum_capacity_slack = float(np.min(capacity_mwh - reconstructed))

    maximum_mapping_residual = 0.0
    if network_profile_mw is not None or network_mapping is not None:
        if network_profile_mw is None or network_mapping is None:
            raise ValueError("network_profile_mw and network_mapping must be supplied together")
        mapping = np.asarray(network_mapping, dtype=float)
        profile = np.asarray(network_profile_mw, dtype=float)
        expected = mapping @ (reconstructed / float(dt_h))
        if expected.shape != profile.shape:
            raise ValueError("network mapping and profile dimensions do not agree")
        maximum_mapping_residual = float(np.max(np.abs(expected - profile), initial=0.0))

    minimum_service = float(np.min(service)) if len(service) else 0.0
    certificate = CouplingInvariantCertificate(
        version="coupling-invariant-v1",
        jobs=int(len(energy)),
        service_variables=int(len(service)),
        regions=int(aggregate.shape[0]),
        slots=int(aggregate.shape[1]),
        dt_h=float(dt_h),
        max_job_energy_residual_mwh=float(np.max(np.abs(job_residual), initial=0.0)),
        max_aggregation_residual_mwh=float(np.max(np.abs(aggregation_residual), initial=0.0)),
        max_network_mapping_residual_mw=maximum_mapping_residual,
        minimum_service_mwh=minimum_service,
        minimum_gpu_bound_slack_mwh=minimum_gpu_slack,
        maximum_gpu_bound_violation_mwh=maximum_gpu_violation,
        minimum_site_capacity_slack_mwh=minimum_capacity_slack,
        valid=bool(
            minimum_service >= -1e-12
            and np.max(np.abs(job_residual), initial=0.0) <= 1e-12
            and np.max(np.abs(aggregation_residual), initial=0.0) <= 1e-12
            and maximum_gpu_violation <= 1e-12
            and minimum_capacity_slack >= -1e-12
            and maximum_mapping_residual <= 1e-10
        ),
    )
    return certificate


def assert_valid_certificate(certificate: CouplingInvariantCertificate) -> None:
    """Fail closed with all residuals if a coupling certificate is invalid."""

    if not certificate.valid:
        raise RuntimeError(
            "invalid job/network coupling certificate: "
            f"job={certificate.max_job_energy_residual_mwh:.3e}, "
            f"aggregation={certificate.max_aggregation_residual_mwh:.3e}, "
            f"mapping={certificate.max_network_mapping_residual_mw:.3e}, "
            f"GPU={certificate.maximum_gpu_bound_violation_mwh:.3e}, "
            f"capacity={certificate.minimum_site_capacity_slack_mwh:.3e}"
        )
