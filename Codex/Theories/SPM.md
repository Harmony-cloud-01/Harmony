
# SPM — Simulated Perception Matrix (CHRS v2.1)

> Draft @ 2025-09-01T01:08:26+00:00 (UTC) • Status: scaffold • Version: v2.1

## Overview
Experience is **rendered** by recursive loops of perception, prediction, and simulation. SPM is the rendering engine abstraction.

## Core claims
- Perception is **active inference**; rendering adapts to state.
- Latency and fidelity matter for subjective quality.
- Rendering stack is tunable per-application.

## Why it matters (for AI)
Real-time assistants, AR/VR, and robotics require **adaptive rendering** of the world state.

## Interfaces
- **Inputs:** world model, sensor streams, SPRC hooks, task goals.
- **Outputs:** rendered frames/states, uncertainty overlays, action suggestions.

## Metrics
- Perceptual latency, fidelity, uncertainty calibration.

## Safety & Ethics
- Avoid hallucination amplification; show provenance and uncertainty.

## References / Lineage
- Active inference, predictive processing, robotics control loops.

## Change log
- v2.1: Defined rendering I/O and uncertainty overlays.
