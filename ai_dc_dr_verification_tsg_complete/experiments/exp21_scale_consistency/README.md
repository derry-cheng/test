# Experiment 21: capacity-consistent job-level witness

This audit takes the stored feasible primal from Experiment 19 and applies a
single homogeneous scale. Job release/deadline support, exact energy
equalities, nonnegativity, and proportional GPU upper bounds are preserved by
construction. The capacity-proportional witness reaches the committed 118-MW
nameplate at 2146.204x. A second calculation holds the 0.001-MW/GPU nameplate
fixed and certifies 1.480x, which is the deployment interpretation. The
audit therefore avoids a second multi-million-variable LP; it does not claim a
re-optimised objective at either scaled point.
