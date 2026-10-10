# 🌿 Field Guide — Touch Grass AI Nature Companion

[![Hacktoberfest 2026](https://img.shields.io/badge/Hacktoberfest-2026-orange.svg)](https://hacktoberfest.com/)
[![Theme](https://img.shields.io/badge/Theme-Touch%20Grass%20%26%20Open--Source%20AI-brightgreen.svg)]()
[![Open-Weight LLM](https://img.shields.io/badge/Open--Weight%20LLM-Google%20Gemma%202%209B-8E75C4.svg)](https://ai.google.dev/gemma)
[![Inference Engine](https://img.shields.io/badge/Inference-Ollama%20(Open--Source)-orange.svg)](https://ollama.com)
[![Voice AI](https://img.shields.io/badge/ElevenLabs-Turbo%20v2.5%20%7C%20Scribe-black.svg)](https://elevenlabs.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **A voice-first, screen-minimizing field guide built entirely on Open-Weight AI (Google Gemma 2 9B) and Open-Source foundations. Built to help you put the phone down, observe wildlife with your own eyes, and build an offline collectible field journal.**

---

## 🏛️ Built on Open Weights & Open Source

This project is built from the ground up around **open-weight and open-source models**, eliminating closed proprietary cloud LLM lock-in and ensuring complete privacy, zero tracking, and true offline capability for hikers and naturalists:

1. **Primary Open-Weight Intelligence: Google Gemma 2 9B (`gemma2:9b`)**
   - High-capacity 9-billion parameter open-weight reasoning model by Google DeepMind.
   - Handles multi-turn biological inquiry, morphological reasoning (beak structures, leaf margins, bark textures), and cross-lingual English/Tamil vernacular matching.
   - Runs locally and privately through **Ollama** with zero data leaving your machine.
2. **Edge Tier Support: Google Gemma 2 2B (`gemma2:2b`)**
   - Seamlessly falls back to the ultra-compact 2B open-weight tier on lower-memory laptops or embedded hardware.
3. **Deterministic Grounding & Zero Hallucinations**
   - Uses strict constrained decoding: Gemma 2 9B evaluates verified regional candidates, and an enforcement layer discards any hallucinated species IDs outside the verified database.
4. **Touch Grass & Pocket Mode Architecture**
   - Minimalist UI with OLED AMOLED dark mode, pedometer step tracking, and audio cues designed to maximize eye contact with real nature.

---

## 🎯 Target Categories

1. **Touch Grass Challenge**
   - Observation flow takes under **30 seconds**.
   - No endless feeds or doomscrolling: prompts the user to **"Now look up. Watch it for a minute."**
   - Features **Touch Grass Pocket Mode** with screen-off walk tracking, nature radar, and audio guidance.
2. **Open-Weight AI Foundation (Google Gemma 2 9B)**
   - Candidate reasoning and diagnostic dialogue powered strictly by open-weight models.
   - Completely offline-capable, private, and auditable.
3. **Best Use of ElevenLabs ($100 Prize)**
   - **Speech-to-Text (Scribe v1)**: Captures outdoor voice field notes in real time without typing.
   - **Text-to-Speech (Turbo v2.5)**: Naturalist audio guide ("George" storyteller voice) speaks confirmation questions through earphones so your eyes stay on the wildlife.

---

## 📍 Grounded Regional Data Pack (Coimbatore, India)

- **Geographic Bounds:** `11.0168° N, 76.9558° E`, 20 km radius around Coimbatore.
- **105 Canonical Regional Species:**
  - **80 Bird Species:** Verified against local eBird & GBIF occurrences with canonical English and Wikidata Tamil vernacular names.
  - **25 Native Tree Species:** Neem, Peepal, Banyan, Gulmohar, Tamarind, Teak, and more with botanical traits.
- **Percentile Rarity:** Segmented into `Everyday`, `Regular`, and `Special find`.
- **100% Offline Ready:** Self-contained SQLite database (`data/field_guide.db`), pre-cached bird audio calls, and local offline photos for complete airplane mode usability.

---

## 🚀 Quickstart

### 1. Prerequisites: Open-Weight Model & Python

* **Python 3.10+**
* **[Ollama](https://ollama.com/)** running Google's open-weight **Gemma 2 9B**:
  ```bash
  # Download and run Google's open-weight Gemma 2 9B model
  ollama run gemma2:9b
  ```
  *(Note: For machines with < 8GB RAM, you can optionally run `ollama run gemma2:2b` as the edge alternative).*

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

Configure your local model and optional ElevenLabs audio keys:
```env
# Open-Weight LLM Inference (Local & Open-Source)
OLLAMA_API_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=gemma2:9b

# ElevenLabs Naturalist Audio
ELEVENLABS_API_KEY=your_key_here
ELEVENLABS_MODEL_ID=eleven_turbo_v2_5
ELEVENLABS_VOICE_ID=JBFqnCBsd6RMkjVDRZzb
```

### 4. Run the Application

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open **`http://localhost:8000`** in your browser.

---

## 📱 How It Works

1. **Tap & Speak:** Tap the mic and describe what you see (e.g., *"A large banyan tree with hanging aerial roots and dense broad leaves"*).
2. **Open-Weight AI Reasoning:** **Gemma 2 9B** extracts key diagnostic traits, compares against regional biodiversity records, and identifies the best candidate.
3. **Hands-Free Audio Dialogue:** Naturalist voice asks a diagnostic confirmation question (*"Look closely: do you see aerial prop roots dropping down towards the ground?"*).
4. **Gotcha! Wild Species Registered:** Confirm the sighting to earn Nature XP and unlock the species card in your Field Journal.
5. **Touch Grass Pocket Mode:** Tap **🚶 Walk** to switch to the AMOLED screen-off outdoor walk mode, put the phone in your pocket, listen to nature cues, and earn XP for real-world outdoor time.

---

## 📂 Project Structure

```
├── app/
│   ├── config/categories.json   # Category-agnostic observation rules (Birds, Trees)
│   ├── database.py              # SQLite schema & database connection
│   ├── encounter.py             # Pokemon Go style interactive 2-way dialogue engine
│   ├── main.py                  # FastAPI server & REST API endpoints
│   ├── matcher.py               # Gemma 2 9B open-weight inference & grounded ranker
│   ├── pack_builder.py          # Regional pack builder (GBIF + Wikipedia + Wikidata)
│   ├── voice.py                 # ElevenLabs STT & TTS integration
│   ├── static/                  # CSS, JS, offline species photos, audio cache
│   └── templates/               # Responsive mobile-first HTML interface
├── data/
│   ├── field_guide.db           # 105 species offline SQLite database
│   └── pack_region_1.json       # Seed regional dataset
├── requirements.txt
├── .env.example
└── README.md
```

---

## 📜 License

MIT License — Built for Hacktoberfest 2026.
