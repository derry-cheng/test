from __future__ import annotations

import pandas as pd

from aicdr.data import load_mit_job_ledger


def test_declared_timelimit_is_not_extended_by_measured_runtime(tmp_path):
    """A retrospective completion time cannot enlarge a submitted window."""

    scheduler = tmp_path / "scheduler.csv"
    dcgm = tmp_path / "dcgm.csv"
    pd.DataFrame(
        [
            {
                "id_job": 101,
                "time_submit": 0,
                "time_start": 900,
                "time_end": 36_000,
                "timelimit": 900,
                "gres_req": "gpu:1",
                "job_type": "batch",
                "state": "COMPLETED",
            }
        ]
    ).to_csv(scheduler, index=False)
    # The measured energy needs two 15-minute slots at the declared
    # nameplate cap, while the submit-time timelimit declares only one.
    pd.DataFrame(
        [
            {
                "id_job": 101,
                "energyconsumed_joules": 1_800_000.0,
                "powerusage_watts_avg": 1000.0,
                "totalexecutiontime_sec": 35_100.0,
            }
        ]
    ).to_csv(dcgm, index=False)

    jobs = load_mit_job_ledger(
        scheduler,
        dcgm,
        interval_s=900,
        n_slots=16,
        n_regions=2,
        deadline_mode="declared_timelimit",
        declared_per_gpu_power_cap_mw=1.0e-3,
    )

    row = jobs.iloc[0]
    assert int(row["declared_window_slots"]) == 1
    assert int(row["deadline_slot_declared_timelimit"]) == int(row["submit_slot"]) + 1
    assert int(row["deadline_slot"]) == int(row["submit_slot"]) + 1
    assert int(row["deadline_slot_observed"]) > int(row["deadline_slot"])
    assert int(row["required_service_slots"]) == 2
    assert jobs.attrs["declared_window_infeasible_jobs"] == 1
    assert "never a deadline extension" in jobs.attrs["deadline_window_rule"]


def test_slurm_runtime_is_separated_from_precommitted_queue_allowance(tmp_path):
    """The service window records runtime and queue allowance separately."""

    scheduler = tmp_path / "scheduler.csv"
    dcgm = tmp_path / "dcgm.csv"
    pd.DataFrame(
        [
            {
                "id_job": 7,
                "time_submit": 0,
                "time_start": 900,
                "time_end": 3600,
                "timelimit": 900,
                "gres_req": "gpu:1",
                "job_type": "batch",
                "state": "COMPLETED",
            }
        ]
    ).to_csv(scheduler, index=False)
    pd.DataFrame(
        [
            {
                "id_job": 7,
                "energyconsumed_joules": 900_000.0,
                "powerusage_watts_avg": 1000.0,
                "totalexecutiontime_sec": 2700.0,
            }
        ]
    ).to_csv(dcgm, index=False)
    jobs = load_mit_job_ledger(
        scheduler,
        dcgm,
        interval_s=900,
        n_slots=16,
        n_regions=1,
        deadline_mode="declared_timelimit",
        submission_buffer_slots=2,
        declared_per_gpu_power_cap_mw=1.0e-3,
    )
    row = jobs.iloc[0]
    assert int(row["declared_runtime_slots"]) == 1
    assert int(row["declared_window_slots"]) == 3
    assert int(row["deadline_slot_declared_runtime"]) == int(row["submit_slot"]) + 3
    assert int(jobs.attrs["submission_buffer_slots"]) == 2
    assert "allocation runtime plus a precommitted queue allowance" in jobs.attrs["deadline_window_rule"]
