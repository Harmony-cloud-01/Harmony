#!/usr/bin/env python3
"""
scripts/merge_daily_law_logs.py

Merge Codex/Reflections/daily_law_logs into a weekly master log.
"""

import os, glob, yaml
from datetime import datetime

# Constants
DAILY_DIR   = "Codex/Reflections/daily_law_logs"
MASTER_PATH = "Codex/Reflections/weekly_law_log.yaml"

def load_yaml(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"⚠️  Error loading {path}: {e}")
        return {}

def save_yaml(path, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)

def merge_logs():
    merged = {"merged_on": datetime.utcnow().isoformat()+"Z", "entries": []}
    files = sorted(glob.glob(f"{DAILY_DIR}/*.yaml"))
    for f in files:
        data = load_yaml(f)
        if data:
            merged["entries"].append({"source": os.path.basename(f), **data})
    return merged

def main(dry_run=False):
    merged = merge_logs()
    if dry_run:
        print(yaml.safe_dump(merged, sort_keys=False, allow_unicode=True))
    else:
        os.makedirs(os.path.dirname(MASTER_PATH), exist_ok=True)
        save_yaml(MASTER_PATH, merged)
        print(f"✅ Merged {len(merged['entries'])} daily logs → {MASTER_PATH}")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Show merged output, don’t save")
    args = ap.parse_args()
    main(dry_run=args.dry_run)
