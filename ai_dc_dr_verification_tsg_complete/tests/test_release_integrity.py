"""Release checks distinguish an archive from a newly executed full pipeline."""
from pathlib import Path
from aicdr.audit import _audit_risk_revision, _audit_gate_revision, _canonical_manifest_scope
from aicdr.utils import load_config


def _manifest(count):
    return {"stage_requested": "all", "stages": {key: {"status": "completed"} for key in ["data", "audit"] + [f"exp{i}" for i in range(1, count + 1)]}}


def test_historical_run_requires_explicit_targeted_scope():
    legacy = _manifest(30)
    assert not _canonical_manifest_scope(legacy, {})[0]
    assert _canonical_manifest_scope(legacy, {"historical_full_run_not_reexecuted": True})[0]
    assert "historical" in _canonical_manifest_scope(legacy, {"historical_full_run_not_reexecuted": True})[1]


def test_current_full_run_must_really_complete_added_stages():
    current = _manifest(32)
    assert _canonical_manifest_scope(current, {})[0]
    current["stages"]["exp32"]["status"] = "pending"
    assert not _canonical_manifest_scope(current, {"historical_full_run_not_reexecuted": True})[0]
    del current["stages"]["exp32"]
    assert not _canonical_manifest_scope(current, {"historical_full_run_not_reexecuted": True})[0]


def test_risk_revision_artifacts_pass_evidence_not_superiority_checks():
    root = Path(__file__).resolve().parents[1]
    checks = []
    _audit_risk_revision(root, load_config(root / "configs/default.yaml"), checks)
    assert len(checks) == 4
    assert all(item["passed"] for item in checks), [item for item in checks if not item["passed"]]


def test_gate_runtime_release_reconciles_denominators_status_and_lineage():
    root = Path(__file__).resolve().parents[1]
    checks = []
    _audit_gate_revision(root, load_config(root / "configs/default.yaml"), checks)
    assert len(checks) == 4
    assert all(item["passed"] for item in checks), [item for item in checks if not item["passed"]]
