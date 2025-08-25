# scripts/speech_capture_test.py

import speech_recognition as sr
from MMSI.modules.symbolic_bridge import handle_symbolic_input
from MMSI.modules.reflection_logger import log_reflection

def main():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        print("🎙️ Listening... say something.")
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        print(f"🗣️ You said: {text}")

        # 📝 Log reflection to Mona’s memory
        log_reflection(
            input_text=text,
            response_text="Symbolic voice input captured on Aletheia.",
            tags=["@voice", "@symbolic", "@Aletheia"],
            shen_level=0
        )

        # 🌀 Trigger symbolic input handler (e.g., start passage, reopen path)
        handle_symbolic_input(text)

    except sr.UnknownValueError:
        print("⚠️ Could not understand audio.")
    except sr.RequestError as e:
        print(f"❌ Could not request results from recognition service; {e}")

if __name__ == "__main__":
    main()
