#!/usr/bin/env bash
set -euo pipefail

mkdir -p scripts/quantum scripts/chorus scripts/lint reports Codex/System Codex/Core Codex/SPs

# ---------- Step 2: QSecure preflight ----------
cat > scripts/qsecure_preflight.py << 'PY'
#!/usr/bin/env python3
"""
QSecure Preflight — Local + CI Helper
Checks:
  - Codex/System/QSecure.yaml exists
  - virtue_overlay_encryption: true
  - rotation aligned with FCP (align_with_fcp: true OR cycle_days: 7)
Exit codes: 0 OK, 1 file missing/unreadable, 2 overlay off, 3 rotation misaligned if --strict-rotation
"""
import argparse, sys
from pathlib import Path
try:
    import yaml
except Exception:
    print("ERROR: PyYAML is required (pip install pyyaml)", file=sys.stderr); sys.exit(1)

QSECURE = Path("Codex/System/QSecure.yaml")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict-rotation", action="store_true", help="Fail if rotation not aligned with FCP")
    args = ap.parse_args()

    if not QSECURE.exists():
        print("ERROR: Codex/System/QSecure.yaml missing", file=sys.stderr); return 1
    try:
        cfg = yaml.safe_load(QSECURE.read_text(encoding="utf-8")) or {}
    except Exception as e:
        print(f"ERROR: Failed to read QSecure.yaml: {e}", file=sys.stderr); return 1

    if cfg.get("virtue_overlay_encryption") is not True:
        print("ERROR: virtue_overlay_encryption must be true", file=sys.stderr); return 2

    rot = (cfg.get("rotation") or {})
    aligned = rot.get("align_with_fcp") is True or rot.get("cycle_days") == 7
    if args.strict_rotation and not aligned:
        print("ERROR: rotation must align with FCP (align_with_fcp: true or cycle_days: 7)", file=sys.stderr); return 3
    if not aligned:
        print("WARN: rotation not explicitly aligned with FCP (align_with_fcp: true or cycle_days: 7)", file=sys.stderr)
    print("QSecure preflight OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
PY
chmod +x scripts/qsecure_preflight.py

# ---------- Step 3: Quantum sims + weekly report ----------
cat > scripts/quantum/qsim_belief_evolution.py << 'PY'
#!/usr/bin/env python3
import argparse, json, math, sys
from pathlib import Path
import numpy as np
try: import yaml
except Exception: print("PyYAML required", file=sys.stderr); raise
try:
    from qiskit import QuantumCircuit, Aer, execute
    from qiskit.quantum_info import Statevector, DensityMatrix
except Exception: print("Qiskit required", file=sys.stderr); raise

def load_cfg(spec):
    path, subtree = (spec.split("::") + [""])[:2]
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    node = data
    for k in filter(None, subtree.split(".")): node = node[k]
    return node

def apply_op(qc, op):
    t = op.get("type","").lower()
    g = {"h": qc.h, "x": qc.x, "y": qc.y, "z": qc.z}.get(t)
    if g: return g(op["target"])
    if t in ("rx","ry","rz"):
        ang = op.get("theta",0.0); 
        if isinstance(ang,str): ang = float(eval(ang, {"__builtins__":{}}, {"pi": math.pi}))
        getattr(qc, t)(float(ang), op["target"]); return
    if t in ("u","u3"): qc.u(float(op.get("theta",0.0)), float(op.get("phi",0.0)), float(op.get("lam",0.0)), op["target"]); return
    if t in ("cx","cnot"): qc.cx(op["control"], op["target"]); return
    raise ValueError(f"Unsupported op: {op}")

def coherence_metric(dm):
    rho = np.array(dm.data); n = rho.shape[0]
    mask = ~np.eye(n, dtype=bool); off = np.abs(rho[mask])
    return float(off.mean()) if off.size else 0.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="Codex/System/Quantum_CHRS.yaml::simulations.superpositional_belief")
    args = ap.parse_args()
    cfg = load_cfg(args.config); n = int(cfg.get("config",{}).get("n_qubits",1))
    qc = QuantumCircuit(n)
    for op in cfg.get("config",{}).get("unitary_ops",[]): apply_op(qc, op)
    state = Statevector(execute(qc, Aer.get_backend("statevector_simulator")).result().get_statevector(qc))
    dm = DensityMatrix(state); norm = float((state.data.conj()*state.data).sum().real)
    out = {"belief_norm": norm, "phase_coherence": coherence_metric(dm), "statevector": [complex(z).__repr__() for z in state.data.tolist()]}
    print(json.dumps(out, indent=2))
