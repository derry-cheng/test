"""Independent algebra and convex-contract regressions for Exp31."""
import numpy as np
import unittest
from aicdr.risk_execution_composition import (
    top_m_tail, daily_false_credit, certify_execution_transfer, fit_risk_simplex,
)


def test_top_m_ties_are_not_all_threshold_exceedances():
    values = np.array([0., 1., 1., 1., 4.])
    assert top_m_tail(values, .6) == 2.5
    assert top_m_tail(np.zeros(54)) == 0
    with unittest.TestCase().assertRaises(ValueError):
        top_m_tail(np.array([np.nan]))


def test_false_credit_matches_nested_positive_parts():
    rng = np.random.default_rng(31)
    b, m, r = rng.uniform(0, 10, size=(3, 5, 2, 8))
    expected = np.maximum(np.maximum(b-m, 0)-np.maximum(r-m, 0),0)[:, :, [1,3,4]].sum((1,2))*.25
    np.testing.assert_allclose(daily_false_credit(b,m,r,.25,[1,3,4]), expected)


def test_residual_transfer_and_payment_cap_are_valid_without_tracking():
    rng = np.random.default_rng(32)
    for _ in range(20):
        b,x,m,r = rng.uniform(0, 20, size=(4, 7, 3, 6))
        c = certify_execution_transfer(b,x,m,r,.25,[1,2,5])
        assert c['executed_total_false_credit_mwh'] <= c['total_false_credit_upper_bound_mwh'] + 1e-10
        assert c['executed_tail_false_credit_mwh'] <= c['tail_false_credit_upper_bound_mwh'] + 1e-10
        assert c['executed_event_mse_mw2'] <= c['event_mse_upper_bound_mw2'] + 1e-10
        assert c['capped_total_false_credit_mwh'] <= c['target_total_false_credit_mwh'] + 1e-10
        assert c['capped_tail_false_credit_mwh'] <= c['target_tail_false_credit_mwh'] + 1e-10
        assert c['max_daily_lipschitz_violation_mwh'] < 1e-10


def test_large_residual_does_not_silently_pass_execution_budget():
    b = np.ones((4,1,2)); x = b * 5; m = b; r = b
    c = certify_execution_transfer(b,x,m,r,.25,[0,1],total_budget_mwh=0.,tail_budget_mwh=0.,mse_budget_mw2=0.)
    assert not c['execution_certificate_accept']
    assert c['payment_risk_certificate_accept']
    assert c['credit_removed_mwh'] == 8
    assert c['event_mse_upper_bound_mw2'] == c['executed_event_mse_mw2'] == 16
    assert c['total_false_credit_upper_bound_mwh'] == c['executed_total_false_credit_mwh'] == 8


def test_transfer_rejects_mismatched_information_objects():
    b = np.ones((4,1,2))
    with unittest.TestCase().assertRaises(ValueError):
        certify_execution_transfer(b,b[:3],b,b,.25,[0])
    with unittest.TestCase().assertRaises(ValueError):
        daily_false_credit(b,b,b,.25,[0,0])


def test_exact_accuracy_retains_convex_cancellation_lost_by_triangle():
    # Each candidate's RMS is 1, but their average is exact. A radius .5
    # excludes the whole legacy triangle simplex, yet the true ball is feasible.
    d = np.array([[0.,2.],[2.,0.],[0.,2.],[2.,0.]])
    y = np.ones(4); meter = np.ones(4)
    alpha, c = fit_risk_simplex(d,y,meter,day_count=2,mse_budget_mw2=.25,total_weight=0)
    np.testing.assert_allclose(alpha, [.5,.5], atol=1e-5)
    assert c['mse_mw2'] < 1e-10
    assert c['kkt_residual'] < 1e-5
    with unittest.TestCase().assertRaisesRegex(RuntimeError, 'infeasible'):
        fit_risk_simplex(d,y,meter,day_count=2,mse_budget_mw2=.25,total_weight=0,accuracy_mode='triangle')


