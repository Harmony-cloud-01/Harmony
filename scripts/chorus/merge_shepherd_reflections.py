#!/usr/bin/env python3
"""
Merge Shepherd Reflections:
Scans reflections logs for Confucian overlay prompts and emits a weekly 'Confucian Chorus' block.
"""
import sys, json
from datetime import datetime, timezone
from pathlib import Path

REFLECTIONS = Path("Codex/Reflections/Shepherd.json")
OUT = Path("reports/Confucian_Chorus_Weekly.md")

def extract_blocks():
    if not REFLECTIONS.exists(): return []
    obj = json.loads(REFLECTIONS.read_text(encoding="utf-8"))
    items = obj if isinstance(obj, list) else obj.get("entries", [])
    out=[]
    for e in items:
        msg = e.get("text") or e.get("message","")
        if "FCP" in msg or "virtue" in msg or "Confucian" in msg:
            out.append({"timestamp": e.get("timestamp"), "text": msg})
    return out

def main():
    blocks = extract_blocks()
    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    lines = [f"# Confucian Chorus — Weekly Merge\n\n**Generated (UTC):** {ts}\n\n"]
    if not blocks: lines.append("_No Confucian overlay reflections found this week._\n")
    else:
        for b in blocks[-10:]:
            lines.append(f"- {b.get('timestamp')}: {b.get('text')}\n")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")
if __name__=="__main__": sys.exit(main())
