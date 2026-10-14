"""Regressions for the locked audit's finite-tail and inference conventions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from aicdr.risk_tail_audit import _cvar, _paired_locked_panel, _tail_count

ROOT = Path(__file__).resolve().parents[1]
METHODS = ["total+CVaR ensemble", "total-budget-only ensemble", "CVaR-only ensemble"]


def _must_reject(callback, message: str) -> None:
    try:
        callback()
    except ValueError:
        return
    raise AssertionError(message)


def test_tail_ties_do_not_expand_the_declared_tail_mass() -> None:
    # A bootstrap can duplicate the cutoff. Quantile-threshold inclusion would
    # use all three positive observations and give 14/3, instead of top-2 = 6.
    values = np.array([0., 0., 0., 0., 0., 2., 2., 10.])
    assert _tail_count(len(values), 0.75) == 2
    assert _cvar(values, 0.75) == 6.0
    assert _cvar(np.repeat(3., 8), 0.75) == 3.0


def test_tail_mean_equals_the_integer_mass_epigraph_with_ties() -> None:
    for values in [np.array([0., 0., 1., 1., 1., 3., 9.]), np.array([2., 2., 2., 9.])]:
        for level in (0., .5, .75, .99):
            m = _tail_count(len(values), level)
            # An optimum lies at a sample knot; this independently computes
            # the exact epigraph used by the risk contract.
            epigraph = min(float(nu + np.maximum(values - nu, 0.).sum() / m) for nu in np.unique(values))
            assert np.isclose(_cvar(values, level), epigraph, atol=1e-12)
    assert _tail_count(54, .75) == 14


def test_tail_statistic_rejects_invalid_or_nonfinite_samples() -> None:
    for values, level in [(np.array([]), .75), (np.array([1., np.nan]), .75), (np.array([1., np.inf]), .75), (np.ones((2, 2)), .75), (np.ones(3), -0.1), (np.ones(3), 1.), (np.ones(3), np.nan)]:
        _must_reject(lambda: _cvar(values, level), "invalid CVaR input accepted")


def _paired_frame() -> pd.DataFrame:
    return pd.DataFrame([{"day": day, "split": "test", "ablation": method, "false_response_mwh": float(day), "oracle_response_mwh": 10.} for day in (1, 2, 3) for method in METHODS])


def test_tail_pairing_rejects_missing_duplicate_and_changed_truth_rows() -> None:
    frame = _paired_frame()
    pivot, oracle = _paired_locked_panel(frame, METHODS, 3)
    assert pivot.shape == (3, 3)
    assert oracle.eq(10.).all()
    _must_reject(lambda: _paired_locked_panel(frame.iloc[:-1], METHODS, 3), "missing paired day accepted")
    _must_reject(lambda: _paired_locked_panel(pd.concat([frame, frame.iloc[:1]]), METHODS, 3), "duplicate paired day accepted")
    changed = frame.copy()
    changed.loc[0, "oracle_response_mwh"] += 1.
    _must_reject(lambda: _paired_locked_panel(changed, METHODS, 3), "method-dependent oracle accepted")
    _must_reject(lambda: _paired_locked_panel(frame, METHODS, 54), "wrong locked-day count accepted")


def test_locked_tail_release_has_source_lineage_and_unadjusted_intervals() -> None:
    folder = ROOT / "experiments/exp28_risk_tail_audit/results/final"
    meta = json.loads((folder / "experiment_metadata.json").read_text())
    assert meta["source_sha256"] == hashlib.sha256((ROOT / meta["source_file"]).read_bytes()).hexdigest()
    assert meta["implementation_sha256"] == hashlib.sha256((ROOT / "code/src/aicdr/risk_tail_audit.py").read_bytes()).hexdigest()
    assert meta["cvar_tail_days"] == 14
    assert meta["multiplicity_adjusted"] is False
    assert "no Holm" in meta["holm_scope"]
    summary = pd.read_csv(folder / "risk_tail_audit.csv").set_index("ablation")
    boot = pd.read_csv(folder / "risk_tail_paired_bootstrap.csv")
    assert len(summary) == 3 and len(boot) == 12
    assert boot["interval_type"].eq("unadjusted_exploratory_percentile_95").all()
    assert not boot["multiplicity_adjusted"].any()
    assert boot["cvar_tail_days"].eq(14).all()
    assert np.allclose(boot["joint_minus_comparator_mean"], boot["bootstrap_mean_difference"])
    for row in boot.itertuples(index=False):
        expected = summary.loc[METHODS[0], row.metric] - summary.loc[row.comparison, row.metric]
        assert np.isclose(row.joint_minus_comparator_point_estimate, expected, atol=1e-12)
