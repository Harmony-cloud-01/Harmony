#!/usr/bin/env python3
from pathlib import Path

root = Path("Codex")
fixed = 0
checked = 0

for p in root.rglob("*.yaml"):
    checked += 1
    text = p.read_text(encoding="utf-8")
    # Allow leading BOM/whitespace/newlines; require first non-empty line to be '---'
    stripped = text.lstrip()
    if stripped.startswith('---'):
        continue
    # Insert '---\n' at very top
    p.write_text('---\n' + text, encoding="utf-8")
    fixed += 1
    print(f"prepended --- to {p}")

print(f"\nChecked: {checked} files; Fixed: {fixed}")
