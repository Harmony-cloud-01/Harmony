#!/usr/bin/env python3
"""
Tighten YAML flow-style spacing across Codex:
- "{  foo: 1 }"  -> "{foo: 1}"
- "[  a,  b ]"   -> "[a, b]"
- ",   "         -> ", "   (single space after comma)
It only rewrites files that actually change and prints a summary.
"""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("Codex")

def tighten_flow_spaces(text: str) -> str:
    s = text

    # 1) Tighten spaces just inside braces/brackets
    #    Examples: "{  a: 1}" -> "{a: 1}", "[  a, b ]" -> "[a, b]"
    s = re.sub(r"\{\s+", "{", s)
    s = re.sub(r"\s+\}", "}", s)
    s = re.sub(r"\[\s+", "[", s)
    s = re.sub(r"\s+\]", "]", s)

    # 2) Normalize multiple spaces after commas in flow contexts:
    #    ",    " -> ", "
    #    We avoid touching line starts; this is a mild heuristic.
    s = re.sub(r",\s{2,}", ", ", s)

    return s

def main():
    yaml_paths = list(ROOT.rglob("*.yaml")) + list(ROOT.rglob("*.yml"))
    changed = 0
    checked = 0
    for p in sorted(yaml_paths):
        try:
            original = p.read_text(encoding="utf-8")
        except Exception:
            continue
        checked += 1
        tightened = tighten_flow_spaces(original)
        if tightened != original:
            p.write_text(tightened, encoding="utf-8")
            changed += 1
            print(f"[TIGHTENED] {p}")
    print(f"\nChecked: {checked} files; Tightened: {changed}")

if __name__ == "__main__":
    main()
