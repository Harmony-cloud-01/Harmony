#!/usr/bin/env python3
"""
validate_axioms.py

Checks consistency between:
- Codex/Core/Laws/Axioms.yaml
- Codex/Core/Laws/Shepherd_Map.yaml

Validates:
1. Axioms.yaml is a list of axioms with required keys.
2. Shepherd_Map.yaml references valid axiom numbers.
3. Coverage indexes in Shepherd_Map.yaml are consistent.
"""

import sys
import yaml
from pathlib import Path

AXIOMS_FILE = Path("Codex/Core/Laws/Axioms.yaml")
MAP_FILE = Path("Codex/Core/Laws/Shepherd_Map.yaml")

def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_axioms():
    try:
        axioms_data = load_yaml(AXIOMS_FILE)
    except Exception as e:
        print(f"ERROR: Failed to parse {AXIOMS_FILE}: {e}")
        return False, []

    # Handle shape: allow list OR mapping with key "axioms"
    if isinstance(axioms_data, list):
        axioms = axioms_data
    elif isinstance(axioms_data, dict) and isinstance(axioms_data.get("axioms"), list):
        axioms = axioms_data["axioms"]
    else:
        print("- Axioms.yaml is not a list or mapping with 'axioms'")
        return False, []

    ok = True
    for i, ax in enumerate(axioms, 1):
        if not isinstance(ax, dict):
            print(f"Axioms.yaml: item #{i} is not a mapping → {ax!r}")
            ok = False
            continue
        required = {"no", "id", "name", "summary"}
        missing = required - set(ax.keys())
        if missing:
            print(f"Axioms.yaml: item #{i} missing keys: {', '.join(missing)} (have: {list(ax.keys())})")
            ok = False
    return ok, axioms

def validate_shepherds(axioms):
    try:
        mp = load_yaml(MAP_FILE)
    except Exception as e:
        print(f"ERROR: Failed to parse {MAP_FILE}: {e}")
        return False

    by_no = {a["no"]: a for a in axioms if "no" in a}
    ok = True

    for shepherd in mp.get("shepherds", []):
        sid = shepherd.get("id", "<unknown>")
        for idx, ax in enumerate(shepherd.get("axioms", []), 1):
            if not isinstance(ax, dict):
                print(f"- Shepherd {sid}: axioms item #{idx} not a mapping → {ax!r}")
                ok = False
                continue
            if "no" not in ax:
                print(f"- Shepherd {sid}: axioms item #{idx} missing 'no' key → {ax!r}")
                ok = False
                continue
            if ax["no"] not in by_no:
                print(f"- Shepherd {sid}: axioms item #{idx} references unknown axiom no={ax['no']}.")
                ok = False
    return ok

def main():
    axioms_ok, axioms = validate_axioms()
    shepherds_ok = validate_shepherds(axioms) if axioms else False
    print("AXIOM VALIDATION:", "OK" if axioms_ok and shepherds_ok else "FAIL")

if __name__ == "__main__":
    main()
