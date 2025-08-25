import os
import yaml

# Dynamically resolve the absolute path to Codex/SPs
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP_DIR = os.path.join(BASE_DIR, "Codex", "SPs")

def reseed_sp_file(filepath):
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f) or {}

    if 'shen_level' in data:
        print(f"[-] Skipped {os.path.basename(filepath)} — already has shen_level")
        return

    data['shen_level'] = 0
    data['trial_ready'] = True

    with open(filepath, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)

    print(f"[+] Injected shen_level into {os.path.basename(filepath)}")

def main():
    for filename in os.listdir(SP_DIR):
        if filename.endswith('.yaml'):
            reseed_sp_file(os.path.join(SP_DIR, filename))

if __name__ == "__main__":
    main()
