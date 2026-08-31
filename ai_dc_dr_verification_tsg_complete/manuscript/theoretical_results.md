# Theoretical Results for the TSG Manuscript

## Proposition 1: marginal condition for baseline manipulation

Consider a ten-day arithmetic-mean baseline and an event called with probability
\(q\). Let \(\pi^{\mathrm{DR}}\) denote the response price. If reference-day
\(j\) increases event-window participant service by \(\delta R_j\), expected
payment increases by

\[
q\pi^{\mathrm{DR}}\Delta B
=\frac{q\pi^{\mathrm{DR}}}{10}\sum_{j=1}^{10}\delta R_j,
\qquad
\Delta B=\frac{1}{10}\sum_{j=1}^{10}\delta R_j .
\]

All ten operating-cost increments are physically incurred, so the matching
profit change is

\[
\Delta\Pi
=\frac{q\pi^{\mathrm{DR}}}{10}\sum_{j=1}^{10}\delta R_j
-\sum_{j=1}^{10}\Delta \mathcal C_{\mathrm w,j} .
\]

Let \(c'_j\) be the right derivative of the optimal physical operating cost with
respect to an event-window minimum-service constraint on reference day \(j\).
Historical-day baselines and their manipulation risk are documented in
\cite{caiso2017baseline,wang2022baseline}; the following closed-form
specialization is derived here. A strictly profitable local manipulation exists
exactly when

\[
\frac{q\pi^{\mathrm{DR}}}{10} > \min_j c'_j.
\]

The result follows by differentiating expected settlement with respect to one
reference-day MWh and choosing the feasible reference day with the smallest
marginal cost. At equality, alternative schedules may exist but cannot be called
strictly profitable. Experiment 1 obtains each \(c'_j\) independently as the
negative right-hand-side dual marginal of
\(-R_j\leq-R_j^0\), implements \(q\pi^{\mathrm{DR}}/10\) directly in the
strategic objective, and solves both certificate and behavioral programs to
global LP optimality. The reported profit uses the sum of ten physical
reference-day cost increments, not their mean. No behavioral coefficient is
fitted from the reported outcomes.

## Proposition 2: exact cumulative-state formulation

Let \(x_{skdt}\) be workload of source \(s\), class \(k\), served at destination
\(d\) in interval \(t\), and define

\[
y_{skt}=\sum_{\tau=0}^{t}\sum_d x_{skd\tau}.
\]

Deadline-constrained workload deferral and geographical assignment follow the
modeling foundations in \cite{cao2022flexibility,cao2024nonwire}. The cumulative
state equivalence below is this paper's sparse reformulation.

The release and deadline conditions are exactly equivalent to

\[
y_{skt}\leq A_{skt}, \qquad
y_{skt}\geq A_{sk,t-D_k},
\]

where \(A\) is cumulative arrival energy and the second constraint applies for
\(t\geq D_k\). The equality

\[
y_{skt}-y_{sk,t-1}=\sum_d x_{skdt}
\]

and terminal conservation complete the formulation. Substitution proves both
directions of equivalence. The original prefix-matrix construction required
\(O(SKDT^2)\) nonzeros; the cumulative-state formulation requires
\(O(SKDT)\) nonzeros. This reduction enables the 1,216-slot continuous
real-arrival certificate: a maximum-deadline washout plus one day precedes the
event day and the full maximum deadline follows it. The terminal equality
completes all in-window due work and all event-day arrivals without forcing
later unexpired batch jobs.

## Corollary 2.1: feasibility of the convex projection ensemble

Let \(\mathcal F(a)\) denote the workload-scheduling polytope for fixed arrivals
\(a\). If \(x^{(j)}\in\mathcal F(a)\) are the six exact projections and
\(\alpha_j\geq0\), \(\sum_j\alpha_j=1\), then

\[
\bar x=\sum_j\alpha_jx^{(j)}\in\mathcal F(a).
\]

Every equality constraint is preserved by affine combination, and every linear
inequality is preserved by convexity. The simplex coefficients are obtained by
minimizing event-window squared error on the 16-day validation set. Consequently,
the ensemble introduces neither feasibility repair nor a rule-based dispatch step.
The general convex-set closure argument follows \cite{boyd2004convex}; its
application here additionally requires all six schedules to share identical
arrivals and constraints.

## Corollary 2.2: day-wise risk reserve on the validation contract

Let \(\ell^\star\) be the independently selected single feasible projection.
For each source \(z\in\{\mathrm{obs},\mathrm{sim}\}\), define submitted and
true credit

\[
\widehat r_n^{(z)}=[p_n^{(\ell^\star)}-p_n^{(z)}]_+,\qquad
r_n^{(z)}=[p_n^0-p_n^{(z)}]_+,
\]

and source-specific false credit

\[
F_j^{(z)}=\sum_{n\in\mathcal V_j}
[\widehat r_n^{(z)}-r_n^{(z)}]_+.
\]

The validation risk contract uses \(z=\mathrm{sim}\), while the observed
meter is an independent locked replay. No maximum over the two sources is
taken: doing so would mix an offline oracle with the deployable risk
definition. For a pre-declared reserve
\(\beta\in(0,1]\), the risk-constrained program imposes

\[
\sum_j F_j^{(\mathrm{sim})}(\alpha)
\leq\beta\sum_jF_j^{(\mathrm{sim})}(\ell^\star),
\qquad
\operatorname{CVaR}_{0.75}\!\left(F_j^{(\mathrm{sim})}(\alpha)\right)
\leq\beta\operatorname{CVaR}_{0.75}\!\left(F_j^{(\mathrm{sim})}(\ell^\star)\right).
\]

The first inequality controls total risk and the second controls the mean of the
worst daily tail. The empirical CVaR epigraph is convex
\cite{rockafellar2000cvar}. Because \(\beta<1\) can exclude the single
projection, feasibility and error noninferiority are explicit acceptance
certificates: an infeasible reserve is discarded, and the final refit must
numerically satisfy both risk inequalities and

\[
\operatorname{MSE}_{\mathcal V}(\bar p)
\leq
\operatorname{MSE}_{\mathcal V}(p^{(\ell^\star)}).
\]

Four contiguous folds select \(\beta\) without locked-test labels. The accepted
ensemble is workload feasible and satisfies a total-plus-daily-tail validation
risk contract.

For the final schedule, let \(p^{\mathrm{safe}}\) solve the same exact workload
model with two-sided event constraints

\[
p_n^{(\ell^\star)}-\varepsilon
\leq p_n^{\mathrm{safe}}\leq p_n^{(\ell^\star)},
\qquad n\in\mathcal D\times\mathcal E.
\]

The reference schedule itself proves nonemptiness. Here \(\varepsilon=1\) MW is
fixed before the locked test split. Since \(z\mapsto[z-c]_+\) is
monotone,

\[
[p_n^{\mathrm{safe}}-c_n]_+
\leq[p_n^{(\ell^\star)}-c_n]_+
\]

for every sample and every possible unseen \(c_n\). Summing proves daily and
full-panel false-credit-MWh noninferiority on the locked test set without using
test labels. The statement is relative to the selected workload-feasible
reference; it does not make that reference a distribution-free estimate of an
arbitrary operator's no-event meter. The lower inequality also gives
\[
[c_n-p_n^{\mathrm{safe}}]_+
\leq[c_n-p_n^{(\ell^\star)}]_++\varepsilon,
\]
so the additional under-credit is at most
\(\varepsilon|\mathcal D||\mathcal E|\Delta t\). This is a structural
two-sided certificate; nRMSE and \(F_1\) remain empirical.

## Proposition 3: global polyhedral value-gap certificate

Let \(V(p)\) be the optimal SCED cost as a function of nodal demand. Under the
implemented continuous piecewise-linear SCED, \(V\) is a convex piecewise-affine
value function and the baseline LMP vector
\(\lambda^0\in\partial V(p^0)\) is a demand-value subgradient. Nodal signed linear
settlement uses

\[
\Delta V_{\mathrm{lin}}=(\lambda^0)^{\mathsf T}(p^0-p^1),
\]

whereas the proposed bilateral rule uses the exact signed avoided cost

\[
\Delta V=V(p^0)-V(p^1).
\]

The DC optimal-flow and nodal-dual model follows
\cite{zimmerman2011matpower,babaeinejadsarookolaee2021pglib}, while the
value-function argument uses standard convex duality \cite{boyd2004convex}.

Thus \(\Delta V>0\) earns a credit and \(\Delta V<0\) creates a debit. Within
the declared 10-segment settlement model, an oracle counterfactual equals that
model's value difference. The empirical score retains the same topology,
generator buses, capacities, line limits, and public quadratic cost curves but
independently re-solves them at 80-segment resolution. Zero error is therefore
not guaranteed even with a trace-anchored counterfactual. With an estimated
counterfactual, the measured error includes baseline error and declared
resolution discrepancy rather than a positive-payment truncation artifact.

The subgradient inequality at \(p^0\) gives the global certificate

\[
\Delta V_{\mathrm{lin}}-\Delta V
=V(p^1)-V(p^0)-(\lambda^0)^{\mathsf T}(p^1-p^0)
:=D_V(p^1,p^0;\lambda^0)\geq0.
\]

Thus signed nodal linear settlement globally upper-bounds the exact signed value.
Equality holds whenever a common dual subgradient supports the value function at
both endpoints; a positive gap certifies a change in the supporting affine piece.
For any \(\lambda^1\in\partial V(p^1)\), the endpoint subgradient inequalities also give

\[
0\leq\Delta V_{\mathrm{lin}}-\Delta V
\leq
\left(\lambda^1-\lambda^0\right)^{\mathsf T}(p^1-p^0)
\leq
\lVert \lambda^1-\lambda^0\rVert_*\lVert p^1-p^0\rVert.
\]

This result matches the piecewise-affine model actually solved and requires no
unimplemented smoothing parameter. Gross positive-only settlement drops negative
spatial components and has no corresponding signed-value certificate. Experiments
3 and 5 separately compare gross versus signed accounting, uniform versus nodal
pricing, and signed linear versus signed exact value under a matched price scale.
Experiment 3 records this nonnegative polyhedral Bregman gap for every interval
and every candidate counterfactual.

## Cited theorem: coalition allocation efficiency

Let \(N\) be the participating data centers and let \(v(S)\) be the signed SCED
avoided cost when coalition \(S\subseteq N\) moves from baseline to actual demand
while every nonmember remains at baseline. For participant \(i\), define

\[
\phi_i(v)=\sum_{S\subseteq N\setminus\{i\}}
\frac{|S|!(|N|-|S|-1)!}{|N|!}
\left[v(S\cup\{i\})-v(S)\right].
\]

This allocation is the Shapley value \cite{shapley1953value}; the formula and
efficiency axiom are prior theory, whereas the signed SCED characteristic
function and its exact experimental implementation are specific to this study.

If \(v(\varnothing)=0\), then the exact allocation is efficient:

\[
\sum_{i\in N}\phi_i(v)=v(N).
\]

To prove the identity, group each marginal term by coalition size. Every
nonempty coalition value appears with total positive coefficient one and every
proper coalition appears with an equal negative coefficient, so all intermediate
terms cancel and only \(v(N)-v(\varnothing)\) remains. Experiment 7 enumerates all
\(2^4=16\) coalition values per interval in the primary PGLib 118-bus panel. Its
scalability panel uses two contractual portfolios at each site and enumerates all
\(2^8=256\) coalition values for all 54 locked days and eight event intervals on
IEEE RTS-24. It uses neither permutation sampling nor an approximate Shapley
estimator. The participant sum is independently checked against the
grand-coalition value in every interval.

If each of \(G\) electrical sites contains \(m\) exchangeable contractual
slices, coalition value depends only on the count vector
\(k\in\{0,\ldots,m\}^G\). For a fixed member of group \(g\), each marginal at
count vector \(k\) has multiplicity

\[
\binom{m-1}{k_g}\prod_{h\ne g}\binom{m}{k_h}.
\]

Multiplying this quantity by the standard Shapley coefficient and summing over
all count vectors is algebraically identical to summing every labeled
coalition. It evaluates \((m+1)^G\) characteristic-function states and remains
exact. Experiment 7 checks efficiency for \(G=4\) and up to \(m=5\), i.e.,
20 participants.

## Standard representation: non-islanding line outages with LODFs

## Proposition 6: provenance-bound workload certificate

For every joined job \(j\), let the canonical tuple be

\[
 r_j=(\mathrm{id}_j,t_j^{\rm submit},t_j^{\rm start},t_j^{\rm end},
 E_j, n_j^{\rm telemetry},q_j,\kappa_j,\sigma_j),
\]

where \(E_j>0\) is the aggregated DCGM energy, \(n_j^{\rm telemetry}\) is
the number of raw telemetry records, \(q_j\) is the requested GPU field,
\(\kappa_j\) is the workload type, and \(\sigma_j\) is the scheduler state.
The ledger commitment is the SHA-256 digest of the deterministically sorted
CSV serialization of all \(r_j\), following the Secure Hash Standard
\cite{nist2015fips1804}.

If the scheduler--telemetry join is one-to-one after the declared last-record
rule, every retained job has
\(t_j^{\rm submit}\le t_j^{\rm start}<t_j^{\rm end}\),
and the positive-energy sum in the joined table equals the positive-energy sum
of the retained raw telemetry IDs, then the exact job-level flow LP is a
certificate for the committed ledger: any changed, inserted, removed, or
reassigned canonical row changes the commitment or causes one of the explicit
join and conservation checks to fail, subject to the collision resistance of
SHA-256. The certificate detects post-commit data changes; it does not by
itself establish that an operator did not submit a fictitious job before the
commitment was created. This distinction is part of the threat model.

The proof is direct. A canonical row alteration changes its serialized byte
string and therefore its digest except with negligible collision probability.
An inserted or removed row changes the row count, join cardinality, energy
sum, or digest. A timestamp alteration violating the release--execution order
fails the temporal predicate. The LP then preserves the exact energy of each
committed job and the measured aggregate slot profile, so its numerical
residual certifies solver feasibility rather than unverified provenance.
Experiment 16 evaluates all conditions on the complete scheduler/DCGM release,
stores the digest and source hashes, and reconciles the measured regional
capacity envelope with the 118-MW nameplate committed before the
validation/test split. The envelope is not used to select that nameplate.

Let the intact-network branch-flow vector be

\[
f=H(C_g g-p),
\]

and let \(L_{\ell k}\) be the line-outage distribution factor for monitored
line \(\ell\) when line \(k\) is removed. For every non-islanding outage with a
finite LODF column, the post-contingency monitored flow is exactly

\[
f_\ell^{(k)}
=f_\ell+L_{\ell k}f_k
=(H_\ell+L_{\ell k}H_k)(C_gg-p).
\]

The PTDF/LODF relation follows the standard lossless DC network model
\cite{stott2009dc,tejada2018lodf}. Therefore, simultaneously imposing

\[
-\bar f_\ell\leq
(H_\ell+L_{\ell k}H_k)(C_gg-p)
\leq\bar f_\ell,\qquad \ell\neq k,
\]

for every finite outage column is necessary and sufficient for preventive
feasibility against the declared set of non-islanding single-line outages in
that DC model. Experiment 8 applies this complete formulation to the public
IEEE RTS-24 system \cite{grigg1999rts}; it retains every native rating and
does not use contingency screening. The one islanding outage is reported
separately because a connected single-reference PTDF/LODF representation does
not define the separated-island balancing problem. This scope is consistent
with the stated N--1 criterion \cite{nerc2020tpl}; it is not an AC voltage or
transient-stability certificate.

## Proposition 4: scenario-robust daily N--1 payment noninferiority

Let \(p^\alpha\) be a convex combination of six independently solved
first-stage workload-feasible projections and the validation-selected
feasible-quantile comparator. The contractual reference \(p^{\rm ref}\) is
the validation-selected single feasible projection. The risk-constrained verifier is
an external approximation target and cannot be selected directly. Let \(\Xi\)
be the 1st, 10th, 50th, 90th, and 99th percentile of held-out per-job
measured-to-predicted GPU energy. For each \(\xi\in\Xi\), embed a feasible
N--1 dispatch \(g_t^\xi\) for
\(p_t^{\rm native}+M\xi p^\alpha_t\) in every event interval and impose

\[
\Delta t\sum_{t\in\mathcal E}C(g_t^\xi)
\leq(1-\eta)
\Delta t\sum_{t\in\mathcal E}
V_{N-1}(p_t^{\rm native}+M\xi p^{\rm ref}_t),
\qquad \xi\in\Xi.
\]

Because \(V_{N-1}\) is the minimum over the same dispatch feasible set,

\[
\sum_t\Delta t V_{N-1}(p_t^{\rm native}+M\xi p^\alpha_t)
\leq
\sum_t\Delta t
V_{N-1}(p_t^{\rm native}+M\xi p^{\rm ref}_t)
\quad\forall\xi\in\Xi.
\]

For any realized event load \(p^{1,\xi}\), subtracting
\(\sum_t\Delta t V_{N-1}(p^{1,\xi}_t)\) from the same-\(\xi\) inequality
proves that daily payment under \(p^\alpha\) cannot exceed the selected-single
reference payment in any declared scenario. The reference unit vector simultaneously
proves nonemptiness, and workload feasibility follows from convex closure.
Two linear programs implement the lexicographic objective: minimum trajectory
error is solved first, then its optimal value is retained while the common
fractional cost margin \(\eta\) is maximized.
The scenario set comes from the independent MIT telemetry
\cite{samsi2021supercloud}. The proof uses the standard SCED primal
\cite{zimmerman2011matpower} and linear-program value-function theory
\cite{boyd2004convex}; the payment certificate is the paper's specialization.

## Proposition 9: ledger-to-settlement coupling invariant

Partition the committed ledger into \(\mathcal J_{skd}\), and let
\(u_{j\tau}\) be the exact job-indexed service witness on its submitted
release--deadline window. Let \(B_{dj}=\mathbf 1\{s_j=d\}\) be the committed
job-to-region incidence and let \(M\in\{0,1\}^{|\mathcal B|\times|\mathcal D|}\)
map regions to network buses. Define

\[
x^{\rm job}_{skd\tau}
=\sum_{j\in\mathcal J_{skd}:\,r_j\leq\tau<d_j}u_{j\tau},
\qquad
X^{\rm job}_{d\tau}=\sum_{s,k}x^{\rm job}_{skd\tau}.
\]

The machine-readable certificate additionally evaluates
\[
r^{\rm job}_j=\sum_{\tau=r_j}^{d_j-1}u_{j\tau}-E_j,\quad
r^{\rm agg}_{d\tau}=X_{d\tau}-\sum_jB_{dj}u_{j\tau},\quad
r^{\rm map}_{b\tau}=p_{b\tau}-P^{\rm fix}_{b\tau}
-\Delta t^{-1}\sum_dM_{bd}X_{d\tau}.
\]
If the typed dimensions are satisfied and all three residual norms are at most
\(\varepsilon\), the profile used by the network is the image of the same
indexed witness up to \(\varepsilon\) in the declared units. At zero residual,
an independently optimized aggregate trajectory cannot receive a network
value. The result follows by finite summation over the disjoint ledger
partition; no optimization or rounding is involved in the mapping. Experiment
22 reconstructs the profile from all 12,296,675 stored job--slot variables,
checks the job, aggregation, bus-mapping, GPU-bound, and site-capacity rows,
and records zero residual before either SCED solve. The coupled replay is
pinned to the public IEEE RTS-24 case and uses a deterministic arithmetic-mean
event-window representation; it is not evidence from a separately optimized
aggregate trajectory.

## Identification boundary

Workload telemetry identifies a feasible counterfactual set, not necessarily a
single trajectory. The proposed estimator combines a statistical pre-estimator
with exact projection onto that set. Its empirical claim is therefore evaluated
against trace-observed execution produced independently of the verifier. No result
uses a verifier-generated trajectory as scoring truth.
