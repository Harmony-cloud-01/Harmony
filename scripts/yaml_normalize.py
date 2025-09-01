#!/usr/bin/env python3
"""
Normalize YAML in Codex/*:
- Ensure leading '---'
- Re-emit with consistent 2/2 indent (maps/sequences)
- Preserve order & comments where possible
Skips files that can't be parsed; prints them for manual follow-up.
"""
from pathlib import Path
from ruamel.yaml import YAML

TARGET = Path("Codex")
yaml = YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=2, offset=2)
yaml.width = 120  # don't hard-wrap aggressively

fixed, skipped = [], []

for p in sorted(TARGET.rglob("*.yml*")):
    text = p.read_text(encoding="utf-8")
    # make sure we have a doc-start
    if not text.lstrip().startswith("---"):
        text = "---\n" + text
    try:
        data = yaml.load(text)
        # If file was empty or only comments, keep header
        if data is None:
            p.write_text("---\n", encoding="utf-8")
            fixed.append(str(p))
            continue
        with p.open("w", encoding="utf-8") as f:
            yaml.dump(data, f)
        fixed.append(str(p))
    except Exception as e:
        skipped.append((str(p), str(e)))

print(f"[OK] normalized: {len(fixed)} files")
if skipped:
    print("[SKIP] manual follow-up needed:")
    for path, err in skipped:
        print(f"  - {path}: {err}")
