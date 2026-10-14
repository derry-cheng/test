"""Risk contracts that compose with executable, fixed-runtime schedules.

All guarantees are deterministic for a *common, fixed* meter and reference.
They are not counterfactual-identification or out-of-sample guarantees.  The
profile certificate and the payable-credit certificate are deliberately
separate: a credit cap cannot repair an inaccurate executable trajectory.
"""
from __future__ import annotations

from typing import Any
import numpy as np


def top_m_tail(values: np.ndarray, level: float = .75) -> float:
    """Mean of the largest ceil((1-level)*H) observations, including ties once.

    Its effective confidence is 1-m/H, which need not equal ``level``.
    """
    values = np.asarray(values, dtype=float).reshape(-1)
    if not len(values) or not np.isfinite(values).all() or not 0 < level < 1:
        raise ValueError("finite nonempty losses and 0 < level < 1 required")
    m = max(1, int(np.ceil((1. - level) * len(values))))
    return float(np.partition(values, len(values) - m)[-m:].mean())


def _matched_profiles(*profiles: np.ndarray) -> list[np.ndarray]:
    arrays = [np.asarray(x, dtype=float) for x in profiles]
    if any(x.ndim != 3 or x.shape != arrays[0].shape or not np.isfinite(x).all()
           for x in arrays):
        raise ValueError("profiles must be finite, matched (day, region, slot) arrays")
    if not all(arrays[0].shape):
        raise ValueError("profiles must be nonempty")
    return arrays


def daily_false_credit(baseline: np.ndarray, meter: np.ndarray,
                       reference: np.ndarray, dt_h: float,
                       event_slots: list[int] | np.ndarray) -> np.ndarray:
    """Daily false credit [ [b-m]+ - [r-m]+ ]+ in MWh."""
    baseline, meter, reference = _matched_profiles(baseline, meter, reference)
    if not np.isfinite(dt_h) or dt_h <= 0:
        raise ValueError("positive finite interval required")
    event = np.asarray(event_slots, dtype=int)
    if (event.ndim != 1 or not len(event) or len(np.unique(event)) != len(event)
            or np.any(event < 0) or np.any(event >= baseline.shape[-1])):
        raise ValueError("event slots must be distinct valid slot indices")
    # This compact hinge is exactly the nested positive-part definition.
    return (np.maximum(baseline - np.maximum(meter, reference), 0.)
            [:, :, event].sum(axis=(1, 2)) * dt_h)


