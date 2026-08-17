from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, csr_matrix, vstack


@dataclass
class PowerSystem:
    base_mva: float
    bus: np.ndarray
    gen: np.ndarray
    branch: np.ndarray
    gencost: np.ndarray
    ptdf: np.ndarray
    gen_bus: np.ndarray


@dataclass
class SCEDResult:
    success: bool
    objective: float
    generation_mw: np.ndarray
    line_flow_mw: np.ndarray
    lmp_per_mwh: np.ndarray
    max_loading: float
    congested_lines: int
    max_post_contingency_loading: float = 0.0
    binding_contingency_constraints: int = 0
    credible_contingencies: int = 0


@dataclass
class ScheduleResult:
    success: bool
    objective: float
    power_mw: np.ndarray
    served_mwh: np.ndarray
    migrated_mwh: float
    solver_message: str
    minimum_service_shadow_price: float
    projection_l1_mw: float = np.nan


@dataclass
class PaymentCertifiedResult:
    """Lexicographically optimal counterfactual with robust grid-value caps."""

    success: bool
    profile_mw: np.ndarray
    weights: np.ndarray
    objective_l1_mw: float
    certified_baseline_cost_usd: float
    reference_baseline_cost_usd: float
    maximum_cost_violation_usd: float
    solver_message: str
    conversion_scale_factors: np.ndarray
    scenario_certified_cost_usd: np.ndarray
    scenario_reference_cost_usd: np.ndarray
    worst_case_fractional_cost_margin: float = np.nan
    first_stage_optimal_l1_mw: float = np.nan


@dataclass(frozen=True)
class PaymentIntervalResult:
    """Set-valued settlement payment induced by a feasible workload hull.

    ``baseline_costs_usd`` are evaluated by the same secure network-value
    model for the frozen segment vertices.  When
    ``segment_minimum_baseline_cost_usd`` is supplied, it is the exact minimum
    from the joint segment LP; the convex value function makes the vertex
    maximum exact. Subtracting one realized counterfactual cost therefore maps
    the declared workload segment into an explicit payment interval rather than
    treating a single baseline forecast as ground truth.
    """

    lower_usd: float
    upper_usd: float
    width_usd: float
    selected_payment_usd: float
    oracle_payment_usd: float = np.nan
    oracle_inside: bool = False


def _sced_structure(system: PowerSystem, segments: int) -> dict[str, Any]:
    """Build the load-independent SCED matrices once per system/resolution.

    Cross-network panels solve the same public network for many loads.  The
    generator segment costs, PTDF incidence, sparse inequality matrix, and
    bounds are invariant across those solves; caching them removes repeated
    matrix construction without changing the LP itself.  A copied
    ``PowerSystem`` receives its own cache, so contingency or rating changes
    cannot leak into another system instance.
    """
    if segments <= 0:
        raise ValueError("segments must be positive")
    cache = getattr(system, "_sced_structure_cache", None)
    if cache is None:
        cache = {}
        setattr(system, "_sced_structure_cache", cache)
    cached = cache.get(int(segments))
    if cached is not None:
        return cached

    active = system.gen[:, 7] > 0
    gen = system.gen[active]
    gencost = system.gencost[active]
    gen_bus = system.gen_bus[active]
    pmax = gen[:, 8]
    pmin = gen[:, 9]
    widths: list[float] = []
    costs: list[float] = []
    segment_gen: list[int] = []
    fixed_cost = 0.0
    for g in range(len(gen)):
        model = int(gencost[g, 0])
        if model != 2:
            raise ValueError("Only polynomial PGLib generator costs are supported")
        ncoef = int(gencost[g, 3])
        coeff = gencost[g, 4 : 4 + ncoef]
        if ncoef == 3:
            a, b, c0 = coeff
        elif ncoef == 2:
            a, b, c0 = 0.0, coeff[0], coeff[1]
        else:
            a, b, c0 = 0.0, 0.0, coeff[-1] if len(coeff) else 0.0
        fixed_cost += a * pmin[g] ** 2 + b * pmin[g] + c0
        width = max(0.0, pmax[g] - pmin[g]) / segments
        for s in range(segments):
            midpoint = pmin[g] + (s + 0.5) * width
            widths.append(width)
            costs.append(2.0 * a * midpoint + b)
            segment_gen.append(g)

    widths_a = np.asarray(widths)
    c = np.asarray(costs)
    cg = np.zeros((system.bus.shape[0], len(gen)))
    cg[gen_bus, np.arange(len(gen))] = 1.0
    hgen = system.ptdf @ cg
    hseg = hgen[:, np.asarray(segment_gen)]
    rate = system.branch[:, 5].copy()
    rate[rate <= 0] = 1e6
    aub = vstack([csr_matrix(hseg), csr_matrix(-hseg)], format="csr")
    structure = {
        "active": active,
        "pmin": pmin,
        "widths": widths_a,
        "costs": c,
        "segment_gen": np.asarray(segment_gen, dtype=int),
        "fixed_cost": float(fixed_cost),
        "cg": cg,
        "hseg": hseg,
        "aub": aub,
        "aeq": csr_matrix(np.ones((1, len(c)))),
        "bounds": list(zip(np.zeros(len(widths_a)), widths_a)),
        "rate": rate,
    }
    cache[int(segments)] = structure
    return structure


def payment_value_interval(
    baseline_costs_usd: np.ndarray,
    counterfactual_cost_usd: float,
    selected_baseline_cost_usd: float,
    oracle_baseline_cost_usd: float | None = None,
    segment_minimum_baseline_cost_usd: float | None = None,
) -> PaymentIntervalResult:
    """Map a workload-feasible baseline hull to a certified payment interval.

    The interval is contractual: it is computed only from the predeclared
    candidate hull and the realized counterfactual network value.  The oracle
    argument is optional and is used solely for an independent coverage audit.
    No oracle quantity participates in the interval endpoints.
    """
    costs = np.asarray(baseline_costs_usd, dtype=float).reshape(-1)
    if costs.size == 0 or not np.isfinite(costs).all():
        raise ValueError("baseline_costs_usd must be a non-empty finite array")
    counterfactual = float(counterfactual_cost_usd)
    # The lower endpoint must cover the declared continuous segment, not only
    # its two vertices.  When supplied, ``segment_minimum_baseline_cost_usd``
    # is the optimum of the exact joint LP over the segment parameter.  The
    # upper endpoint remains the maximum of the vertices because the secure
    # SCED value is convex in the affine load profile.
    if segment_minimum_baseline_cost_usd is None:
        lower_baseline = float(costs.min())
    else:
        lower_baseline = float(segment_minimum_baseline_cost_usd)
        if not np.isfinite(lower_baseline):
            raise ValueError("segment_minimum_baseline_cost_usd must be finite")
        if lower_baseline > float(costs.min()) + 1e-6:
            raise ValueError("segment minimum cannot exceed a declared endpoint cost")
    lower = float(lower_baseline - counterfactual)
    upper = float(costs.max() - counterfactual)
    selected = float(selected_baseline_cost_usd - counterfactual)
    if selected < lower - 1e-7 or selected > upper + 1e-7:
        raise ValueError("selected baseline cost is outside the declared hull")
    if oracle_baseline_cost_usd is None:
        oracle_payment = np.nan
        inside = False
    else:
        oracle_payment = float(oracle_baseline_cost_usd - counterfactual)
        inside = bool(lower - 1e-7 <= oracle_payment <= upper + 1e-7)
    return PaymentIntervalResult(
        lower_usd=lower,
        upper_usd=upper,
        width_usd=float(upper - lower),
        selected_payment_usd=selected,
        oracle_payment_usd=oracle_payment,
        oracle_inside=inside,
    )


