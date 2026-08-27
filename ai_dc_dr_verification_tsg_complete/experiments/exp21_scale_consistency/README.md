# Experiment 21: capacity-consistent job-level witness

This audit takes the stored feasible primal from Experiment 19 and applies a
single homogeneous scale. Job release/deadline support, exact energy
equalities, nonnegativity, and proportional GPU upper bounds are preserved by
construction. The audit therefore avoids a second multi-million-variable LP;
it does not claim a re-optimised objective at the scaled point.
