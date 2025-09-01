#!/usr/bin/env python3
from pathlib import Path
from ruamel.yaml import YAML
import sys
yaml = YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=2, offset=0)
yaml.width = 120

def coerce(v):
    from ruamel.yaml.scalarstring import ScalarString
    if isinstance(v, dict):
        return {k: coerce(v[k]) for k in v}
    if isinstance(v, list):
        return [coerce(x) for x in v]
    if isinstance(v, (str, ScalarString)):
        s = str(v).strip().lower()
        if s in ("yes","true","on"):  return True
        if s in ("no","false","off"): return False
    return v

def normalize(p):
    t = p.read_text(encoding="utf-8")
    has_doc = t.lstrip().startswith('---')
    try:
        data = yaml.load(t)
    except Exception as e:
        print(f"[SKIP ] {p} (parse error: {e})", file=sys.stderr)
        return False
    data = coerce(data)
    tmp = p.with_suffix(p.suffix+".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        if not has_doc: f.write("---\n")
        yaml.dump(data, f)
    tmp.replace(p)
    print(f"[FIXED] {p}")
    return True

count=0
for p in sorted(Path("Codex").rglob("*.yaml")):
    if normalize(p): count+=1
print(f"\nNormalized {count} YAML files.")
