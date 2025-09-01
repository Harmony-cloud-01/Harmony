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
