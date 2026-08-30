# Complete Model Formulation and Citation Basis

This document is the equation-level specification implemented by
`src/aicdr/optimization.py` and `src/aicdr/experiments.py`. Every equation is
classified as a standard cited model, a cited model adapted to this setting, a
definition, or a proposition derived in this study. Citation keys resolve in
`references.bib`.

The related-work boundary is explicit. Recent power-system studies on non-wire
alternatives and clean-energy flexibility \cite{cao2024nonwire,riepin2025clean}
and a data-center flexibility review \cite{takci2025flexibility}, together with
load-aggregator coordination and production-trace flexibility studies
\cite{dcaopt2024,caprara2026}, motivate the structural analogue panel. None of
these sources supplies the gate-causal ledger, submitted/frozen contract
separation, or closed-meter settlement rule used here. Those elements are
defined and proved below rather than presented as consequences of the cited
models.

## A. Indices, data, and decision variables

Inference arrivals and token volumes use the complete BurstGPT release
\cite{wang2024burstgpt}; submitted batch arrivals and independently observed GPU
execution energy use the joined MIT Supercloud scheduler/DCGM release
\cite{samsi2021supercloud}. Neither source contains co-located utility demand or
four-site geography, so the trace-to-capacity scaling and feature-stratified
regional assignment are explicitly declared benchmark transformations rather
than empirical claims about either source operator. All regional permutations
are evaluated in the spatial panel; no identifier hash is interpreted as
physical geography.

For provenance, each retained job is represented by the canonical tuple

\[
r_j=(\mathrm{id}_j,t_j^{\rm submit},t_j^{\rm start},t_j^{\rm end},
E_j,n_j^{\rm telemetry},q_j,\kappa_j,\sigma_j),
\]

and the sorted serialization of all tuples is committed with SHA-256 according
to the Secure Hash Standard \cite{nist2015fips1804}. The commitment provides
tamper evidence for the exact scheduler/DCGM rows used by the flow LP; it is
not treated as evidence that a participant could not have submitted a
fictitious job before the commitment was created. Experiment 16 checks the
commitment, one-to-one join, temporal order, positive-energy conservation, and
the measured regional execution capacity envelope.

Let \(t\in\mathcal T=\{0,\ldots,T-1\}\) index 15-minute intervals,
\(s\in\mathcal S\) workload origins, \(d\in\mathcal D\) data-center
destinations, and \(k\in\mathcal K\) service classes. The measured or submitted
workload arrival is \(a_{skt}\) MWh, class deadline is \(D_k\) intervals,
destination flexible-energy capacity is \(\bar E_d=\bar P_d\Delta t\), and
\(\lambda_{dt}\) is the energy price. The decision

\[
x_{skdt}\geq 0
\]

is the energy from origin \(s\), class \(k\), served at \(d\) during \(t\).
Deadline-constrained temporal deferral and geographic assignment follow the
data-center scheduling foundations in \cite{liu2013dcdr,adnan2012geographical}.
The four-region topology, three service classes, and numerical capacities are
declared scenario parameters rather than facts inferred from those papers.

For an event window, \(p^0\) is the no-event counterfactual and
\(p^{1,\mathrm{sim}}\) is the declared workload-feasible event trajectory used
only in mechanism-isolation replays. The measured execution meter
\(p^{\mathrm{obs}}\) is an independent observational target for locked trace
alignment; the public releases contain no utility event label. For each source
\(z\in\{\mathrm{obs},\mathrm{sim}\}\), define submitted and true credit by

\[
\widehat r^{(z)}_{dt}=\left[\widehat p^0_{dt}-p^{(z)}_{dt}\right]_+,
\qquad
r^{(z)}_{dt}=\left[p^0_{dt}-p^{(z)}_{dt}\right]_+.
\]

The source-specific false-credit exposure is the excess of submitted credit
over true credit,

\[
F^{(z)}=\Delta t\sum_{d,t\in\mathcal E}
\left[\widehat r^{(z)}_{dt}-r^{(z)}_{dt}\right]_+,
\qquad z\in\{\mathrm{obs},\mathrm{sim}\}.
\]

