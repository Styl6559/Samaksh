# Samaksh — Assistive Reading Device

A small, offline-capable reading assistant that runs on a **Raspberry Pi Zero 2W**. Point a webcam at any printed text — a book page, a letter, a medicine label — and it reads it out loud. Ask a follow-up question with your voice and it answers using GPT-4o-mini.

Built as a working prototype for visually impaired users. No cloud dependency for the core read-aloud feature — it works without internet.

---

## What it does

1. **Captures** a frame from your USB webcam
2. **Cleans up** the image with OpenCV (grayscale → denoise → threshold)
3. **Reads the text** using EasyOCR — supports Hindi, English, and 80+ other languages
4. **Speaks it aloud** using pyttsx3 + espeak (fully offline)
5. **Listens for a question** via USB microphone (optional, needs internet)
6. **Answers it** using OpenAI GPT-4o-mini and reads the answer back

---

## Hardware

| Component | Details |
|---|---|
| Board | Raspberry Pi Zero 2W |
| OS | Raspberry Pi OS Lite (64-bit) |
| Camera | Any USB webcam |
| Microphone | Any USB microphone |
| Speaker | USB or 3.5mm audio output |
| RAM | 512 MB (works fine for core features) |

---

## Project Structure

```
samaksh/
├── assistive_reader.py   # main script — run this
├── setup.sh              # one-time setup for a fresh Pi
└── README.md
```

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/samaksh.git
cd samaksh
```

### 2. Run setup (once)

```bash
bash setup.sh
```

This will install all system packages and Python dependencies. EasyOCR will download its model weights (~100 MB) the first time you run the script — that's normal, it only happens once and gets cached.

### 3. Set your OpenAI API key

Open `assistive_reader.py` and find this line near the top:

```python
OPENAI_API_KEY = "sk-YOUR_OPENAI_API_KEY_HERE"
```

Replace it with your actual key. This is only needed for the voice question feature. If you just want read-aloud without Q&A, you can leave it as-is.

### 4. Run it

```bash
python3 assistive_reader.py
```

Hold a document in front of the webcam when prompted. After it reads the text, you'll be asked if you want to ask a question.

---

## Configuration

All tunable settings are at the top of `assistive_reader.py`:

```python
CAMERA_INDEX    = 0          # change if your webcam isn't index 0
OCR_LANGUAGES   = ["en", "hi"]   # add any EasyOCR language codes here
MIC_RECORD_SECONDS = 6       # how long to listen for a question
STT_LANGUAGE    = "hi-IN"    # language hint for Google speech recognition
TTS_RATE        = 145        # speaking speed (words per minute)
```

### Supported OCR languages (sample)

| Code | Language |
|---|---|
| `en` | English |
| `hi` | Hindi |
| `fr` | French |
| `de` | German |
| `es` | Spanish |
| `ar` | Arabic |
| `zh_sim` | Simplified Chinese |
| `ja` | Japanese |

Full list: [EasyOCR supported languages](https://www.jaided.ai/easyocr/)

---

## How the offline TTS works

pyttsx3 uses **espeak-ng** as its backend on Raspberry Pi OS Lite. No internet, no API calls — it synthesises speech directly on the device. The voice won't win any awards, but it's clear, fast, and works at 512 MB RAM.

If you want a better voice, look into `mimic3` or `piper-tts` as drop-in espeak replacements.

---

## Voice Question Mode

After the text is read aloud, the script asks if you want to ask a question. Press **Enter** to proceed or type `skip` to exit.

- Your question is recorded from the USB microphone
- Sent to Google Speech-to-Text (needs Wi-Fi)
- The OCR text + your question go to GPT-4o-mini
- The answer comes back and is spoken aloud

The model is told to reply in the **same language you asked in**, so you can ask in Hindi and get a Hindi answer, ask in English and get English, etc.

---

## Known limitations

- **EasyOCR on Pi Zero 2W is slow** — expect 15–40 seconds for OCR on a full page. The model is CPU-only. For faster results, consider Pi 4 or Pi 5.
- **Handwritten text** recognition is hit-or-miss. EasyOCR handles printed text well.
- **Low-light images** will degrade OCR accuracy. Good, even lighting makes a big difference.
- **Voice questions need internet.** The Google STT API is free within limits but requires a connection.

---

## Dependencies

```
opencv-python-headless   — image capture and preprocessing
easyocr                  — multilingual OCR (no Tesseract needed)
pyttsx3                  — offline text-to-speech
SpeechRecognition        — microphone input + Google STT
pyaudio                  — audio I/O backend for SpeechRecognition
openai                   — GPT-4o-mini for question answering
```

---

## License

MIT — do whatever you want with it. If it helps someone, that's the point.
