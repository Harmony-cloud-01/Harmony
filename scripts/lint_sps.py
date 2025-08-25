import os
import yaml

# Corrected path
sps_dir = "codex/sps"
report = []

# Expected fields in SP files
required_fields = ['title', 'domains', 'functions']

for filename in os.listdir(sps_dir):
    if filename.endswith(".yaml"):
        filepath = os.path.join(sps_dir, filename)
        try:
            with open(filepath, 'r') as file:
                data = yaml.safe_load(file)

            if not isinstance(data, dict):
                report.append(f"⚠️ Skipping non-dict YAML: {filename}")
                continue

            repaired = False
            for field in required_fields:
                if field not in data:
                    data[field] = f"[[ placeholder {field} ]]"
                    report.append(f"🩺 Missing `{field}` in {filename} → inserting placeholder")
                    repaired = True

            if repaired:
                with open(filepath, 'w') as file:
                    yaml.dump(data, file, sort_keys=False)
                report.append(f"✅ Repaired: {filename}")
            else:
                report.append(f"✅ OK: {filename}")

        except Exception as e:
            report.append(f"❌ Error processing {filename}: {e}")

# Print final report
print("\n".join(report))
