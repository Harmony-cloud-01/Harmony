import speech_recognition as sr

def listen_for_phrase():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎧 Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source)
        print("🔊 Listening now...")
        try:
            audio = recognizer.listen(source, timeout=5)
            print("📡 Processing...")
            return recognizer.recognize_google(audio)
        except sr.WaitTimeoutError:
            print("⚠️ No speech detected.")
        except sr.UnknownValueError:
            print("🤷 Could not understand.")
        except sr.RequestError as e:
            print(f"❌ API error: {e}")
    return None
# ~/Projects/Harmony/MMSI/modules/audio.py

import speech_recognition as sr

def listen_for_phrase():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            print("🌀 Listening...")
            audio = r.listen(source, timeout=5)
            return r.recognize_google(audio)
        except Exception as e:
            return None

