#!/usr/bin/env python3
"""
FCP Guard / Controller

Reads Codex/System/fcp.yaml (baseline) and Codex/System/fcp_state.yaml (runtime),
keeps activation window in-bounds, emits simple status, and appends audit logs.

Usage:
  python3 scripts/fcp_guard.py status
  python3 scripts/fcp_guard.py check
  python3 scripts/fcp_guard.py activate "reason" [--days 7]
  python3 scripts/fcp_guard.py deactivate "reason"

Exit codes:
  0  OK (inactive) or successful command
  10 ACTIVE (info for check-mode)
  11 EXPIRED (was active, now auto-deactivated)
  12 BLOCKED (active + hard_block_on_active true)
  2  Bad usage / config error
"""
from __future__ import annotations
import sys, os, json, argparse, datetime as dt
from pathlib import Path

try:
    import yaml  # PyYAML
except Exception:
    print("ERROR: PyYAML not installed. pip install pyyaml", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
FCP_BASE = ROOT / "Codex" / "System" / "fcp.yaml"          # baseline spec (already in repo)
FCP_STATE = ROOT / "Codex" / "System" / "fcp_state.yaml"   # runtime state (created by scripts)
LOG_DIR   = ROOT / "Codex" / "System" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_LOG = LOG_DIR / "fcp_audit.jsonl"

def now_utc() -> dt.datetime:
    return dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)

def iso(dtobj: dt.datetime | None) -> str | None:
    return None if dtobj is None else dtobj.isoformat().replace("+00:00", "Z")

def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def save_yaml(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)

def audit(event: str, details: dict | None = None):
    rec = {"at": iso(now_utc()), "event": event, **(details or {})}
    with AUDIT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def coerce_duration_days(raw) -> int:
    try:
        d = int(raw)
        return max(1, min(d, 30))  # safety cap: 1..30 days
    except Exception:
        return 7

def ensure_state(base: dict, state: dict) -> dict:
    """Ensure required keys present, merge sensible defaults."""
    defaults = {
        "enabled": False,
        "reason": None,
        "activated_at": None,
        "expires_at": None,
        "hard_block_on_active": bool(base.get("policy", {}).get("hard_block_on_active", False)),
    }
    merged = {**defaults, **state}
    # hard_block_on_active inherits from base if not set explicitly
    if "hard_block_on_active" not in state:
        merged["hard_block_on_active"] = defaults["hard_block_on_active"]
    return merged

def auto_expire(state: dict) -> tuple[dict, int]:
    """If expired, flip enabled->False and log. Returns (state, exitcode_hint)."""
    if state.get("enabled") and state.get("expires_at"):
        try:
            exp = dt.datetime.fromisoformat(state["expires_at"].replace("Z", "+00:00"))
            if now_utc() >= exp:
                prev = dict(state)
                state["enabled"] = False
                state["reason"] = "auto_expired"
                state["activated_at"] = None
                state["expires_at"] = None
                audit("auto_deactivate_expired", {"prev": prev})
                return state, 11  # EXPIRED
        except Exception:
            # malformed expires_at -> force deactivate to be safe
            prev = dict(state)
            state["enabled"] = False
            state["reason"] = "auto_expired_malformed"
            state["activated_at"] = None
            state["expires_at"] = None
            audit("auto_deactivate_malformed", {"prev": prev})
            return state, 11
    return state, 0

def cmd_status():
    base = load_yaml(FCP_BASE)
    state = ensure_state(base, load_yaml(FCP_STATE))
    state, hint = auto_expire(state)
    save_yaml(FCP_STATE, state)  # persist any auto-expire
    print(yaml.safe_dump({"baseline": base.get("meta", {}), "state": state}, sort_keys=False, allow_unicode=True))
    sys.exit(0 if not state["enabled"] else (10 if hint == 0 else hint))

def cmd_check():
    base = load_yaml(FCP_BASE)
    state = ensure_state(base, load_yaml(FCP_STATE))
    state, hint = auto_expire(state)
    save_yaml(FCP_STATE, state)
    if not state["enabled"]:
        print("FCP: INACTIVE")
        sys.exit(0)
    # active
    print("FCP: ACTIVE")
    if state.get("hard_block_on_active", False):
        sys.exit(12)  # BLOCKED
    sys.exit(10)      # ACTIVE (informational)

def cmd_activate(reason: str, days: int):
    base = load_yaml(FCP_BASE)
    state = ensure_state(base, load_yaml(FCP_STATE))
    now = now_utc()
    exp = now + dt.timedelta(days=days)
    prev = dict(state)
    state.update({
        "enabled": True,
        "reason": reason,
        "activated_at": iso(now),
        "expires_at": iso(exp),
        # inherit current hard_block_on_active from baseline (if present)
        "hard_block_on_active": bool(base.get("policy", {}).get("hard_block_on_active", state.get("hard_block_on_active", False))),
    })
    save_yaml(FCP_STATE, state)
    audit("activate", {"prev": prev, "state": state})
    print(f"FCP ACTIVATED for {days} day(s). Reason: {reason}")
    sys.exit(0)

def cmd_deactivate(reason: str):
    base = load_yaml(FCP_BASE)
    state = ensure_state(base, load_yaml(FCP_STATE))
    prev = dict(state)
    state.update({
        "enabled": False,
        "reason": reason,
        "activated_at": None,
        "expires_at": None,
        "hard_block_on_active": state.get("hard_block_on_active", False),
    })
    save_yaml(FCP_STATE, state)
    audit("deactivate", {"prev": prev, "state": state})
    print("FCP DEACTIVATED. Reason:", reason)
    sys.exit(0)

def main(argv=None):
    p = argparse.ArgumentParser(description="Harmony FCP guard/controller")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status")
    sub.add_parser("check")

    pa = sub.add_parser("activate")
    pa.add_argument("reason", help="why activating")
    pa.add_argument("--days", default="7", help="duration in days (1..30)")

    pd = sub.add_parser("deactivate")
    pd.add_argument("reason", help="why deactivating")

    args = p.parse_args(argv)

    if args.cmd == "status":
        return cmd_status()
    if args.cmd == "check":
        return cmd_check()
    if args.cmd == "activate":
        return cmd_activate(args.reason, coerce_duration_days(args.days))
    if args.cmd == "deactivate":
        return cmd_deactivate(args.reason)

if __name__ == "__main__":
    main()
