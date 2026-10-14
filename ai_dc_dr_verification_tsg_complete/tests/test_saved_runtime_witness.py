"""Reconstruct saved Exp32 blocks without calling its scheduler or aggregator."""
from pathlib import Path
import hashlib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "experiments/exp32_matched_gate_capacity/results/final"


def _hash_array(value):
    value = np.ascontiguousarray(value)
    return hashlib.sha256(str(value.shape).encode() + str(value.dtype).encode() + value.tobytes()).hexdigest()


def _reconstruct(witness, day, joint=False):
    gate = int(day) * 96 + 62
    original = np.load(ROOT / "experiments/exp27_executable_common_witness/results/final/runtime_complete_witness.npz")
    index = witness["source_job_index"]
    for field, source_field in [("release", "submit_slot"), ("deadline", "deadline_slot"), ("runtime_slots", "runtime_slots"), ("region", "region")]:
        np.testing.assert_array_equal(witness[field], original[source_field][index])
    np.testing.assert_allclose(witness["fixed_power_mw"], original["requested_gpus"][index] * .001, rtol=0, atol=1e-14)
    if joint:
        pending_positions = np.arange(len(index))
        starts = witness["starts_absolute"]
    else:
        pending_index = witness["pending_source_job_index"]
        positions = {int(job): i for i, job in enumerate(index)}
        pending_positions = np.array([positions[int(job)] for job in pending_index])
        starts = witness["selected_start_absolute"]
    rebuilt = witness["fixed_profile_mw"].copy()
    energy = 0.
    for position, start in zip(pending_positions, starts):
        runtime = int(witness["runtime_slots"][position])
        assert int(start) >= max(gate, int(witness["release"][position]))
        assert int(start) + runtime <= int(witness["deadline"][position])
        region = int(witness["region"][position]); power = float(witness["fixed_power_mw"][position])
        rebuilt[region, int(start)-gate:int(start)-gate+runtime] += power
        energy += power * runtime * .25
    np.testing.assert_allclose(rebuilt, witness["profile_mw"], rtol=0, atol=1e-12)
    assert abs((rebuilt - witness["fixed_profile_mw"]).sum() * .25 - energy) <= 1e-10
    assert np.max(rebuilt - witness["capacity_mw"][:, None]) <= 1e-7


def test_all_saved_runtime_blocks_preserve_original_full_entitlements():
    cells = pd.read_csv(FINAL / "runtime_capacity_cells.csv")
    assert len(cells) == 24
    for row in cells.itertuples(index=False):
        if not row.success:
            continue
        name = f"runtime_day{row.day}_u{row.nominal_reference_peak_utilization:.2f}_{row.method}.npz"
        with np.load(FINAL / name) as witness:
            _reconstruct(witness, row.day)


def test_joint_runtime_witness_recomputes_risk_and_exact_unpadded_mse():
    cells = pd.read_csv(FINAL / "joint_runtime_risk_mse_cells.csv")
    assert len(cells) == 12
    assert len(cells[cells.method.eq("joint_zero_risk_exact_mse")]) == 6
    for row in cells.itertuples(index=False):
        if not row.success:
            assert not row.optimal
            continue
        name = f"joint_runtime_day{row.day}_u{row.nominal_reference_peak_utilization:.2f}_{row.method}.npz"
        with np.load(FINAL / name) as witness:
            _reconstruct(witness, row.day, joint=True)
            event = witness["event_mask"].astype(bool)
            profile, ref, meter = witness["profile_mw"], witness["reference_mw"], witness["modeled_response_mw"]
            mse = float(np.mean((profile[:, event] - ref[:, event])**2))
            false = float(np.maximum(profile[:, event] - np.maximum(ref[:, event], meter[:, event]), 0.).sum() * .25)
            assert abs(mse - row.independently_recomputed_event_mse_mw2) <= 1e-14
            assert abs(false - row.independently_recomputed_total_false_credit_mwh) <= 1e-12
            assert false <= 1e-8
            if row.method == "joint_zero_risk_exact_mse":
                assert mse <= row.mse_budget_mw2 + 1e-12


def test_matched_gate_profile_hashes_and_baseline_definition_are_shared():
    daily = pd.read_csv(FINAL / "matched_gate_daily.csv")
    with np.load(FINAL / "matched_gate_frozen_profiles.npz") as witness:
        assert witness["profiles"].shape == (70, 13, 4, 96)
        for index, day in enumerate(witness["days"]):
            paired = daily.loc[daily.day.eq(day)]
            assert len(paired) == 13
            for key in ["eligible_ledger_sha256", "common_reference_sha256", "common_modeled_response_sha256"]:
                assert paired[key].nunique() == 1
            assert paired["common_reference_sha256"].iloc[0] == _hash_array(witness["reference"][index])
            assert paired["common_modeled_response_sha256"].iloc[0] == _hash_array(witness["modeled_response"][index])
            assert paired.baseline_event_service_floor_mwh.eq(3.).all()
            assert paired.baseline_event_service_mwh.ge(3. - 1e-8).all()