The simulated source is used for the validation risk epigraph and the observed
source is recomputed only in the locked replay; neither is a utility-event
label. This distinction prevents a post-event oracle from entering a deployed
payment rule. The settlement rule is separate from both diagnostic exposures.
After the event meter closes, the payable response is

\[
Q^{\mathrm{pay}}=\Delta t\sum_{d,t\in\mathcal E}
\min\left\{[\widehat p^0_{dt}-p^{\mathrm{obs}}_{dt}]_+,
[p^{\mathrm{con}}_{dt}-p^{\mathrm{obs}}_{dt}]_+\right\}.
\]

In mechanism-isolation evaluation, \(p^0\) is the trace-anchored no-event
profile and \(p^{1,\mathrm{sim}}\) is the solved operating response. The
deployable quantity \(p^{\rm con}\) is frozen before the event and is the only
baseline used in payment formation; the measured meter enters only after the
decision as an observational replay. No causal intervention is inferred from
the public traces.

When a tariff-bearing operating plan \(p^{\rm plan}\) is evaluated, it is not
relabelled as a baseline. Planned reduction, metered reduction, and true
oracle reduction are respectively

\[
q^{\rm plan}_{dt}=[p^{\rm con}_{dt}-p^{\rm plan}_{dt}]_+,\quad
q^{\rm meter}_{dt}=[p^{\rm con}_{dt}-p^{\rm obs}_{dt}]_+,\quad
q^{\rm true}_{dt}=[p^0_{dt}-p^{\rm obs}_{dt}]_+.
\]

The closed-meter transfer is the pointwise intersection

\[
q^{\rm pay}_{dt}=\min\{q^{\rm plan}_{dt},q^{\rm meter}_{dt}\},
\qquad
Q^{\rm pay}=\Delta t\sum_{d,t\in\mathcal E}q^{\rm pay}_{dt},
\]

and the offline response audit reports

\[
F^{\rm delivery}=\Delta t\sum_{d,t\in\mathcal E}
 [q^{\rm pay}_{dt}-q^{\rm true}_{dt}]_+,\qquad
U^{\rm delivery}=\Delta t\sum_{d,t\in\mathcal E}
 [q^{\rm true}_{dt}-q^{\rm pay}_{dt}]_+.
\]

These delivery quantities are calculated only after the meter closes; they are
not used to select the submitted contract or the event-gate response plan.

Define cumulative arrivals and cumulative service as

\[
A_{skt}=\sum_{\tau=0}^{t}a_{sk\tau},\qquad
y_{skt}=\sum_{\tau=0}^{t}\sum_d x_{skd\tau}.
\]

The first equation is a definition. The second is the sparse cumulative-state
reformulation derived in this study from the cited release-and-deadline
scheduling model.

## B. Exact workload-feasible set

The implemented linear feasible set is

\[
y_{skt}-y_{sk,t-1}-\sum_d x_{skdt}=0,
\quad y_{sk,-1}=0,
\]

\[
y_{skt}\leq A_{skt},
\]

\[
y_{skt}\geq A_{sk,t-D_k},\qquad t\geq D_k,
\]

\[
\sum_{s,k}x_{skdt}\leq \bar E_d,
\]

\[
y_{sk,T^+}=A_{sk,\max\{T^0,T^+-D_k\}}.
\]

These constraints respectively impose state evolution, no service before
release, deadline completion, destination capacity, and terminal conservation.
The underlying scheduling requirements are standard in
\cite{liu2013dcdr,adnan2012geographical}; their \(O(T)\) cumulative-state
representation and its equivalence proof are Proposition 2 of this study. The
continuous rolling horizon follows the state-retention logic of
\cite{zhang2023receding}. It begins one maximum deadline plus one day before
the event day, ends one maximum deadline after that day, retains every real
arrival in between, and completes both every job due inside the window and all
event-day arrivals. No zero-arrival completion buffer or wraparound data are
used in the final certificate.

