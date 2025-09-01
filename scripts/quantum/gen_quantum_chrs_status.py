#!/usr/bin/env python3
import argparse, json
from datetime import datetime, timezone
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
    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

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
