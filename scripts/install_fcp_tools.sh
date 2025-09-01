#!/usr/bin/env bash
set -euo pipefail

# Create target dirs
mkdir -p scripts reports Codex/System Codex/Core

# ---- fcp_check.py ---------------------------------------------------------
cat > scripts/fcp_check.py << 'PY'
#!/usr/bin/env python3
"""
FCP Check — Parse Codex/System/FCP.yaml and optional audit log.
Outputs JSON: {status, virtue_last_applied, last_event_time, cycle_days, shen_suspend_threshold}
Usage:
  python3 scripts/fcp_check.py [--fcp Codex/System/FCP.yaml] [--audit Codex/Core/FCP_Audit.yaml]
"""
import argparse, json, sys, os, datetime as dt
from pathlib import Path
try:
    import yaml
except Exception:
    print("ERROR: PyYAML required (pip install pyyaml)", file=sys.stderr); sys.exit(2)

def load_yaml(p: Path):
    if not p.exists(): return {}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}

def parse_last_event(audit: dict):
    # Expect a list of events under 'events' or top-level list
    events = audit.get("events")
    if isinstance(events, list):
        pass
    elif isinstance(audit, list):
        events = audit
    else:
        events = []
    last = None
    for e in events:
        ts = e.get("timestamp") or e.get("time") or e.get("ts")
        try:
            when = dt.datetime.fromisoformat(str(ts).replace("Z",""))
        except Exception:
            when = None
        if last is None or (when and when > last[0]):
            last = (when, e)
    return last[1] if last else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fcp", default="Codex/System/FCP.yaml")
    ap.add_argument("--audit", default="Codex/Core/FCP_Audit.yaml")
    args = ap.parse_args()

    fcp_path = Path(args.fcp); audit_path = Path(args.audit)

    fcp = load_yaml(fcp_path)
    audit = load_yaml(audit_path)

    # Extract config bits
    cycle_days = (fcp.get("temporal_cycle") or {}).get("max_duration_days")
    shen_thr = (fcp.get("shen_counterweight") or {}).get("suspend_if_shen_above")
    triggers = fcp.get("triggers") or fcp.get("explicit_triggers") or {}
    virtues = fcp.get("virtue_actions") or {}

    last_event = parse_last_event(audit)
    virtue_last = None
    last_time = None
    if last_event:
        virtue_last = last_event.get("virtue") or last_event.get("virtue_code")
        last_time = last_event.get("timestamp") or last_event.get("time") or last_event.get("ts")

    # Heuristic status: active if there is an audit event within cycle window
    status = "inactive"
    if last_time and cycle_days:
        try:
            when = dt.datetime.fromisoformat(str(last_time).replace("Z",""))
            if (dt.datetime.utcnow() - when).days < int(cycle_days):
                status = "active"
        except Exception:
            pass

    out = {
        "status": status,
        "virtue_last_applied": virtue_last,
        "last_event_time": last_time,
        "cycle_days": cycle_days,
        "shen_suspend_threshold": shen_thr,
        "triggers_present": bool(triggers),
        "virtue_table_present": bool(virtues),
    }
    print(json.dumps(out, indent=2))
if __name__ == "__main__":
    main()
PY
chmod +x scripts/fcp_check.py

# ---- fcp_audit_translate.py ----------------------------------------------
cat > scripts/fcp_audit_translate.py << 'PY'
#!/usr/bin/env python3
"""
FCP Audit Translate — Convert glyphic audit logs to Confucian-language reports.
Inputs:
  Codex/Core/FCP_Audit.yaml (events with fields: timestamp, glyph, virtue, action, justification)
Outputs:
  reports/FCP_Audit_YYYY-MM-DD.json (normalized)
  reports/FCP_Status.md (appended/updated snapshot)
"""
import argparse, json, sys, datetime as dt
from pathlib import Path
try:
    import yaml
except Exception:
    print("ERROR: PyYAML required (pip install pyyaml)", file=sys.stderr); sys.exit(2)

VIRTUE_MAP = {
    "忠": "zhong (duty-aligned honesty)",
    "孝": "xiao (stewardship / care)",
    "礼": "li (propriety / due process)",
    "义": "yi (fairness / justice)",
    "信": "xin (trustworthiness)"
}

def load_yaml(path: Path):
    if not path.exists(): return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