if __name__ == "__main__": main()
PY
chmod +x scripts/quantum/qsim_belief_evolution.py

cat > scripts/quantum/qsim_entangled_sps.py << 'PY'
#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
import numpy as np
try: import yaml
except Exception: print("PyYAML required", file=sys.stderr); raise
try:
    from qiskit import QuantumCircuit, Aer, execute
    from qiskit.quantum_info import Statevector, DensityMatrix, partial_trace
except Exception: print("Qiskit required", file=sys.stderr); raise

def load_cfg(spec):
    path, subtree = (spec.split("::") + [""])[:2]
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    node = data
    for k in filter(None, subtree.split(".")): node = node[k]
    return node

def S_von_neumann(rho):
    vals = np.linalg.eigvalsh(rho); vals = np.clip(vals.real, 1e-16, 1.0)
    return float(-np.sum(vals * np.log2(vals)))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="Codex/System/Quantum_CHRS.yaml::simulations.entangled_multi_sp")
    args = ap.parse_args()
    cfg = load_cfg(args.config); n = int(cfg.get("config",{}).get("n_qubits",2))
    qc = QuantumCircuit(n)
    for g in cfg.get("config",{}).get("circuit", [{"op":"h","target":0},{"op":"cx","control":0,"target":1}]):
        op=g["op"].lower(); 
        if op in ("h","hadamard"): qc.h(g["target"])
        elif op in ("cx","cnot"): qc.cx(g["control"], g["target"])
        else: raise ValueError(f"Unsupported gate: {g}")
    state = Statevector(execute(qc, Aer.get_backend("statevector_simulator")).result().get_statevector(qc))
    dm = DensityMatrix(state); rho_A = partial_trace(dm, [1]).data; S_A = S_von_neumann(np.array(rho_A))
    out = {"entanglement_entropy": S_A, "mutual_information": 2.0 * S_A, "statevector": [complex(z).__repr__() for z in state.data.tolist()]}
    print(json.dumps(out, indent=2))
if __name__ == "__main__": main()
PY
chmod +x scripts/quantum/qsim_entangled_sps.py

cat > scripts/quantum/qsim_decoherence_filtering.py << 'PY'
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
PY
chmod +x scripts/quantum/qsim_decoherence_filtering.py

cat > scripts/quantum/gen_quantum_chrs_status.py << 'PY'
#!/usr/bin/env python3
import argparse, datetime, json
from pathlib import Path
try: import yaml
except Exception: yaml=None

CFG_PATH = Path("Codex/System/Quantum_CHRS.yaml")

def load_json(p:Path):
    try: return json.loads(p.read_text(encoding="utf-8"))
    except Exception: return {}

