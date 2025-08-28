#!/usr/bin/env python3
# scripts/rotate_qkeys.py
"""
Local key 'rotation': updates QSecure.yaml fields to simulate a QKD key change.
Writes a rotation log under reports/qsecure_rotations.log.
Use --commit to git add/commit the change automatically.
"""
import argparse, subprocess
from datetime import datetime, timezone
from pathlib import Path
import yaml

CFG = Path("Codex/System/QSecure.yaml")
LOG = Path("reports/qsecure_rotations.log")

def iso_now(): return datetime.now(timezone.utc).isoformat()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reason", default="scheduled", help="why rotation occurred")
    ap.add_argument("--commit", action="store_true", help="git add/commit after write")
    ap.add_argument("--no-bump", action="store_true", help="don't bump audit_rev")
    args = ap.parse_args()

    if not CFG.exists():
        raise SystemExit("Missing Codex/System/QSecure.yaml")

    with CFG.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    q = data.setdefault("qsecure", {})
    meta = q.setdefault("meta", {})
    ep = q.setdefault("endpoints", {}).setdefault("qkd", {})

    ts = iso_now()
    old_id = ep.get("qkd_key_id", "QKD-UNKNOWN")
    new_id = f"{old_id.split('@')[0]}@{ts.replace(':','').replace('-','')[:15]}"
    ep["qkd_key_id"] = new_id
    ep["status"] = "active"
    ep["last_rotation_ts"] = ts
    meta["updated_at"] = ts

    if not args.no_bump:
        meta["audit_rev"] = int(meta.get("audit_rev", 1)) + 1

    CFG.parent.mkdir(parents=True, exist_ok=True)
    with CFG.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)

    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{ts} ROTATE id:{old_id} -> {new_id} reason:{args.reason}\n")

    print(f"✓ Rotated local qkd_key_id: {old_id} -> {new_id}")

    if args.commit:
        try:
            subprocess.check_call(["git", "add", str(CFG), str(LOG)])
            subprocess.check_call(["git", "commit", "-m", f"QSecure: rotate QKD key ({args.reason})"])
            print("✓ Changes committed.")
        except Exception as e:
            print(f"! Commit skipped/failed: {e}")

if __name__ == "__main__":
    main()