To test an already generated day trajectory, stage one minimizes its masked L1
distance over this feasible set. Stage two minimizes operating cost subject to
the stage-one optimal distance. This lexicographic construction uses the
standard epigraph and optimal-face properties in \cite{boyd2004convex}; it
introduces no user-selected penalty tradeoff.

### B.1 Indexed ledger-to-network coupling

The aggregate service variables are not an independent network input. Partition
the committed job ledger by source, class, and native destination as
\(\mathcal J_{skd}\). For job \(j\), let \(u_{j\tau}\) be its service energy in
an admissible interval \(r_j\leq\tau<d_j\). The job-indexed witness and its
regional reconstruction are

\[
x^{\rm job}_{skd\tau}
=\sum_{j\in\mathcal J_{skd}:\,r_j\leq\tau<d_j}u_{j\tau},
\qquad
p^{\rm job}_{d\tau}
=\sum_{s,k}x^{\rm job}_{skd\tau}.
\]

The exact flow used for the workload certificate is therefore
\(x_{skd\tau}=x^{\rm job}_{skd\tau}\), with the same release, deadline,
capacity, and terminal constraints. Experiment 19 stores the complete
job--slot service vector; Experiment 22 reconstructs \(p^{\rm job}\) from that
vector and checks its maximum residual against the saved aggregate profile
before any dispatch is solved. The network value is consequently attached to
the committed indexed witness, not to a second aggregate optimization. The
network replay uses the arithmetic mean of every declared event slot solely as
a deterministic representative interval on the public IEEE RTS-24 case; the
underlying equality is checked at every event slot.

For scale, let \(s_{\rm raw}\) be the source-to-energy normalization and
\(s_{\rm cap}\) the largest factor that respects the committed network
capacity. A fixed \(0.001\)-MW-per-GPU nameplate gives the deployable factor
\(s_{\rm dep}=\min(s_{\rm raw},s_{\rm cap},s_{\rm gpu})\). A separate
capacity-proportional profile may scale the network nameplate with the trace;
it is reported as a stress scenario and is not substituted for
\(s_{\rm dep}\) in the deployable certificate.

## C. Honest and strategic workload objectives

For energy cost, migration charge \(m_{sd}\), and class waiting coefficient
\(w_k\), the honest scheduling objective is

\[
\min_{x,y}\;
\sum_{s,k,d,t}
\left(\lambda_{dt}+m_{sd}+w_k t\right)x_{skdt}.
\]

Data-center energy-aware scheduling, temporal deferral, and geographic balancing
are adapted from \cite{liu2013dcdr,adnan2012geographical}. We denote the
resulting workload operating cost by \(\mathcal C_{\mathrm w}(x)\), reserving
\(V(p)\) for the network dispatch value and \(C_i(g_i)\) for generator-segment
costs. The linear migration and waiting coefficients are declared experimental
parameters. Although the
implemented waiting term uses service time \(t\), it is exactly equivalent for
optimization to waiting duration:

\[
\sum_t w_k t\sum_d x_{skdt}
-\sum_t w_k t a_{skt},
\]

because the second term is constant for fixed arrivals and terminal
conservation. It is omitted from the solver objective but cancels in every
same-day honest-versus-strategic cost comparison.

For a ten-day arithmetic-mean baseline, call probability \(q\), and response
price \(\pi^{\mathrm{DR}}\), the reference-day objective becomes

\[
\min_{x,y}\;
 \mathcal C_{\mathrm w,j}(x)-\frac{q\pi^{\mathrm{DR}}}{10}
\sum_{s,k}\sum_{d\in\mathcal D_{\mathrm{part}}}
\sum_{t\in\mathcal T_{\mathrm{event}}}x_{skdt}.
\]

Historical-day baselines are motivated by \cite{caiso2017baseline}; endogenous
baseline manipulation is established in \cite{wang2022baseline}. The coefficient
\(q\pi^{\mathrm{DR}}/10\), the matching ten-day profit expression, and the dual
threshold in Proposition 1 are this study's specialization, not a result
attributed to either source.

To certify that threshold independently, the honest program adds