def parse_pglib_case(path: Path) -> PowerSystem:
    text = path.read_text(encoding="utf-8")
    base_match = re.search(r"mpc\.baseMVA\s*=\s*([0-9.eE+-]+)", text)
    if not base_match:
        raise ValueError(f"Cannot parse baseMVA from {path}")
    arrays: dict[str, np.ndarray] = {}
    for name in ("bus", "gen", "branch", "gencost"):
        match = re.search(rf"mpc\.{name}\s*=\s*\[(.*?)\];", text, re.S)
        if not match:
            raise ValueError(f"Cannot parse {name} matrix from {path}")
        rows: list[list[float]] = []
        for line in match.group(1).splitlines():
            line = line.split("%", 1)[0].strip().rstrip(";")
            if line:
                rows.append([float(token) for token in line.split()])
        arrays[name] = np.asarray(rows, dtype=float)

    from pypower.makePTDF import makePTDF

    base_mva = float(base_match.group(1))
    bus = arrays["bus"]
    branch = arrays["branch"]
    # PYPOWER's low-level PTDF routine requires zero-based consecutive internal bus
    # numbering. Retain the original public-case matrices for reporting, but convert
    # copies for the network factorization.
    bus_internal = bus.copy()
    branch_internal = branch.copy()
    bus_internal[:, 0] -= 1
    branch_internal[:, 0:2] -= 1
    ptdf = makePTDF(base_mva, bus_internal, branch_internal, 0)
    gen_bus = arrays["gen"][:, 0].astype(int) - 1
    return PowerSystem(base_mva, bus, arrays["gen"], branch, arrays["gencost"], ptdf, gen_bus)


def power_system_from_ppc(ppc: dict[str, Any]) -> PowerSystem:
    """Construct the common network representation from a PYPOWER benchmark."""
    from pypower.ext2int import ext2int
    from pypower.makePTDF import makePTDF

    internal = ext2int({
        "version": ppc.get("version", "2"),
        "baseMVA": float(ppc["baseMVA"]),
        "bus": np.asarray(ppc["bus"], dtype=float).copy(),
        "gen": np.asarray(ppc["gen"], dtype=float).copy(),
        "branch": np.asarray(ppc["branch"], dtype=float).copy(),
        "gencost": np.asarray(ppc["gencost"], dtype=float).copy(),
    })
    bus = internal["bus"]
    gen = internal["gen"]
    branch = internal["branch"]
    gencost = internal["gencost"]
    base_mva = float(internal["baseMVA"])
    ptdf = makePTDF(base_mva, bus, branch, 0)
    return PowerSystem(base_mva, bus, gen, branch, gencost, ptdf, gen[:, 0].astype(int))


def solve_sced(system: PowerSystem, load_mw: np.ndarray, segments: int = 10) -> SCEDResult:
    structure = _sced_structure(system, int(segments))
    load = np.asarray(load_mw, dtype=float)
    if load.shape != (system.bus.shape[0],):
        raise ValueError("load_mw must have one entry per bus")
    pmin = structure["pmin"]
    fixed_injection = structure["cg"] @ pmin - load
    fixed_flow = system.ptdf @ fixed_injection
    rate = structure["rate"]
    bub = np.concatenate([rate - fixed_flow, rate + fixed_flow])
    beq = np.array([float(load.sum() - pmin.sum())])
    result = linprog(
        structure["costs"],
        A_ub=structure["aub"],
        b_ub=bub,
        A_eq=structure["aeq"],
        b_eq=beq,
        bounds=structure["bounds"],
        method="highs",
        options={"presolve": True},
    )
    if not result.success:
        raise RuntimeError(f"SCED failed: {result.message}; demand={load.sum():.2f} MW")
    q_by_gen = np.bincount(
        structure["segment_gen"],
        weights=result.x,
        minlength=len(pmin),
    )
    pg_active = pmin + q_by_gen
    pg_all = np.zeros(system.gen.shape[0])
    pg_all[np.where(structure["active"])[0]] = pg_active
    injection = structure["cg"] @ pg_active - load
    flow = system.ptdf @ injection
    mu_upper = result.ineqlin.marginals[: len(rate)]
    mu_lower = result.ineqlin.marginals[len(rate) :]
    lambda_energy = float(result.eqlin.marginals[0])
    lmp = lambda_energy + system.ptdf.T @ (mu_upper - mu_lower)
    loading = np.abs(flow) / rate
    return SCEDResult(
        True,
        float(result.fun + structure["fixed_cost"]),
        pg_all,
        flow,
        lmp,
        float(loading.max()),
        int(np.sum(loading >= 0.999)),
    )


