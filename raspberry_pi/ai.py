#!/usr/bin/env python3
"""
Samaksh — Raspberry Pi Controller
==================================
Captures images from USB webcam, processes with Gemini 2.5 Flash,
and communicates via Firebase Realtime Database to assist blind users.

Usage:
    export GEMINI_API_KEY="your-key"
    export FIREBASE_DB_URL="https://your-project-default-rtdb.firebaseio.com"
    python3 ai.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

import time
import threading
import signal
import tempfile
import cv2
import firebase_admin
from firebase_admin import credentials, db
from google import genai
from PIL import Image

# ─── Configuration ───────────────────────────────────────────────

FIREBASE_CRED_PATH = os.environ.get("FIREBASE_CRED_PATH", "serviceAccountKey.json")
FIREBASE_DB_URL = os.environ.get("FIREBASE_DB_URL", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
NAV_INTERVAL = 10  # seconds between navigation captures
CAMERA_INDEX = 0  # USB webcam index (try 0, then 1 if it fails)

# ─── Gemini Prompts ──────────────────────────────────────────────

PROMPT_NAVIGATION = """You are an AI assistant helping a blind person navigate safely.
Analyze this image and provide clear, concise navigation guidance in 2-3 sentences:
- Is the path ahead clear? Any turns needed?
- Are there obstacles, stairs, people, vehicles, or hazards?
- Give specific directions: go straight, turn left/right, stop, slow down.
- PRIORITY: If there is readable text present, read it to the user and do NOT describe the environment. If the text is in another language, translate it and ONLY output the English translation.
Be direct and actionable. Do not describe the image aesthetically."""

PROMPT_READ = """You are an AI assistant helping a blind person read text.
Look at this image and read ALL visible text clearly and accurately.
If there are multiple text areas, read them in logical order (top to bottom, left to right).
If no text is visible, say 'I don't see any readable text in the current view.'
Just provide the text content, no extra commentary."""

PROMPT_LOCATION = """You are an AI assistant helping a blind person understand their surroundings.
Describe this scene in 2-3 sentences:
- What type of location is this? (indoor/outdoor, room type, street, etc.)
- What are the notable features or landmarks?
- Any useful details for orientation?
Be practical and helpful, not poetic."""

PROMPT_GENERAL = """You are an AI assistant helping a blind person.
Look at this image and respond to the user's request: {command}
Be clear, concise, and helpful in 2-3 sentences."""


# ─── Globals ─────────────────────────────────────────────────────

camera = None
gemini_client = None
nav_thread = None
nav_stop_event = threading.Event()
current_mode = "normal"
command_listener = None
mode_listener = None


# ─── Camera ──────────────────────────────────────────────────────

def init_camera():
    """Initialize USB webcam."""
    global camera
    for idx in [CAMERA_INDEX, 0, 1, 2]:
        # Force Video4Linux2 backend. GStreamer often crashes on Raspberry Pi.
        cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        if cap.isOpened():
            # Set to a highly compatible resolution
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            camera = cap
            print(f"✅ Camera initialized on index {idx}")
            return True
        cap.release()
    print("❌ No camera found. Please connect a USB webcam.")
    return False


def capture_image():
    """Capture a single frame from the webcam and return the file path."""
    if camera is None or not camera.isOpened():
        print("❌ Camera not available")
        return None

    # Read a few frames to get a fresh one (discard buffered frames)
    for _ in range(3):
        camera.read()

    ret, frame = camera.read()
    if not ret:
        print("❌ Failed to capture image")
        return None

    # Save to temp file
    tmp_path = os.path.join(tempfile.gettempdir(), "samaksh_capture.jpg")
    cv2.imwrite(tmp_path, frame)
    print(f"📸 Image captured: {tmp_path}")
    return tmp_path


# ─── Gemini ──────────────────────────────────────────────────────

def init_gemini():
    """Initialize Gemini client."""
    global gemini_client
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY not set")
        sys.exit(1)
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    print("✅ Gemini client initialized")


def process_image(image_path, prompt):
    """Send image to Gemini and return the response text."""
    try:
        img = Image.open(image_path)
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, img],
        )
        text = response.text.strip()
        print(f"🤖 Gemini response: {text[:100]}...")
        return text
    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return f"Sorry, I encountered an error processing the image. Please try again."


# ─── Firebase ────────────────────────────────────────────────────

def init_firebase():
    """Initialize Firebase Admin SDK."""
    if not FIREBASE_DB_URL:
        print("❌ FIREBASE_DB_URL not set")
        sys.exit(1)
    if not os.path.exists(FIREBASE_CRED_PATH):
        print(f"❌ Firebase credentials not found at: {FIREBASE_CRED_PATH}")
        sys.exit(1)

    cred = credentials.Certificate(FIREBASE_CRED_PATH)
    firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DB_URL})
    print("✅ Firebase initialized")


def push_assistant_message(text):
    """Push an assistant message to Firebase."""
    ref = db.reference("messages")
    ref.push({
        "role": "assistant",
        "text": text,
        "timestamp": int(time.time() * 1000),
        "spoken": False,
    })
    print("📤 Message pushed to Firebase")


def update_command_status(status):
    """Update command status in Firebase."""
    db.reference("session/command/status").set(status)


# ─── Navigation Mode ────────────────────────────────────────────

def navigation_loop():
    """Capture images every NAV_INTERVAL seconds in navigation mode."""
    print("🧭 Navigation loop started")
    while not nav_stop_event.is_set():
        image_path = capture_image()
        if image_path:
            response = process_image(image_path, PROMPT_NAVIGATION)
            push_assistant_message(response)
            try:
                os.remove(image_path)
            except OSError:
                pass

        # Wait NAV_INTERVAL seconds, but check for stop every 0.5s
        for _ in range(NAV_INTERVAL * 2):
            if nav_stop_event.is_set():
                break
            time.sleep(0.5)

    print("🧭 Navigation loop stopped")


def start_navigation():
    """Start navigation mode."""
    global nav_thread
    nav_stop_event.clear()
    if nav_thread and nav_thread.is_alive():
        return
    nav_thread = threading.Thread(target=navigation_loop, daemon=True)
    nav_thread.start()


def stop_navigation():
    """Stop navigation mode."""
    nav_stop_event.set()
    if nav_thread:
        nav_thread.join(timeout=5)


# ─── Command Processing ─────────────────────────────────────────

def handle_command(command_data):
    """Process a single command from Firebase."""
    if not command_data or command_data.get("status") != "pending":
        return

    cmd_type = command_data.get("type", "general")
    cmd_text = command_data.get("text", "")
    print(f"📥 Command received: type={cmd_type}, text='{cmd_text}'")

    update_command_status("processing")

    # Capture image
    image_path = capture_image()
    if not image_path:
        push_assistant_message("Sorry, I couldn't capture an image. Please check the camera.")
        update_command_status("done")
        return

    # Select prompt based on command type
    if cmd_type == "read":
        prompt = PROMPT_READ
    elif cmd_type == "location":
        prompt = PROMPT_LOCATION
    else:
        prompt = PROMPT_GENERAL.format(command=cmd_text)

    # Process with Gemini
    response = process_image(image_path, prompt)
    push_assistant_message(response)
    update_command_status("done")

    # Clean up
    try:
        os.remove(image_path)
    except OSError:
        pass


# ─── Firebase Listeners ─────────────────────────────────────────

def on_session_change(event):
    """Handle session changes (mode and commands)."""
    global current_mode

    if event.path == "/" or event.path == "/mode" or event.path == "/navigation_active":
        # Read the full session data
        session = db.reference("session").get()
        if not session:
            return

        new_mode = session.get("mode", "normal")
        nav_active = session.get("navigation_active", False)

        if new_mode != current_mode:
            current_mode = new_mode
            print(f"🔄 Mode changed to: {current_mode}")

            if current_mode == "navigation" and nav_active:
                start_navigation()
            else:
                stop_navigation()

    if event.path == "/command" or event.path == "/command/status":
        # Check if there's a pending command
        command = db.reference("session/command").get()
        if command and command.get("status") == "pending" and current_mode == "normal":
            handle_command(command)


# ─── Main ────────────────────────────────────────────────────────

def cleanup(signum=None, frame=None):
    """Clean shutdown."""
    print("\n🛑 Shutting down Samaksh...")
    stop_navigation()
    if camera and camera.isOpened():
        camera.release()
    if mode_listener:
        mode_listener.close()
    print("👋 Goodbye!")
    sys.exit(0)


def main():
    global mode_listener

    print("=" * 50)
    print("  👁️  SAMAKSH — Blind Assistance System")
    print("  Raspberry Pi Controller")
    print("=" * 50)
    print()

    # Initialize components
    init_firebase()
    init_gemini()
    if not init_camera():
        sys.exit(1)

    # Register signal handlers for clean shutdown
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # Check initial mode
    session = db.reference("session").get()
    if session:
        global current_mode
        current_mode = session.get("mode", "normal")
        if current_mode == "navigation" and session.get("navigation_active", False):
            start_navigation()
        print(f"📡 Current mode: {current_mode}")

    # Start listening for session changes
    print("👂 Listening for commands...")
    mode_listener = db.reference("session").listen(on_session_change)

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
