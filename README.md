# 👁️ Samaksh — AI Blind Assistance System

A real-time assistive system for visually impaired users, powered by **Raspberry Pi**, **Gemini 2.5 Flash**, and **Firebase**.

## How It Works

```
📱 Mobile Website  ←→  🔥 Firebase  ←→  🍓 Raspberry Pi + Webcam → 🤖 Gemini AI
     (Voice I/O)        (Real-time)        (Image Capture)           (Vision AI)
```

1. **User speaks** a command on the website (e.g., "read this", "where am I")
2. **Website sends** the command to Firebase
3. **Raspberry Pi reads** the command, captures an image with the webcam
4. **Gemini 2.5 Flash** analyzes the image and generates a response
5. **Response is sent** back through Firebase to the website
6. **Website speaks** the response aloud in the user's chosen language

### Two Modes

| Mode | How It Works |
|------|-------------|
| **🧭 Navigation** | Pi auto-captures every 7 seconds and provides walking guidance (obstacles, directions) |
| **💬 Normal** | User gives voice commands; Pi captures one image per command and responds |

---

## Prerequisites

- **Raspberry Pi** (any model) with a **USB webcam**
- **Firebase project** with Realtime Database enabled
- **Gemini API key** from [Google AI Studio](https://aistudio.google.com/)
- **Node.js 18+** (for the website)
- **Python 3.9+** (on the Raspberry Pi)
- **Chrome/Edge** browser on phone (for Web Speech API)

---

## Setup Guide

### Step 1: Firebase Setup

1. Go to [Firebase Console](https://console.firebase.google.com/) → **Create Project**
2. Enable **Realtime Database** (not Firestore)
   - Choose your preferred region
   - Start in **Test mode** (or set rules below)
3. Set database rules (for prototype — open access):
   ```json
   {
     "rules": {
       ".read": true,
       ".write": true
     }
   }
   ```
4. Go to **Project Settings → General** → Add a **Web App** → Copy the config object
5. Go to **Project Settings → Service Accounts** → **Generate new private key** → Save the JSON file

### Step 2: Website Setup

```bash
cd website
npm install
```

Copy the environment template and add your Firebase configuration:
```bash
cp .env.example .env
```
Edit the `.env` file to match your Firebase config:
```
VITE_FIREBASE_API_KEY="your-actual-api-key"
VITE_FIREBASE_AUTH_DOMAIN="your-project.firebaseapp.com"
VITE_FIREBASE_DATABASE_URL="https://your-project-default-rtdb.firebaseio.com"
VITE_FIREBASE_PROJECT_ID="your-project"
VITE_FIREBASE_STORAGE_BUCKET="your-project.appspot.com"
VITE_FIREBASE_MESSAGING_SENDER_ID="123456789"
VITE_FIREBASE_APP_ID="1:123456789:web:abcdef"
```

Start the dev server:
```bash
npm run dev
```

Open `http://localhost:5173` on your phone's Chrome browser (both devices must be on the same network, use the network URL shown in terminal).

### Step 3: Deploy Website to Netlify (Optional)

You can easily host this Vite React app on Netlify for free:
1. Push the `website/` folder to a GitHub repository.
2. Log into [Netlify](https://www.netlify.com/) and click **Add new site** → **Import an existing project**.
3. Connect your GitHub repository.
4. Configure the build settings:
   - **Base directory**: `website`
   - **Build command**: `npm run build`
   - **Publish directory**: `website/dist`
5. Click **Deploy site**.
6. Open the Netlify URL on your phone's browser.

---

### Step 4: Raspberry Pi Setup

Copy the `ai/` folder and your Firebase service account JSON to the Pi.

```bash
# Install system dependency for OpenCV
sudo apt update
sudo apt install python3-opencv

# Create and activate a Python virtual environment (required on newer Raspberry Pi OS)
# --system-site-packages lets the venv access apt-installed packages like python3-opencv
cd ai
python3 -m venv --system-site-packages venv
source venv/bin/activate

# Install Python packages
pip3 install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit the .env file and add your GEMINI_API_KEY and FIREBASE_DB_URL
nano .env

# Run
python3 ai.py
```

---

## Voice Commands

| Command | What Happens |
|---------|-------------|
| **"mode navigation"** | Switches to navigation mode (auto-capture every 7s) |
| **"mode normal"** | Switches back to normal mode |
| **"read this"** / **"read the newspaper"** | Captures image and reads all visible text |
| **"where am I"** | Captures image and describes surroundings |
| **Any other phrase** | Captures image and answers based on what's visible |

---

## Supported Languages

Audio output is translated and spoken in the user's selected language.

### Indian Languages
Hindi, Bengali, Tamil, Telugu, Kannada, Malayalam, Marathi, Gujarati, Punjabi, Odia

### International Languages
English, Spanish, French, German, Japanese, Chinese, Arabic, Portuguese

---

## Project Structure

```
Samaksh/
├── website/                  # React website (Vite)
│   ├── src/
│   │   ├── App.jsx           # Root component (state management)
│   │   ├── firebase.js       # Firebase config & helpers
│   │   ├── languages.js      # Language definitions & translation
│   │   ├── components/
│   │   │   ├── Onboarding.jsx   # Name + language setup
│   │   │   └── MainScreen.jsx   # Mode toggle + messages
│   │   └── hooks/
│   │       ├── useSpeechRecognition.js  # Continuous voice input
│   │       └── useTextToSpeech.js       # Translated TTS output
│   └── index.html
├── raspberry_pi/
│   ├── ai.py         # Main Pi script
│   └── requirements.txt      # Python dependencies
└── README.md
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Camera not found | Try `ls /dev/video*` on Pi. Change `CAMERA_INDEX` in the script. |
| Speech recognition not working | Use Chrome/Edge. Safari has limited support. |
| No audio output on phone | Tap the screen first — browsers require user interaction for audio. |
| Firebase errors | Double-check your config and database URL. Ensure Realtime Database (not Firestore) is enabled. |
| Gemini errors | Verify your API key at [Google AI Studio](https://aistudio.google.com/). |

---

## License

MIT — Built for accessibility. 🤍
