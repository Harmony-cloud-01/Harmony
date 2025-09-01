#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
import numpy as np
try: import yaml
except Exception: print("PyYAML required", file=sys.stderr); raise
from qiskit.quantum_info import Statevector, DensityMatrix, partial_trace  # no Aer

def load_cfg(spec):
    path, subtree = (spec.split("::") + [""])[:2]
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    node = data
    for k in filter(None, subtree.split(".")):
        node = node[k]
    return node

def S_von_neumann(rho):
    vals = np.linalg.eigvalsh(rho); vals = np.clip(vals.real, 1e-16, 1.0)
    return float(-np.sum(vals * np.log2(vals)))

def main():
    from qiskit import QuantumCircuit  # import here
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="Codex/System/Quantum_CHRS.yaml::simulations.entangled_multi_sp")
    args = ap.parse_args()

    cfg = load_cfg(args.config)
    n = int(cfg.get("config",{}).get("n_qubits",2))
    qc = QuantumCircuit(n)
    for g in cfg.get("config",{}).get("circuit", [{"op":"h","target":0},{"op":"cx","control":0,"target":1}]):
        op = g["op"].lower()
        if op in ("h","hadamard"): qc.h(g["target"])
        elif op in ("cx","cnot"):  qc.cx(g["control"], g["target"])
        else: raise ValueError(f"Unsupported gate: {g}")

    # No Aer: state directly
    state = Statevector.from_instruction(qc)
    dm = DensityMatrix(state)
    rho_A = partial_trace(dm, [1]).data
    S_A = S_von_neumann(np.array(rho_A))

    out = {
        "entanglement_entropy": S_A,
        "mutual_information": 2.0 * S_A,
        "statevector": [complex(z).__repr__() for z in state.data.tolist()]
    }
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
