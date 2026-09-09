# Revision log — C1–C5 closure

The current branch closes the five critical review issues with executable
checks. The indexed model enumerates 13,198,247 admissible job–slot starts over
the complete 75,326-record scheduler population; the selected witness activates
one start per submitted job and is reconstructed before network valuation;
job-energy, regional aggregation, region-to-bus mapping,
GPU-nameplate, and site-capacity residuals are checked before network dispatch.
The deployment panel now includes an independently generated controlled-event
replay over 54 locked days. The security panel freezes both profiles and checks
all 37 finite non-islanding RTS-24 outages in 864 cells. Slurm `timelimit` is
treated as allocation runtime, with a precommitted 96-slot queue allowance;
observed completion is never used to extend a counterfactual window. Payment
cap selection and payment-target selection are separate validation-only roles.
The independent event replay uses a distinct predeclared 30 USD/MWh tariff
against the common 150 USD/MWh tariff, enumerates every declaration-feasible
start, and checks trajectory separation before scoring. It uses no future
arrivals or execution telemetry and does not claim a field-causal intervention.

The current locked rerun uses a strict 40-day training, 16-day
calibration-validation, and 41,154-record locked power split. Experiment 9
embeds the calibration-validation conversion factors (0.582671, 0.687118,
0.969849, 1.349061, and 5.320913) and lineage digests; Experiment 11 contains
all 24 trace-to-bus permutations plus the two predeclared concentration controls
(16,848 rows), Experiment 12 contains 216 complete-cycle outcomes with all 54
contracts activated, and Experiment 18 contains 9,648 fixed-active-plan AC
N--1 outcomes across RTS-24, IEEE-30, IEEE-39, and IEEE-118. The final audit is
rerun after all dependent artifacts are regenerated; its check count and the
LaTeX page count are recorded from the release build and not copied from an
earlier run.
Experiment 12 now names its complete-cycle metric as a settlement-value
residual and records the no-event reference definition explicitly, preventing
the zero residual on a shared minimum-cost face from being misread as forecast
accuracy.

The follow-up risk refit also removes a latent identifiability failure: the
joint total-plus-daily-CVaR program now includes predeclared, equally weighted
normalized total-exposure and daily-CVaR preferences in its convex objective.
The validation fit has 200.988 MW-slot total false-credit exposure against a
206.571 budget and a 0.231370 daily-CVaR ratio against a 0.238078 budget
with normalized slack 0.006709. Its KKT residual is (2.63\times10^{-10}),
and its simplex differs from the CVaR-only ablation by
\(2.95\times10^{-2}\) in (L_\infty). The five-point validation-only stress
frontier reaches an active boundary at reserve 0.97, while no locked outcome is
used for selection. The downstream payment, AC, spatial, information-boundary,
and trace-replay panels are regenerated from the current profile lineage. The
release audit now reports 372/372 checks passed, and the final IEEEtran build is
10 pages with no overfull boxes or unresolved references.

Experiment 26 closes the remaining declaration-to-settlement hand-off with a
cached-only lineage certificate. It recomputes the indexed job, aggregation,
region-to-network residuals, and the declared RTS-24 region-to-bus incidence
before valuation, checks the validation-fitted risk and relative payment
certificates, verifies all 37 finite RTS-24 outages, and records SHA-256 digests
for seven upstream artifacts, including the runtime-complete common witness and
its N--1 settlement replay. The certificate stores explicit profile roles and
checks the identity of that common witness before network valuation.

Experiments 27 and 28 close the two remaining release checks. Experiment 27
constructs the runtime-complete declaration witness for all 75,326 submissions,
uses its digest for 432 common-witness RTS-24 settlement cells, and reports the
same witness at the job and network layers. Experiment 28 independently audits
the held-out total-plus-CVaR tail against the total-budget-only ablation with a
paired block bootstrap. The final release tree contains the updated paper,
figures, manifests, and all 372 audit checks. The canonical all-stage manifest
now records Exp27 and Exp28 explicitly, and Exp27 exports a typed runtime
coupling certificate for both the baseline and declaration-only counterfactual
service vectors; Exp26 verifies that certificate before accepting the settlement
lineage. The witness digest now covers both saved indexed service vectors,
their start blocks, and the regional profiles; Exp26 reconstructs those vectors
from the saved declarations and recomputes the digest before accepting any
network result. The obsolete alternate Exp23 implementation and its unused
configuration keys were removed so the released source has one information
boundary.
