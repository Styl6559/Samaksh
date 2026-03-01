#!/bin/bash
# =============================================================================
# SETUP SCRIPT — Assistive Reading Device (Raspberry Pi Zero 2W)
# Run once after a fresh Raspberry Pi OS Lite install.
# Usage:  bash setup.sh
# =============================================================================

set -e   # exit immediately on any error

echo ""
echo "================================================"
echo "  Assistive Reading Device — Setup"
echo "================================================"
echo ""

# ─── System packages ────────────────────────────────────────────────
echo "[1/4] Installing system dependencies..."
sudo apt update
sudo apt install -y \
    python3-pip \
    python3-dev \
    portaudio19-dev \
    libopenblas-dev \
    libatlas-base-dev \
    espeak \
    espeak-ng \
    ffmpeg \
    libgl1

# Note: No Tesseract needed — we use EasyOCR (neural-network-based OCR)
# EasyOCR supports 80+ languages out of the box, including Hindi.

# ─── Python packages ───────────────────────────────────────────────
echo ""
echo "[2/4] Installing Python packages..."
pip3 install --upgrade pip

pip3 install \
    opencv-python-headless \
    easyocr \
    pyttsx3 \
    SpeechRecognition \
    pyaudio \
    openai

# ─── Verify imports ────────────────────────────────────────────────
echo ""
echo "[3/4] Verifying audio hardware..."
aplay -l || echo "  (No ALSA devices shown — verify USB audio is connected)"
arecord -l || echo "  (No recording devices shown — verify USB microphone is connected)"

# ─── Verify Python imports ─────────────────────────────────────────
echo ""
echo "[4/4] Verifying Python imports..."
python3 -c "
import cv2, easyocr, pyttsx3, speech_recognition, openai
print('cv2         :', cv2.__version__)
print('easyocr     :', easyocr.__version__)
print('openai      :', openai.__version__)
print('All packages imported successfully.')
"

echo ""
echo "================================================"
echo "  Setup complete!"
echo ""
echo "  NEXT STEPS:"
echo "  1. Open assistive_reader.py"
echo "  2. Set your OPENAI_API_KEY near the top"
echo "     (only needed for the Voice Question feature)"
echo "  3. Run:  python3 assistive_reader.py"
echo ""
echo "  NOTE: EasyOCR downloads model weights (~100 MB)"
echo "  on first run. This is normal."
echo "================================================"
echo ""