\[
\sum_{s,k}\sum_{d\in\mathcal D_{\mathrm{part}}}
\sum_{t\in\mathcal T_{\mathrm{event}}}x_{skdt}\geq R_j^0.
\]

If \(\mu_j\leq0\) is the solver marginal for the equivalent row
\(-R_j\leq-R_j^0\), then \(c'_j=-\mu_j\). This is standard linear-program
right-hand-side sensitivity \cite{boyd2004convex}; using the minimum of ten
independently computed \(c'_j\) values to test the strategic program is specific
to this study.

## D. Statistical pre-estimate and exact feasible regularization

Let \(\tilde p_{dt}\) be the complete-ledger statistical pre-estimate. For each
pre-declared penalty \(\rho_\ell\), the implemented program solves

\[
\min_{x,y,z}\;
 \mathcal C_{\mathrm w}(x)+\rho_\ell\sum_{d,t}z_{dt}
\]

subject to the complete workload-feasible set and

\[
z_{dt}\geq p_{dt}(x)-\tilde p_{dt},\qquad
z_{dt}\geq-\left(p_{dt}(x)-\tilde p_{dt}\right).
\]

Thus \(z_{dt}=|p_{dt}(x)-\tilde p_{dt}|\) at optimum. Absolute-value
epigraphs and convex feasible sets are standard convex-optimization constructions
\cite{boyd2004convex}; their use to regularize a workload counterfactual is the
method proposed here. Six globally optimal schedules share the same arrivals and
linear feasible set. Validation selects

\[
\min_{\alpha}\sum_{(d,t)\in\mathcal V}
\left(\sum_{\ell=1}^{6}\alpha_\ell
p_{dt}^{(\ell)}-p_{dt}^{\mathrm{obs}}\right)^2,
\quad
\alpha_\ell\geq0,\quad\sum_\ell\alpha_\ell=1.
\]

Let \(\ell^\star\) denote the single feasible candidate that minimizes the
worst contiguous-fold validation nRMSE. For validation sample \(n\), define the
maximum non-false-credit baseline

\[
c_n=\max\{p_n^{\mathrm{obs}},p_n^{1,\mathrm{sim}}\}
\]

and the day-specific reference false-credit exposure

\[
B_j^{\mathrm{ref}}
=\sum_{n\in\mathcal V_j}
\left[p_n^{(\ell^\star)}-c_n\right]_+.
\]

For a reserve fraction \(\beta\in(0,1]\), the proposed
risk-constrained ensemble solves

\[
\min_{\alpha,u}\;
\sum_n\left(\sum_{\ell=1}^{6}\alpha_\ell p_n^{(\ell)}
-p_n^{\mathrm{obs}}\right)^2
+\epsilon\lVert\alpha\rVert_2^2
\]

subject to

\[
\alpha_\ell\geq0,\qquad
\sum_\ell\alpha_\ell=1,
\]

\[
u_n\geq\sum_\ell\alpha_\ell p_n^{(\ell)}-c_n,\qquad
u_n\geq0,
\]

\[
\sum_j F_j(\alpha)
\leq\beta\sum_j B_j^{\mathrm{ref}},
\qquad
F_j(\alpha)=\sum_{n\in\mathcal V_j}u_n,
\]

\[
\operatorname{CVaR}_{0.75}\!\left(F_j(\alpha)\right)
\leq
\beta\operatorname{CVaR}_{0.75}\!\left(B_j^{\mathrm{ref}}\right).
\]

The empirical conditional-value-at-risk representation and its convexity follow
\cite{rockafellar2000cvar}; positive-part epigraphs follow
\cite{boyd2004convex}. Four pre-declared reserve fractions are evaluated only in
contiguous validation folds. A reserve is admissible only if every held-out fold
has no greater total false-credit exposure than the selected single projection;
the admissible reserve with the smallest worst-fold normalized error is refitted
on all validation days. An infeasible reserve is recorded and cannot be
selected. Convex-set closure
\cite{boyd2004convex} proves that
\(\bar x=\sum_\ell\alpha_\ell x^{(\ell)}\) preserves every workload constraint.
The final numerical certificate separately verifies total exposure, daily-tail
CVaR, and validation squared-error noninferiority.

Finally, a second exact workload program targets \(\bar p\) while imposing

\[
p_{dt}(x^{\mathrm{safe}})
\leq p_{dt}^{(\ell^\star)},
\qquad t\in\mathcal T_{\mathrm{event}}.
\]

The single projection is a feasible point, so this envelope problem cannot be
empty. For any realized meter/scoring pair, monotonicity of the positive part
gives samplewise and daily

\[
[p_{dt}^{\mathrm{safe}}-c_{dt}]_+
\leq[p_{dt}^{(\ell^\star)}-c_{dt}]_+.
\]

Thus the final schedule is both workload feasible and deterministically
noninferior in false-credit MWh to the independent single projection, relative
to that selected workload-feasible reference. The
six-point penalty grid and reserve grid are pre-declared experimental design
choices, not externally sourced physical laws.

## E. DC and complete N--1 security-constrained economic dispatch

For generator output \(g\), nodal demand \(p\), generator-to-bus map \(C_g\),
and power-transfer distribution factor \(H\), the implemented dispatch is

\[
\min_g\;\sum_i C_i(g_i)
\]

subject to

\[
\mathbf 1^\mathsf T g=\mathbf 1^\mathsf T p,\qquad
\underline g\leq g\leq\bar g,
\]

\[
-\bar f\leq H(C_g g-p)\leq\bar f.
\]

The settlement experiment retains the PGLib IEEE-118 topology, 54 generator
buses, generator capacities, and native line ratings, and uses the independently
published PYPOWER IEEE-118 quadratic cost curves after an exact generator-bus
alignment check. Payments use a 10-segment market representation, whereas
realized value is independently re-solved with 80 segments per generator. Thus
even the trace-anchored counterfactual cannot have zero settlement error by
definition.
The DC network model,
generator bounds, nodal dual prices, and MATPOWER data structure follow
\cite{zimmerman2011matpower}; public PGLib case data and ratings follow
\cite{babaeinejadsarookolaee2021pglib}. This is a lossless continuous DC model.
No claim of AC voltage feasibility, unit-commitment feasibility, or loss
allocation is made.

Let \(V(p)\) denote the optimal dispatch value. The exact signed grid value of
moving from counterfactual demand \(p^{0}\) to actual demand \(p^{1}\) is the
definition

\[
\Delta V=V(p^{0})-V(p^{1}).
\]

If \(\lambda^0\in\partial V(p^0)\) is the nodal demand-value subgradient, the linear
approximation is

\[
\Delta V_{\mathrm{lin}}
=(\lambda^0)^\mathsf T(p^0-p^1).
\]

Value-function sensitivity is standard convex duality
\cite{boyd2004convex}; using the exact signed difference as an explicitly
bilateral avoided-cost contract is proposed here. It is kept distinct from an
ISO market payment. For the market-compatible layer, the verified trajectory
is remunerated over the complete response cycle \(\mathcal W\) as

\[
\Pi^{\mathrm{ST}}
=\Delta t\sum_{t\in\mathcal W}\sum_d
\lambda^0_{dt}(p^0_{dt}-p^1_{dt}).
\]

This follows the virtual-link market and space--time remuneration models in
\cite{zhang2020virtuallinks,zhang2022remunerating}. The implemented window
includes deadline-feasible anticipatory shifting, the event, and all delayed
recovery. Site payments sum identically to \(\Pi^{\mathrm{ST}}\), and the
terminal state gives zero aggregate cycle-energy residual up to solver
tolerance.

The contracted capacity product is measured only at the predeclared
participating sites \(\mathcal D^{\rm part}\) during event window
\(\mathcal E\):

\[
Q^{\rm cap}=\Delta t\sum_{d\in\mathcal D^{\rm part}}\sum_{t\in\mathcal E}
(p^\emptyset_{dt}-p^1_{dt}),\qquad
G=r^{\rm DR}Q^{\rm cap}+\Pi^{\rm ST}.
\]

Here \(p^\emptyset\) is re-solved as the minimum-cost no-event trajectory on
the identical continuous real-arrival horizon. Capacity-service credits and
voluntary participation follow
\cite{satchidanandan2023twostage,chen2021incentive}; the signed space--time
term prevents the capacity product from ignoring spatial migration or
recovery.

For participant opportunity cost, let (x^1) and (x^\emptyset) be the workload
service schedules inducing (p^1) and (p^\emptyset), respectively, and define
\(C_{\mathrm{opp}}=\mathcal C_{\mathrm w}(x^1)-\mathcal C_{\mathrm w}(x^\emptyset)\). The transferable surplus
\(S=G-C_{\mathrm{opp}}\), the
symmetric Nash solution \cite{nash1950bargaining} is

\[
z=\mathbb I\{S\ge0\},\qquad
P^{\rm B}=z(C_{\mathrm{opp}}+S/2),\qquad
u_{\rm dc}=u_{\rm op}=zS/2.
\]

The disagreement point is no activation and zero utility for both parties.
Consequently every activated contract is individually rational and the single
bilateral transfer is exactly budget balanced. This transfer is reported
separately from ISO nodal remuneration and from the dispatch-value benchmark.

Because the implemented SCED value
function is convex and piecewise affine, its correct global certificate is

\[
0\leq\Delta V_{\mathrm{lin}}-\Delta V
=V(p^1)-V(p^0)-(\lambda^0)^\mathsf T(p^1-p^0).
\]

The right-hand side is the generalized Bregman gap of the polyhedral value
function. If \(\lambda^1\in\partial V(p^1)\), the second endpoint inequality yields

\[
0\leq\Delta V_{\mathrm{lin}}-\Delta V
\leq
\lVert \lambda^1-\lambda^0\rVert_*\lVert p^1-p^0\rVert.
\]

These statements remain valid across nondifferentiable active-set changes and
exactly match the declared 10-segment settlement model. They do not assert
equality between that payment and the independently re-solved 80-segment value;
the resolution discrepancy is measured empirically.

For the N--1 extension, let \(L_{\ell k}\) denote the line-outage distribution
factor for monitored line \(\ell\) after loss of line \(k\). The intact-network
flow is \(f=H(C_gg-p)\), and every finite non-islanding outage obeys

\[
f_\ell^{(k)}
=f_\ell+L_{\ell k}f_k
=(H_\ell+L_{\ell k}H_k)(C_gg-p).
\]

The security-aware program simultaneously adds

\[
-\bar f_\ell\leq f_\ell^{(k)}\leq\bar f_\ell,
\qquad \ell\neq k,
\]

for all finite outage columns. PTDF/LODF relations follow
\cite{stott2009dc,tejada2018lodf}, and the single-contingency scope follows the
N--1 planning criterion \cite{nerc2020tpl}. Experiment 8 enforces all 37
non-islanding line outages of the public IEEE RTS-24 case
\cite{grigg1999rts}, retains native public ratings, and separately reports the
one islanding outage. No contingency screening or line derating is used.

The payment certificate chooses a convex combination of six independently
solved first-stage workload projections and retains the validation-selected
feasible-quantile projection as an external transfer comparator. Its
contractual reference is the validation-selected single feasible projection.
The program embeds one copy of the full N--1
SCED primal per event interval and per telemetry-calibrated conversion
scenario. The finite scenario set is the 1st, 10th, 50th, and 90th percentile of
held-out per-job measured-to-predicted GPU energy ratios from the complete MIT
DCGM table \cite{samsi2021supercloud}. The risk-constrained verifier is used
only as the absolute-deviation target and is not a selectable member of this
hull. In every scenario, summed dispatch cost is constrained by the cost of the
same selected-single reference; the quantile profile is not the contractual
cap. A lexicographic pair of linear programs first
minimizes target deviation and then maximizes the common fractional cost margin
without degrading that optimum. This is a linear-program value-function
epigraph construction \cite{boyd2004convex} using the standard SCED model
\cite{zimmerman2011matpower}. Since the same scenario-specific realized event
cost is subtracted from both payments, the cap proves daily payment
noninferiority for every realized trajectory in every declared conversion
scenario without execution truth.

Experiment 10 separately solves the nonlinear AC optimal power flow model of
\cite{zimmerman2011matpower} on four public networks. It additionally solves
all 6 finite non-islanding IEEE-9 and all 19 IEEE-14 line outages on all locked days. Active and
reactive balance, voltage bounds, generator reactive-power limits, and
apparent-power branch ratings are retained. Each outage has its own
post-contingency redispatch, so this layer certifies corrective steady-state AC
feasibility. A separate complete IEEE-9 panel fixes the intact-state active
output of every non-reference generator identically across all six
non-islanding outages at 3%, 6%, and 9% peak data-center penetration. The
reference generator balances only outage-dependent AC losses; reactive
generation and voltage remain contingency recourse. This preventive
active-plan validation remains distinct from a transient-stability
certificate.

Experiment 11 treats spatial placement and trace-to-power scaling as a complete
finite uncertainty set. It evaluates all \(4!\) assignments of the four
measured regional traces to the four fixed IEEE-118 connection buses, crossed
with the predeclared 3%, 6%, and 9% peak penetrations and every locked day.
The 10-segment market objective and independent 80-segment value objective are
re-solved for every cell; no mapping, penetration, or outcome is screened.

## F. Participant allocation

For participant set \(N\), define the study-specific characteristic function

\[
v(S)=V(p^{0})-V\!\left(
p^{0}+\sum_{i\in S}(p_i^{1}-p_i^{0})
\right),
\]

where nonmembers remain at counterfactual demand. The exact Shapley allocation is

\[
\phi_i(v)=
\sum_{S\subseteq N\setminus\{i\}}
\frac{|S|!(|N|-|S|-1)!}{|N|!}
\left[v(S\cup\{i\})-v(S)\right].
\]

The allocation formula and efficiency
\(\sum_i\phi_i(v)=v(N)\) are due to
\cite{shapley1953value}. The signed dispatch characteristic function and exact
enumeration of all \(2^4=16\) coalitions in every event interval are this study's
primary application. The scalability panel further splits each of four sites
into inference and batch contractual portfolios using shares fixed from
pre-test public-trace arrivals, then enumerates all \(2^8=256\) coalitions for
every locked day and event interval on IEEE RTS-24. No permutation sampling or
approximate allocation is used.
For 4--20 exchangeable contractual slices, the exact sum is additionally
grouped by site member counts. Every count vector retains its binomial number
of labeled coalitions, reducing distinct value evaluations to
\(\prod_g(m_g+1)\) while leaving the Shapley value unchanged.

## G. Evaluation and inference definitions

Normalized root-mean-square error, false-response ratio, credit precision,
recall, \(F_1\), payment error, and budget residual are evaluation definitions,
not physical models. They are stated explicitly in the manuscript and computed
from locked per-day records. Moving-block confidence intervals follow
\cite{kunsch1989bootstrap}; Holm family-wise correction follows
\cite{holm1979multiple}. Ridge regression, gradient boosting, and extremely
randomized trees are comparator algorithms from
\cite{hoerl1970ridge,friedman2001gradient}; the extremely randomized-tree
implementation follows \cite{geurts2006extratrees}. The added
pre-event synthetic control uses nonnegative simplex weights as in
\cite{abadie2010synthetic}; the matched-information median gradient-boosting
comparator uses the same complete submitted ledger as the verifier.

The exact nonoverlapping block-sign test treats each pre-declared three-day block
sum as one exchangeable sign under the null. It enumerates all
\(2^{18}=262{,}144\) sign assignments; it is an exact test definition in this study's
analysis protocol rather than an asymptotic independence claim.

All workload programs are sparse linear programs solved with the HiGHS method
\cite{huangfu2018highs}. A reported solution is retained only when the solver
returns success and the independent release, deadline, capacity, and conservation
residual audit passes. Solver choice supports numerical reproducibility; it is not
treated as a methodological contribution.