def certify_execution_transfer(
    target: np.ndarray, execution: np.ndarray, meter: np.ndarray,
    reference: np.ndarray, dt_h: float, event_slots: list[int] | np.ndarray,
    total_budget_mwh: float | None = None, tail_budget_mwh: float | None = None,
    mse_budget_mw2: float | None = None, level: float = .75,
    tolerance: float = 1e-8,
) -> dict[str, Any]:
    """Exact postexecution audit, Lipschitz bounds and contract credit cap.

    For e=x-b and delta_d=dt*sum_event |e|, F_d(x)<=F_d(b)+delta_d.
    Monotonicity/subadditivity of top-m yields T_m(F(x))<=T_m(F(b))+T_m(delta).
    RMSE(x,r)<=RMSE(b,r)+RMSE(e).  Payment q=min([x-m]+,[b-m]+)
    has pointwise false credit no larger than b's, regardless of e.  Every
    quantity uses the same sample indices, meter, reference, and MW units.
    """
    target, execution, meter, reference = _matched_profiles(target, execution, meter, reference)
    before = daily_false_credit(target, meter, reference, dt_h, event_slots)
    after = daily_false_credit(execution, meter, reference, dt_h, event_slots)
    event = np.asarray(event_slots, dtype=int)
    e = (execution - target)[:, :, event]
    delta = dt_h * np.abs(e).sum(axis=(1, 2))
    raw_credit = np.maximum(execution - meter, 0.)[:, :, event]
    target_credit = np.maximum(target - meter, 0.)[:, :, event]
    true_credit = np.maximum(reference - meter, 0.)[:, :, event]
    capped = np.minimum(raw_credit, target_credit)
    capped_false = np.maximum(capped - true_credit, 0.).sum(axis=(1, 2)) * dt_h
    target_mse = float(np.mean((target[:, :, event] - reference[:, :, event]) ** 2))
    executed_mse = float(np.mean((execution[:, :, event] - reference[:, :, event]) ** 2))
    rms_bound = np.sqrt(target_mse) + np.sqrt(np.mean(e ** 2))
    m = max(1, int(np.ceil((1 - level) * len(before))))
    out: dict[str, Any] = {
        "target_total_false_credit_mwh": float(before.sum()),
        "executed_total_false_credit_mwh": float(after.sum()),
        "capped_total_false_credit_mwh": float(capped_false.sum()),
        "target_tail_false_credit_mwh": top_m_tail(before, level),
        "executed_tail_false_credit_mwh": top_m_tail(after, level),
        "capped_tail_false_credit_mwh": top_m_tail(capped_false, level),
        "target_event_mse_mw2": target_mse,
        "executed_event_mse_mw2": executed_mse,
        "event_residual_l1_mwh": float(delta.sum()),
        "total_false_credit_upper_bound_mwh": float(before.sum() + delta.sum()),
        "tail_false_credit_upper_bound_mwh": top_m_tail(before, level) + top_m_tail(delta, level),
        "event_mse_upper_bound_mw2": float(rms_bound ** 2),
        "uncapped_credit_mwh": float(raw_credit.sum() * dt_h),
        "contract_capped_credit_mwh": float(capped.sum() * dt_h),
        "credit_removed_mwh": float((raw_credit - capped).sum() * dt_h),
        "tail_count": m, "effective_tail_level": float(1 - m / len(before)),
        "max_daily_lipschitz_violation_mwh": float(max(0., np.max(after - before - delta))),
        "max_daily_cap_risk_violation_mwh": float(max(0., np.max(capped_false - before))),
        "daily_target_false_credit_mwh": before.tolist(),
        "daily_executed_false_credit_mwh": after.tolist(),
        "daily_capped_false_credit_mwh": capped_false.tolist(),
        "daily_residual_l1_mwh": delta.tolist(),
    }
    for key, value in (("total", total_budget_mwh), ("tail", tail_budget_mwh)):
        if value is not None:
            if not np.isfinite(value) or value < 0:
                raise ValueError("risk budgets must be finite and nonnegative")
            out[f"{key}_budget_mwh"] = float(value)
            for prefix in ("target", "executed", "capped"):
                out[f"{prefix}_{key}_budget_pass"] = bool(out[f"{prefix}_{key}_false_credit_mwh"] <= value + tolerance)
    if mse_budget_mw2 is not None:
        if not np.isfinite(mse_budget_mw2) or mse_budget_mw2 < 0:
            raise ValueError("MSE budget must be finite and nonnegative")
        out["mse_budget_mw2"] = float(mse_budget_mw2)
        out["executed_mse_budget_pass"] = bool(executed_mse <= mse_budget_mw2 + tolerance)
    out["budgets_checked"] = any(x is not None for x in (total_budget_mwh, tail_budget_mwh, mse_budget_mw2))
    out["execution_certificate_accept"] = out["budgets_checked"] and all(out[k] for k in out if k.startswith("executed_") and k.endswith("budget_pass"))
    risk_budgets_checked = total_budget_mwh is not None or tail_budget_mwh is not None
    out["payment_risk_certificate_accept"] = risk_budgets_checked and all(out[k] for k in out if k.startswith("capped_") and k.endswith("budget_pass"))
    return out


