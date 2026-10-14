from itertools import product
import numpy as np
from aicdr.runtime_capacity import solve_runtime_milp, top_m_mean


def test_capacity_full_runtime_matches_bruteforce():
    releases = np.array([0, 0, 1]); deadlines = np.array([4, 4, 5])
    runtime = np.array([2, 2, 2]); power = np.array([1., 1., 1.])
    cost = np.array([[0., 3., 1., 5., 0.]])
    result = solve_runtime_milp(releases, deadlines, runtime, [0, 0, 0], power, cost, 2., waiting_cost=.2)
    candidates = []
    for ss in product(range(3), range(3), range(1, 4)):
        p = np.zeros(5); obj = 0
        for j, start in enumerate(ss):
            p[start:start + 2] += 1
            obj += .25 * (cost[0, start:start + 2].sum() + .2 * (2 * (start - releases[j]) + 1))
        if p.max() <= 2:
            candidates.append(obj)
    assert result.optimal and np.isclose(result.objective, min(candidates))
    assert np.isclose(result.profile_mw.sum() * .25, 1.5)
    assert result.max_job_energy_residual_mwh == 0


def test_capacity_checks_non_event_and_carry_in():
    # The only conflict is outside the event window. Event-only capacity
    # enforcement would incorrectly accept this instance.
    out = solve_runtime_milp([0], [3], [3], [0], [1.], np.zeros((1, 3)), 1.,
                             fixed_profile_mw=np.array([[0., 0., 1.]]), event_mask=[1, 0, 0])
    assert not out.success and out.status == 2


def test_direct_risk_row_changes_runtime_schedule():
    args = ([0], [4], [2], [0], [1.], np.zeros((1, 4)), 1.)
    raw = solve_runtime_milp(*args, waiting_cost=1.)
    safe = solve_runtime_milp(*args, waiting_cost=1., event_mask=[1, 1, 0, 0],
                              risk_ceiling_mw=np.zeros((1, 4)), risk_day_index=[0, 0, 0, 0],
                              total_budget_mwh=0., tail_budget_mwh=0.)
    assert raw.starts[0] == 0 and safe.starts[0] == 2
    assert safe.total_false_credit_mwh == 0 and safe.tail_false_credit_mwh == 0
    assert safe.profile_mw.sum() == raw.profile_mw.sum() == 2


def test_declared_runtime_cannot_be_shortened_to_fit():
    import pytest
    with pytest.raises(ValueError, match="no full-runtime"):
        solve_runtime_milp([0], [2], [3], [0], [1.], np.zeros((1, 3)), 1.)


def test_top_m_ties_and_fractional_level():
    assert top_m_mean(np.array([0., 1., 1., 4.]), .5) == 2.5
    assert top_m_mean(np.arange(54), .75) == np.arange(40, 54).mean()


def test_exact_quantized_mse_constraint_and_phase_one():
    # Reference power is a fractional convex profile. Binary fixed-power
    # schedules cannot attain zero MSE, despite aggregate feasibility.
    args = ([0], [2], [1], [0], [1.], np.zeros((1, 2)), 1.)
    reference = np.array([[.5, .5]])
    blocked = solve_runtime_milp(*args, event_mask=[1, 1], mse_reference_mw=reference,
                                 mse_budget_mw2=0., power_quantum_mw=1.)
    assert not blocked.success and blocked.status == 2
    minimum = solve_runtime_milp(*args, event_mask=[1, 1], mse_reference_mw=reference,
                                 power_quantum_mw=1., objective_mode="minimum_mse")
    assert minimum.optimal and np.isclose(minimum.event_mse_mw2, .25)
    feasible = solve_runtime_milp(*args, event_mask=[1, 1], mse_reference_mw=reference,
                                  mse_budget_mw2=.25, power_quantum_mw=1.)
    assert feasible.optimal and feasible.mse_epigraph_exact_on_power_grid


