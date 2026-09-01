"""Small deterministic regression suite for the ex-ante evidence boundary."""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from aicdr.coupling_invariant import validate_job_network_coupling
from aicdr.data import _parse_requested_gpu_count, load_mit_submission_ledger


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
    print("all regression tests passed")


if __name__ == "__main__":
    main()
