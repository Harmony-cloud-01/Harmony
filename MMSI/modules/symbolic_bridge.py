import datetime

def trigger_symbolic_bridge():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"🌀 Ritual triggered at {now} — Path reopened in symbolic bridge.")
    # Optional: integrate with Harmony CLI here
    # Example: os.system("harmony chronicle-entry 'The path reopened via MMSI trigger.'")
# ~/Projects/Harmony/MMSI/modules/symbolic_bridge.py

from subprocess import run

def trigger_ritual(phrase):
    if "reopen the path" in phrase.lower():
        run(["harmony", "chronicle-entry"], input=b"The voice reopened the path.", check=True)

