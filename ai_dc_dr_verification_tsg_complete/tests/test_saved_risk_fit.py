"""Recompute frozen risk statistics from arrays, independently of the fitter."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_validation_weights_reproduce_every_risk_certificate():
    final = ROOT / "experiments/exp31_risk_execution_composition/results/final"
    weights = pd.read_csv(final / "validation_frozen_weights.csv").set_index("method")
    certs = pd.read_csv(final / "validation_solver_certificates.csv").set_index("method")
    with np.load(ROOT / "experiments/exp2_baseline_verification/results/intermediate/validation_profiles.npz") as cache:
        candidates = cache["risk_candidate_profiles"]
        reference = cache["oracle"][:, :, 64:72]
        meter = cache["actual"][:, :, 64:72]
        assert candidates.shape[0] == 7 and len(reference) == 16
        for method, cert in certs.iterrows():
            alpha = weights.loc[method].to_numpy(dtype=float)
            profile = np.tensordot(alpha, candidates, axes=(0, 0))[:, :, 64:72]
            mse = np.mean((profile - reference)**2)
            per_day = np.maximum(profile - np.maximum(reference, meter), 0.).sum(axis=(1, 2)) * .25
            tail = sum(sorted(per_day)[-4:]) / 4
            np.testing.assert_allclose([mse, per_day.sum(), tail], cert[["mse_mw2", "total_false_credit_mwh", "tail_false_credit_mwh"]].to_numpy(dtype=float), rtol=0, atol=1e-9)
            assert mse <= cert.mse_budget_mw2 + 1e-5
            if pd.notna(cert.total_budget_mwh):
                assert per_day.sum() <= cert.total_budget_mwh + 1e-5
            if pd.notna(cert.tail_budget_mwh):
                assert tail <= cert.tail_budget_mwh + 1e-5


def test_locked_risk_scores_reproduce_all_frozen_new_methods():
    final = ROOT / "experiments/exp31_risk_execution_composition/results/final"
    weights = pd.read_csv(final / "validation_frozen_weights.csv").set_index("method")
    summary = pd.read_csv(final / "risk_frontier_summary.csv")
    summary = summary.loc[summary.split.eq("locked")].set_index("method")
    with np.load(ROOT / "experiments/exp2_baseline_verification/results/intermediate/test_profiles.npz") as cache:
        candidates = cache["risk_candidate_profiles"]
        reference = cache["oracle"][:, :, 64:72]
        meter = cache["actual"][:, :, 64:72]
        assert candidates.shape[:2] == (54, 7)
        for method, row in weights.iterrows():
            # Input orientation differs between the frozen validation/test files.
            profile = np.tensordot(candidates, row.to_numpy(dtype=float), axes=(1, 0))[:, :, 64:72]
            per_day = np.maximum(profile - np.maximum(reference, meter), 0.).sum(axis=(1, 2)) * .25
            recorded = summary.loc[method]
            assert abs(per_day.mean() - recorded.false_credit_mean_mwh) < 1e-9
            assert abs(np.mean(np.sort(per_day)[-14:]) - recorded.false_credit_tail_mwh) < 1e-9
