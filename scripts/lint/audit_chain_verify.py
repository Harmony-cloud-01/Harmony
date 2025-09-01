#!/usr/bin/env python3
"""
Audit Chain Verify:
Placeholder integrity checker for QSecure/GlyphCrypt chain over audits + reports.
Currently: hashes files and prints a digest list (for CI diffing).
"""
import sys, hashlib, glob
from pathlib import Path

def digest(p:Path):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""): h.update(chunk)
    return h.hexdigest()

def main():
    targets = []
    targets += glob.glob("Codex/Core/*Audit.yaml")
    targets += glob.glob("reports/*.json")
    targets += glob.glob("reports/*.md")
    if not targets:
        print("WARN: no audit/report files found"); return 0
    lines=["# Audit Chain Digests\n"]
    for t in sorted(targets):
        lines.append(f"- {t} · sha256={digest(Path(t))}\n")
    Path("reports/Audit_Chain_Digests.md").write_text("".join(lines), encoding="utf-8")
    print("Wrote reports/Audit_Chain_Digests.md"); return 0

if __name__=="__main__": sys.exit(main())