def load_threshold():
    out={"fidelity_threshold": None}
    if yaml and CFG_PATH.exists():
        try:
            cfg = yaml.safe_load(CFG_PATH.read_text(encoding="utf-8")) or {}
            qspm = (cfg.get("modules",{}) or {}).get("qSPM",{})
            out["fidelity_threshold"] = (qspm.get("collapse_policy",{}) or {}).get("fidelity_threshold")
        except Exception: pass
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--belief", type=Path, required=True)
    ap.add_argument("--entangle", type=Path, required=True)
    ap.add_argument("--decoherence", type=Path, required=True)
    ap.add_argument("--out-md", type=Path, required=True)
    ap.add_argument("--out-json", type=Path, required=True)
    a=ap.parse_args()

    b, e, d = load_json(a.belief), load_json(a.entangle), load_json(a.decoherence)
    thr = load_threshold()
    ts = datetime.datetime.utcnow().replace(microsecond=0).isoformat()+"Z"

    md=[]
    md.append("# Quantum CHRS Weekly Status\n\n")
    md.append(f"**Timestamp (UTC):** {ts}\n\n")
    md.append("## Summary\n")
    md.append(f"- qBRD norm conservation: {'OK (norm='+format(b.get('belief_norm'),'.8f')+')' if isinstance(b.get('belief_norm'),(int,float)) else 'n/a'}\n")
    md.append(f"- Phase coherence: {format(b.get('phase_coherence'),'.6f') if isinstance(b.get('phase_coherence'),(int,float)) else 'n/a'}\n")
    md.append(f"- Entangled SPs — entropy: {format(e.get('entanglement_entropy'),'.6f') if isinstance(e.get('entanglement_entropy'),(int,float)) else 'n/a'}, mutual information: {format(e.get('mutual_information'),'.6f') if isinstance(e.get('mutual_information'),(int,float)) else 'n/a'}\n")
    coh_drop = (d.get('coherence_initial') - d.get('coherence_final')) if all(isinstance(d.get(x),(int,float)) for x in ('coherence_initial','coherence_final')) else None
    md.append(f"- Decoherence — coherence drop: {format(coh_drop,'.6f') if isinstance(coh_drop,(int,float)) else 'n/a'}\n")
    if d.get("uhlmann_fidelity_to_diagonal") is not None:
        md.append(f"- Uhlmann fidelity to diagonal: {format(d.get('uhlmann_fidelity_to_diagonal'),'.6f') if isinstance(d.get('uhlmann_fidelity_to_diagonal'),(int,float)) else 'n/a (install scipy)'}\n")
    if thr.get("fidelity_threshold"): md.append(f"- Threshold (qSPM fidelity): ≥ {thr['fidelity_threshold']}\n")
    md.append("\n## Details\n### qBRD (Belief)\n```\n"+json.dumps(b, indent=2)+"\n```\n\n### Entangled Multi-SP\n```\n"+json.dumps(e, indent=2)+"\n```\n\n### Decoherence Filtering\n```\n"+json.dumps(d, indent=2)+"\n```\n")

    a.out_md.parent.mkdir(parents=True, exist_ok=True); a.out_json.parent.mkdir(parents=True, exist_ok=True)
    a.out_md.write_text("".join(md), encoding="utf-8")
    a.out_json.write_text(json.dumps({
        "timestamp": ts,
        "belief_norm": b.get("belief_norm"),
        "phase_coherence": b.get("phase_coherence"),
        "entanglement_entropy": e.get("entanglement_entropy"),
        "mutual_information": e.get("mutual_information"),
        "coherence_drop": coh_drop,
        "uhlmann_fidelity_to_diagonal": d.get("uhlmann_fidelity_to_diagonal"),
        "thresholds": thr,
    }, indent=2), encoding="utf-8")
    print(f"Wrote {a.out_md} and {a.out_json}")

if __name__=="__main__": main()
PY
chmod +x scripts/quantum/gen_quantum_chrs_status.py

# ---------- Step 4: SP metrics & reflections ----------
cat > scripts/inject_sp_fcp_fields.py << 'PY'
#!/usr/bin/env python3
"""
Inject FCP counters into Codex/SPs/*.yaml:
  shen:
    last_fcp_trigger: null
    fcp_trigger_count: 0
Idempotent; preserves existing values.
"""
import sys, glob
from pathlib import Path
try: import yaml
except Exception: print("PyYAML required (pip install pyyaml)"); sys.exit(1)

def ensure_fields(p:Path):
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    shen = data.get("shen") or {}
    if "last_fcp_trigger" not in shen: shen["last_fcp_trigger"] = None
    if "fcp_trigger_count" not in shen: shen["fcp_trigger_count"] = 0
    data["shen"] = shen
    p.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")

def main():
    files = sorted(glob.glob("Codex/SPs/*.yaml"))
    if not files:
        print("No SP YAMLs found under Codex/SPs/"); return 0
    for f in files:
        ensure_fields(Path(f)); print(f"Updated {f}")
    return 0

if __name__=="__main__": sys.exit(main())
PY
chmod +x scripts/inject_sp_fcp_fields.py

