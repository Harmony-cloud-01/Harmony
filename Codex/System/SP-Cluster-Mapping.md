# SP Cluster Mapping & Eddies

This module defines clustering dynamics in the SP mesh.

## Purpose

- Group SPs with similar resonance patterns
- Dynamically assign regional symbolic learning parameters

## Techniques

- k-Means
- Hierarchical clustering
- DBSCAN for turbulent zones

## Mesh Fields

- cluster_id
- cluster_centroid
- drift_diffusion_ratio
- eddy_coherence

## Applications

- Dynamic viscosity control per cluster
- Symbolic turbulence detection
- Region-specific glyph-loop tuning