# Exp32: matched event-gate comparison and full-runtime capacity stress

This targeted revision was specified before its new solves. It contains two
separate tests and does **not** equate an aggregate convex contract with a
single nonpreemptive executable schedule or a modeled response with a real
closed utility meter.

## A. Matched gate contracts

Use the existing chronological validation days 45–60 and locked days 61–114,
gate slot 62, event slots 64–71, all four participating sites, and the unchanged
3-MWh baseline event-service floor. Remove every post-gate arrival before any
current-day feature or schedule is formed. Historical targets use earlier days
only. Build one declaration-only no-tariff eligible reference, freeze its
pre-gate aggregate regional power for every candidate, and generate one shared
modeled response under the predeclared independent replay tariff (the configured 30 USD/MWh).
The reference is an offline modeled diagnostic, not an identified real-world
no-event counterfactual. The pre-gate state is a supplied benchmark state, not
reconstructed observed scheduler state.

Seven feasible profiles: High-5-of-10 projections at weights 1/3/10, historical
mean projection at weight 1, and masked causal-metadata projections at weights
0.3/1/3. Every projection has the same eligible arrivals, capacity, deadlines,
pre-gate state, participation and 3-MWh floor. Select the single metadata
projection and High-5 anchor on validation MSE only. Fit unconstrained,
total-only, CVaR-only and joint simplex contracts on validation only, using the
same 10% MSE neighborhood and reference-derived total/tail budgets. Report all
causal candidates and fitted contracts under *one baseline-credit definition*,
with the same eligible reference and same response, including payable modeled
credit, false credit, recall, and an explicitly modeled 3-MWh credit shortfall
indicator. This shortfall indicator is not an observed contractual default.
It is supplementary and does not reinterpret the baseline service floor as a
DR-delivery promise. No full-ledger headline is compared directly with it.

The aggregate feasibility LP remains a divisible-service envelope. A shared
pre-gate regional profile fixes aggregate state only; it is not a job-indexed
or observed online execution state. These limitations remain explicit.

## B. Full-runtime all-slot coupled stress

Take locked days 61/88/114 (first/middle/last locked snapshots), the original
Exp27 release/deadline/region/requested-GPU runtime ledger and the unchanged
0.001 MW/GPU rate. Define a possible declaration-only gate state by holding a
job until the first daily gate strictly after submission (at most 96 slots,
within the original queue allowance). Previously started blocks continue
without interruption. Exclude future arrivals. Within each pending/running
state and each region, select up to eight jobs at equally spaced indices in
release/job-index order; this is a bounded, disclosed 64-job representative
cohort, not a claim about full-scale congested operation.

For each cohort fix its immediate-at-gate reference peak using declarations
available at that gate. Divide per-region peaks by nominal utilization
0.20/0.80/0.98/1.10. This varies hypothetical installed capacity, never job
energy, power, runtime or deadline. Capacity is enforced in every future slot,
including rebound and non-event slots. The final calendar day is completed
with zero-load slots, giving the optimizer and independent audit identical
day/event samples. Report every scenario, including
infeasible and time-limited cells, full solver status/gap, waiting, achieved
utilization, energy/deadline checks and fixed-power service semantics.

Also solve a direct-risk variant at each capacity: the reference and an
independent 30-USD/MWh modeled response define fixed scenario ceilings; the
same full-runtime MILP imposes total and discrete worst-day tail exposure
budgets (zero in this deterministic known-scenario feasibility test). This
checks that risk rows constrain the executable schedule itself. It is not an
ex-ante stochastic guarantee for an unknown future meter. MSE is measured after
execution, not silently inherited from an aggregate target. Each solve has a
60-second limit and one HiGHS/BLAS thread; no failed cell is dropped or retuned.

Run: PYTHONPATH=code/src:vendor python experiments/exp32_matched_gate_capacity/run.py
Optional --part gate or --part capacity reruns one panel. Input/config/protocol
hashes and complete method/day/scenario denominators are saved with results.

## C. Exact joint risk/MSE execution diagnostic (sequential extension)

After the primary capacity scan, add a transparently labeled mechanistic
extension on the same unaltered cohorts at nominal utilization .98 and 1.10.
The chosen endpoint is exact event-profile matching (MSE budget zero) with zero
total/tail false-credit budgets under the same pre-gate declaration scenarios.
It is deliberately stringent; feasibility is an outcome, not guaranteed by
construction. Retain all six joint cells. Independently solve minimum possible
MSE under the unchanged total/tail/capacity rows in all six cells, so an
infeasible exact-match contract has an explicit achievable-accuracy bound.
No population, entitlement, deadline, capacity or scoring scenario is refitted.
This sequential extension is diagnostic rather than a preregistered claim of
held-out performance improvement.

The MILP represents squared event-profile error exactly on the declared
0.001-MW GPU lattice. For integer load z and arbitrary target t, the maximum
of tangents (2k−2t)z+t²−k² over every capacity-admissible integer k equals
(z−t)², because k=z is included. Auxiliary variables upper-bound this finite
maximum; an MSE upper-budget or minimum-MSE objective therefore enforces the
actual square. Every returned profile is reconstructed and rescored without
using its epigraph variables. Tiny independent exhaustive tests check this
property, including a fractional aggregate target unattainable by any binary
runtime schedule.