def build_n1_security_factors(
    system: PowerSystem,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    """Build all finite non-islanding N-1 branch-flow sensitivities.

    For outage ``k``, the monitored-line flow is
    ``f_l^(k) = f_l + LODF[l, k] f_k``.  Each returned row therefore maps the
    pre-contingency nodal injection directly to one post-contingency monitored
    flow.  Islanding outages are excluded because a connected-network PTDF/LODF
    model cannot represent the resulting islands; their count is reported
    separately by the calling experiment.
    """
    from pypower.makeLODF import makeLODF

    branch = system.branch.copy()
    nbus = system.bus.shape[0]
    # PGLib files retain one-based external bus labels, whereas PYPOWER cases
    # have already passed through ext2int.  makeLODF requires internal labels.
    if (
        np.min(branch[:, 0:2]) >= 1
        and np.max(branch[:, 0:2]) <= nbus
    ):
        branch[:, 0:2] -= 1
    # Islanding outages produce the expected zero denominator in the LODF
    # formula. They are identified from the resulting non-finite column below.
    with np.errstate(divide="ignore", invalid="ignore"):
        lodf = np.asarray(makeLODF(branch, system.ptdf), dtype=float)
    rate = system.branch[:, 5].copy()
    rate[rate <= 0] = 1e6
    factors: list[np.ndarray] = []
    limits: list[float] = []
    outage_ids: list[int] = []
    credible = 0
    for outage in range(system.branch.shape[0]):
        column = lodf[:, outage]
        monitored = np.arange(system.branch.shape[0]) != outage
        if not np.all(np.isfinite(column[monitored])):
            continue
        credible += 1
        for line in np.where(monitored)[0]:
            factors.append(
                system.ptdf[line] + column[line] * system.ptdf[outage]
            )
            limits.append(float(rate[line]))
            outage_ids.append(outage)
    if not factors:
        raise RuntimeError("No finite non-islanding N-1 contingencies found")
    return (
        np.asarray(factors, dtype=float),
        np.asarray(limits, dtype=float),
        np.asarray(outage_ids, dtype=int),
        credible,
    )


def solve_n1_sced(
    system: PowerSystem,
    load_mw: np.ndarray,
    segments: int = 10,
    security_factors: tuple[np.ndarray, np.ndarray, np.ndarray, int] | None = None,
) -> SCEDResult:
    """Solve a continuous DC dispatch secure against every non-islanding line outage.

    Base-case line limits and every finite post-contingency line limit are
    imposed simultaneously in one linear program.  No contingency screening,
    rating adjustment, or outcome-dependent line selection is used.
    """
    active = system.gen[:, 7] > 0
    gen = system.gen[active]
    gencost = system.gencost[active]
    gen_bus = system.gen_bus[active]
    pmax = gen[:, 8]
    pmin = gen[:, 9]
    widths: list[float] = []
    costs: list[float] = []
    segment_gen: list[int] = []
    fixed_cost = 0.0
    for g in range(len(gen)):
        model = int(gencost[g, 0])
        if model != 2:
            raise ValueError("Only polynomial generator costs are supported")
        ncoef = int(gencost[g, 3])
        coeff = gencost[g, 4 : 4 + ncoef]
        if ncoef == 3:
            a, b, c0 = coeff
        elif ncoef == 2:
            a, b, c0 = 0.0, coeff[0], coeff[1]
        else:
            a, b, c0 = 0.0, 0.0, coeff[-1] if len(coeff) else 0.0
        fixed_cost += a * pmin[g] ** 2 + b * pmin[g] + c0
        width = max(0.0, pmax[g] - pmin[g]) / segments
        for s in range(segments):
            midpoint = pmin[g] + (s + 0.5) * width
            widths.append(width)
            costs.append(2.0 * a * midpoint + b)
            segment_gen.append(g)

    widths_a = np.asarray(widths)
    c = np.asarray(costs)
    cg = np.zeros((system.bus.shape[0], len(gen)))
    cg[gen_bus, np.arange(len(gen))] = 1.0
    if security_factors is None:
        security_factors = build_n1_security_factors(system)
    contingency_factors, contingency_limits, outage_ids, credible = (
        security_factors
    )
    base_limits = system.branch[:, 5].copy()
    base_limits[base_limits <= 0] = 1e6
    security_factors = np.vstack([system.ptdf, contingency_factors])
    security_limits = np.concatenate([base_limits, contingency_limits])
    hgen = security_factors @ cg
    hseg = hgen[:, np.asarray(segment_gen)]
    fixed_injection = cg @ pmin - load_mw
    fixed_flow = security_factors @ fixed_injection
    aub = np.vstack([hseg, -hseg])
    bub = np.concatenate(
        [security_limits - fixed_flow, security_limits + fixed_flow]
    )
    result = linprog(
        c,
        A_ub=csr_matrix(aub),
        b_ub=bub,
        A_eq=csr_matrix(np.ones((1, len(c)))),
        b_eq=np.array([float(load_mw.sum() - pmin.sum())]),
        bounds=list(zip(np.zeros(len(c)), widths_a)),
        method="highs",
        options={"presolve": True},
    )
    if not result.success:
        raise RuntimeError(
            f"N-1 SCED failed: {result.message}; demand={load_mw.sum():.2f} MW"
        )
    q_by_gen = np.bincount(
        np.asarray(segment_gen), weights=result.x, minlength=len(gen)
    )
    pg_active = pmin + q_by_gen
    pg_all = np.zeros(system.gen.shape[0])
    pg_all[np.where(active)[0]] = pg_active
    injection = cg @ pg_active - load_mw
    all_flows = security_factors @ injection
    base_flow = all_flows[: system.branch.shape[0]]
    contingency_loading = (
        np.abs(all_flows[system.branch.shape[0] :]) / contingency_limits
    )
    mu_upper = result.ineqlin.marginals[: len(security_limits)]
    mu_lower = result.ineqlin.marginals[len(security_limits) :]
    lambda_energy = float(result.eqlin.marginals[0])
    lmp = lambda_energy + security_factors.T @ (mu_upper - mu_lower)
    base_loading = np.abs(base_flow) / base_limits
    return SCEDResult(
        success=True,
        objective=float(result.fun + fixed_cost),
        generation_mw=pg_all,
        line_flow_mw=base_flow,
        lmp_per_mwh=lmp,
        max_loading=float(base_loading.max()),
        congested_lines=int(np.sum(base_loading >= 0.999)),
        max_post_contingency_loading=float(contingency_loading.max()),
        binding_contingency_constraints=int(
            np.sum(contingency_loading >= 0.999)
        ),
        credible_contingencies=int(credible),
    )


def solve_n1_sced_segment_minimum(
    system: PowerSystem,
    endpoint_load_profiles_mw: np.ndarray,
    segments: int = 10,
    security_factors: tuple[np.ndarray, np.ndarray, np.ndarray, int] | None = None,
    dt_h: float = 1.0,
) -> float:
    """Minimize the exact secure SCED value over a two-profile segment.

    ``endpoint_load_profiles_mw`` has shape ``[2, time, bus]``.  A single
    scalar ``theta`` is shared by all intervals, so the solved profile is
    ``(1-theta) * endpoint[0] + theta * endpoint[1]``.  Generation dispatch
    variables and all base-case and finite N-1 constraints are included for
    every interval in one LP.  Consequently the returned value is a true
    continuous-segment minimum, rather than a grid approximation or an
    endpoint surrogate.
    """
    profiles = np.asarray(endpoint_load_profiles_mw, dtype=float)
    if profiles.ndim != 3 or profiles.shape[0] != 2:
        raise ValueError("endpoint_load_profiles_mw must have shape [2, time, bus]")
    if not np.isfinite(profiles).all() or profiles.shape[1] == 0:
        raise ValueError("endpoint_load_profiles_mw must be finite and non-empty")
    if dt_h <= 0:
        raise ValueError("dt_h must be positive")

    active = system.gen[:, 7] > 0
    gen = system.gen[active]
    gencost = system.gencost[active]
    gen_bus = system.gen_bus[active]
    pmax = gen[:, 8]
    pmin = gen[:, 9]
    widths: list[float] = []
    costs: list[float] = []
    segment_gen: list[int] = []
    fixed_cost = 0.0
    for g in range(len(gen)):
        if int(gencost[g, 0]) != 2:
            raise ValueError("Only polynomial generator costs are supported")
        ncoef = int(gencost[g, 3])
        coeff = gencost[g, 4 : 4 + ncoef]
        if ncoef == 3:
            quadratic, linear, constant = coeff
        elif ncoef == 2:
            quadratic, linear, constant = 0.0, coeff[0], coeff[1]
        else:
            quadratic, linear = 0.0, 0.0
            constant = coeff[-1] if len(coeff) else 0.0
        fixed_cost += quadratic * pmin[g] ** 2 + linear * pmin[g] + constant
        width = max(0.0, pmax[g] - pmin[g]) / int(segments)
        for segment in range(int(segments)):
            midpoint = pmin[g] + (segment + 0.5) * width
            widths.append(width)
            costs.append(2.0 * quadratic * midpoint + linear)
            segment_gen.append(g)
    widths_a = np.asarray(widths, dtype=float)
    costs_a = np.asarray(costs, dtype=float)
    segment_gen_a = np.asarray(segment_gen, dtype=int)
    segment_count = len(costs_a)

    cg = np.zeros((system.bus.shape[0], len(gen)))
    cg[gen_bus, np.arange(len(gen))] = 1.0
    if security_factors is None:
        security_factors = build_n1_security_factors(system)
    contingency_factors, contingency_limits, _, _ = security_factors
    base_limits = system.branch[:, 5].copy()
    base_limits[base_limits <= 0] = 1e6
    factors = np.vstack([system.ptdf, contingency_factors])
    limits = np.concatenate([base_limits, contingency_limits])
    hseg = (factors @ cg)[:, segment_gen_a]
    time_count = profiles.shape[1]
    load0 = profiles[0]
    load_delta = profiles[1] - profiles[0]
    fixed_flow = np.asarray([factors @ (cg @ pmin - load0[t]) for t in range(time_count)])
    delta_flow = np.asarray([-factors @ load_delta[t] for t in range(time_count)])

    # Variable layout: q[t, segment] followed by the shared segment parameter.
    theta_index = time_count * segment_count
    variable_count = theta_index + 1
    objective = np.zeros(variable_count, dtype=float)
    objective[:theta_index] = np.tile(costs_a, time_count) * float(dt_h)
    eq_rows: list[int] = []
    eq_cols: list[int] = []
    eq_data: list[float] = []
    b_eq: list[float] = []
    for t in range(time_count):
        row = t
        start = t * segment_count
        for segment in range(segment_count):
            eq_rows.append(row)
            eq_cols.append(start + segment)
            eq_data.append(1.0)
        eq_rows.append(row)
        eq_cols.append(theta_index)
        eq_data.append(-float(load_delta[t].sum()))
        b_eq.append(float(load0[t].sum() - pmin.sum()))

    ub_rows: list[int] = []
    ub_cols: list[int] = []
    ub_data: list[float] = []
    b_ub: list[float] = []
    row = 0
    for t in range(time_count):
        start = t * segment_count
        for monitored in range(len(limits)):
            for segment in range(segment_count):
                value = float(hseg[monitored, segment])
                if value:
                    ub_rows.append(row)
                    ub_cols.append(start + segment)
                    ub_data.append(value)
            theta_value = float(delta_flow[t, monitored])
            if theta_value:
                ub_rows.append(row)
                ub_cols.append(theta_index)
                ub_data.append(theta_value)
            b_ub.append(float(limits[monitored] - fixed_flow[t, monitored]))
            row += 1
            for segment in range(segment_count):
                value = -float(hseg[monitored, segment])
                if value:
                    ub_rows.append(row)
                    ub_cols.append(start + segment)
                    ub_data.append(value)
            theta_value = -float(delta_flow[t, monitored])
            if theta_value:
                ub_rows.append(row)
                ub_cols.append(theta_index)
                ub_data.append(theta_value)
            b_ub.append(float(limits[monitored] + fixed_flow[t, monitored]))
            row += 1

    result = linprog(
        objective,
        A_ub=coo_matrix((ub_data, (ub_rows, ub_cols)), shape=(row, variable_count)).tocsr(),
        b_ub=np.asarray(b_ub, dtype=float),
        A_eq=coo_matrix((eq_data, (eq_rows, eq_cols)), shape=(time_count, variable_count)).tocsr(),
        b_eq=np.asarray(b_eq, dtype=float),
        bounds=[(0.0, float(width)) for width in np.tile(widths_a, time_count)]
        + [(0.0, 1.0)],
        method="highs",
        options={"presolve": True},
    )
    if not result.success:
        raise RuntimeError(f"Joint N-1 SCED segment minimum failed: {result.message}")
    return float(result.fun + time_count * float(dt_h) * fixed_cost)


def solve_payment_certified_n1_projection(
    system: PowerSystem,
    native_load_mw: np.ndarray,
    dc_buses: np.ndarray,
    candidate_profiles_mw: np.ndarray,
    target_profile_mw: np.ndarray,
    reference_candidate: int,
    event_slots: list[int],
    dt_h: float,
    segments: int = 10,
    security_factors: tuple[np.ndarray, np.ndarray, np.ndarray, int] | None = None,
    conversion_scale_factors: np.ndarray | None = None,
) -> PaymentCertifiedResult:
    """Project onto a feasible hull under scenario-robust N-1 payment caps.

    Candidate profiles are complete workload-feasible schedules for the same
    submitted-job ledger. Their convex hull therefore preserves every linear
    release, deadline, capacity, and conservation constraint. The contractual
    implementation uses vertex N-1 SCED values as a Jensen upper bound for the
    convex optimal-value function, followed by an independent exact N-1 replay
    of the selected profile. Two global linear programs implement a
    lexicographic objective: the first minimizes trajectory error and the
    second preserves that optimum while maximizing the worst fractional cost
    margin over all declared conversion scenarios. No contingency, scenario,
    or candidate is screened, and no post-solution acceptance rule is used.
    """
    candidates = np.asarray(candidate_profiles_mw, dtype=float)
    target = np.asarray(target_profile_mw, dtype=float)
    buses = np.asarray(dc_buses, dtype=int)
    native = np.asarray(native_load_mw, dtype=float)
    slots = [int(value) for value in event_slots]
    scale_factors = np.asarray(
        [1.0] if conversion_scale_factors is None else conversion_scale_factors,
        dtype=float,
    )
    if candidates.ndim != 3:
        raise ValueError("candidate_profiles_mw must have [candidate, data_center, time] dimensions")
    candidate_count, dc_count, time_count = candidates.shape
    if target.shape != (dc_count, time_count):
        raise ValueError(f"target_profile_mw has shape {target.shape}, expected {(dc_count, time_count)}")
    if native.shape != (system.bus.shape[0],):
        raise ValueError("native_load_mw does not match the network bus count")
    if buses.shape != (dc_count,) or np.any(buses < 0) or np.any(buses >= len(native)):
        raise ValueError("dc_buses does not match the profile data-center dimension")
    if not 0 <= int(reference_candidate) < candidate_count:
        raise ValueError("reference_candidate is outside the candidate set")
    if not slots or min(slots) < 0 or max(slots) >= time_count:
        raise ValueError("event_slots are outside the candidate horizon")
    if (
        scale_factors.ndim != 1
        or len(scale_factors) == 0
        or not np.isfinite(scale_factors).all()
        or np.any(scale_factors <= 0)
    ):
        raise ValueError(
            "conversion_scale_factors must be a nonempty positive finite vector"
        )

    # The contractual certificate uses a compact global LP whose security
    # constraints are the exact convex-value upper bound at every declared
    # candidate vertex.  For a convex optimal SCED value function f,
    # f(sum(alpha_i p_i)) <= sum(alpha_i f(p_i)); constraining the right-hand
    # side by the reference value is therefore a rigorous certificate for the
    # selected convex combination.  This replaces repeated embedded dispatch
    # copies while retaining an independent exact N-1 replay of the selected
    # profile below.  No candidate or contingency is screened.
    if security_factors is None:
        security_factors = build_n1_security_factors(system)
    scenario_count = len(scale_factors)
    vertex_costs = np.zeros(
        (scenario_count, len(slots), candidate_count), dtype=float
    )
    for scenario, scale_factor in enumerate(scale_factors):
        for local_slot, slot in enumerate(slots):
            for candidate in range(candidate_count):
                load = native.copy()
                load[buses] += (
                    float(scale_factor) * candidates[candidate, :, slot]
                )
                solved = solve_n1_sced(
                    system,
                    load,
                    int(segments),
                    security_factors=security_factors,
                )
                if not solved.success:
                    raise RuntimeError(
                        "Vertex-cost Jensen certificate evaluator failed: "
                        f"{solved.solver_message}"
                    )
                vertex_costs[scenario, local_slot, candidate] = (
                    float(solved.objective) * float(dt_h)
                )
    reference_costs = vertex_costs[:, :, int(reference_candidate)].sum(axis=1)
    total_vertex_costs = vertex_costs.sum(axis=1)
    error_count = dc_count * len(slots)
    eta_index = candidate_count + error_count
    variable_count = eta_index + 1
    objective = np.zeros(variable_count, dtype=float)
    objective[candidate_count:eta_index] = 1.0 / max(1, error_count)

    eq_rows = np.zeros(candidate_count, dtype=int)
    eq_cols = np.arange(candidate_count, dtype=int)
    eq_data = np.ones(candidate_count, dtype=float)
    a_eq = coo_matrix(
        (eq_data, (eq_rows, eq_cols)), shape=(1, variable_count)
    ).tocsr()
    b_eq = np.asarray([1.0], dtype=float)
    ub_rows: list[int] = []
    ub_cols: list[int] = []
    ub_data: list[float] = []
    b_ub: list[float] = []
    row = 0
    def error_index(dc: int, local_slot: int) -> int:
        return candidate_count + local_slot * dc_count + dc

    for local_slot, slot in enumerate(slots):
        for dc in range(dc_count):
            for sign in (1.0, -1.0):
                for candidate in range(candidate_count):
                    value = sign * float(candidates[candidate, dc, slot])
                    if value:
                        ub_rows.append(row)
                        ub_cols.append(candidate)
                        ub_data.append(value)
                ub_rows.append(row)
                ub_cols.append(error_index(dc, local_slot))
                ub_data.append(-1.0)
                b_ub.append(sign * float(target[dc, slot]))
                row += 1
    for scenario in range(scenario_count):
        for candidate, value in enumerate(total_vertex_costs[scenario]):
            if value:
                ub_rows.append(row)
                ub_cols.append(candidate)
                ub_data.append(float(value))
        b_ub.append(float(reference_costs[scenario]) + 1e-8)
        row += 1
        # The same inequality with eta is used in the second lexicographic
        # stage to maximize a common fractional slack without changing the
        # first-stage target projection.
        ub_rows.append(row)
        ub_cols.append(eta_index)
        ub_data.append(float(reference_costs[scenario]))
        for candidate, value in enumerate(total_vertex_costs[scenario]):
            if value:
                ub_rows.append(row)
                ub_cols.append(candidate)
                ub_data.append(float(value))
        b_ub.append(float(reference_costs[scenario]) + 1e-8)
        row += 1
    a_ub = coo_matrix(
        (ub_data, (ub_rows, ub_cols)), shape=(row, variable_count)
    ).tocsr()
    bounds = (
        [(0.0, 1.0)] * candidate_count
        + [(0.0, None)] * error_count
        + [(0.0, 1.0)]
    )
    first_stage = linprog(
        objective,
        A_ub=a_ub,
        b_ub=np.asarray(b_ub, dtype=float),
        A_eq=a_eq,
        b_eq=b_eq,
        bounds=bounds,
        method="highs",
        options={"presolve": True},
    )
    if not first_stage.success:
        return PaymentCertifiedResult(
            False,
            np.empty_like(target),
            np.empty(candidate_count),
            np.inf,
            np.inf,
            np.inf,
            np.inf,
            first_stage.message,
            scale_factors,
            np.full(scenario_count, np.inf),
            reference_costs,
        )
    l1_tolerance = max(1e-9, 1e-9 * abs(float(first_stage.fun)))
    l1_row = csr_matrix(objective.reshape(1, -1))
    second_objective = np.zeros(variable_count, dtype=float)
    second_objective[eta_index] = -1.0
    second_stage = linprog(
        second_objective,
        A_ub=vstack([a_ub, l1_row], format="csr"),
        b_ub=np.concatenate(
            [np.asarray(b_ub, dtype=float), [float(first_stage.fun) + l1_tolerance]]
        ),
        A_eq=a_eq,
        b_eq=b_eq,
        bounds=bounds,
        method="highs",
        options={"presolve": True},
    )
    result = second_stage if second_stage.success else first_stage
    weights = np.asarray(result.x[:candidate_count], dtype=float)
    profile = np.tensordot(weights, candidates, axes=(0, 0))
    certified_costs = np.zeros(scenario_count, dtype=float)
    for scenario, scale_factor in enumerate(scale_factors):
        for slot in slots:
            load = native.copy()
            load[buses] += float(scale_factor) * profile[:, slot]
            solved = solve_n1_sced(
                system,
                load,
                int(segments),
                security_factors=security_factors,
            )
            certified_costs[scenario] += float(solved.objective) * float(dt_h)
    nominal_scenario = int(np.argmin(np.abs(scale_factors - 1.0)))
    cost_violations = certified_costs - reference_costs
    return PaymentCertifiedResult(
        True,
        profile,
        weights,
        float(np.mean(result.x[candidate_count:eta_index])),
        float(certified_costs[nominal_scenario]),
        float(reference_costs[nominal_scenario]),
        float(max(0.0, cost_violations.max(initial=0.0))),
        "Vertex-cost Jensen certificate: exact global LP with independent N-1 replay",
        scale_factors,
        certified_costs,
        reference_costs,
        float(result.x[eta_index]),
        float(first_stage.fun),
    )

    active = system.gen[:, 7] > 0
    gen = system.gen[active]
    gencost = system.gencost[active]
    gen_bus = system.gen_bus[active]
    pmax = gen[:, 8]
    pmin = gen[:, 9]
    widths: list[float] = []
    costs: list[float] = []
    segment_gen: list[int] = []
    fixed_cost = 0.0
    for g in range(len(gen)):
        if int(gencost[g, 0]) != 2:
            raise ValueError("Only polynomial generator costs are supported")
        ncoef = int(gencost[g, 3])
        coeff = gencost[g, 4 : 4 + ncoef]
        if ncoef == 3:
            quadratic, linear, constant = coeff
        elif ncoef == 2:
            quadratic, linear, constant = 0.0, coeff[0], coeff[1]
        else:
            quadratic, linear = 0.0, 0.0
            constant = coeff[-1] if len(coeff) else 0.0
        fixed_cost += quadratic * pmin[g] ** 2 + linear * pmin[g] + constant
        width = max(0.0, pmax[g] - pmin[g]) / int(segments)
        for segment in range(int(segments)):
            midpoint = pmin[g] + (segment + 0.5) * width
            widths.append(width)
            costs.append(2.0 * quadratic * midpoint + linear)
            segment_gen.append(g)
    widths_array = np.asarray(widths, dtype=float)
    costs_array = np.asarray(costs, dtype=float)
    segment_gen_array = np.asarray(segment_gen, dtype=int)
    segment_count = len(costs_array)

    cg = np.zeros((system.bus.shape[0], len(gen)))
    cg[gen_bus, np.arange(len(gen))] = 1.0
    if security_factors is None:
        security_factors = build_n1_security_factors(system)
    contingency_factors, contingency_limits, _, _ = security_factors
    base_limits = system.branch[:, 5].copy()
    base_limits[base_limits <= 0] = 1e6
    factors = np.vstack([system.ptdf, contingency_factors])
    limits = np.concatenate([base_limits, contingency_limits])
    hseg = (factors @ cg)[:, segment_gen_array]
    fixed_network_flow = factors @ (cg @ pmin - native)

    error_count = dc_count * len(slots)
    scenario_count = len(scale_factors)
    weight_offset = 0
    error_offset = candidate_count
    dispatch_offset = error_offset + error_count
    margin_index = (
        dispatch_offset + scenario_count * len(slots) * segment_count
    )
    variable_count = margin_index + 1

    def error_index(dc: int, local_slot: int) -> int:
        return error_offset + local_slot * dc_count + dc

    def dispatch_index(
        scenario: int, local_slot: int, segment: int
    ) -> int:
        return (
            dispatch_offset
            + (scenario * len(slots) + local_slot) * segment_count
            + segment
        )

    objective = np.zeros(variable_count)
    objective[error_offset:dispatch_offset] = 1.0 / max(1, error_count)

    eq_rows: list[int] = []
    eq_cols: list[int] = []
    eq_data: list[float] = []
    b_eq: list[float] = []
    eq_row = 0
    for candidate in range(candidate_count):
        eq_rows.append(eq_row)
        eq_cols.append(weight_offset + candidate)
        eq_data.append(1.0)
    b_eq.append(1.0)
    eq_row += 1
    for scenario, scale_factor in enumerate(scale_factors):
        for local_slot, slot in enumerate(slots):
            for segment in range(segment_count):
                eq_rows.append(eq_row)
                eq_cols.append(
                    dispatch_index(scenario, local_slot, segment)
                )
                eq_data.append(1.0)
            for candidate in range(candidate_count):
                eq_rows.append(eq_row)
                eq_cols.append(weight_offset + candidate)
                eq_data.append(
                    -float(scale_factor)
                    * float(candidates[candidate, :, slot].sum())
                )
            b_eq.append(float(native.sum() - pmin.sum()))
            eq_row += 1

    ub_rows: list[int] = []
    ub_cols: list[int] = []
    ub_data: list[float] = []
    b_ub: list[float] = []
    ub_row = 0
    for local_slot, slot in enumerate(slots):
        for dc in range(dc_count):
            for sign in (1.0, -1.0):
                for candidate in range(candidate_count):
                    ub_rows.append(ub_row)
                    ub_cols.append(weight_offset + candidate)
                    ub_data.append(sign * float(candidates[candidate, dc, slot]))
                ub_rows.append(ub_row)
                ub_cols.append(error_index(dc, local_slot))
                ub_data.append(-1.0)
                b_ub.append(sign * float(target[dc, slot]))
                ub_row += 1

        dc_candidate_injections = np.zeros((system.bus.shape[0], candidate_count))
        dc_candidate_injections[buses, :] = candidates[:, :, slot].T
        candidate_flows = factors @ dc_candidate_injections
        for scenario, scale_factor in enumerate(scale_factors):
            for monitored in range(len(limits)):
                for candidate in range(candidate_count):
                    ub_rows.append(ub_row)
                    ub_cols.append(weight_offset + candidate)
                    ub_data.append(
                        -float(scale_factor)
                        * float(candidate_flows[monitored, candidate])
                    )
                for segment in range(segment_count):
                    value = float(hseg[monitored, segment])
                    if value:
                        ub_rows.append(ub_row)
                        ub_cols.append(
                            dispatch_index(scenario, local_slot, segment)
                        )
                        ub_data.append(value)
                b_ub.append(
                    float(limits[monitored] - fixed_network_flow[monitored])
                )
                ub_row += 1
                for candidate in range(candidate_count):
                    ub_rows.append(ub_row)
                    ub_cols.append(weight_offset + candidate)
                    ub_data.append(
                        float(scale_factor)
                        * float(candidate_flows[monitored, candidate])
                    )
                for segment in range(segment_count):
                    value = -float(hseg[monitored, segment])
                    if value:
                        ub_rows.append(ub_row)
                        ub_cols.append(
                            dispatch_index(scenario, local_slot, segment)
                        )
                        ub_data.append(value)
                b_ub.append(
                    float(limits[monitored] + fixed_network_flow[monitored])
                )
                ub_row += 1

    reference_costs = np.zeros(scenario_count, dtype=float)
    for scenario, scale_factor in enumerate(scale_factors):
        for slot in slots:
            load = native.copy()
            load[buses] += (
                float(scale_factor)
                * candidates[int(reference_candidate), :, slot]
            )
            reference_costs[scenario] += solve_n1_sced(
                system,
                load,
                int(segments),
                security_factors=security_factors,
            ).objective * float(dt_h)
        for local_slot in range(len(slots)):
            for segment in range(segment_count):
                ub_rows.append(ub_row)
                ub_cols.append(
                    dispatch_index(scenario, local_slot, segment)
                )
                ub_data.append(float(dt_h) * float(costs_array[segment]))
        # certified variable cost + fixed cost + eta * reference total cost
        # <= reference total cost.  eta is therefore a common fractional
        # economic margin across every declared conversion scenario.
        ub_rows.append(ub_row)
        ub_cols.append(margin_index)
        ub_data.append(float(reference_costs[scenario]))
        b_ub.append(
            float(reference_costs[scenario])
            - len(slots) * float(dt_h) * float(fixed_cost)
            + 1e-8
        )
        ub_row += 1

    a_eq = coo_matrix(
        (eq_data, (eq_rows, eq_cols)), shape=(eq_row, variable_count)
    ).tocsr()
    a_ub = coo_matrix(
        (ub_data, (ub_rows, ub_cols)), shape=(ub_row, variable_count)
    ).tocsr()
    bounds = (
        [(0.0, 1.0)] * candidate_count
        + [(0.0, None)] * error_count
        + [
            (0.0, float(widths_array[segment]))
            for _ in range(scenario_count)
            for _ in slots
            for segment in range(segment_count)
        ]
        + [(0.0, 1.0)]
    )
    first_stage = linprog(
        objective,
        A_ub=a_ub,
        b_ub=np.asarray(b_ub),
        A_eq=a_eq,
        b_eq=np.asarray(b_eq),
        bounds=bounds,
        method="highs",
        options={"presolve": True},
    )
    if not first_stage.success:
        return PaymentCertifiedResult(
            False,
            np.empty_like(target),
            np.empty(candidate_count),
            np.inf,
            np.inf,
            np.inf,
            np.inf,
            first_stage.message,
            scale_factors,
            np.full(scenario_count, np.inf),
            reference_costs,
        )
    # Preserve the exact first-stage optimum within a numerical tolerance and
    # maximize the common scenario margin. This removes arbitrary LP
    # tie-breaking without changing the primary trajectory objective.
    l1_tolerance = max(1e-9, 1e-9 * abs(float(first_stage.fun)))
    l1_row = csr_matrix(objective.reshape(1, -1))
    second_objective = np.zeros(variable_count)
    second_objective[margin_index] = -1.0
    second_stage = linprog(
        second_objective,
        A_ub=vstack([a_ub, l1_row], format="csr"),
        b_ub=np.concatenate(
            [np.asarray(b_ub), [float(first_stage.fun) + l1_tolerance]]
        ),
        A_eq=a_eq,
        b_eq=np.asarray(b_eq),
        bounds=bounds,
        method="highs",
        options={"presolve": True},
    )
    result = second_stage if second_stage.success else first_stage
    weights = result.x[:candidate_count]
    profile = np.tensordot(weights, candidates, axes=(0, 0))
    certified_costs = np.zeros(scenario_count, dtype=float)
    for scenario, scale_factor in enumerate(scale_factors):
        for slot in slots:
            load = native.copy()
            load[buses] += float(scale_factor) * profile[:, slot]
            certified_costs[scenario] += solve_n1_sced(
                system,
                load,
                int(segments),
                security_factors=security_factors,
            ).objective * float(dt_h)
    nominal_scenario = int(np.argmin(np.abs(scale_factors - 1.0)))
    cost_violations = certified_costs - reference_costs
    return PaymentCertifiedResult(
        True,
        profile,
        weights,
        float(np.mean(result.x[error_offset:dispatch_offset])),
        float(certified_costs[nominal_scenario]),
        float(reference_costs[nominal_scenario]),
        float(max(0.0, cost_violations.max(initial=0.0))),
        result.message,
        scale_factors,
        certified_costs,
        reference_costs,
        float(result.x[margin_index]),
        float(first_stage.fun),
    )


def build_grid_profiles(system: PowerSystem, cfg: dict[str, Any], logger: logging.Logger) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    slots = int(cfg["project"]["slots_per_day"])
    hourly = np.asarray(cfg["market"]["load_profile"], dtype=float)
    factor = np.repeat(hourly, slots // len(hourly))
    if len(factor) != slots:
        factor = np.interp(np.linspace(0, len(hourly), slots, endpoint=False), np.arange(len(hourly)), hourly)
    base_load = system.bus[:, 2]
    dc_buses = np.asarray(cfg["project"]["data_center_buses"], dtype=int) - 1
    base_profiles = np.zeros((slots, len(base_load)))
    lmp_profiles = np.zeros((len(dc_buses), slots))
    objectives = np.zeros(slots)
    fixed_dc = float(cfg["project"]["fixed_facility_load_mw"])
    for t in range(slots):
        load = base_load * factor[t]
        load = load.copy()
        load[dc_buses] += fixed_dc
        result = solve_sced(system, load, int(cfg["market"]["generator_segments"]))
        base_profiles[t] = load
        lmp_profiles[:, t] = result.lmp_per_mwh[dc_buses]
        objectives[t] = result.objective
    logger.info(
        "SCED-derived price profile built: range %.2f--%.2f $/MWh",
        lmp_profiles.min(),
        lmp_profiles.max(),
    )
    return base_profiles, lmp_profiles, objectives


def solve_workload_schedule(
    arrivals_mwh: np.ndarray,
    prices: np.ndarray,
    cfg: dict[str, Any],
    mode: str = "honest",
    dr_price: float = 0.0,
    event_probability: float = 0.0,
    target_power_mw: np.ndarray | None = None,
    projection_weight: float = 0.0,
    participating_destinations: list[int] | None = None,
    minimum_participant_event_mwh: float | None = None,
    power_upper_mw: np.ndarray | None = None,
    power_lower_mw: np.ndarray | None = None,
    projection_mask: np.ndarray | None = None,
    maximum_projection_l1_mw: float | None = None,
    operating_cost_weight: float = 1.0,
    require_all_arrivals_at_terminal: bool = True,
    terminal_completion_index: int | None = None,
    event_slots_override: list[int] | None = None,
) -> ScheduleResult:
    """Solve the full workload-conservation LP for one settlement day.

    arrivals_mwh has shape [time, source_region, workload_class]. The optimization
    jointly chooses service time and destination data center subject to release,
    deadline, capacity, and terminal completion constraints.  The default
    terminal condition completes every arrival.  Rolling-horizon callers may
    instead require completion only through ``terminal_completion_index``;
    later real arrivals remain in the model and cannot be served before release.
    """
    t_count, sources, classes = arrivals_mwh.shape
    destinations = prices.shape[0]
    if prices.shape[1] != t_count:
        raise ValueError("Price horizon and workload horizon differ")
    deadlines = np.asarray(cfg["workload"]["deadlines_slots"], dtype=int)
    wait_cost = np.asarray(cfg["workload"]["waiting_cost_per_mwh_slot"], dtype=float)
    dt_h = cfg["project"]["interval_minutes"] / 60.0
    flexible_cap_mwh = float(cfg["project"]["flexible_capacity_mw"]) * dt_h
    fixed_mw = float(cfg["project"]["fixed_facility_load_mw"])
    migration_cost = float(cfg["workload"]["migration_cost_per_mwh"])
    latency_cost = float(cfg["workload"]["cross_region_latency_penalty_per_mwh"])
    configured_event_slots = (
        cfg["market"]["event_slots"]
        if event_slots_override is None
        else event_slots_override
    )
    event_slots = set(
        int(x) for x in configured_event_slots if 0 <= int(x) < t_count
    )
    participants = set(participating_destinations if participating_destinations is not None else [0])

    def x_index(s: int, k: int, d: int, t: int) -> int:
        return (((s * classes + k) * destinations + d) * t_count + t)

    n_x = sources * classes * destinations * t_count
    n_y = sources * classes * t_count

    def y_index(s: int, k: int, t: int) -> int:
        return n_x + (s * classes + k) * t_count + t

    use_projection = target_power_mw is not None and (
        projection_weight > 0 or maximum_projection_l1_mw is not None
    )
    n_z = destinations * t_count if use_projection else 0
    z_offset = n_x + n_y
    n_var = n_x + n_y + n_z
    c = np.zeros(n_var)
    migrated_mask = np.zeros(n_x, dtype=bool)
    for s in range(sources):
        for k in range(classes):
            for d in range(destinations):
                spatial_cost = 0.0 if d == s else migration_cost + latency_cost * abs(d - s)
                for t in range(t_count):
                    idx = x_index(s, k, d, t)
                    value = prices[d, t] + spatial_cost + wait_cost[k] * t
                    if t in event_slots and d in participants:
                        if mode == "strategic_reference":
                            value -= dr_price * event_probability
                        elif mode == "event_response":
                            value += dr_price
                    c[idx] = float(operating_cost_weight) * value
                    migrated_mask[idx] = d != s
    if use_projection:
        if projection_mask is None:
            projection_mask_array = np.ones(
                (destinations, t_count), dtype=bool
            )
        else:
            projection_mask_array = np.asarray(projection_mask, dtype=bool)
            if projection_mask_array.shape != (destinations, t_count):
                raise ValueError(
                    "projection_mask has shape "
                    f"{projection_mask_array.shape}, expected "
                    f"{(destinations, t_count)}"
                )
        c[z_offset:] = (
            float(projection_weight)
            * projection_mask_array.reshape(-1).astype(float)
        )

    ub_rows: list[int] = []
    ub_cols: list[int] = []
    ub_data: list[float] = []
    b_ub: list[float] = []
    row = 0
    cumulative = np.cumsum(arrivals_mwh, axis=0)
    # Release and deadline bounds on explicit cumulative-service states. This
    # formulation is O(T), unlike a dense prefix matrix, and therefore supports
    # multi-day completion buffers without changing the exact feasible set.
    for s in range(sources):
        for k in range(classes):
            for t in range(t_count):
                ub_rows.append(row)
                ub_cols.append(y_index(s, k, t))
                ub_data.append(1.0)
                b_ub.append(float(cumulative[t, s, k]))
                row += 1
                due_t = t - int(deadlines[k])
                if due_t >= 0:
                    ub_rows.append(row)
                    ub_cols.append(y_index(s, k, t))
                    ub_data.append(-1.0)
                    b_ub.append(float(-cumulative[due_t, s, k]))
                    row += 1
    # Data-center capacity constraints.
    for d in range(destinations):
        for t in range(t_count):
            for s in range(sources):
                for k in range(classes):
                    ub_rows.append(row)
                    ub_cols.append(x_index(s, k, d, t))
                    ub_data.append(1.0)
            b_ub.append(flexible_cap_mwh)
            row += 1
    # Optional auditable risk envelope. The cap is expressed directly in
    # facility MW and therefore remains a linear workload constraint. It is
    # used to ensure that the final credited counterfactual cannot exceed an
    # independently selected feasible reference at any event sample.
    if power_upper_mw is not None:
        upper_power = np.asarray(power_upper_mw, dtype=float)
        if upper_power.shape != (destinations, t_count):
            raise ValueError(
                f"power_upper_mw has shape {upper_power.shape}, expected "
                f"{(destinations, t_count)}"
            )
        for d in range(destinations):
            for t in range(t_count):
                for s in range(sources):
                    for k in range(classes):
                        ub_rows.append(row)
                        ub_cols.append(x_index(s, k, d, t))
                        ub_data.append(1.0)
                b_ub.append(
                    max(0.0, float(upper_power[d, t] - fixed_mw)) * dt_h
                )
                row += 1
    if power_lower_mw is not None:
        lower_power = np.asarray(power_lower_mw, dtype=float)
        if lower_power.shape != (destinations, t_count):
            raise ValueError(
                f"power_lower_mw has shape {lower_power.shape}, expected "
                f"{(destinations, t_count)}"
            )
        for d in range(destinations):
            for t in range(t_count):
                for s in range(sources):
                    for k in range(classes):
                        ub_rows.append(row)
                        ub_cols.append(x_index(s, k, d, t))
                        ub_data.append(-1.0)
                b_ub.append(
                    -max(0.0, float(lower_power[d, t] - fixed_mw)) * dt_h
                )
                row += 1
    # L1 projection of the statistical baseline onto the workload-feasible set.
    if use_projection:
        target = np.asarray(target_power_mw)
        if target.shape != (destinations, t_count):
            raise ValueError(f"target_power_mw has shape {target.shape}, expected {(destinations, t_count)}")
        for d in range(destinations):
            for t in range(t_count):
                z = z_offset + d * t_count + t
                for s in range(sources):
                    for k in range(classes):
                        ub_rows.append(row)
                        ub_cols.append(x_index(s, k, d, t))
                        ub_data.append(1.0 / dt_h)
                ub_rows.append(row)
                ub_cols.append(z)
                ub_data.append(-1.0)
                b_ub.append(float(target[d, t] - fixed_mw))
                row += 1
                for s in range(sources):
                    for k in range(classes):
                        ub_rows.append(row)
                        ub_cols.append(x_index(s, k, d, t))
                        ub_data.append(-1.0 / dt_h)
                ub_rows.append(row)
                ub_cols.append(z)
                ub_data.append(-1.0)
                b_ub.append(float(-target[d, t] + fixed_mw))
                row += 1
        if maximum_projection_l1_mw is not None:
            for d in range(destinations):
                for t in range(t_count):
                    if projection_mask_array[d, t]:
                        ub_rows.append(row)
                        ub_cols.append(z_offset + d * t_count + t)
                        ub_data.append(1.0)
            b_ub.append(float(maximum_projection_l1_mw))
            row += 1

    # Optional parametric-service constraint used to obtain an independent
    # right-hand-side sensitivity certificate for the manipulation threshold:
    #     sum_{s,k,d in participants,t in event} x[s,k,d,t] >= R_min.
    # HiGHS reports dV/db for the equivalent -R <= -R_min row, so -dV/db is
    # the marginal physical cost of one additional MWh of event-window service.
    minimum_service_row: int | None = None
    if minimum_participant_event_mwh is not None:
        minimum_service_row = row
        for s in range(sources):
            for k in range(classes):
                for d in participants:
                    for t in event_slots:
                        ub_rows.append(row)
                        ub_cols.append(x_index(s, k, d, t))
                        ub_data.append(-1.0)
        b_ub.append(-float(minimum_participant_event_mwh))
        row += 1

    eq_rows: list[int] = []
    eq_cols: list[int] = []
    eq_data: list[float] = []
    b_eq: list[float] = []
    eq_row = 0
    for s in range(sources):
        for k in range(classes):
            for t in range(t_count):
                eq_rows.append(eq_row)
                eq_cols.append(y_index(s, k, t))
                eq_data.append(1.0)
                if t > 0:
                    eq_rows.append(eq_row)
                    eq_cols.append(y_index(s, k, t - 1))
                    eq_data.append(-1.0)
                for d in range(destinations):
                    eq_rows.append(eq_row)
                    eq_cols.append(x_index(s, k, d, t))
                    eq_data.append(-1.0)
                b_eq.append(0.0)
                eq_row += 1
            if require_all_arrivals_at_terminal:
                completion_index = t_count - 1
            else:
                completion_index = terminal_completion_index
            if completion_index is not None:
                # Arrivals whose deadlines fall inside the optimization window
                # are mandatory even when the economic comparison closes at an
                # earlier accounting cutoff.
                completion_index = max(
                    int(completion_index),
                    t_count - 1 - int(deadlines[k]),
                )
                if not 0 <= int(completion_index) < t_count:
                    raise ValueError(
                        "terminal_completion_index must lie within the horizon"
                    )
                eq_rows.append(eq_row)
                eq_cols.append(y_index(s, k, t_count - 1))
                eq_data.append(1.0)
                b_eq.append(
                    float(cumulative[int(completion_index), s, k])
                )
                eq_row += 1

    aub = coo_matrix((ub_data, (ub_rows, ub_cols)), shape=(row, n_var)).tocsr()
    aeq = coo_matrix((eq_data, (eq_rows, eq_cols)), shape=(eq_row, n_var)).tocsr()
    bounds = [(0.0, None)] * n_var
    result = linprog(
        c,
        A_ub=aub,
        b_ub=np.asarray(b_ub),
        A_eq=aeq,
        b_eq=np.asarray(b_eq),
        bounds=bounds,
        method="highs",
        options={"presolve": True},
    )
    if not result.success:
        return ScheduleResult(
            False,
            np.inf,
            np.empty((destinations, t_count)),
            np.empty(0),
            np.nan,
            result.message,
            np.nan,
            np.nan,
        )
    x = result.x[:n_x].reshape(sources, classes, destinations, t_count)
    power = fixed_mw + x.sum(axis=(0, 1)) / dt_h
    migrated = float(result.x[:n_x][migrated_mask].sum())
    shadow = (
        -float(result.ineqlin.marginals[minimum_service_row])
        if minimum_service_row is not None
        else np.nan
    )
    projection_l1 = (
        max(
            0.0,
            float(
                result.x[z_offset:]
                .reshape(destinations, t_count)[projection_mask_array]
                .sum()
            ),
        )
        if use_projection
        else np.nan
    )
    return ScheduleResult(
        True,
        float(result.fun),
        power,
        x,
        migrated,
        result.message,
        shadow,
        projection_l1,
    )


def solve_lexicographic_workload_projection(
    arrivals_mwh: np.ndarray,
    prices: np.ndarray,
    cfg: dict[str, Any],
    target_power_mw: np.ndarray,
    projection_mask: np.ndarray,
    *,
    require_all_arrivals_at_terminal: bool = True,
    terminal_completion_index: int | None = None,
    event_slots_override: list[int] | None = None,
) -> tuple[ScheduleResult, ScheduleResult]:
    """Project a power trajectory without a user-selected penalty weight.

    Stage one minimizes the masked L1 distance to the submitted trajectory.
    Stage two minimizes operating cost over the stage-one optimal face.  The
    only relaxation is a scale-aware numerical tolerance matching the linear
    solver's feasibility precision; it is reported through the returned
    stage-one and stage-two distances.
    """
    first = solve_workload_schedule(
        arrivals_mwh,
        prices,
        cfg,
        target_power_mw=target_power_mw,
        projection_weight=1.0,
        projection_mask=projection_mask,
        operating_cost_weight=0.0,
        require_all_arrivals_at_terminal=require_all_arrivals_at_terminal,
        terminal_completion_index=terminal_completion_index,
        event_slots_override=event_slots_override,
    )
    if not first.success:
        return first, first
    # HiGHS permits aggregate sparse-model residuals slightly above its
    # per-row primal tolerance. Five micro-MW is below metering resolution and
    # prevented from becoming a modeling degree of freedom by reporting it.
    tolerance = max(5e-6, 1e-9 * max(1.0, first.projection_l1_mw))
    second = solve_workload_schedule(
        arrivals_mwh,
        prices,
        cfg,
        target_power_mw=target_power_mw,
        projection_mask=projection_mask,
        maximum_projection_l1_mw=first.projection_l1_mw + tolerance,
        operating_cost_weight=1.0,
        require_all_arrivals_at_terminal=require_all_arrivals_at_terminal,
        terminal_completion_index=terminal_completion_index,
        event_slots_override=event_slots_override,
    )
    return first, second
