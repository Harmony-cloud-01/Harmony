#!/usr/bin/env python3
"""
FCP Audit Translate — Convert glyphic audit logs to Confucian-language reports.
Inputs:
  Codex/Core/FCP_Audit.yaml (events with fields: timestamp, glyph, virtue, action, justification)
Outputs:
  reports/FCP_Audit_YYYY-MM-DD.json (normalized)
  reports/FCP_Status.md (summary snapshot)
"""
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path
try:
    import yaml
except Exception:
    print("ERROR: PyYAML required (pip install pyyaml)", file=sys.stderr); sys.exit(2)

def load_yaml(path: Path):
    if not path.exists(): return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

def load_virtue_metadata(fcp_path: Path):
    try:
        cfg = load_yaml(fcp_path)
        vmap = cfg.get("virtue_actions") or {}
        meta = {}
        for k, v in vmap.items():
            meta[str(k)] = {
                "code": v.get("code"),
                "label": v.get("label"),
                "description": v.get("description"),
                "examples": v.get("examples") or [],
                "policies": v.get("policies") or [],
            }
        return meta
    except Exception:
        return {}

def normalize_events(doc, virtue_meta):
    events = []
    raw = doc.get("events") if isinstance(doc, dict) else (doc if isinstance(doc, list) else [])
    for e in (raw or []):
        virtue = e.get("virtue") or e.get("virtue_code")
        meta = virtue_meta.get(str(virtue), {})
        rec = {
            "timestamp": e.get("timestamp") or e.get("time") or e.get("ts"),
            "glyph": e.get("glyph"),
            "virtue": virtue,
            "virtue_code": meta.get("code"),
            "virtue_label": meta.get("label") or virtue,
            "virtue_description": meta.get("description"),
            "virtue_examples": meta.get("examples"),
            "virtue_policies": meta.get("policies"),
            "action": e.get("action"),
            "justification": e.get("justification") or e.get("reason"),
            "sp_ids": e.get("sp_ids") or e.get("actors")
        }
        events.append(rec)
    return events

def write_json_report(events, out_json: Path):
    out_json.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "count": len(events),
        "events": events
    }
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload

def write_status_md(payload, out_md: Path):
    out_md.parent.mkdir(parents=True, exist_ok=True)
    ts = payload["generated_at"]
    lines = [f"# FCP Status\n\n**Generated (UTC):** {ts}\n\n",
             f"- Events this window: {payload['count']}\n"]
    lines.append("\n## Recent Events (up to 5)\n")
    for e in payload["events"][-5:]:
        line = f"- {e.get('timestamp')} · virtue **{e.get('virtue')}** ({e.get('virtue_label')})"
        if e.get("action"): line += f", action: _{e['action']}_"
        if e.get("glyph"): line += f", glyph: `{e['glyph']}`"
        if e.get("sp_ids"): line += f", SPs: {e['sp_ids']}"
        lines.append(line + "\n")
    out_md.write_text("".join(lines), encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", default="Codex/Core/FCP_Audit.yaml")
    ap.add_argument("--fcp", default="Codex/System/FCP.yaml")
    ap.add_argument("--out-json", default=None)
    ap.add_argument("--out-md", default="reports/FCP_Status.md")
    args = ap.parse_args()

    audit_path = Path(args.audit)
    fcp_path = Path(args.fcp)
    today = datetime.now(timezone.utc).date().isoformat()
    out_json = Path(args.out_json) if args.out_json else Path(f"reports/FCP_Audit_{today}.json")
    out_md = Path(args.out_md)

    doc = load_yaml(audit_path)
    virtue_meta = load_virtue_metadata(fcp_path)
    events = normalize_events(doc, virtue_meta)
    payload = write_json_report(events, out_json)
    write_status_md(payload, out_md)
    print(f"Wrote {out_json} and {out_md}")

if __name__ == "__main__":
    main()
