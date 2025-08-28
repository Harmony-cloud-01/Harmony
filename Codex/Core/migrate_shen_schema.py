#!/usr/bin/env python3
# scripts/migrate_shen_schema.py
import os, sys, glob, yaml, datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SP_DIR = os.path.join(ROOT, "Codex", "SPs")
REPORT_PATH = os.path.join(ROOT, "reports", "shen_migration_report.txt")

DEFAULT_SHEN = {
    "level": 0,
    "xp": 0,
    "tier": "Novice",
    "last_trial": None,        # or {"id": "TRIAL_...", "at": "..."} after trials
    "history": [],             # list of {"at", "trial_id", "delta_level", "delta_xp", "notes"}
    "protections": {
        "consent_layer": True,
        "non_coercion": True,
        "recall_guard": True
    }
}

def ensure_shen_block(data):
    changed = False

    # 1) Migrate legacy flat field -> shen.level
    if "shen_level" in data and (data.get("shen") is None or not isinstance(data.get("shen"), dict)):
        lvl = data.get("shen_level") or 0
        data["shen"] = dict(DEFAULT_SHEN)
        data["shen"]["level"] = int(lvl) if isinstance(lvl, int) else 0
        changed = True
        del data["shen_level"]

    # 2) If no shen block, create default
    if "shen" not in data or not isinstance(data["shen"], dict):
        data["shen"] = dict(DEFAULT_SHEN)
        changed = True

    # 3) Ensure required keys exist within shen
    shen = data["shen"]
    for k, v in DEFAULT_SHEN.items():
        if k not in shen or shen[k] is None:
            # copy nested dicts; avoid shared references
            shen[k] = dict(v) if isinstance(v, dict) else (list(v) if isinstance(v, list) else v)
            changed = True

    # 4) Normalize types
    if not isinstance(shen.get("level", 0), int):
        try:
            shen["level"] = int(shen["level"])
            changed = True
        except Exception:
            shen["level"] = 0
            changed = True
    if not isinstance(shen.get("xp", 0), int):
        try:
            shen["xp"] = int(shen["xp"])
            changed = True
        except Exception:
            shen["xp"] = 0
            changed = True

    # 5) Derive tier from level (simple mapping; UI refinement comes from System/Shen_Leveling.yaml)
    level = shen["level"]
    tier = (
        "Novice" if level <= 2 else
        "Adept"  if level <= 5 else
        "Seer"   if level <= 8 else
        "Sage"   if level <= 12 else
        "Silent"
    )
    if shen.get("tier") != tier:
        shen["tier"] = tier
        changed = True

    return changed

def main():
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    changed_files, skipped, errors = [], [], []

    for path in sorted(glob.glob(os.path.join(SP_DIR, "*.yaml"))):
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            data = yaml.safe_load(text)
            if not isinstance(data, dict):
                skipped.append((path, "not a YAML mapping"))
                continue

            changed = ensure_shen_block(data)

            if changed:
                with open(path, "w", encoding="utf-8") as f:
                    yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
                changed_files.append(os.path.relpath(path, ROOT))
            else:
                skipped.append((os.path.relpath(path, ROOT), "no change"))

        except Exception as e:
            errors.append((os.path.relpath(path, ROOT), str(e)))

    # Report
    now = datetime.datetime.utcnow().isoformat() + "Z"
    with open(REPORT_PATH, "w", encoding="utf-8") as r:
        r.write(f"Shen migration report — {now}\n\n")
        r.write("Changed files:\n")
        if changed_files:
            for p in changed_files:
                r.write(f"  - {p}\n")
        else:
            r.write("  <none>\n")

        r.write("\nNo-change files:\n")
        if skipped:
            for p, why in skipped:
                r.write(f"  - {p} — {why}\n")
        else:
            r.write("  <none>\n")

        r.write("\nErrors:\n")
        if errors:
            for p, err in errors:
                r.write(f"  - {p} — {err}\n")
        else:
            r.write("  <none>\n")

    print(f"✅ Migration complete. See {REPORT_PATH}")
    if errors:
        print("⚠️ Some files had issues. Check the report for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
