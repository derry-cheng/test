"""C5 regressions: outcomes cannot change the common outage denominator."""
from __future__ import annotations
import numpy as np
import pandas as pd
import pytest
from aicdr.ac_common_domain import classify_result, connected_outages, assert_complete, summarize


def candidate(loading=0.5, voltage=1.0, pg=10.0, success=True):
    bus = np.zeros((2, 13))
    bus[:, 0] = [10, 20]
    bus[:, 7] = voltage
    bus[:, 11] = 1.1
    bus[:, 12] = 0.9
    branch = np.zeros((1, 17))
    branch[0, :2] = [10, 20]
    branch[0, 5] = 100
    branch[0, 10] = 1
    branch[0, 13] = loading * 100
    gen = np.zeros((2, 21))
    gen[:, 1] = [pg, 5.0]
    return {'success': success, 'bus': bus, 'branch': branch, 'gen': gen}


def test_failure_is_unknown_not_physical_infeasibility():
    row = classify_result(candidate(loading=8, success=False), np.array([10., 5.]), np.array([0]), 1e-8)
    assert row['outcome'] == 'numerical_unknown'
    assert row['limit_violation'] == 0
    assert row['physical_infeasibility_proven'] == 0
    assert np.isnan(row['maximum_apparent_line_loading'])


@pytest.mark.parametrize('kwargs', [{'loading': 1.02}, {'voltage': 1.2}, {'pg': 10.1}])
def test_successful_constraint_violation_is_retained(kwargs):
    row = classify_result(candidate(**kwargs), np.array([10., 5.]), np.array([0]), 1e-8)
    assert row['outcome'] == 'converged_limit_violation'
    assert row['solver_success'] == 1
    assert row['certificate_success'] == 0
    assert row['physical_infeasibility_proven'] == 0


def test_nonfinite_success_is_unknown():
    row = classify_result(candidate(pg=np.nan), np.array([10., 5.]), np.array([0]), 1e-8)
    assert row['outcome'] == 'numerical_unknown'


def test_certificate_uses_declared_tolerance():
    row = classify_result(candidate(pg=10 + 5e-7), np.array([10., 5.]), np.array([0]), 1e-8)
    assert row['outcome'] == 'certified'
    assert row['certificate_success'] == 1


def test_connected_domain_handles_parallel_and_inactive_branches():
    case = candidate()
    case['branch'] = np.repeat(case['branch'], 3, axis=0)
    case['branch'][2, 10] = 0
    assert connected_outages(case) == [0, 1]
    case['branch'][1, 10] = 0
    assert connected_outages(case) == []


def test_missing_or_duplicate_failed_cells_are_rejected():
    rows = []
    for method, success in [('A', True), ('B', False)]:
        row = dict(network='N', method=method, peak_dc_penetration=.03, outage=0,
                   day=61, event_slot=64, snapshot_index=0)
        row.update(classify_result(candidate(success=success), np.array([10., 5.]), np.array([0]), 1e-8))
        rows.append(row)
    frame = pd.DataFrame(rows)
    expected = {('N', .03, method, 0, 61, 64) for method in ['A', 'B']}
    assert_complete(frame, expected)
    summary = summarize(frame)
    assert summary.declared_cells.tolist() == [1, 1]
    assert summary.certified_fraction_common_denominator.tolist() == [1., 0.]
    assert summary.coverage_fraction.tolist() == [1., 1.]
    with pytest.raises(RuntimeError, match='Incomplete'):
        assert_complete(frame.iloc[:1], expected)
    with pytest.raises(RuntimeError, match='duplicated'):
        assert_complete(pd.concat([frame, frame.iloc[:1]]), expected)


def test_restarts_use_same_pristine_case_and_bounded_budget(monkeypatch):
    import importlib
    from aicdr.ac_common_domain import solve_cell
    opf = importlib.import_module('pypower.runopf')
    pf = importlib.import_module('pypower.runpf')
    calls = []
    def fail_opf(case, options):
        calls.append((options['OPF_ALG'], float(case['bus'][0, 2])))
        case['bus'][0, 2] = 999.0
        return {'success': False}
    monkeypatch.setattr(opf, 'runopf', fail_opf)
    monkeypatch.setattr(pf, 'runpf', lambda case, options: (case, False))
    case = candidate()
    case['bus'][0, 2] = 12.0
    solved = solve_cell({'case': case})
    assert calls == [(0, 12.0), (0, 12.0), (565, 12.0), (565, 12.0)]
    assert len(solved['attempts']) == 5
    assert solved['result']['success'] is False
    assert case['bus'][0, 2] == 12.0


def test_restarts_do_not_relax_constraints_to_obtain_a_pass(monkeypatch):
    import importlib
    from aicdr.ac_common_domain import solve_cell
    opf = importlib.import_module('pypower.runopf')
    calls = []
    def violating_opf(case, options):
        calls.append(1)
        return candidate(loading=1.5)
    monkeypatch.setattr(opf, 'runopf', violating_opf)
    solved = solve_cell({'case': candidate()})
    scored = classify_result(solved['result'], np.array([10., 5.]), np.array([0]), 1e-8)
    assert calls == [1]
    assert scored['outcome'] == 'converged_limit_violation'
