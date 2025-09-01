#!/usr/bin/env python3
from pathlib import Path
import argparse
from ruamel.yaml import YAML

parser = argparse.ArgumentParser()
parser.add_argument("--force", action="store_true", help="Re-dump all YAMLs even if they look fine.")
args = parser.parse_args()

root = Path("Codex")
yaml = YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=2, offset=0)
yaml.width = 1000000   # don't wrap
yaml.explicit_start = True  # add '---'

fixed = 0
checked = 0
for p in sorted(root.rglob("*.yaml")):
    checked += 1
    txt = p.read_text(encoding="utf-8")
    try:
        data = yaml.load(txt)
    except Exception as e:
        print(f"[SKIP ] {p} (parse error: {e})")
        continue

    # Always re-dump when --force; otherwise only when header missing
    needs = args.force or (not txt.lstrip().startswith("---"))
    if not needs:
        # cheap heuristic: ensure indentation is normalized by comparing a re-dump in-memory
        from io import StringIO
        buf = StringIO()
        yaml.dump(data, buf)
        if buf.getvalue() != txt if isinstance(txt, str) else txt.decode("utf-8"):
            needs = True

    if needs:
        # Write back normalized
        with p.open("w", encoding="utf-8", newline="\n") as f:
            yaml.dump(data, f)
        print(f"[FIXED] {p}")
        fixed += 1
    else:
        print(f"[OK   ] {p}")

print(f"\nChecked: {checked}; Normalized: {fixed}")
