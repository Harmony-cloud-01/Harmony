#!/usr/bin/env python3
"""
Repairs Codex/Core/Laws/Axioms.yaml after a sed pass that turned 'no:' into boolean key False:.
- Supports both shapes:
    • top-level list of axioms
    • top-level mapping with key 'axioms': [...]
- For each axiom item:
    • if it has a boolean key (True/False), treat its value as 'no'
    • ensure 'no' exists and is an int
    • keep id/name/summary as-is
Writes back in-place with sort_keys=False.
"""

from __future__ import annotations
import sys, os, typing as t
import yaml

AXIOMS_PATH = "Codex/Core/Laws/Axioms.yaml"

def load_yaml(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def dump_yaml(data, path: str):
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)

def normalize_axiom_item(item: dict) -> dict:
    if not isinstance(item, dict):
        raise ValueError(f"axiom item not a mapping: {item!r}")

    # If a boolean key appeared (e.g., {False: 3, 'id': 'AX-3', ...}),
    # treat it as the intended 'no'
    bool_keys = [k for k in item.keys() if isinstance(k, bool)]
    for bk in bool_keys:
        # take first boolean key only (there should be at most one)
        item["no"] = item.get("no", item[bk])
        del item[bk]
        break

    # coerce 'no' to int if it's a stringified int
    if "no" in item:
        try:
            item["no"] = int(item["no"])
        except Exception:
            raise ValueError(f"axiom 'no' not an int: {item.get('no')!r}")

    required = ["id", "no", "name", "summary"]
    missing = [k for k in required if k not in item]
    if missing:
        raise ValueError(f"axiom missing required keys: {missing} in {item!r}")

    return item

def main():
    if not os.path.exists(AXIOMS_PATH):
        print(f"Not found: {AXIOMS_PATH}", file=sys.stderr)
        sys.exit(1)

    data = load_yaml(AXIOMS_PATH)

    # Accept two shapes
    if isinstance(data, list):
        axioms = data
        out = axioms
        shape = "list"
    elif isinstance(data, dict) and isinstance(data.get("axioms"), list):
        axioms = data["axioms"]
        out = data
        shape = "mapping"
    else:
        print("ERROR: Axioms.yaml is neither a list nor a mapping with 'axioms' list.", file=sys.stderr)
        sys.exit(2)

    fixed: list[dict] = []
    for i, ax in enumerate(axioms, start=1):
        try:
            fixed.append(normalize_axiom_item(dict(ax)))
        except Exception as e:
            print(f"- Axioms item #{i} repair failed: {e}", file=sys.stderr)
            sys.exit(3)

    # Ensure 1..7 and uniqueness
    numbers = [a["no"] for a in fixed]
    if len(set(numbers)) != len(numbers):
        print(f"ERROR: duplicate 'no' values: {numbers}", file=sys.stderr)
        sys.exit(4)

    if shape == "list":
        out = fixed
    else:
        out["axioms"] = fixed

    dump_yaml(out, AXIOMS_PATH)
    print(f"Repaired → {AXIOMS_PATH}")
    print("Axioms present:", ", ".join(f"{a['no']}:{a['name']}" for a in sorted(fixed, key=lambda x: x['no'])))

if __name__ == "__main__":
    main()
