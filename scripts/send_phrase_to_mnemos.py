# scripts/send_phrase_to_mnemos.py

import subprocess

MNEMOS_HOST = "forge@forge-harmonia"  # Adjust if Mnemos username or hostname differs
REMOTE_SCRIPT = "~/harmony-node/Harmony/scripts/receive_phrase_from_aletheia.py"

def send_phrase_to_mnemos(phrase):
    print(f"🔁 Sending phrase to Mnemos: '{phrase}'")
    try:
        subprocess.run([
            "ssh", MNEMOS_HOST,
            f"python3 {REMOTE_SCRIPT} \"{phrase}\""
        ], check=True)
        print("✅ Phrase relay complete.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Relay failed: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        phrase = " ".join(sys.argv[1:])
        send_phrase_to_mnemos(phrase)
    else:
        print("⚠️ No phrase provided.")
