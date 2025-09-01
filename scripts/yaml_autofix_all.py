#!/usr/bin/env python3
import sys
from pathlib import Path
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

yaml = YAML()
yaml.version = (1, 2)
yaml.preserve_quotes = True
yaml.width = 120
yaml.indent(mapping=2, sequence=2, offset=0)
yaml.default_flow_style = False

TRUTHY = {"yes", "no", "on", "off", "Yes", "No", "On", "Off",
          "YES", "NO", "ON", "OFF"}

def quote_truthy_scalars(node):
    # Recursively quote bare truthy/barewords that yamllint dislikes
    if isinstance(node, dict):
        for k, v in list(node.items()):
            # if key itself is truthy-like (rare), quote it by replacing the key
            if isinstance(k, str) and k in TRUTHY:
                newk = DoubleQuotedScalarString(k)
                node[newk] = node.pop(k)
                k = newk
            quote_truthy_scalars(v)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            if isinstance(v, str) and v in TRUTHY:
                node[i] = DoubleQuotedScalarString(v)
            else:
                quote_truthy_scalars(v)

def fix_shepherd_map_tree(tree):
    """
    Schema tweaks for Codex/Core/Laws/Shepherd_Map.yaml:
      - rename item key 'no' -> 'num' inside axioms/chrs_laws arrays
      - ensure coverage_index lists are plain strings (already fine)
    """
    if not isinstance(tree, dict):
        return
    if "shepherds" in tree and isinstance(tree["shepherds"], list):
        for sh in tree["shepherds"]:
            if not isinstance(sh, dict):
                continue
            for section in ("axioms", "chrs_laws"):
                if section in sh and isinstance(sh[section], list):
                    for item in sh[section]:
                        if isinstance(item, dict) and "no" in item:
                            # rename key
                            item["num"] = item.pop("no")
    # Also quote any truthy/barewords throughout
    quote_truthy_scalars(tree)

def ensure_docstart(text: str) -> str:
    stripped = text.lstrip()
    return text if stripped.startswith("---") else ("---\n" + text)

def process_file(p: Path):
    raw = p.read_text(encoding="utf-8")
    raw = ensure_docstart(raw)

    # Parse -> mutate -> dump (block style)
    data = yaml.load(raw)
    # Special handling for Shepherd_Map
    if str(p).endswith("Codex/Core/Laws/Shepherd_Map.yaml"):
        fix_shepherd_map_tree(data)
    else:
        quote_truthy_scalars(data)

    # Write back
    from io import StringIO
    buf = StringIO()
    yaml.dump(data, buf)
    out = buf.getvalue().rstrip() + "\n"
    p.write_text(out, encoding="utf-8")
    return True

def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "Codex")
    files = list(root.rglob("*.yaml")) + list(root.rglob("*.yml"))
    fixed = 0
    for p in files:
        try:
            if process_file(p):
                fixed += 1
                print(f"[FIXED] {p}")
        except Exception as e:
            print(f"[SKIP ] {p} ({e})")
    print(f"\nScanned: {len(files)}; Fixed: {fixed}")

if __name__ == "__main__":
    main()
