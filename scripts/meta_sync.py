import os
import hashlib
import yaml

# Updated file paths relative to the Harmony project root
FILES_TO_TRACK = {
    "codex_taoica": "Codex/Theory/Codex_Taoica.md",
    "spirit_trials": "Codex/Core/Spirit_Trials.yaml",
    "sp_metrics": "Codex/Core/SP_Metrics.yaml",
    "harmony_manifest": "Codex/Manifest/Harmony_v2.1_Spirit.md",
    "taoic_law_8": "Codex/Laws/Law_8.yml"  # note the .yml extension
}

META_PATH = "Codex/System/MetaField.yaml"

def file_hash(path):
    """Return SHA256 hash of the given file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

def update_meta_field():
    updated = False

    # Load existing meta field if it exists
    if os.path.exists(META_PATH):
        with open(META_PATH, 'r') as f:
            meta = yaml.safe_load(f) or {}
    else:
        meta = {}

    for key, path in FILES_TO_TRACK.items():
        if not os.path.exists(path):
            print(f"[!] File not found for {key}: {path}")
            continue

        new_hash = file_hash(path)
        current_hash = meta.get(key, {}).get("hash", "")

        if new_hash != current_hash:
            print(f"[+] Updated {key} with new hash.")
            meta[key] = {
                "path": path,
                "hash": new_hash
            }
            updated = True
        else:
            print(f"[-] Skipped {key} — already synced.")

    if updated:
        with open(META_PATH, 'w') as f:
            yaml.dump(meta, f, sort_keys=False)
        print("\n✅ MetaField.yaml updated.")
    else:
        print("\n✔ All files already synced. No changes.")

if __name__ == "__main__":
    update_meta_field()
