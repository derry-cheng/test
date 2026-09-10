from __future__ import annotations

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, minimize
from scipy.sparse import coo_matrix, csr_matrix


def test_daily_cvar_epigraph_aggregates_slots_and_meets_kkt():
    """The exact epigraph uses one daily tail row, not one row per slot."""

    # Two days, two event slots per day, and two convex candidates.
    design = np.array([[1.0, 2.0], [1.0, 0.0], [1.0, 2.0], [1.0, 0.0]])
    target = np.array([1.5, 0.5, 1.5, 0.5])
    ceiling = np.array([1.0, 0.5, 1.0, 0.5])
    days, slots, candidates = 2, 2, 2
    tail_count = 1  # CVaR_75 over two daily losses
    nvar = candidates + len(target) + days + 1
    nu = nvar - 1
    rows, cols, values, upper = [], [], [], []
    row = 0
    for sample in range(len(target)):
        rows.extend([row, row])
        cols.extend([0, candidates + sample])
        values.extend([design[sample, 0], -1.0])
        rows.append(row)
        cols.append(1)
        values.append(design[sample, 1])
        upper.append(float(ceiling[sample]))
        row += 1
    for day in range(days):
        for sample in range(day * slots, (day + 1) * slots):
            rows.append(row)
            cols.append(candidates + sample)
            values.append(1.0)
        rows.extend([row, row])
        cols.extend([nu, candidates + len(target) + day])
        values.extend([-1.0, -1.0])
        upper.append(0.0)
        row += 1
    # A positive CVaR reserve keeps the small test problem feasible.
    rows.append(row)
    cols.append(nu)
    values.append(1.0)
    for day in range(days):
        rows.append(row)
        cols.append(candidates + len(target) + day)
        values.append(1.0 / tail_count)
    upper.append(1.0)
    row += 1
    a_ub = coo_matrix((values, (rows, cols)), shape=(row, nvar)).tocsr()
    a_eq = csr_matrix(
        (np.ones(candidates), (np.zeros(candidates), np.arange(candidates))),
        shape=(1, nvar),
    )
    lower = np.zeros(nvar)
    upper_bounds = np.full(nvar, np.inf)
    upper_bounds[:candidates] = 1.0
    warm = linprog(
        np.zeros(nvar),
        A_ub=a_ub,
        b_ub=np.asarray(upper),
        A_eq=a_eq,
        b_eq=np.ones(1),
        bounds=list(zip(lower, upper_bounds)),
        method="highs",
    )
    assert warm.success

    def objective(x):
        residual = design @ x[:candidates] - target
        return float(np.mean(residual**2))

    def gradient(x):
        out = np.zeros(nvar)
        out[:candidates] = 2.0 * design.T @ (design @ x[:candidates] - target) / len(target)
        return out

    def hessian(_x, _multipliers=None):
        out = csr_matrix((nvar, nvar), dtype=float).tolil()
        out[:candidates, :candidates] = 2.0 * design.T @ design / len(target)
        return out.tocsr()

    fitted = minimize(
        objective,
        warm.x,
        jac=gradient,
        hess=hessian,
        method="trust-constr",
        bounds=Bounds(lower, upper_bounds),
        constraints=[
            LinearConstraint(a_eq, np.ones(1), np.ones(1)),
            LinearConstraint(a_ub, -np.inf * np.ones(row), np.asarray(upper)),
        ],
        options={
            "gtol": 1e-9,
            "xtol": 1e-10,
            "barrier_tol": 1e-9,
            "maxiter": 500,
            "sparse_jacobian": True,
        },
    )
    assert fitted.success
    assert fitted.optimality <= 1e-5
    assert np.max(np.abs(a_eq @ fitted.x - 1.0)) <= 1e-6
    assert np.max(a_ub @ fitted.x - np.asarray(upper)) <= 1e-6
    # The two slacks in each tail row are summed before CVaR is bounded.
    assert a_ub.shape[0] == len(target) + days + 1
