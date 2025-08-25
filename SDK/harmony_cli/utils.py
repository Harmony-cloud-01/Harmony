# /Volumes/Public/harmony/SDK/harmony_cli/utils.py

def log_event(message):
    with open("/Volumes/Public/harmony/logs/cli.log", "a") as f:
        from datetime import datetime
        f.write(f"[{datetime.now()}] {message}\n")