def fit_risk_simplex(
    design: np.ndarray, target: np.ndarray, meter: np.ndarray, day_count: int,
    dt_h: float = .25, level: float = .75,
    total_budget_mwh: float | None = None, tail_budget_mwh: float | None = None,
    mse_budget_mw2: float | None = None, total_weight: float = 1.,
    tail_weight: float = 0., total_scale_mwh: float | None = None,
    tail_scale_mwh: float | None = None, accuracy_mode: str = "exact",
    objective_mode: str = "fit", warm_alpha: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Fit a convex simplex with independently switchable objectives/budgets.

    Unlike the legacy ablation, disabling a hard row never removes a soft
    preference. ``exact`` enforces actual validation MSE; ``triangle`` keeps
    the legacy sufficient RMS certificate for a like-for-like control.
    ``minimum_tail`` computes the feasible validation tail endpoint without
    a point-estimation objective.  No locked observations are accepted here.
    """
    import cvxpy as cp
    d = np.asarray(design, dtype=float)
    y, meter = np.asarray(target, dtype=float).reshape(-1), np.asarray(meter, dtype=float).reshape(-1)
    if d.ndim != 2 or d.shape[0] != len(y) or y.shape != meter.shape or not np.isfinite(d).all() or not np.isfinite(y).all() or not np.isfinite(meter).all():
        raise ValueError("finite matched design, reference and meter required")
    n, k = d.shape
    if day_count <= 0 or n % day_count or dt_h <= 0 or not 0 < level < 1:
        raise ValueError("invalid day partition, interval or tail level")
    if min(total_weight, tail_weight) < 0 or accuracy_mode not in {"exact", "triangle"} or objective_mode not in {"fit", "minimum_tail"}:
        raise ValueError("invalid objective or accuracy mode")
    if any(x is not None and (not np.isfinite(x) or x < 0) for x in (total_budget_mwh, tail_budget_mwh, mse_budget_mw2)):
        raise ValueError("budgets must be finite and nonnegative")
    m = max(1, int(np.ceil((1 - level) * day_count)))
    s = n // day_count
    ceiling = np.maximum(y, meter)
    scale = max(float(np.mean(y ** 2)), 1.)  # fixed 1 MW^2 normalization floor
    total_scale = max(float(total_scale_mwh or 1.), 1e-12)
    tail_scale = max(float(tail_scale_mwh or 1.), 1e-12)
    alpha, f, u, eta = cp.Variable(k), cp.Variable(n), cp.Variable(day_count), cp.Variable()
    daily = dt_h * cp.sum(cp.reshape(f, (day_count, s), order="C"), axis=1)
    tail = eta + cp.sum(u) / m
    residual = d @ alpha - y
    # Thin QR is an exact norm-preserving reduction, not a surrogate: the
    # conic accuracy row has at most k+1 dimensions instead of n samples.
    _, qr_r = np.linalg.qr(np.column_stack((d, -y)), mode="reduced")
    mse = cp.sum_squares(qr_r @ cp.hstack((alpha, 1.))) / n
    rms_candidates = np.sqrt(np.mean((d - y[:, None]) ** 2, axis=0))
    con = {
        "simplex": cp.sum(alpha) == 1., "alpha_lower": -alpha <= 0.,
        "false_lower": -f <= 0., "false_epigraph": d @ alpha - f <= ceiling,
        "u_lower": -u <= 0., "eta_lower": -eta <= 0.,
        "tail_epigraph": daily - eta - u <= 0.,
    }
    if total_budget_mwh is not None:
        con["total_budget"] = dt_h * cp.sum(f) <= total_budget_mwh
    if tail_budget_mwh is not None:
        con["tail_budget"] = tail <= tail_budget_mwh
    if mse_budget_mw2 is not None:
        con["accuracy"] = (mse / scale <= mse_budget_mw2 / scale if accuracy_mode == "exact"
                           else rms_candidates @ alpha <= np.sqrt(mse_budget_mw2))
    reg = 1e-8
    if objective_mode == "fit":
        objective = mse / scale + reg * cp.sum_squares(alpha)
        objective += total_weight * dt_h * cp.sum(f) / total_scale + tail_weight * tail / tail_scale
    else:
        objective = tail / tail_scale + reg * cp.sum_squares(alpha)
    if warm_alpha is not None:
        alpha.value = np.asarray(warm_alpha, dtype=float)
    problem = cp.Problem(cp.Minimize(objective), list(con.values()))
    problem.solve(solver="CLARABEL", tol_gap_abs=1e-10, tol_gap_rel=1e-10, tol_feas=1e-10, max_iter=500)
    if problem.status not in (cp.OPTIMAL, cp.OPTIMAL_INACCURATE):
        raise RuntimeError(f"Risk simplex is {problem.status}")
    a, fv, uv, ev = np.asarray(alpha.value), np.asarray(f.value), np.asarray(u.value), float(eta.value)
    pred = d @ a
    exact_day = np.maximum(pred - ceiling, 0.).reshape(day_count, s).sum(axis=1) * dt_h
    exact_total, exact_tail = float(exact_day.sum()), top_m_tail(exact_day, level)
    exact_mse = float(np.mean((pred - y) ** 2))
    # Recompute stationarity, feasibility and complementarity in original
    # variables from explicit row duals; never equate solver success to proof.
    dual = {name: np.asarray(c.dual_value, dtype=float).squeeze() for name, c in con.items()}
    ga = 2 * reg * a
    gf, gu, ge = np.zeros(n), np.zeros(day_count), 0.
    if objective_mode == "fit":
        ga += 2 * d.T @ (pred - y) / (n * scale)
        gf += total_weight * dt_h / total_scale
        gu += tail_weight / (m * tail_scale); ge += tail_weight / tail_scale
    else:
        gu += 1 / (m * tail_scale); ge += 1 / tail_scale
    ga += float(dual["simplex"]) - dual["alpha_lower"] + d.T @ dual["false_epigraph"]
    gf += -dual["false_lower"] - dual["false_epigraph"] + dt_h * np.repeat(dual["tail_epigraph"], s)
    gu += -dual["u_lower"] - dual["tail_epigraph"]
    ge += -float(dual["eta_lower"]) - float(np.sum(dual["tail_epigraph"]))
    if "total_budget" in dual: gf += dt_h * float(dual["total_budget"])
    if "tail_budget" in dual:
        gu += float(dual["tail_budget"]) / m; ge += float(dual["tail_budget"])
    if "accuracy" in dual:
        ga += float(dual["accuracy"]) * (2 * d.T @ (pred - y) / (n * scale) if accuracy_mode == "exact" else rms_candidates)
    slacks: dict[str, np.ndarray | float] = {
        "alpha_lower": a, "false_lower": fv, "false_epigraph": ceiling - pred + fv,
        "u_lower": uv, "eta_lower": ev,
        "tail_epigraph": ev + uv - dt_h * fv.reshape(day_count, s).sum(axis=1),
    }
    if "total_budget" in dual: slacks["total_budget"] = total_budget_mwh - dt_h * fv.sum()
    if "tail_budget" in dual: slacks["tail_budget"] = tail_budget_mwh - ev - uv.sum() / m
    if "accuracy" in dual: slacks["accuracy"] = ((mse_budget_mw2 - exact_mse) / scale if accuracy_mode == "exact" else np.sqrt(mse_budget_mw2) - rms_candidates @ a)
    primal = max(abs(a.sum() - 1), max(max(0., -float(np.min(v))) for v in slacks.values()))
    comp = max(float(np.max(np.abs(dual[name] * value))) for name, value in slacks.items())
    stationary = float(np.max(np.abs(np.r_[ga, gf, gu, ge])))
    dual_neg = max(max(0., -float(np.min(v))) for name, v in dual.items() if name != "simplex")
    kkt = max(comp, stationary, dual_neg)
    if primal > 1e-5 or kkt > 1e-5:
        raise RuntimeError(f"Risk certificate rejected: primal={primal:g}, KKT={kkt:g}")
    cert: dict[str, Any] = {
        "solver": "CVXPY CLARABEL", "solver_status": str(problem.status),
        "objective_mode": objective_mode, "accuracy_mode": accuracy_mode,
        "objective": float(problem.value), "mse_mw2": exact_mse,
        "total_false_credit_mwh": exact_total, "tail_false_credit_mwh": exact_tail,
        "tail_count": m, "effective_tail_level": 1. - m / day_count,
        "total_weight": total_weight, "tail_weight": tail_weight,
        "primal_residual": float(primal), "kkt_residual": kkt,
        "stationarity_residual": stationary, "complementarity_residual": comp,
        "total_budget_mwh": total_budget_mwh, "tail_budget_mwh": tail_budget_mwh,
        "mse_budget_mw2": mse_budget_mw2, "day_count": day_count,
        "daily_false_credit_mwh": exact_day.tolist(),
        "total_budget_dual": float(dual.get("total_budget", 0.)),
        "tail_budget_dual": float(dual.get("tail_budget", 0.)),
        "accuracy_dual": float(dual.get("accuracy", 0.)),
    }
    for label, budget, actual in (("total", total_budget_mwh, exact_total), ("tail", tail_budget_mwh, exact_tail)):
        cert[f"{label}_budget_slack_mwh"] = None if budget is None else float(budget - actual)
        cert[f"{label}_budget_binding"] = bool(budget is not None and abs(budget - actual) <= 1e-6 * max(1., budget))
    return a, cert


def run_exp31_risk_execution_composition(root, cfg, logger) -> None:
    """Run the frozen retrospective redesign, then its untouched locked audit."""
    from pathlib import Path
    import json
    import pandas as pd
    from .utils import write_json, sha256
    from .baselines import response_metrics, baseline_metrics
    root = Path(root)
    final = root / "experiments/exp31_risk_execution_composition/results/final"
    final.mkdir(parents=True, exist_ok=True)
    exp2 = root / "experiments/exp2_baseline_verification/results"
    validation_path = exp2 / "intermediate/validation_profiles.npz"
    test_path = exp2 / "intermediate/test_profiles.npz"
    event = np.asarray(cfg["market"]["event_slots"], dtype=int)
    dt = float(cfg["project"]["interval_minutes"]) / 60.
    level = float(cfg["experiments"].get("risk_cvar_level", .75))
    with np.load(validation_path, allow_pickle=False) as cache:
        candidates = np.asarray(cache["risk_candidate_profiles"])
        validation_days = np.asarray(cache["days"])
        y_profile, meter_profile = np.asarray(cache["oracle"]), np.asarray(cache["actual"])
        reference_index = int(cache["risk_reference_index"])
    h, k = len(validation_days), candidates.shape[0]
    design = candidates[:, :, :, event].transpose(1, 2, 3, 0).reshape(-1, k)
    y, meter = y_profile[:, :, event].reshape(-1), meter_profile[:, :, event].reshape(-1)
    anchor = design[:, reference_index]
    anchor_day = np.maximum(anchor - np.maximum(y, meter), 0.).reshape(h, -1).sum(axis=1) * dt
    anchor_total, anchor_tail = float(anchor_day.sum()), top_m_tail(anchor_day, level)
    mse_budget = float(1.1 * np.mean((anchor - y) ** 2))
    common = dict(design=design, target=y, meter=meter, day_count=h, dt_h=dt, level=level,
                  mse_budget_mw2=mse_budget, total_scale_mwh=anchor_total, tail_scale_mwh=anchor_tail)
    fitted: dict[str, tuple[np.ndarray, dict]] = {}
    failures: list[dict] = []
    def fit(name, **kwargs):
        try:
            a, cert = fit_risk_simplex(**common, **kwargs)
            fitted[name] = (a, cert)
            logger.info("Exp31 %s: validation total %.6f, tail %.6f MWh, KKT %.2g", name, cert["total_false_credit_mwh"], cert["tail_false_credit_mwh"], cert["kkt_residual"])
            return a, cert
        except Exception as exc:
            failures.append({"method": name, "error_type": type(exc).__name__, "message": str(exc)})
            write_json(final / "solver_failures.json", failures)
            raise
    fit("legacy_same_objective_hard", accuracy_mode="triangle", total_weight=1., tail_weight=.5,
        total_budget_mwh=anchor_total, tail_budget_mwh=anchor_tail)
    fit("legacy_same_objective_no_hard", accuracy_mode="triangle", total_weight=1., tail_weight=.5)
    fit("exact_mse_fixed_soft_joint", total_weight=1., tail_weight=.5,
        total_budget_mwh=anchor_total, tail_budget_mwh=anchor_tail)
    total_a, total_cert = fit("exact_mse_total_only", total_weight=1., tail_weight=0., total_budget_mwh=anchor_total)
    total_budget = 1.1 * total_cert["total_false_credit_mwh"]
    min_a, min_cert = fit("minimum_feasible_tail_endpoint", objective_mode="minimum_tail", total_budget_mwh=total_budget)
    minimum_tail, total_tail = min_cert["tail_false_credit_mwh"], total_cert["tail_false_credit_mwh"]
    if minimum_tail > total_tail + 1e-6:
        raise RuntimeError("The tail endpoint exceeded the feasible total-only point")
    for fraction in (.25, .5, .75):
        budget = minimum_tail + fraction * (total_tail - minimum_tail)
        fit(f"active_tail_fraction_{fraction:.2f}", total_weight=1., tail_weight=0., total_budget_mwh=total_budget,
            tail_budget_mwh=budget, warm_alpha=min_a)
    weight_rows = [dict(method=name, **{f"alpha_{i}": float(v) for i, v in enumerate(a)}) for name, (a, _) in fitted.items()]
    pd.DataFrame(weight_rows).to_csv(final / "validation_frozen_weights.csv", index=False)
    certificates = [{"method": name, **{key: value for key, value in cert.items() if not isinstance(value, list)}} for name, (_, cert) in fitted.items()]
    pd.DataFrame(certificates).to_csv(final / "validation_solver_certificates.csv", index=False)
    protocol = {
        "schema_version": 1, "experiment": 31,
        "method_source_sha256": sha256(Path(__file__)),
        "protocol_readme_sha256": sha256(root / "experiments/exp31_risk_execution_composition/README.md"),
        "primary_method": "active_tail_fraction_0.50", "primary_fraction_fixed_before_test_scoring": .5,
        "validation_days": validation_days.tolist(), "source_validation_sha256": sha256(validation_path),
        "validation_weights_sha256": sha256(final / "validation_frozen_weights.csv"),
        "validation_certificates_sha256": sha256(final / "validation_solver_certificates.csv"),
        "validation_total_budget_mwh": total_budget, "minimum_feasible_tail_mwh": minimum_tail,
        "total_only_tail_mwh": total_tail, "validation_mse_budget_mw2": mse_budget,
        "retrospective_method_development": True, "new_external_validation": False,
        "locked_outcome_hyperparameter_selection": False,
        "source_candidates_and_original_results_modified": False,
        "tail_definition": "mean largest ceil((1-level)*H) observations with ties counted once",
        "paired_bootstrap": "5000 circular 3-day paired blocks; exploratory unadjusted percentile intervals",
        "cpu_workers": 1, "blas_threads_per_worker": 1,
        "risk_scope": "fixed model-defined reference and modeled response; no physical counterfactual identification",
    }
    # Critical protocol boundary: freeze the entire fitted method before
    # reading the locked candidate/reference/meter values below.
    write_json(final / "validation_freeze_manifest.json", protocol)
    with np.load(test_path, allow_pickle=False) as cache:
        test_candidates = np.asarray(cache["risk_candidate_profiles"])
        test_days = np.asarray(cache["days"])
        test_y, test_meter = np.asarray(cache["oracle"]), np.asarray(cache["actual"])
        methods = [str(x) for x in cache["methods"]]
        legacy_joint = np.asarray(cache["baselines"][:, methods.index("Risk-Constrained Convex Verifier")])
    daily_rows: list[dict] = []
    profiles_by_split = {
        "validation": {name: np.einsum("k,kdrt->drt", a, candidates) for name, (a, _) in fitted.items()},
        "locked": {name: np.einsum("k,dkrt->drt", a, test_candidates) for name, (a, _) in fitted.items()},
    }
    profiles_by_split["locked"]["archived_joint"] = legacy_joint
    old_weights = pd.read_csv(exp2 / "final/risk_module_ablation_weights.csv")
    old_total = old_weights.loc[(old_weights["ablation"] == "total-budget-only ensemble") & (old_weights["split"] == "validation")].iloc[0]
    archived_a = old_total[[c for c in old_weights.columns if c.startswith("weight_")]].to_numpy(dtype=float)
    profiles_by_split["locked"]["archived_total_only"] = np.einsum("k,dkrt->drt", archived_a, test_candidates)
    for split, source in profiles_by_split.items():
        days, ref, observed = (validation_days, y_profile, meter_profile) if split == "validation" else (test_days, test_y, test_meter)
        for name, profile in source.items():
            for i, day in enumerate(days):
                row = {"split": split, "day": int(day), "method": name}
                row.update(baseline_metrics(profile[i], ref[i], event.tolist()))
                row.update(response_metrics(profile[i], ref[i], observed[i], event.tolist(), dt))
                row["event_mse_mw2"] = float(np.mean((profile[i][:, event] - ref[i][:, event]) ** 2))
                daily_rows.append(row)
    daily = pd.DataFrame(daily_rows)
    daily.to_csv(final / "risk_frontier_daily.csv", index=False)
    summary_rows = []
    for (split, name), frame in daily.groupby(["split", "method"], sort=False):
        f = frame["false_response_mwh"].to_numpy()
        ratios = f / np.maximum(frame["oracle_response_mwh"].to_numpy(), 1e-12)
        summary_rows.append({"split": split, "method": name, "days": len(frame),
            "nrmse_mean": frame["nrmse"].mean(), "event_mse_mw2": frame["event_mse_mw2"].mean(),
            "false_credit_mean_mwh": f.mean(), "false_credit_tail_mwh": top_m_tail(f, level),
            "false_credit_ratio_tail": top_m_tail(ratios, level),
            "undercredit_mean_mwh": frame["underestimation_mwh"].mean(), "credit_f1_mean": frame["credit_f1"].mean(),
            "tail_count": int(np.ceil((1-level)*len(frame))), "effective_tail_level": 1-np.ceil((1-level)*len(frame))/len(frame)})
    pd.DataFrame(summary_rows).to_csv(final / "risk_frontier_summary.csv", index=False)
    rng = np.random.default_rng(int(cfg["project"]["seed"]))
    boot_rows = []
    locked = daily[daily["split"] == "locked"]
    pivot = locked.pivot(index="day", columns="method", values="false_response_mwh").sort_index()
    count = len(pivot); block = 3
    draws = (rng.integers(0, count, size=(5000, int(np.ceil(count/block)), 1)) + np.arange(block)).reshape(5000, -1)[:, :count] % count
    for method, comparator in (("active_tail_fraction_0.50", "exact_mse_total_only"),
                               ("exact_mse_fixed_soft_joint", "archived_joint"),
                               ("active_tail_fraction_0.50", "archived_joint"),
                               ("exact_mse_total_only", "archived_total_only")):
        lhs, rhs = pivot[method].to_numpy(), pivot[comparator].to_numpy()
        for label, op in (("false_credit_mean_mwh", np.mean), ("false_credit_top_m_tail_mwh", lambda z: top_m_tail(z, level))):
            bdiff = np.array([op(lhs[ix]) - op(rhs[ix]) for ix in draws])
            boot_rows.append({"method": method, "comparator": comparator, "metric": label,
                              "paired_difference": float(op(lhs)-op(rhs)), "ci_low": float(np.quantile(bdiff,.025)),
                              "ci_high": float(np.quantile(bdiff,.975)), "replications":5000,"block_days":3,
                              "inference":"exploratory unadjusted percentile CI"})
    pd.DataFrame(boot_rows).to_csv(final / "paired_tail_bootstrap.csv", index=False)
    # Original scale-aligned fixed-runtime bridge, scored without modifying it.
    witness_path = root / "experiments/exp27_executable_common_witness/results/final/runtime_complete_witness.npz"
    bridge_path = root / "experiments/exp27_executable_common_witness/results/final/risk_to_executable_bridge_certificate.json"
    bridge_days_path = bridge_path.with_name("risk_to_executable_bridge.csv")
    bridge_days = pd.read_csv(bridge_days_path)["day"].to_numpy(dtype=int)
    if not np.array_equal(bridge_days, test_days):
        raise RuntimeError("The executable and statistical risk objects have different day indices")
    fixed = float(cfg["project"]["fixed_facility_load_mw"])
    slots = int(cfg["project"]["slots_per_day"])
    with np.load(witness_path, allow_pickle=False) as witness:
        target = np.asarray(witness["risk_contract_profile_upper"])
        original = np.asarray(witness["locked_risk_profile"])
        flex = np.maximum(original-fixed, 0.)
        gamma = float((target-fixed).sum() / flex.sum())
        matched_y = fixed + gamma * (test_y-fixed)
        matched_meter = fixed + gamma * (test_meter-fixed)
        risk_rows, risk_daily = [], []
        for key in ("baseline_mwh", "counterfactual_mwh", "risk_aligned_mwh"):
            full = np.asarray(witness[key]) / dt + fixed
            executed = np.stack([full[:, int(day)*slots:(int(day)+1)*slots] for day in test_days])
            cert = certify_execution_transfer(target, executed, matched_meter, matched_y, dt, event,
                total_budget_mwh=anchor_total * gamma * len(test_days)/h,
                tail_budget_mwh=anchor_tail*gamma, mse_budget_mw2=mse_budget*gamma**2, level=level)
            risk_rows.append({"executable_profile":key,"audit_scope":"ex-post common affine scale; modeled reference and response", "scale":gamma,
                              **{k:v for k,v in cert.items() if not isinstance(v,list)}})
            for i,day in enumerate(test_days):
                risk_daily.append({"executable_profile":key,"day":int(day),
                    **{k.removeprefix("daily_"):v[i] for k,v in cert.items() if isinstance(v,list)}})
    pd.DataFrame(risk_rows).to_csv(final / "execution_transfer_certificates.csv", index=False)
    pd.DataFrame(risk_daily).to_csv(final / "execution_transfer_daily.csv", index=False)
    protocol.update({"source_test_sha256":sha256(test_path),"source_witness_sha256":sha256(witness_path),
                     "archived_bridge_certificate_sha256":sha256(bridge_path),
                     "locked_days":test_days.tolist(),"failures":failures,
                     "solver_certificate_max_kkt":max(c["kkt_residual"] for _,c in fitted.values()),
                     "solver_certificate_max_primal":max(c["primal_residual"] for _,c in fitted.values())})
    write_json(final / "experiment_metadata.json", protocol)
    write_json(final / "solver_failures.json", failures)
    logger.info("Exp31 complete; all new fit choices were frozen before locked-profile scoring")
