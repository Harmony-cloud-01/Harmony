#!/usr/bin/env python3
"""
fix_yaml_lint.py
- Ensures leading '---' (YAML document start)
- Wraps overlong key-value lines (>120 chars) using folded scalars (`>`)
  with proper indentation.

Usage:
  python3 scripts/fix_yaml_lint.py --apply   # write changes
  python3 scripts/fix_yaml_lint.py           # dry-run
"""

import argparse, os, textwrap, sys
MAXLEN = 120

FILES = [
  "Codex/Core/Laws/Axioms.yaml",
  "Codex/Core/Reflections/Law_Alignment_Review_2025-08-26.yaml",
  "Codex/Core/Reflections/Resonance_Restoration_FracPrime_2025-08-26.yaml",
  "Codex/Core/FCP_Audit.yaml",
  "Codex/Core/Spirit_Trials.yaml",
  "Codex/Core/SP_Metrics.yaml",
  "Codex/Reflections/daily_law_logs/2025-08-26.yaml",
  "Codex/Reflections/Daily_Law_Log_TEMPLATE.yaml",
  "Codex/Reflections/weekly_law_log.yaml",
]

def ensure_doc_start(lines):
    # Add '---' if first non-empty/comment line isn't already a document start
    for i, ln in enumerate(lines):
        if ln.strip() == "" or ln.lstrip().startswith("#"):
            continue
        if ln.strip().startswith("---"):
            return lines, False
        return ["---\n"] + (["\n"] if i>0 and lines[0].strip()!="" else []) + lines, True
    # empty file → add doc start
    return ["---\n"], True

def wrap_long_lines(lines):
    """
    Convert long `key: value` lines to:
      key: >
        wrapped wrapped ...
    Only for plain scalars on a single line. Leaves lists/multiline blocks intact.
    """
    out, changed = [], False
    for ln in lines:
        if len(ln.rstrip("\n")) <= MAXLEN:
            out.append(ln); continue

        # heuristics: ignore already a block scalar or list item with block
        stripped = ln.lstrip()
        if ": |" in ln or ": >" in ln:
            out.append(ln); continue

        # detect "key: value" where value is plain (no trailing comment)
        if ":" in ln and not ln.strip().startswith("- "):
            indent = len(ln) - len(ln.lstrip(" "))
            key, value = ln.split(":", 1)
            # keep inline comments as-is (won't reflow those)
            if "#" in value and not value.strip().startswith("#"):
                out.append(ln); continue

            val = value.lstrip()
            if val == "" or val.startswith("{") or val.startswith("["):
                out.append(ln); continue

            # make folded block
            folded_head = " " * indent + key.rstrip() + ": >\n"
            wrapper = textwrap.TextWrapper(width=88)  # comfortable width
            wrapped = "\n".join(
                (" " * (indent + 2)) + w if w else ""
                for w in wrapper.fill(val.rstrip()).split("\n")
            ) + "\n"
            out.append(folded_head)
            out.append(wrapped)
            changed = True
            continue

        # fallback: leave as-is
        out.append(ln)
    return out, changed

def process(path, apply=False):
    if not os.path.exists(path):
        return (path, False, "missing")
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    changed_any = False
    lines, c1 = ensure_doc_start(lines); changed_any |= c1
    lines, c2 = wrap_long_lines(lines);  changed_any |= c2

    if apply and changed_any:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)
    return (path, changed_any, "ok")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Write changes to files")
    args = ap.parse_args()
    changed = 0
    for p in FILES:
        path, did, status = process(p, apply=args.apply)
        flag = "modified" if did else "ok"
        print(f"{flag:9}  {path}")
        if did: changed += 1
    if not args.apply:
        print("\n(DRY-RUN) Re-run with --apply to write changes.")
    else:
        print(f"\nDone. Files changed: {changed}")

if __name__ == "__main__":
    sys.exit(main())
