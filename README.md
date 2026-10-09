# 🌿 Field Guide — Touch Grass AI Nature Companion

[![Hacktoberfest 2026](https://img.shields.io/badge/Hacktoberfest-2026-orange.svg)](https://hacktoberfest.com/)
[![Theme](https://img.shields.io/badge/Theme-Touch%20Grass-brightgreen.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![ElevenLabs](https://img.shields.io/badge/ElevenLabs-Turbo%20v2.5%20%7C%20Scribe-black.svg)](https://elevenlabs.io)
[![Gemma 2](https://img.shields.io/badge/LLM-Gemma%202%20(Local)-blue.svg)](https://ai.google.dev/gemma)

> **A voice-first, screen-minimizing field guide that helps you put the phone down, observe wildlife with your own eyes, and build an offline collectible field journal.**

---

## 🎯 Target Categories

1. **Touch Grass Challenge**
   - Observation flow takes under **30 seconds**.
   - No endless feeds or doomscrolling: prompts the user to **"Now look up. Watch it for a minute."**
   - High-contrast outdoor UI designed for direct sunlight.
2. **Best Use of ElevenLabs ($100 Prize)**
   - **Speech-to-Text (Scribe v1)**: Captures outdoor voice field notes in real time without typing.
   - **Text-to-Speech (Turbo v2.5)**: Naturalist audio guide ("George" storyteller voice) plays confirmation questions and educational facts through earphones so you don't stare at the screen.
3. **Best Use of Gemma ($200 Prize)**
   - Grounded species candidate reasoning and observation question generation powered by local **Gemma 2** (`gemma2:2b`).
   - Zero hallucinations: hard validation restricts matches strictly to verified regional biodiversity packs.

---

## 📍 Grounded Regional Data Pack (Coimbatore, India)

- **Geographic Bounds:** `11.0168° N, 76.9558° E`, 20 km radius around Coimbatore.
- **80 Canonical Species:** Verified against local eBird & GBIF occurrences with single canonical English names and Wikidata Tamil vernacular names.
- **Percentile Rarity:** Segmented into `Everyday`, `Regular`, and `Special find`.
- **Offline First:** Self-contained SQLite database (`data/field_guide.db`) and local images for full functionality in airplane mode.

---

## 🚀 Quickstart

### 1. Prerequisites
- Python 3.10+
- (Optional) [Ollama](https://ollama.com/) with `gemma2:2b` for local LLM inference:
  ```bash
  ollama run gemma2:2b
  ```

### 2. Clone and Setup
```bash
git clone https://github.com/Karthick-564/Hacktoberfest-Touch_the_grass.git
cd Hacktoberfest-Touch_the_grass

# Create virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Add your ElevenLabs API key:
```env
ELEVENLABS_API_KEY=your_key_here
ELEVENLABS_MODEL_ID=eleven_turbo_v2_5
ELEVENLABS_VOICE_ID=JBFqnCBsd6RMkjVDRZzb
```

### 4. Run Locally
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Open **`http://localhost:8000`** in your browser.

---

## 📱 How It Works

1. **Tap & Speak:** Tap the mic and describe what you see (e.g., *"A black bird with a crest on its head and red under the tail"*).
2. **AI Matching:** ElevenLabs Scribe transcribes your words; Gemma 2 / regional matcher extracts traits and matches against Coimbatore species.
3. **Audio Confirmation:** The naturalist voice asks you a specific diagnostic question through your headphones (*"Check closely: does it have a red vent under the tail?"*).
4. **Collect & Touch Grass:** Confirm the sighting to unlock the card in your Field Journal, then put your phone away and watch the bird.

---

## 📂 Project Structure

```
├── app/
│   ├── config/categories.json   # Category-agnostic observation rules (Birds, Trees)
│   ├── database.py              # SQLite schema & helpers
│   ├── main.py                  # FastAPI endpoints & PWA routing
│   ├── matcher.py               # Grounded Gemma 2 / rule matching engine
│   ├── pack_builder.py          # Regional pack builder (GBIF + Wikipedia + Wikidata)
│   ├── voice.py                 # ElevenLabs STT & TTS integration
│   ├── static/                  # CSS, JS, offline species photos, audio cache
│   └── templates/               # Minimalist mobile-first HTML
├── data/
│   ├── field_guide.db           # 80 species local SQLite pack
│   └── pack_region_1.json       # Seed JSON export
├── requirements.txt
├── .env.example
└── README.md
```

---

## 📜 License
MIT License — Built for Hacktoberfest 2026.
