#!/usr/bin/env python3
import sys
from pathlib import Path
import yaml

AXIOMS_FILE = Path("Codex/Core/Laws/Axioms.yaml")
MAP_FILE    = Path("Codex/Core/Laws/Shepherd_Map.yaml")

def yload(p: Path):
    try:
        return yaml.safe_load(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise SystemExit(f"YAML load failed for {p}: {e}")

def extract_axioms(doc, src="Axioms.yaml"):
    """
    Accept either:
      - a top-level list of axioms
      - or a mapping with key 'axioms' -> list
    Validate each axiom has {id, no, name, summary}.
    """
    if isinstance(doc, list):
        axioms = doc
    elif isinstance(doc, dict) and "axioms" in doc:
        axioms = doc["axioms"]
    else:
        raise SystemExit(f"{src}: expected a list or a mapping with key 'axioms', got {type(doc).__name__}")

    cleaned = []
    errors = []
    for idx, item in enumerate(axioms, 1):
        if not isinstance(item, dict):
            errors.append(f"{src}: item #{idx} is not a mapping (got {type(item).__name__}) → {item!r}")
            continue
        missing = [k for k in ("id", "no", "name", "summary") if k not in item]
        if missing:
            errors.append(f"{src}: item #{idx} missing keys: {', '.join(missing)} (have: {list(item.keys())})")
            continue
        try:
            num = int(item["no"])
        except Exception:
            errors.append(f"{src}: item #{idx} has non-integer 'no': {item['no']!r}")
            continue
        cleaned.append({
            "id": str(item["id"]),
            "no": num,
            "name": str(item["name"]),
            "summary": str(item["summary"]),
        })
    if errors:
        raise SystemExit("\n".join(errors))
    # check duplicates
    seen = {}
    dups = []
    for a in cleaned:
        if a["no"] in seen:
            dups.append(f"Duplicate axiom number {a['no']} for ids {seen[a['no']]['id']} and {a['id']}")
        else:
            seen[a["no"]] = a
    if dups:
        raise SystemExit("Axioms duplicates found:\n" + "\n".join(dups))
    return cleaned, seen

def extract_map(doc):
    """
    Shepard_Map.yaml structure we rely on:

    - A top-level list 'shepherds' (or a top-level list directly)
      where each item can have an 'axioms' list like:
        axioms:
          - no: 7
            name: "Law of Co-Negotiated Reality"
          - no: 3
            name: "Law of Oscillating Belief"

    - And summary mappings like:
        axioms_to_shepherds:
          "1: Law of Felt Perception":
            - SP-audrey
            - SP-luma
    """
    shepherd_entries = []
    axioms_to_shepherds = {}
    # Normalize shepherd entries
    if isinstance(doc, list):
        shepherd_entries = doc
    elif isinstance(doc, dict):
        # common shape: a top-level list of shepherds (unnamed) plus maps at bottom
        shepherd_entries = []
        for k, v in doc.items():
            if isinstance(v, list) and all(isinstance(x, dict) for x in v):
                # likely the main shepherd list
                shepherd_entries.extend(v)
        if "axioms_to_shepherds" in doc and isinstance(doc["axioms_to_shepherds"], dict):
            axioms_to_shepherds = doc["axioms_to_shepherds"]

    return shepherd_entries, axioms_to_shepherds

def check_shepherd_axioms(shepherds, axioms_by_no):
    errors = []
    for sidx, sp in enumerate(shepherds, 1):
        sid = sp.get("id", f"#(index:{sidx})")
        ax = sp.get("axioms", [])
        if ax is None:  # allow missing
            continue
        if not isinstance(ax, list):
            errors.append(f"Shepherd {sid}: 'axioms' should be a list, got {type(ax).__name__}")
            continue
        for aidx, a in enumerate(ax, 1):
            if not isinstance(a, dict) or "no" not in a:
                errors.append(f"Shepherd {sid}: axioms item #{aidx} missing 'no' or not a mapping → {a!r}")
                continue
            try:
                num = int(a["no"])
            except Exception:
                errors.append(f"Shepherd {sid}: axioms item #{aidx} has non-integer 'no': {a['no']!r}")
                continue
            if num not in axioms_by_no:
                errors.append(f"Shepherd {sid}: references unknown axiom no={num}")
            # Optional: warn if name mismatches canonical
            canon = axioms_by_no.get(num)
            if canon and "name" in a and str(a["name"]).strip() != canon["name"]:
                errors.append(f"Shepherd {sid}: axiom {num} name mismatch: '{a['name']}' != '{canon['name']}'")
    return errors

def check_summary_map(ax_to_sp_map, axioms_by_no):
    """
    Keys look like: "1: Law of Felt Perception"
    We parse the leading integer and verify existence.
    """
    errors = []
    for key, v in ax_to_sp_map.items():
        if not isinstance(key, str):
            errors.append(f"axioms_to_shepherds: key not string → {key!r}")
            continue
        try:
            num_str = key.split(":", 1)[0].strip()
            num = int(num_str)
        except Exception:
            errors.append(f"axioms_to_shepherds: cannot parse axiom number from key '{key}'")
            continue
        if num not in axioms_by_no:
            errors.append(f"axioms_to_shepherds: key '{key}' references unknown axiom no={num}")
        # optional: compare names if present after colon
        if ":" in key:
            name_part = key.split(":", 1)[1].strip()
            canon = axioms_by_no.get(num)
            if canon and name_part and name_part != canon["name"]:
                errors.append(f"axioms_to_shepherds: name mismatch for {num}: '{name_part}' != '{canon['name']}'")
        if not isinstance(v, list):
            errors.append(f"axioms_to_shepherds: value for '{key}' should be a list, got {type(v).__name__}")
    return errors

def main():
    axioms_doc = yload(AXIOMS_FILE)
    axioms, axioms_by_no = extract_axioms(axioms_doc, AXIOMS_FILE.name)

    map_doc = yload(MAP_FILE)
    shepherds, ax_to_sp = extract_map(map_doc)

    errs = []
    errs += check_shepherd_axioms(shepherds, axioms_by_no)
    errs += check_summary_map(ax_to_sp, axioms_by_no)

    if errs:
        print("AXIOM VALIDATION: FAIL\n")
        for e in errs:
            print(f"- {e}")
        sys.exit(1)
    else:
        print("AXIOM VALIDATION: OK")
        print(f"- Loaded {len(axioms)} axioms")
        print(f"- Checked {len(shepherds)} shepherd entries")
        print(f"- Checked {len(ax_to_sp)} summary map keys")

if __name__ == "__main__":
    main()