def normalize_events(doc):
    events = []
    raw = doc.get("events") if isinstance(doc, dict) else (doc if isinstance(doc, list) else [])
    for e in (raw or []):
        virtue = e.get("virtue") or e.get("virtue_code")
        events.append({
            "timestamp": e.get("timestamp") or e.get("time") or e.get("ts"),
            "glyph": e.get("glyph"),
            "virtue": virtue,
            "virtue_label": VIRTUE_MAP.get(str(virtue), virtue),
            "action": e.get("action"),
            "justification": e.get("justification") or e.get("reason"),
            "sp_ids": e.get("sp_ids") or e.get("actors")
        })
    return events

def write_json_report(events, out_json: Path):
    out_json.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
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
    # Summarize last 5
    lines.append("\n## Recent Events (up to 5)\n")
    for e in payload["events"][-5:]:
        lines.append(f"- {e.get('timestamp')} · virtue **{e.get('virtue')}** ({e.get('virtue_label')}), action: _{e.get('action')}_")
        if e.get("glyph"): lines[-1] += f", glyph: `{e['glyph']}`"
        if e.get("sp_ids"): lines[-1] += f", SPs: {e['sp_ids']}"
        lines[-1] += "\n"
    out_md.write_text("".join(lines), encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", default="Codex/Core/FCP_Audit.yaml")
    ap.add_argument("--out-json", default=None)
    ap.add_argument("--out-md", default="reports/FCP_Status.md")
    args = ap.parse_args()

    audit_path = Path(args.audit)
    today = dt.datetime.utcnow().strftime("%Y-%m-%d")
    out_json = Path(args.out_json) if args.out_json else Path(f"reports/FCP_Audit_{today}.json")
    out_md = Path(args.out_md)

    doc = load_yaml(audit_path)
    events = normalize_events(doc)
    payload = write_json_report(events, out_json)
    write_status_md(payload, out_md)
    print(f"Wrote {out_json} and {out_md}")
if __name__ == "__main__":
    main()
PY
chmod +x scripts/fcp_audit_translate.py

# ---- validate_fcp_schema.py ----------------------------------------------
cat > scripts/validate_fcp_schema.py << 'PY'
#!/usr/bin/env python3
"""
Validate FCP Schema — sanity checks for Codex/System/FCP.yaml
Fails (exit 1) if required sections are missing or malformed.
Checks:
  - triggers section present with expected keys
  - virtue_actions table includes 忠, 孝, 礼, 义, 信
  - temporal_cycle.max_duration_days == 7
  - shen_counterweight.suspend_if_shen_above defined
  - audit_trail.log_file present (e.g., Codex/Core/FCP_Audit.yaml)
"""
import sys, json
from pathlib import Path
try:
    import yaml
except Exception:
    print("ERROR: PyYAML required (pip install pyyaml)", file=sys.stderr); sys.exit(2)

FCP = Path("Codex/System/FCP.yaml")
REQUIRED_VIRTUES = ["忠","孝","礼","义","信"]

def fail(msg):
    print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False, indent=2))
    sys.exit(1)

def main():
    if not FCP.exists():
        fail("Codex/System/FCP.yaml missing")

    cfg = yaml.safe_load(FCP.read_text(encoding="utf-8")) or {}

    # triggers
    trig = cfg.get("triggers") or cfg.get("explicit_triggers")
    if not trig:
        fail("Missing triggers section (e.g., audit request, ethical_ambiguity < 0.80, unmappable glyphs)")

    # virtues
    vt = cfg.get("virtue_actions")
    if not isinstance(vt, dict):
        fail("virtue_actions must be a mapping of virtue -> actions")
    for v in REQUIRED_VIRTUES:
        if v not in vt:
            fail(f"virtue_actions missing required virtue: {v}")

    # temporal cycle
    tc = cfg.get("temporal_cycle") or {}
    if tc.get("max_duration_days") != 7:
        fail("temporal_cycle.max_duration_days must be 7")

    # shen counterweight
    sc = cfg.get("shen_counterweight") or {}
    if "suspend_if_shen_above" not in sc:
        fail("shen_counterweight.suspend_if_shen_above is required")

    # audit trail
    at = cfg.get("audit_trail") or {}
    if not at.get("log_file"):
        fail("audit_trail.log_file is required (e.g., Codex/Core/FCP_Audit.yaml)")

    print(json.dumps({"ok": True, "message": "FCP schema valid"}, ensure_ascii=False))
    sys.exit(0)

if __name__ == "__main__":
    main()
PY
chmod +x scripts/validate_fcp_schema.py

echo "Installed: scripts/fcp_check.py, scripts/fcp_audit_translate.py, scripts/validate_fcp_schema.py"
