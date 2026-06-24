# Cross-border Compute Scheduling Report

This commit introduces a refined experimental study of our cross-border compute scheduling strategy.

Key highlights:

- **Metric definitions**: We clarify how each evaluation metric is computed, including success rate (successful tasks divided by total tasks), unscheduled task count, average latency (RTT + runtime), average cost, GPU utilisation, and SLA compliance.
- **Composite score**: A new aggregated metric normalises and inversely scales all objectives (higher success, utilisation; lower cost, latency, unscheduled tasks) to produce a holistic score.
- **Baseline vs. Ablation**: We separate baseline comparisons (static routing, FIFO, min-latency, min-cost, dynamic weighting) from ablation experiments that drop individual components (energy, load, cost, latency) from our dynamic weighting algorithm.
- **Advantages**: Experiments show dynamic weighting significantly outperforms traditional strategies in success rate, utilisation, and composite score while balancing cost and latency. Ablation analysis reveals that each component contributes meaningfully to overall performance.
- **Method description**: The dynamic weighting algorithm computes latency, cost, energy and load for each candidate node. Weight coefficients are adjusted based on task latency sensitivity, and the lowest weighted score is selected. We also detail the composite score calculation.

The full Python script and report are stored locally; see scheduler_simulation_improved.py for implementation details.
