"""Check signed system-interval netting before the cash presentation floor."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def test_saved_runtime_settlement_uses_interval_energy_and_system_netting():
    df = pd.read_csv(ROOT / 'experiments/exp27_executable_common_witness/results/final/common_witness_settlement.csv')
    assert len(df) == 54 * 96
    np.testing.assert_allclose(df.network_value_usd,
        df.baseline_secure_cost_usd_per_interval - df.counterfactual_secure_cost_usd_per_interval,
        atol=1e-10, rtol=1e-9)
    np.testing.assert_allclose(df.signed_settlement_usd,
        df.capacity_payment_usd + df.network_value_usd, atol=1e-10, rtol=1e-9)
    np.testing.assert_allclose(df.cash_settlement_usd,
        np.maximum(df.signed_settlement_usd, 0), atol=1e-10, rtol=1e-9)
    assert (df.loc[df.is_event_slot.eq(0), 'capacity_payment_usd'] == 0).all()
    assert df.cash_settlement_usd.sum() >= df.signed_settlement_usd.sum()

def test_regional_cash_floors_are_not_system_interval_cash_floor():
    signed_regional = np.array([3.0, -2.0])
    assert max(float(signed_regional.sum()), 0.0) == 1.0
    assert np.maximum(signed_regional, 0).sum() == 3.0
