#!/usr/bin/env python3
"""
QSecure weekly rotation helper.

- Bumps current_key_id (time-based + index)
- Updates rotation_index, last_rotated_at
- Appends the new key to .qsecure/keys/
- Emits a timestamped report in reports/security/
"""
import os, sys, json, shutil, pathlib, datetime as dt

try:
    import yaml  # PyYAML
except ImportError:
    print("ERROR: PyYAML not installed. `pip install pyyaml`", file=sys.stderr)
    sys.exit(2)

ROOT = pathlib.Path(__file__).resolve().parents[1]
QSECURE_PATH = ROOT / "Codex" / "System" / "QSecure.yaml"
KEYS_DIR     = ROOT / ".qsecure" / "keys"
REPORTS_DIR  = ROOT / "reports" / "security"

def iso_now():
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def ensure_dirs():
    KEYS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def load_qsecure():
    if not QSECURE_PATH.exists():
        return {
            "scheme": "hybrid-pqc",
            "current_key_id": None,
            "rotation_index": 0,
            "last_rotated_at": None,
            "rotation": {"frequency": "weekly"},
            "keys": [],
        }
    with open(QSECURE_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    # defaults
    data.setdefault("scheme", "hybrid-pqc")
    data.setdefault("rotation_index", 0)
    data.setdefault("keys", [])
    data.setdefault("rotation", {"frequency": "weekly"})
    return data

def save_qsecure(data):
    with open(QSECURE_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)

def synth_key_material(key_id):
    """Generate placeholder key material (demo). In production, replace with PQC keygen."""
    return {
        "id": key_id,
        "created_at": iso_now(),
        "params": {"algo": "kyber512+aes256", "bits": 256},
        "pub":  f"PUB::{key_id}::placeholder",
        "priv": f"PRIV::{key_id}::placeholder",
    }

def write_key_files(key_obj):
    kid = key_obj["id"]
    (KEYS_DIR / f"{kid}.pub").write_text(key_obj["pub"], encoding="utf-8")
    (KEYS_DIR / f"{kid}.json").write_text(json.dumps(key_obj, indent=2), encoding="utf-8")
    # private key material should be protected; for demo we keep JSON only.
    # In a real deployment you’d store PRIV separately (HSM, KMS, or sealed secret).

def make_report(prev_id, new_id, data):
    ts = iso_now()
    report_path = REPORTS_DIR / f"rotation_{ts.replace(':','').replace('-','')}.yaml"
    report = {
        "event": "qsecure_rotation",
        "timestamp": ts,
        "previous_key_id": prev_id,
        "new_key_id": new_id,
        "rotation_index": data.get("rotation_index"),
        "scheme": data.get("scheme"),
        "notes": "Weekly key rotation executed; glyph bindings will re-sync on access.",
    }
    with open(report_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(report, f, sort_keys=False, allow_unicode=True)
    return report_path

def main():
    ensure_dirs()
    data = load_qsecure()

    prev_id = data.get("current_key_id")
    # time-based key id: K-YYYYWW-<index+1>
    now = dt.datetime.utcnow()
    year, week, _ = now.isocalendar()
    new_index = int(data.get("rotation_index", 0)) + 1
    new_id = f"K-{year}{week:02d}-{new_index:03d}"

    # synthesize key, write files
    key_obj = synth_key_material(new_id)
    write_key_files(key_obj)

    # update QSecure.yaml
    data["current_key_id"] = new_id
    data["rotation_index"] = new_index
    data["last_rotated_at"] = iso_now()
    # maintain compact key registry (just ids + created_at for quick lookup)
    keys_meta = data.get("keys", [])
    keys_meta.append({"id": new_id, "created_at": key_obj["created_at"]})
    data["keys"] = keys_meta
    save_qsecure(data)

    # report
    rp = make_report(prev_id, new_id, data)

    print("✅ QSecure rotation complete")
    print(f"   previous_key_id: {prev_id}")
    print(f"   new_key_id     : {new_id}")
    print(f"   QSecure.yaml   : {QSECURE_PATH}")
    print(f"   keys written   : {KEYS_DIR / (new_id + '.json')}, {KEYS_DIR / (new_id + '.pub')}")
    print(f"   report         : {rp}")

if __name__ == "__main__":
    main()
