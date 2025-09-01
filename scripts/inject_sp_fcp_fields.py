#!/usr/bin/env python3
"""
Inject FCP counters into Codex/SPs/*.yaml:
  shen:
    last_fcp_trigger: null
    fcp_trigger_count: 0
Idempotent; preserves existing values.
"""
import sys, glob
from pathlib import Path
try: import yaml
except Exception: print("PyYAML required (pip install pyyaml)"); sys.exit(1)

def ensure_fields(p:Path):
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    shen = data.get("shen") or {}
    if "last_fcp_trigger" not in shen: shen["last_fcp_trigger"] = None
    if "fcp_trigger_count" not in shen: shen["fcp_trigger_count"] = 0
    data["shen"] = shen
    p.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")

def main():
    files = sorted(glob.glob("Codex/SPs/*.yaml"))
    if not files:
        print("No SP YAMLs found under Codex/SPs/"); return 0
    for f in files:
        ensure_fields(Path(f)); print(f"Updated {f}")
    return 0

if __name__=="__main__": sys.exit(main())
