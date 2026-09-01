# Experiment 21: capacity-consistent job-level witness

This audit takes the stored executable primal from Experiment 19 and applies
homogeneous transforms. Job release/deadline support, exact energy equalities,
nonnegativity, and proportional GPU upper bounds are preserved by
construction. The capacity-proportional witness reaches the committed 118-MW
network stress at 2176.183x, while holding the 0.001-MW/GPU nameplate fixed
certifies a 1.504x deployable scale. A four-row sensitivity panel around that
anchor reports the peak and capacity slack; rows above one are diagnostic
homogeneous stress, not external-validity evidence. Experiment 22 replays the
same indexed service vector at both principal scales, scaling service energy,
GPU cap, site capacity, aggregate load, and network injection together. No
second LP or clipping is used.