def test_joint_runtime_risk_and_mse_same_schedule():
    result = solve_runtime_milp([0], [4], [2], [0], [1.], np.zeros((1, 4)), 1.,
                               event_mask=[1, 1, 1, 1], risk_ceiling_mw=np.array([[0., 0., 1., 1.]]),
                               risk_day_index=[0, 0, 1, 1], total_budget_mwh=0., tail_budget_mwh=0.,
                               mse_reference_mw=np.array([[0., 0., 1., 1.]]), mse_budget_mw2=0., power_quantum_mw=1.)
    assert result.optimal and result.starts[0] == 2
    assert result.event_mse_mw2 == 0 and result.total_false_credit_mwh == 0


def test_exact_mse_lattice_tangents_at_all_attainable_levels():
    for target in (-.7, 0., .5, 1., 3.14159, 8.):
        for value in range(9):
            levels=np.arange(9)
            epigraph=np.max((2*levels-2*target)*value+target**2-levels**2)
            assert np.isclose(epigraph,(value-target)**2,atol=1e-12)


def test_joint_milp_matches_independent_exhaustive_search():
    releases=np.array([0,0]);runtime=np.array([2,1]);deadline=np.array([4,4]);power=np.array([1.,2.])
    target=np.array([[1.5,1.5,.5,.5]]);ceiling=np.array([[2.,2.,2.,2.]])
    cost=np.array([[3.,1.,4.,2.]])
    feasible=[]
    for starts in product(range(3),range(4)):
        p=np.zeros(4);obj=0
        for j,start in enumerate(starts):
            p[start:start+runtime[j]]+=power[j]
            obj+=power[j]*.25*(cost[0,start:start+runtime[j]].sum()+.3*sum(start+k for k in range(runtime[j])))
        if p.max()<=3 and np.maximum(p-ceiling[0],0).sum()*.25<=.25 and np.mean((p-target[0])**2)<=1.25:
            feasible.append(obj)
    result=solve_runtime_milp(releases,deadline,runtime,[0,0],power,cost,3.,waiting_cost=.3,event_mask=np.ones(4,bool),
        risk_ceiling_mw=ceiling,risk_day_index=[0,0,1,1],total_budget_mwh=.25,tail_budget_mwh=.25,
        mse_reference_mw=target,mse_budget_mw2=1.25,power_quantum_mw=1.)
    assert result.optimal and np.isclose(result.objective,min(feasible),atol=1e-10)


def test_gate_mask_is_invariant_to_future_arrival_values():
    from aicdr.matched_gate_capacity import mask_gate_arrivals
    original=np.arange(96*4*3,dtype=float).reshape(96,4,3)
    changed=original.copy();changed[62:]=1e12
    assert np.array_equal(mask_gate_arrivals(original,62),mask_gate_arrivals(changed,62))
    assert not mask_gate_arrivals(original,62)[62:].any()


def test_phase_one_objective_reports_mse_and_cost_separately():
    out=solve_runtime_milp([0],[2],[1],[0],[1.],np.array([[1.,4.]]),1.,event_mask=[1,1],
        mse_reference_mw=np.array([[.5,.5]]),power_quantum_mw=1.,objective_mode="minimum_mse")
    assert out.objective_mode=="minimum_mse" and out.objective==out.event_mse_mw2==.25
    assert out.operating_cost is not None and np.isclose(out.solver_objective,.25)


def test_milp_recovers_after_legacy_highs_thread_initialization():
    # Reproduce the pipeline-order regression: a default-thread LP precedes
    # the explicitly single-thread runtime MILP in one process.
    from scipy.optimize import linprog
    import pytest, warnings
    try:
        from scipy.optimize._highspy._core import _Highs
    except ImportError:
        pytest.skip("scheduler reset API is only exposed by recent SciPy")
    _Highs.resetGlobalScheduler(True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert linprog([1.],bounds=[(1.,None)],method="highs",options={"threads": 2}).success
    out=solve_runtime_milp([0],[2],[1],[0],[1.],np.zeros((1,2)),1.)
    assert out.optimal and out.solver_attempt_statuses in {"0","4;0"}


def test_runtime_rejects_fractional_slots_without_truncating():
    import pytest
    with pytest.raises(ValueError,match="finite integer"):
        solve_runtime_milp([.5],[3],[1],[0],[1.],np.zeros((1,3)),1.)
