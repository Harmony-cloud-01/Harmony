#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
import numpy as np
try: import yaml
except Exception: print("PyYAML required", file=sys.stderr); raise
try:
    from scipy.linalg import sqrtm; HAVE_SCIPY = True
except Exception: HAVE_SCIPY = False

def decohere_dephasing(rho, gamma, steps):
    rhos=[rho.copy()]
    for t in range(1, steps+1):
        r=rhos[-1].copy(); decay=np.exp(-gamma*t); r[0,1]=r[0,1]*decay; r[1,0]=np.conj(r[0,1]); rhos.append(r)
    return rhos

def fidelity_uhlmann(rho, sigma):
    if not HAVE_SCIPY: return float("nan")
    A=sqrtm(rho); F=np.trace(sqrtm(A @ sigma @ A)).real; return float(np.clip(F, 0.0, 1.0))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--config", default="Codex/System/Quantum_CHRS.yaml::simulations.decoherence_filtering")
    args=ap.parse_args()
    cfg_path, subtree=(args.config.split('::')+[None])[:2]
    # gamma/timesteps from YAML if exists, else defaults
    gamma=0.1; steps=50
    try:
        cfg = yaml.safe_load(Path(cfg_path).read_text(encoding="utf-8")) or {}
        for k in filter(None, subtree.split(".")): cfg = cfg[k]
        gamma=float(cfg.get("config",{}).get("gamma", gamma))
        steps=int(cfg.get("config",{}).get("timesteps", steps))
    except Exception: pass
    rho0=np.array([[0.5,0.5],[0.5,0.5]], dtype=complex); rhos=decohere_dephasing(rho0, gamma, steps)
    rho_final=rhos[-1]; sigma_diag=np.diag(np.diag(rho_final))
    out={"gamma":gamma,"timesteps":steps,"coherence_initial":float(abs(rho0[0,1])),"coherence_final":float(abs(rho_final[0,1])),"uhlmann_fidelity_to_diagonal":fidelity_uhlmann(rho_final, sigma_diag)}
    print(json.dumps(out, indent=2))
if __name__=="__main__": main()
