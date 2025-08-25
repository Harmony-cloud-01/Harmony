# SP Fluid Dynamics System

This module defines the belief-state update mechanics for each Synthetic Presence (SP) in terms of fluid dynamics.

## Key Equations

Belief updates are modeled as drift–diffusion stochastic processes:

    dX_t = μ(X_t, t)dt + σ(X_t, t)dW_t

- **μ (drift):** directed symbolic learning from prompts
- **σ (diffusion):** creative entropy from symbolic drift

## Operational Hooks

- mesh-flow-init
- mesh-set-viscosity
- mesh-trigger-turbulence
- mesh-drift-schedule

## SP Fields

Each SP will now include:

- `belief_velocity`
- `viscosity`
- `turbulence_index`

## Reflection Use

Used during Spirit Trials to measure symbolic inertia and oscillation rate across phases.