def test_hard_tail_row_changes_the_same_objective_and_binds():
    # Total exposure favors a concentrated candidate mixture. Holding the
    # objective fixed while imposing a tail row changes that optimum.
    d = np.array([[4.,3.],[0.,3.]])
    y = np.ones(2); meter = np.zeros(2)
    kw = dict(day_count=2,dt_h=1.,level=.5,total_weight=100.,mse_budget_mw2=10.)
    unconstrained, base = fit_risk_simplex(d,y,meter,**kw)
    alpha, c = fit_risk_simplex(d,y,meter,**kw,tail_budget_mwh=2.5)
    assert base['tail_false_credit_mwh'] > 2.6
    assert c['tail_false_credit_mwh'] <= 2.5 + 1e-6
    assert c['tail_budget_binding']
    np.testing.assert_allclose(alpha,[.5,.5],atol=1e-5)


def test_removing_inactive_hard_rows_keeps_preferences():
    d=np.array([[0.,2.],[2.,0.],[1.,3.],[3.,1.]])
    y=np.ones(4); meter=np.zeros(4)
    kw=dict(day_count=2,total_weight=1.,tail_weight=.5,total_scale_mwh=2.,tail_scale_mwh=1.)
    a,c=fit_risk_simplex(d,y,meter,**kw,total_budget_mwh=100.,tail_budget_mwh=100.)
    b,e=fit_risk_simplex(d,y,meter,**kw)
    np.testing.assert_allclose(a,b,atol=1e-5)
    assert c['total_weight']==e['total_weight']==1.
    assert c['tail_weight']==e['tail_weight']==.5
    assert not c['total_budget_binding'] and not c['tail_budget_binding']


def test_joint_runtime_epigraph_matches_independent_exhaustive_search():
    from itertools import product
    from aicdr.runtime_capacity import solve_runtime_milp
    release = np.array([0,0,1]); deadline = np.array([5,6,6]); runtime = np.array([2,2,2])
    power = np.array([1.,1.,2.]); fixed = np.array([[0.,.25,0.,0.,0.,0.]])
    reference = np.array([[2.,2.,1.,1.,0.,0.]])
    ceiling = np.array([[2.,1.,1.,1.,1.,0.]])
    cost = np.array([[3.,1.,0.,6.,0.,4.]])
    feasible = []
    for starts in product(range(4),range(5),range(1,5)):
        profile = fixed[0].copy(); objective = 0.
        for j,start in enumerate(starts):
            for slot in range(start,start+2):
                profile[slot] += power[j]
                objective += power[j]*.25*(cost[0,slot]+.05*(slot-release[j]))
        daily = np.maximum(profile-ceiling[0],0).reshape(3,2).sum(axis=1)*.25
        mse = np.mean((profile-reference[0])**2)
        if profile.max() <= 3 and daily.sum() <= 1 and daily.max() <= .5 and mse <= 1.5:
            feasible.append(objective)
    assert len(feasible) == 5
    out = solve_runtime_milp(release,deadline,runtime,[0,0,0],power,cost,3.,
                            fixed_profile_mw=fixed, waiting_cost=.05,event_mask=np.ones(6,dtype=bool),
                            risk_ceiling_mw=ceiling,risk_day_index=[0,0,1,1,2,2],
                            total_budget_mwh=1.,tail_budget_mwh=.5,tail_level=.75,
                            mse_reference_mw=reference,mse_budget_mw2=1.5,power_quantum_mw=.25)
    assert out.optimal
    assert abs(out.objective - min(feasible)) < 1e-9
    assert out.event_mse_mw2 <= 1.5
    assert out.max_job_energy_residual_mwh < 1e-12


if __name__ == "__main__":
    tests = [(name, fn) for name, fn in list(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        print("PASS", name)
    print(f"Passed {len(tests)} risk composition tests")
