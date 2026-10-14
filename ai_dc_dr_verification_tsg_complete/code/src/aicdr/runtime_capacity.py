"""All-slot, full-runtime binary scheduling for declaration-only gate audits.

One start per job, a constant declared nameplate rate for every runtime slot,
unaltered release/deadline windows, and capacity on the entire horizon.  No
calibrated-energy terminal fractional slot or event-only capacity shortcut is
used.  Optional risk rows constrain the *returned schedule*, not a preceding
aggregate target.  The reference/response supplied to those rows is modeled
scenario data, never an assertion that a future meter is known at the gate.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import time
import warnings
import numpy as np
from scipy import sparse
from scipy.optimize import Bounds, LinearConstraint, milp


@dataclass
class RuntimeResult:
    success: bool
    optimal: bool
    status: int
    message: str
    starts: np.ndarray | None
    profile_mw: np.ndarray | None
    objective: float | None
    mip_gap: float | None
    elapsed_seconds: float
    candidate_starts: int
    max_capacity_violation_mw: float | None
    max_job_energy_residual_mwh: float | None
    total_false_credit_mwh: float | None = None
    tail_false_credit_mwh: float | None = None
    max_constraint_violation: float | None = None
    event_mse_mw2: float | None = None
    mse_epigraph_exact_on_power_grid: bool = False
    objective_mode: str = "cost"
    operating_cost: float | None = None
    solver_objective: float | None = None
    solver_attempt_statuses: str = ""



def _integer_vector(values, name):
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or not np.isfinite(array).all() or np.any(array != np.rint(array)):
        raise ValueError(f"{name} must contain finite integer slots/indices")
    return array.astype(np.int64)


def top_m_mean(values: np.ndarray, level: float) -> float:
    values = np.asarray(values, dtype=float).reshape(-1)
    if values.size == 0 or not 0 <= level < 1:
        raise ValueError("a nonempty sample and 0 <= level < 1 are required")
    m = max(1, int(math.ceil((1.0 - level) * values.size - 1e-12)))
    return float(np.sort(values)[-m:].mean())


def solve_runtime_milp(
    release, deadline, runtime, region, power_mw, slot_cost, capacity_mw,
    *, earliest_start=None, fixed_profile_mw=None, dt_h=0.25,
    waiting_cost=1.5, event_mask=None, event_service_min_mwh=0.0,
    risk_ceiling_mw=None, risk_day_index=None, total_budget_mwh=None,
    tail_budget_mwh=None, tail_level=0.75, time_limit=60.0,
    mse_reference_mw=None, mse_budget_mw2=None, power_quantum_mw=None, objective_mode="cost",
) -> RuntimeResult:
    """Solve and independently validate a fixed-rate contiguous start MILP.

    ``slot_cost`` and the returned profile have shape (region, slot).  Releases
    can precede slot zero, but admissible decision starts cannot. Fixed carry-in
    is supplied separately. Capacity excludes facility load, consistently with
    the runtime/nameplate ledger. A finite incumbent is reported as successful
    only when assignment, integrality, all-slot capacity and enabled risk rows
    pass recomputation; a time limit is never called an optimality certificate.
    """
    release = _integer_vector(release, "release")
    deadline = _integer_vector(deadline, "deadline")
    runtime = _integer_vector(runtime, "runtime")
    region = _integer_vector(region, "region")
    power = np.asarray(power_mw, dtype=float)
    cost = np.asarray(slot_cost, dtype=float)
    if cost.ndim != 2 or not np.isfinite(cost).all():
        raise ValueError("slot_cost must be a finite region-by-slot matrix")
    nr, nt = cost.shape
    nj = release.size
    if not all(a.shape == (nj,) for a in (deadline, runtime, region, power)):
        raise ValueError("job arrays must be one-dimensional and aligned")
    if np.any(runtime < 1) or np.any(power <= 0) or not np.isfinite(power).all():
        raise ValueError("runtime and fixed power must be positive")
    if (np.any(region < 0) or np.any(region >= nr) or dt_h <= 0 or time_limit <= 0
            or not np.isfinite([dt_h, time_limit, waiting_cost, event_service_min_mwh]).all()):
        raise ValueError("invalid region, interval, or time limit")
    first = np.maximum(release, 0)
    if earliest_start is not None:
        first = np.maximum(first, _integer_vector(np.broadcast_to(earliest_start, (nj,)), "earliest_start"))
    last = deadline - runtime
    if np.any(last < first) or np.any(deadline > nt):
        raise ValueError("a job has no full-runtime admissible start or exceeds horizon")
    fixed = np.zeros_like(cost) if fixed_profile_mw is None else np.asarray(fixed_profile_mw, dtype=float)
    cap = np.asarray(capacity_mw, dtype=float)
    if cap.ndim == 1 and cap.size == nr:
        cap = cap[:, None]
    cap = np.broadcast_to(cap, cost.shape)
    if fixed.shape != cost.shape or np.any(fixed < -1e-12) or not np.isfinite(fixed).all():
        raise ValueError("invalid fixed carry-in profile")
    if not np.isfinite(cap).all() or np.any(cap < 0):
        raise ValueError("capacity must be finite and nonnegative")
    event = np.zeros(nt, dtype=bool) if event_mask is None else np.asarray(event_mask, dtype=bool)
    if event.shape != (nt,) or event_service_min_mwh < 0:
        raise ValueError("invalid event mask or service floor")
    starts = np.concatenate([np.arange(a, b + 1) for a, b in zip(first, last)]) if nj else np.empty(0, dtype=int)
    owners = np.repeat(np.arange(nj), last - first + 1)
    nx = starts.size
    if not nx:
        raise ValueError("at least one pending job is required")
    ends = starts + runtime[owners]
    offsets = np.concatenate(([0], np.cumsum(runtime[owners])))
    cells = np.concatenate([region[j] * nt + np.arange(s, e) for j, s, e in zip(owners, starts, ends)])
    columns = np.repeat(np.arange(nx), runtime[owners])
    values = np.repeat(power[owners], runtime[owners])
    block = sparse.csc_matrix((values, (cells, columns)), shape=(nr * nt, nx))
    assignment = sparse.csc_matrix((np.ones(nx), (owners, np.arange(nx))), shape=(nj, nx))
    c = np.asarray(block.T @ cost.reshape(-1)).reshape(-1) * dt_h
    delay = starts - release[owners]
    rr = runtime[owners]
    c += waiting_cost * power[owners] * dt_h * (rr * delay + rr * (rr - 1) / 2)
    matrices = [assignment, block]
    lower = [np.ones(nj), np.full(nr * nt, -np.inf)]
    upper = [np.ones(nj), (cap - fixed).reshape(-1)]
    if event_service_min_mwh > 0:
        event_cells = np.tile(event, nr)
        matrices.append(sparse.csc_matrix(np.asarray(block[event_cells].sum(axis=0)) * dt_h))
        lower.append(np.asarray([event_service_min_mwh - fixed[:, event].sum() * dt_h]))
        upper.append(np.asarray([np.inf]))
    risk_active = total_budget_mwh is not None or tail_budget_mwh is not None
    nf = nd = 0
    risk_cells = np.empty(0, dtype=int)
    day_matrix = None
    if any(v is not None and (not np.isfinite(v) or v < 0) for v in (total_budget_mwh, tail_budget_mwh, mse_budget_mw2)):
        raise ValueError("budgets must be finite and nonnegative")
    if objective_mode not in {"cost", "minimum_mse"}:
        raise ValueError("invalid objective mode")
    if risk_active:
        if risk_ceiling_mw is None or risk_day_index is None:
            raise ValueError("enabled risk rows require ceiling and day indices")
        ceiling = np.asarray(risk_ceiling_mw, dtype=float)
        day_index = np.asarray(risk_day_index, dtype=int)
        if ceiling.shape != cost.shape or day_index.shape != (nt,) or not np.isfinite(ceiling).all():
            raise ValueError("invalid risk ceiling/day-index dimensions")
        selected = event & (day_index >= 0)
        if not selected.any():
            raise ValueError("risk rows require an event cell")
        days = np.unique(day_index[selected])
        nd = len(days)
        risk_cells = np.flatnonzero(np.tile(selected, nr))
        nf = len(risk_cells)
        mapped = np.searchsorted(days, np.tile(day_index, nr)[risk_cells])
        day_matrix = sparse.csc_matrix((np.full(nf, dt_h), (mapped, np.arange(nf))), shape=(nd, nf))
        extra = nf + (1 + nd if tail_budget_mwh is not None else 0)
    else:
        extra = 0
    nv = nx + extra
    mats = [sparse.hstack([m, sparse.csc_matrix((m.shape[0], extra))], format="csc") for m in matrices]
    if risk_active:
        mats.append(sparse.hstack([block[risk_cells], -sparse.eye(nf), sparse.csc_matrix((nf, extra - nf))], format="csc"))
        lower.append(np.full(nf, -np.inf))
        upper.append((ceiling - fixed).reshape(-1)[risk_cells])
        if total_budget_mwh is not None:
            if total_budget_mwh < 0:
                raise ValueError("negative total budget")
            m = sparse.lil_matrix((1, nv)); m[0, nx:nx + nf] = dt_h
            mats.append(m.tocsc()); lower.append(np.asarray([-np.inf])); upper.append(np.asarray([total_budget_mwh]))
        if tail_budget_mwh is not None:
            if tail_budget_mwh < 0 or not 0 <= tail_level < 1:
                raise ValueError("invalid tail budget/level")
            m = max(1, int(math.ceil((1 - tail_level) * nd - 1e-12)))
            mats.append(sparse.hstack([sparse.csc_matrix((nd, nx)), day_matrix, -np.ones((nd, 1)), -sparse.eye(nd)], format="csc"))
            lower.append(np.full(nd, -np.inf)); upper.append(np.zeros(nd))
            tail = sparse.lil_matrix((1, nv)); tail[0, nx + nf] = 1; tail[0, nx + nf + 1:] = 1 / m
            mats.append(tail.tocsc()); lower.append(np.asarray([-np.inf])); upper.append(np.asarray([tail_budget_mwh]))
    mse_active = mse_reference_mw is not None
    nq = 0
    if mse_active:
        mse_reference = np.asarray(mse_reference_mw, dtype=float)
        quantum = float(power_quantum_mw or 0.)
        if (mse_reference.shape != cost.shape or not np.isfinite(mse_reference).all()
                or not np.isfinite(quantum) or quantum <= 0):
            raise ValueError("exact MSE requires finite matched reference and positive power quantum")
        if (np.max(np.abs(power / quantum - np.rint(power / quantum))) > 1e-8
                or np.max(np.abs(fixed / quantum - np.rint(fixed / quantum))) > 1e-8):
            raise ValueError("power and fixed carry-in must lie on the declared exact power grid")
        mse_cells = np.flatnonzero(np.tile(event, nr))
        nq = len(mse_cells)
        if not nq:
            raise ValueError("MSE needs event cells")
        previous_nv = nv
        nv += nq
        extra += nq
        mats = [sparse.hstack([mat, sparse.csc_matrix((mat.shape[0], nq))], format="csc") for mat in mats]
        # For integer z=p/quantum, max_k[(2k-2t)z+t²-k²]=(z-t)².
        # Include every capacity-admissible integer power level. This is an
        # exact finite mixed-integer epigraph, not a continuous approximation.
        csr = block.tocsr(); tangent_matrices=[]; tangent_upper=[]
        for qi, cell in enumerate(mse_cells):
            fixed_z = fixed.reshape(-1)[cell] / quantum
            target_z = mse_reference.reshape(-1)[cell] / quantum
            first_k = int(round(fixed_z)); last_k = int(np.floor(cap.reshape(-1)[cell] / quantum + 1e-9))
            levels = np.arange(first_k, max(first_k, last_k) + 1, dtype=float)
            slope = 2 * (levels - target_z)
            left = sparse.csc_matrix(slope[:, None]) @ (csr.getrow(cell) / quantum)
            extra_columns = sparse.csc_matrix((-np.ones(len(levels)), (np.arange(len(levels)), np.full(len(levels), previous_nv - nx + qi))), shape=(len(levels), extra))
            tangent_matrices.append(sparse.hstack([left, extra_columns], format="csc"))
            tangent_upper.append(levels ** 2 - target_z ** 2 - slope * fixed_z)
        tangent = sparse.vstack(tangent_matrices, format="csc")
        mats.append(tangent); lower.append(np.full(tangent.shape[0], -np.inf)); upper.append(np.concatenate(tangent_upper))
        if mse_budget_mw2 is not None:
            bound = sparse.lil_matrix((1, nv)); bound[0, previous_nv:] = 1 / nq
            mats.append(bound.tocsc()); lower.append(np.asarray([-np.inf])); upper.append(np.asarray([mse_budget_mw2 / quantum ** 2]))
    elif mse_budget_mw2 is not None or objective_mode == "minimum_mse":
        raise ValueError("MSE budget/objective requires an MSE reference")
    matrix = sparse.vstack(mats, format="csc")
    lb, ub = np.concatenate(lower), np.concatenate(upper)
    objective = np.concatenate([c, np.zeros(extra)])
    if objective_mode == "minimum_mse":
        objective[:] = 0.; objective[-nq:] = 1 / nq
    integrality = np.concatenate([np.ones(nx, dtype=int), np.zeros(extra, dtype=int)])
    variable_upper = np.concatenate([np.ones(nx), np.full(extra, np.inf)])
    started = time.monotonic()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Unrecognized options detected.*")
        result = milp(objective, integrality=integrality, bounds=Bounds(np.zeros(nv), variable_upper),
                      constraints=LinearConstraint(matrix, lb, ub),
                      options={"time_limit": time_limit, "mip_rel_gap": 1e-8, "threads": 1})
        attempts = [int(result.status)]
        if result.status == 4 and result.x is None:
            # SciPy/HiGHS maintains a process-global scheduler. A prior legacy
            # LP may initialize a different thread count; HiGHS then returns
            # Not Set when the same process requests one-thread MILP work.
            # Reset only for this explicit backend failure, retry the exact
            # same model once, and retain both statuses in the certificate.
            try:
                from scipy.optimize._highspy._core import _Highs
                _Highs.resetGlobalScheduler(True)
            except ImportError:
                pass
            else:
                remaining = max(.001, time_limit - (time.monotonic() - started))
                result = milp(objective, integrality=integrality, bounds=Bounds(np.zeros(nv), variable_upper),
                              constraints=LinearConstraint(matrix, lb, ub),
                              options={"time_limit": remaining, "mip_rel_gap": 1e-8, "threads": 1})
                attempts.append(int(result.status))
    elapsed = time.monotonic() - started
    info = dict(success=False, optimal=False, status=int(result.status), message=str(result.message),
                starts=None, profile_mw=None, objective=None,
                mip_gap=float(result.mip_gap) if getattr(result, "mip_gap", None) is not None else None,
                elapsed_seconds=elapsed, candidate_starts=int(nx), max_capacity_violation_mw=None,
                max_job_energy_residual_mwh=None, objective_mode=objective_mode,
                solver_attempt_statuses=";".join(map(str, attempts)))
    if result.x is None or not np.isfinite(result.x).all():
        return RuntimeResult(**info)
    x = np.asarray(result.x[:nx])
    if np.max(np.abs(x - np.rint(x))) > 1e-5:
        info["message"] += "; rejected nonintegral incumbent"
        return RuntimeResult(**info)
    chosen = np.flatnonzero(x > 0.5)
    if len(chosen) != nj or not np.array_equal(np.sort(owners[chosen]), np.arange(nj)):
        info["message"] += "; rejected assignment incumbent"
        return RuntimeResult(**info)
    selected_starts = np.empty(nj, dtype=int)
    selected_starts[owners[chosen]] = starts[chosen]
    # Reconstruct every slot from selected blocks, independently of the sparse
    # candidate matrix used by the optimizer.
    profile = fixed.copy(); energies = np.zeros(nj)
    support_valid = bool(np.all(selected_starts >= first) and np.all(selected_starts + runtime <= deadline))
    for j, s in enumerate(selected_starts):
        profile[region[j], s:s + runtime[j]] += power[j]
        job_vector = np.zeros(nt); job_vector[s:s + runtime[j]] = power[j]
        energies[j] = job_vector.sum() * dt_h
    violation = max(float(np.max(profile - cap)), 0.0)
    energy_residual = float(np.max(np.abs(energies - power * runtime * dt_h)))
    primal = np.asarray(matrix @ result.x).reshape(-1)
    all_violation = max(float(np.max(np.maximum(lb - primal, 0))), float(np.max(np.maximum(primal - ub, 0))))
    all_violation = max(all_violation, event_service_min_mwh - float(profile[:, event].sum() * dt_h))
    aggregate_energy_residual = abs(float((profile - fixed).sum() * dt_h) - float((power * runtime * dt_h).sum()))
    energy_residual = max(energy_residual, aggregate_energy_residual)
    event_mse = None
    if mse_active:
        event_mse = float(np.mean((profile.reshape(-1)[mse_cells] - mse_reference.reshape(-1)[mse_cells]) ** 2))
        if mse_budget_mw2 is not None:
            all_violation = max(all_violation, (event_mse - mse_budget_mw2) / quantum ** 2)
    total = tail_value = None
    if risk_active:
        false = np.maximum((profile - ceiling).reshape(-1)[risk_cells], 0)
        daily = np.asarray(day_matrix @ false).reshape(-1)
        total, tail_value = float(daily.sum()), top_m_mean(daily, tail_level)
        if total_budget_mwh is not None:
            all_violation = max(all_violation, total - total_budget_mwh)
        if tail_budget_mwh is not None:
            all_violation = max(all_violation, tail_value - tail_budget_mwh)
    valid = support_valid and violation <= 1e-7 and all_violation <= 1e-6 and energy_residual <= 1e-8
    info.update(success=bool(valid), optimal=bool(valid and result.status == 0), starts=selected_starts,
                profile_mw=profile, objective=float(c[chosen].sum()) if objective_mode == "cost" else event_mse, max_capacity_violation_mw=violation,
                max_job_energy_residual_mwh=energy_residual, total_false_credit_mwh=total,
                tail_false_credit_mwh=tail_value, max_constraint_violation=all_violation,
                event_mse_mw2=event_mse, mse_epigraph_exact_on_power_grid=mse_active,
                operating_cost=float(c[chosen].sum()), solver_objective=float(result.fun))
    return RuntimeResult(**info)
