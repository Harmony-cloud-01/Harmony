#!/usr/bin/env python3
# scripts/qsecure_status.py
"""
Read Codex/System/QSecure.yaml and report whether quantum posture is OK.
Exit codes:
  0  OK
  1  WARN (e.g., key stale but grace period)
  2  FAIL (e.g., policies demand quantum but not healthy)
"""
import argparse, json, os, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import yaml

CFG_PATH = Path("Codex/System/QSecure.yaml")

def load_cfg(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def iso_now():
    return datetime.now(timezone.utc)

def parse_iso(ts: str | None):
    if not ts: return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="emit JSON status")
    ap.add_argument("--verbose", "-v", action="store_true", help="extra detail")
    args = ap.parse_args()

    if not CFG_PATH.exists():
        print("QSECURE: FAIL (missing Codex/System/QSecure.yaml)")
        return 2

    cfg = load_cfg(CFG_PATH)
    enabled = bool(cfg.get("qsecure", {}).get("enabled", False))
    require_q = bool(cfg.get("qsecure", {}).get("policies", {}).get("require_quantum_ok", False))
    key = cfg.get("qsecure", {}).get("endpoints", {}).get("qkd", {})
    ks = key.get("status", "unknown")
    last_rot = parse_iso(key.get("last_rotation_ts"))
    r_days = int(cfg.get("qsecure", {}).get("policies", {}).get("rotation_days", 7))
    grace_h = int(cfg.get("qsecure", {}).get("policies", {}).get("grace_hours", 48))

    now = iso_now()
    freshness = None
    state = "WARN"
    code = 1

    if enabled and last_rot:
        freshness = now - last_rot
        due = timedelta(days=r_days)
        grace = timedelta(hours=grace_h)
        if ks == "active" and freshness <= due:
            state, code = "OK", 0
        elif ks == "active" and due < freshness <= due + grace:
            state, code = "WARN", 1
        else:
            state, code = "FAIL", 2
    elif enabled:
        state, code = "FAIL", 2
    else:
        # QSecure disabled ⇒ OK unless require_quantum_ok
        state, code = ("OK", 0) if not require_q else ("FAIL", 2)

    summary = {
        "enabled": enabled,
        "require_quantum_ok": require_q,
        "endpoint_status": ks,
        "last_rotation_ts": key.get("last_rotation_ts"),
        "fresh_hours": None if not last_rot else round(freshness.total_seconds()/3600, 2),
        "rotation_days": r_days,
        "grace_hours": grace_h,
        "state": state,
        "exit_code": code,
        "checked_at": now.isoformat()
    }

    if args.verbose:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    elif args.json:
        print(json.dumps(summary, ensure_ascii=False))
    else:
        print(f"QSECURE: {state} (status={ks}, last_rotation={key.get('last_rotation_ts')}, require={require_q})")

    return code

if __name__ == "__main__":
    sys.exit(main())
