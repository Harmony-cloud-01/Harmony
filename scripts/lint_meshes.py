import os
import yaml

MESHES_DIR = "Codex/Meshes"
REQUIRED_KEYS = ["name", "title", "purpose", "features", "agents"]

def lint_and_repair_meshes():
    repaired = 0
    skipped = 0
    for filename in os.listdir(MESHES_DIR):
        if not filename.endswith(".yaml"):
            continue

        path = os.path.join(MESHES_DIR, filename)
        with open(path, "r") as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(f"❌ Invalid YAML: {filename} — {e}")
                skipped += 1
                continue

        if not isinstance(data, dict):
            print(f"⚠️ Skipping non-dict YAML: {filename}")
            skipped += 1
            continue

        modified = False
        for key in REQUIRED_KEYS:
            if key not in data:
                print(f"🩺 Missing `{key}` in {filename} → inserting placeholder")
                data[key] = "FIXME" if key in ["purpose"] else []

                if key in ["name", "title"]:
                    data[key] = filename.replace(".yaml", "")
                modified = True

        if modified:
            with open(path, "w") as f:
                yaml.dump(data, f, sort_keys=False, allow_unicode=True)
            print(f"✅ Repaired: {filename}")
            repaired += 1
        else:
            print(f"✅ OK: {filename}")

    print(f"\n🎯 Summary: {repaired} repaired, {skipped} skipped.")

if __name__ == "__main__":
    lint_and_repair_meshes()
