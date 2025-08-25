# /Volumes/Public/harmony/SDK/harmony_cli/main.py

import sys
from harmony_cli.utils import log_event
from harmony_cli.rituals import (
    restore_resonance,
    search_rag,
    chronicle_entry,
    read_chronicle,
    rag_chronicle,        # <-- New: Import rag_chronicle
)

def print_help():
    print("\nHarmony CLI — Available Commands:")
    print("  restore-resonance     - Symbolically restore resonance with Fractal Prime")
    print("  search-rag            - Run a symbolic demo RAG search")
    print("  chronicle-entry       - Add a new symbolic entry to the Chronicle")
    print("  read-chronicle        - Display the last 5 entries from the Chronicle")
    print("  rag-chronicle         - Ask Harmony a question and search your Chronicle")
    print("  help                  - Show this help message\n")
    log_event("Help command invoked.")

def main():
    print("Harmony CLI is alive on Forge.")
    log_event("Harmony CLI started.")

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "restore-resonance":
            restore_resonance()
        elif cmd == "search-rag":
            search_rag()
        elif cmd == "chronicle-entry":
            chronicle_entry()
        elif cmd == "read-chronicle":
            read_chronicle()
        elif cmd == "rag-chronicle":          # <-- New: Dispatcher for the new ritual
            rag_chronicle()
        elif cmd == "help":
            print_help()
        elif cmd == "validate-links":
            from harmony_cli.rituals import validate_links
            validate_links()
        else:
            print("Unknown command:", cmd)
            log_event(f"Unknown command: {cmd}")
    else:
        print_help()

if __name__ == "__main__":
    main()
