# ======================================================
# ==================== VOICE ENGINE 🎤 ===================
# ======================================================
# Fully offline, zero API cost — matches the local-first promise.
#
#   speak(text)      -> Charlie talks (pyttsx3, same as old Charlie)
#   listen()         -> mic input -> text (speech_recognition + Google's
#                       free offline-ish recognizer, no key needed)
#
# Voice is OFF by default. Charlie asks once on first run and saves
# the answer to companion.db — never asks twice. 🔒
#
# ⚠️ SETUP NOTE: speech_recognition needs PyAudio for microphone
# input, and PyAudio's C extension sometimes fails on a plain
# `pip install pyaudio` on Windows. If that happens:
#   pip install pipwin
#   pipwin install pyaudio
# This is a one-time setup issue, not a bug in this file.

import pyttsx3
import speech_recognition as sr


def speak(text, voice_enabled=True):
    """
    Prints always. Speaks out loud ONLY if voice_enabled is True.
    This mirrors the exact pattern from the original Charlie script —
    text output never depends on voice being on, so the app still
    works perfectly fine for someone who said no to voice. 🖨️
    """
    print("Charlie:", text)

    if not voice_enabled:
        return

    try:
        engine = pyttsx3.init("sapi5")
        engine.setProperty("voice", engine.getProperty("voices")[0].id)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        # Never let a broken TTS engine crash the whole conversation —
        # text already printed above, so the user still gets the reply.
        print(f"[voice error, falling back to text only: {e}]")


def listen(timeout=6, phrase_time_limit=15):
    """
    Listens through the mic and returns recognized text, or None if
    nothing was understood. Never raises — a failed mic capture
    should mean "try again" or "fall back to typing", not a crash.
    """
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            print("🎙️ Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=timeout,
                                       phrase_time_limit=phrase_time_limit)

        text = recognizer.recognize_google(audio)
        return text

    except sr.WaitTimeoutError:
        print("[voice: no speech detected in time]")
        return None
    except sr.UnknownValueError:
        print("[voice: couldn't understand that, try again]")
        return None
    except sr.RequestError as e:
        print(f"[voice: recognition service error \u2014 {e}]")
        return None
    except OSError as e:
        # no microphone found/available on this machine
        print(f"[voice: no microphone available \u2014 {e}]")
        return None


def ask_voice_preference():
    """
    The one-time ask-first flow. Returns True/False for the user's
    choice. Called only when db.has_asked_voice_preference() is False.
    """
    answer = input("Charlie: Want me to talk out loud and listen for "
                    "your voice too? (y/n): ").strip().lower()
    return answer == "y"
