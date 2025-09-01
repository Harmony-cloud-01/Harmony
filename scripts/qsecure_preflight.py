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
