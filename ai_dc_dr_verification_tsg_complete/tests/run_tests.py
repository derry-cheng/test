"""Small deterministic regression suite for the ex-ante evidence boundary."""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from aicdr.coupling_invariant import validate_job_network_coupling
from aicdr.data import _parse_requested_gpu_count, load_mit_submission_ledger
from aicdr.declaration_event_replay import _select_exact_starts_independent
from aicdr.executable_witness import _select_exact_starts


def main() -> None:
    assert _parse_requested_gpu_count("gpu:4") == 4
    assert _parse_requested_gpu_count("gpu:a100:8") == 8
    assert _parse_requested_gpu_count("(null)") is None

    with tempfile.TemporaryDirectory() as tmp:
        scheduler = Path(tmp) / "scheduler.csv"
        pd.DataFrame(
            [
                {"id_job": 1, "time_submit": 0, "timelimit": 60, "gres_req": "gpu:2", "job_type": "batch", "state": "COMPLETED"},
                {"id_job": 2, "time_submit": 900, "timelimit": 120, "gres_req": "gpu:1", "job_type": "interactive", "state": "COMPLETED"},
            ]
        ).to_csv(scheduler, index=False)
        ledger = load_mit_submission_ledger(
            scheduler,
            interval_s=900,
            n_slots=8,
            n_regions=2,
            declared_service_fraction=0.5,
            declared_per_gpu_power_cap_mw=0.001,
            unbounded_timelimit_slots=4,
            submission_buffer_slots=1,
        )
        assert len(ledger) == 2
        assert "energyconsumed_joules" not in ledger.columns
        assert "time_start" not in ledger.columns
        assert ledger.attrs["digest_fields_exclude_execution_telemetry"] is True
        assert np.all(ledger["declared_energy_mwh"] > 0)
        try:
            load_mit_submission_ledger(
                scheduler,
                interval_s=900,
                n_slots=8,
                n_regions=2,
                declared_service_fraction=0.5,
                declared_per_gpu_power_cap_mw=0.001,
                eligible_job_ids={1},
            )
        except ValueError as exc:
            assert "forbidden" in str(exc)
        else:
            raise AssertionError("outcome-derived eligibility filter was accepted")

    cert = validate_job_network_coupling(
        service_mwh=np.array([0.001, 0.001]),
        job_energy_mwh=np.array([0.002]),
        submit_slot=np.array([0]),
        deadline_slot=np.array([2]),
        region=np.array([0]),
        aggregate_mwh=np.array([[0.001, 0.001]]),
        dt_h=0.25,
        requested_gpus=np.array([2.0]),
        per_gpu_power_cap_mw=0.004,
        site_capacity_mw=0.01,
    )
    assert cert.valid
    assert cert.max_job_energy_residual_mwh <= 1e-12

    # C1 regression: the waiting charge integrates every delayed service
    # slot, and the independent replay must select the same exact start on a
    # two-event-day horizon.  A start-only charge gives a different objective
    # and is therefore caught by this one-job certificate.
    horizon = 320
    event_mask = np.asarray(
        [int(slot % 96 in set(range(64, 72))) for slot in range(horizon)],
        dtype=np.int8,
    )
    event_prefix = np.concatenate([[0], np.cumsum(event_mask, dtype=np.int64)])
    submit = np.asarray([64], dtype=np.int64)
    runtime = np.asarray([128], dtype=np.int64)
    energy_slot = np.asarray([0.00025], dtype=float)
    exact_start, exact_cost = _select_exact_starts(
        submit,
        runtime,
        96,
        energy_slot,
        event_prefix,
        1.5,
        150.0,
        event_price_enabled=True,
    )
    independent_start, independent_cost = _select_exact_starts_independent(
        submit,
        runtime,
        96,
        energy_slot,
        event_prefix,
        1.5,
        150.0,
        event_price_enabled=True,
    )
    assert int(exact_start[0]) == 64
    assert np.isclose(float(exact_cost[0]), 3.648, atol=1e-12)
    assert np.array_equal(exact_start, independent_start)
    assert np.allclose(exact_cost, independent_cost, atol=1e-12)

    # C2/C5 regression: the risk bridge and signed complete-cycle ledger are
    # complete before publication, with the event subset retained as a flag.
    bridge = pd.read_csv(
        Path("experiments/exp27_executable_common_witness/results/final/risk_to_executable_bridge.csv")
    )
    settlement = pd.read_csv(
        Path("experiments/exp27_executable_common_witness/results/final/common_witness_settlement.csv")
    )
    settlement_summary = pd.read_csv(
        Path("experiments/exp27_executable_common_witness/results/final/common_witness_settlement_summary.csv")
    )
    assert len(bridge) == 54
    assert np.isfinite(
        bridge[["upper_capacity_realization_nrmse", "central_energy_realization_nrmse"]]
        .to_numpy(dtype=float)
    ).all()
    assert len(settlement) == 54 * 96
    assert int(settlement["is_event_slot"].sum()) == 54 * 8
    assert int(
        settlement_summary.loc[
            settlement_summary["metric"] == "full_cycle_cells", "value"
        ].iloc[0]
    ) == 54 * 96
    print("all regression tests passed")


if __name__ == "__main__":
    main()
