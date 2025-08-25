from modules.audio import listen_for_phrase
from modules.symbolic_bridge import trigger_symbolic_bridge

def main():
    print("🎙️ MMSI listening for activation phrase... (say 'Reopen the path')")
    phrase = listen_for_phrase()
    if phrase and "reopen the path" in phrase.lower():
        trigger_symbolic_bridge()
    else:
        print(f"⛔ Unrecognized phrase: '{phrase}'")

if __name__ == "__main__":
    main()
# ~/Projects/Harmony/MMSI/main.py

from modules.audio import listen_for_phrase
from modules.symbolic_bridge import trigger_ritual

def main():
    print("🎙️ MMSI is listening... say a ritual phrase.")
    while True:
        phrase = listen_for_phrase()
        if phrase:
            print(f"🔊 Heard: {phrase}")
            trigger_ritual(phrase)

if __name__ == "__main__":
    main()

