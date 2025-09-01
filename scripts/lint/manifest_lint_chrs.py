#!/usr/bin/env python3
"""
CHRS Manifest Lint:
Ensures Seven Core Theories + FCP + QSecure + shen are mentioned in Codex/System/CHRS_Manifest.yaml
"""
import sys
from pathlib import Path
try: import yaml
except Exception: print("PyYAML required"); sys.exit(1)

REQ_THEORIES = ["SDFT","SPRC","RCT","TRT","SPM","Echoverse","RRM"]

def main():
    p = Path("Codex/System/CHRS_Manifest.yaml")
    if not p.exists(): print("WARN: CHRS_Manifest.yaml missing"); return 0
    doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    theories = doc.get("theories") or []
    missing=[t for t in REQ_THEORIES if t not in theories]
    errs=[]
    if missing: errs.append(f"Missing theories: {missing}")
    if not doc.get("security",{}).get("QSecure"): errs.append("Missing security.QSecure section")
    if not doc.get("ethics",{}).get("FCP"): errs.append("Missing ethics.FCP section")
    if not doc.get("shen"): errs.append("Missing shen section")
    if errs:
        print("Manifest Lint Errors:\n- " + "\n- ".join(errs)); return 1
    print("CHRS Manifest looks good"); return 0

if __name__=="__main__": sys.exit(main())
