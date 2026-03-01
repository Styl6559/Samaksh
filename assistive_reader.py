import cv2
import easyocr
import pyttsx3
import speech_recognition as sr
import openai
import sys
import time
import numpy as np

# --- config ---

OPENAI_API_KEY = "OPENAIKEY"  # only used for the Q&A feature

CAMERA_INDEX = 0              # change if your webcam isn't at index 0

# EasyOCR language codes — add/remove as needed
# 'en', 'hi', 'fr', 'de', 'es', 'ar', 'zh_sim', 'ja' ...
# Full list: https://www.jaided.ai/easyocr/
OCR_LANGUAGES = ["en", "hi"]

MIC_RECORD_SECONDS = 6        # max seconds to wait for a spoken question
STT_LANGUAGE = "hi-IN"        # Google STT hint — "en-US", "hi-IN", "fr-FR" etc.
TTS_RATE = 145                # speaking speed in words per minute


def init_tts():
    engine = pyttsx3.init()  # uses espeak on Pi OS Lite
    engine.setProperty("rate", TTS_RATE)
    engine.setProperty("volume", 1.0)
    # engine.setProperty("voice", "english")  # uncomment to pin a specific voice
    return engine


def speak(engine, text):
    text = (text or "").strip()
    if not text:
        return
    preview = text[:90] + ("…" if len(text) > 90 else "")
    print(f"[SPEAK] {preview}")
    engine.say(text)
    engine.runAndWait()


def capture_image():
    print("[CAM] Opening webcam...")
    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        print(f"[ERROR] Could not open camera (index {CAMERA_INDEX}). Is it plugged in?")
        sys.exit(1)

    time.sleep(1.8)  # sensor needs a moment before the first frame is usable

    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        print("[ERROR] Camera opened but returned no frame.")
        sys.exit(1)

    print("[CAM] Frame captured.")
    return frame


def preprocess_image(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)  # smooths grain before thresholding
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # cv2.imwrite("debug_preprocessed.jpg", binary)  # uncomment to inspect output
    print("[IMG] Preprocessed (grayscale + Otsu threshold).")
    return binary


def load_ocr_reader():
    print(f"[OCR] Loading EasyOCR ({OCR_LANGUAGES}) — first run downloads weights, may take a moment.")
    reader = easyocr.Reader(OCR_LANGUAGES, gpu=False)  # Pi has no GPU
    print("[OCR] Ready.")
    return reader


def extract_text(reader, processed_image):
    print("[OCR] Running OCR...")
    results = reader.readtext(processed_image, detail=0, paragraph=True)
    text = "\n".join(results).strip()

    print("\n--- extracted text ---")
    print(text if text else "(nothing detected)")
    print("----------------------\n")

    return text


def record_question(engine):
    """Record from mic, transcribe via Google STT, return text or None."""
    recognizer = sr.Recognizer()

    speak(engine, "Listening. Please ask your question.")
    print(f"[MIC] Listening for up to {MIC_RECORD_SECONDS}s...")

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.8)
        try:
            audio = recognizer.listen(
                source,
                timeout=MIC_RECORD_SECONDS,
                phrase_time_limit=MIC_RECORD_SECONDS
            )
        except sr.WaitTimeoutError:
            print("[MIC] Timed out — no speech detected.")
            return None

    try:
        question = recognizer.recognize_google(audio, language=STT_LANGUAGE)
        print(f"[MIC] Heard: {question}")
        return question
    except sr.UnknownValueError:
        speak(engine, "Sorry, I didn't catch that.")
        return None
    except sr.RequestError as e:
        print(f"[MIC] STT request failed: {e}")
        speak(engine, "Speech recognition unavailable. Check your internet connection.")
        return None


def ask_gpt(ocr_text, question):
    if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("sk-YOUR"):
        print("[ERROR] Set your OPENAI_API_KEY at the top of this script.")
        return None

    print("[GPT] Sending to GPT-4o-mini...")

    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    system_prompt = (
        "You are an assistive reading tool helping a visually impaired person. "
        "You are given text extracted from a printed document that may contain multiple languages. "
        "Answer the user's question based only on the provided text. "
        "Be concise and clear. If the answer isn't in the text, say so briefly. "
        "Reply in the same language the user used to ask the question."
    )

    user_message = (
        f"Here is the extracted text from the document:\n\n{ocr_text}\n\n"
        f"User's question: {question}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
            max_tokens=300,
            temperature=0.3,
        )
        answer = response.choices[0].message.content.strip()
        print(f"[GPT] Answer: {answer}")
        return answer

    except openai.AuthenticationError:
        print("[ERROR] Invalid OpenAI API key.")
        return None
    except openai.APIConnectionError:
        print("[ERROR] Cannot connect to OpenAI. Check internet.")
        return None
    except Exception as e:
        print(f"[ERROR] GPT request failed: {e}")
        return None


def main():
    print("\nAssistive Reading Device — Pi Zero 2W\n")

    engine = init_tts()
    reader = load_ocr_reader()

    speak(engine, "Getting ready. Please hold the document steady.")
    time.sleep(0.5)

    frame = capture_image()
    processed = preprocess_image(frame)
    ocr_text = extract_text(reader, processed)

    if not ocr_text:
        speak(engine, (
            "I could not find any readable text. "
            "Try better lighting or hold the document a bit closer."
        ))
        return

    speak(engine, "Here is what I found.")
    speak(engine, ocr_text)

    print("\nPress ENTER to ask a follow-up question, or type 'skip' to finish.")
    choice = input(">> ").strip().lower()

    if choice in ("skip", "s", "q", "exit", "quit"):
        speak(engine, "Goodbye.")
        return

    question = record_question(engine)
    if not question:
        speak(engine, "No question received. Exiting.")
        return

    answer = ask_gpt(ocr_text, question)
    if answer:
        speak(engine, "Here is the answer.")
        speak(engine, answer)
    else:
        speak(engine, "Sorry, I could not fetch an answer at this time.")

    print("\n[DONE] Session complete.\n")


if __name__ == "__main__":
    main()
