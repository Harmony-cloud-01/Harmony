#!/usr/bin/env python3
# Round-trip load+dump all YAML to normalize:
# - explicit '---' document start
# - 2-space mapping + sequence indentation
# - CRLF stripped
# - preserve comments & key order
import sys, re
from pathlib import Path
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import PreservedScalarString

def normalize_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    # quick sanity: skip clearly non-YAML
    if not text.strip():
        return False
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.explicit_start = True          # add '---'
    yaml.width = 220                    # cooperate with line-length rule
    yaml.indent(mapping=2, sequence=2, offset=2)

    try:
        data = yaml.load(text)
    except Exception:
        # leave files that still fail to parse for manual review
        return False

    # Convert any multiline plain strings to block scalars to avoid line-length/indent grief
    def to_block(node):
        if isinstance(node, dict):
            for k, v in list(node.items()):
                node[k] = to_block(v)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                node[i] = to_block(v)
        elif isinstance(node, str) and ("\n" in node):
            return PreservedScalarString(node)
        return node

    data = to_block(data)

    # Write back
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        yaml.dump(data, f)
    new = tmp.read_text(encoding="utf-8").replace("\r\n", "\n")
    tmp.unlink(missing_ok=True)

    if new != text:
        path.write_text(new, encoding="utf-8")
        return True
    return False

def main():
    roots = [Path(p) for p in (sys.argv[1:] or ["Codex"])]
    changed = 0
    scanned = 0
    exts = {".yaml", ".yml"}
    for root in roots:
        for p in root.rglob("*"):
            if p.is_file() and p.suffix.lower() in exts:
                scanned += 1
                try:
                    if normalize_file(p):
                        print(f"[FIXED] {p}")
                        changed += 1
                except Exception as e:
                    print(f"[SKIP ] {p} ({e})")
    print(f"\nScanned: {scanned}; Fixed: {changed}")

if __name__ == "__main__":
    main()