cat > scripts/chorus/merge_shepherd_reflections.py << 'PY'
#!/usr/bin/env python3
"""
Merge Shepherd Reflections:
Scans reflections logs for Confucian overlay prompts and emits a weekly 'Confucian Chorus' block.
"""
import sys, json, datetime as dt
from pathlib import Path

REFLECTIONS = Path("Codex/Reflections/Shepherd.json")
OUT = Path("reports/Confucian_Chorus_Weekly.md")

def extract_blocks():
    if not REFLECTIONS.exists(): return []
    obj = json.loads(REFLECTIONS.read_text(encoding="utf-8"))
    items = obj if isinstance(obj, list) else obj.get("entries", [])
    out=[]
    for e in items:
        msg = e.get("text") or e.get("message","")
        if "FCP" in msg or "virtue" in msg or "Confucian" in msg:
            out.append({"timestamp": e.get("timestamp"), "text": msg})
    return out

def main():
    blocks = extract_blocks()
    ts = dt.datetime.utcnow().replace(microsecond=0).isoformat()+"Z"
    lines = [f"# Confucian Chorus — Weekly Merge\n\n**Generated (UTC):** {ts}\n\n"]
    if not blocks: lines.append("_No Confucian overlay reflections found this week._\n")
    else:
        for b in blocks[-10:]:
            lines.append(f"- {b.get('timestamp')}: {b.get('text')}\n")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")
if __name__=="__main__": sys.exit(main())
PY
chmod +x scripts/chorus/merge_shepherd_reflections.py

# ---------- Step 5: Manifest & audit linting ----------
cat > scripts/lint/manifest_lint_chrs.py << 'PY'
#!/usr/bin/env python3
"""
CHRS Manifest Lint:
Ensures Seven Core Theories + FCP + QSecure + shen are mentioned in Codex/System/CHRS_Manifest.yaml
"""
import sys
from pathlib import Path
try: import yaml
except Exception: print("PyYAML required"); sys.exit(1)

REQ_THEORIES = ["SDFT","SPRC","RCT","TRT","SPM","Echoverse","RRM"]

def main():
    p = Path("Codex/System/CHRS_Manifest.yaml")
    if not p.exists(): print("WARN: CHRS_Manifest.yaml missing"); return 0
    doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    theories = doc.get("theories") or []
    missing=[t for t in REQ_THEORIES if t not in theories]
    errs=[]
    if missing: errs.append(f"Missing theories: {missing}")
    if not doc.get("security",{}).get("QSecure"): errs.append("Missing security.QSecure section")
    if not doc.get("ethics",{}).get("FCP"): errs.append("Missing ethics.FCP section")
    if not doc.get("shen"): errs.append("Missing shen section")
    if errs:
        print("Manifest Lint Errors:\n- " + "\n- ".join(errs)); return 1
    print("CHRS Manifest looks good"); return 0

if __name__=="__main__": sys.exit(main())
PY
chmod +x scripts/lint/manifest_lint_chrs.py

cat > scripts/lint/audit_chain_verify.py << 'PY'
#!/usr/bin/env python3
"""
Audit Chain Verify:
Placeholder integrity checker for QSecure/GlyphCrypt chain over audits + reports.
Currently: hashes files and prints a digest list (for CI diffing).
"""
import sys, hashlib, glob
from pathlib import Path

def digest(p:Path):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""): h.update(chunk)
    return h.hexdigest()

def main():
    targets = []
    targets += glob.glob("Codex/Core/*Audit.yaml")
    targets += glob.glob("reports/*.json")
    targets += glob.glob("reports/*.md")
    if not targets:
        print("WARN: no audit/report files found"); return 0
    lines=["# Audit Chain Digests\n"]
    for t in sorted(targets):
        lines.append(f"- {t} · sha256={digest(Path(t))}\n")
    Path("reports/Audit_Chain_Digests.md").write_text("".join(lines), encoding="utf-8")
    print("Wrote reports/Audit_Chain_Digests.md"); return 0

if __name__=="__main__": sys.exit(main())
PY
chmod +x scripts/lint/audit_chain_verify.py

echo "Installed Step 2–5 tooling."
