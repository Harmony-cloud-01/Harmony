# Temporal-Difference Learning in the Mesh

This module implements value learning for SPs across the Harmony mesh.

## Update Rule

    V[s_t] += α * (r_t+1 + γ * V[s_t+1] - V[s_t])

- α: learning rate
- γ: discount factor

## SP Mesh Usage

Each SP or PRC node keeps:

- V(state): resonance potential estimate
- TD-error: deviation from expected reward

## Commands

- mesh-td-init
- mesh-td-update
- mesh-td-policy (ε-greedy, softmax)
- mesh-td-report
- mesh-td-sync (multi-agent sync)

## Use Cases

- Reinforcement-based loop training
- Optimizing SP focus allocation
- Symbolic reward tuning for SP trial success