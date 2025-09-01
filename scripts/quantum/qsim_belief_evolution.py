#!/usr/bin/env python3
import argparse, json, math, sys
from pathlib import Path
import numpy as np
try: import yaml
except Exception: print("PyYAML required", file=sys.stderr); raise
from qiskit.quantum_info import Statevector, DensityMatrix  # no Aer

def load_cfg(spec):
    path, subtree = (spec.split("::") + [""])[:2]
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    node = data
    for k in filter(None, subtree.split(".")):
        node = node[k]
    return node

def apply_op(qc, op):
    t = op.get("type","").lower()
    g = {"h": qc.h, "x": qc.x, "y": qc.y, "z": qc.z}.get(t)
    if g:
        return g(op["target"])
    if t in ("rx","ry","rz"):
        ang = op.get("theta",0.0)
        if isinstance(ang,str):
            ang = float(eval(ang, {"__builtins__":{}}, {"pi": math.pi}))
        getattr(qc, t)(float(ang), op["target"]); return
    if t in ("u","u3"):
        qc.u(float(op.get("theta",0.0)), float(op.get("phi",0.0)), float(op.get("lam",0.0)), op["target"]); return
    if t in ("cx","cnot"):
        qc.cx(op["control"], op["target"]); return
    raise ValueError(f"Unsupported op: {op}")

def coherence_metric(dm):
    rho = np.array(dm.data); n = rho.shape[0]
    mask = ~np.eye(n, dtype=bool); off = np.abs(rho[mask])
    return float(off.mean()) if off.size else 0.0

def main():
    from qiskit import QuantumCircuit  # import here to avoid heavy import at module load
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="Codex/System/Quantum_CHRS.yaml::simulations.superpositional_belief")
    args = ap.parse_args()

    cfg = load_cfg(args.config)
    n = int(cfg.get("config",{}).get("n_qubits",1))
    qc = QuantumCircuit(n)
    for op in cfg.get("config",{}).get("unitary_ops",[]):
        apply_op(qc, op)

    # No Aer: build state directly
    state = Statevector.from_instruction(qc)
    dm = DensityMatrix(state)
    norm = float((state.data.conj()*state.data).sum().real)

    out = {
        "belief_norm": norm,
        "phase_coherence": coherence_metric(dm),
        "statevector": [complex(z).__repr__() for z in state.data.tolist()]
    }
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
