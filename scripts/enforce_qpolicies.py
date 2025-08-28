#!/usr/bin/env python3
# scripts/enforce_qpolicies.py
"""
Fail fast if QSecure policy requires quantum OK and status is not OK/WARN per grace.
Intended to wrap CI steps: run this first; if it exits non-zero, skip sensitive tasks.
"""
import json, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone

REPORT = Path("reports/qsecure_enforcement.log")

def run_status():
    # Reuse qsecure_status.py for consistent logic
    out = subprocess.run(
        ["python3", "scripts/qsecure_status.py", "--json"],
        check=False, capture_output=True, text=True
    )
    try:
        data = json.loads(out.stdout or "{}")
    except Exception:
        data = {"state": "FAIL", "parse_error": True}
    data["_rc"] = out.returncode
    return data

def main():
    st = run_status()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "at": datetime.now(timezone.utc).isoformat(),
            "status": st
        }, ensure_ascii=False) + "\n")

    if st.get("_rc", 2) == 0:
        print("QSECURE ENFORCE: OK")
        sys.exit(0)
    elif st.get("_rc") == 1:
        # Grace WARN: allow but warn
        print("QSECURE ENFORCE: WARN (within grace). Proceeding.")
        sys.exit(0)
    else:
        print("QSECURE ENFORCE: FAIL (policy or posture not met).")
        sys.exit(2)

if __name__ == "__main__":
    main()
