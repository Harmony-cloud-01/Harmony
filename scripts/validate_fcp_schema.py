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
