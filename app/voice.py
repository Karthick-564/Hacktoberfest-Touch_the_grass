"""
ElevenLabs Voice Module for 'Field Guide'
Uses eleven_turbo_v2_5 for low credit usage and low latency.
Caches audio locally in app/static/audio/ to conserve credits.
"""

import hashlib
import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

CURRENT_DIR = Path(__file__).resolve().parent
STATIC_AUDIO_DIR = CURRENT_DIR / "static" / "audio"
STATIC_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Load configuration from .env if present
ENV_PATH = CURRENT_DIR.parent / ".env"
API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_turbo_v2_5")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")

if ENV_PATH.exists():
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip()
                if k == "ELEVENLABS_API_KEY":
                    API_KEY = v
                elif k == "ELEVENLABS_MODEL_ID":
                    MODEL_ID = v
                elif k == "ELEVENLABS_VOICE_ID":
                    VOICE_ID = v


def generate_speech(text: str) -> Optional[str]:
    """
    Generates TTS audio via ElevenLabs turbo model.
    Caches audio file locally to avoid re-using credits.
    Returns the web URL path e.g. /static/audio/<hash>.mp3.
    """
    if not text or not API_KEY:
        return None

    # Compute hash of text for caching
    text_hash = hashlib.md5(f"{VOICE_ID}_{MODEL_ID}_{text}".encode("utf-8")).hexdigest()
    file_name = f"guide_{text_hash}.mp3"
    target_path = STATIC_AUDIO_DIR / file_name

    # Return cached audio if already generated
    if target_path.exists() and target_path.stat().st_size > 1000:
        return f"/static/audio/{file_name}"

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    payload = {
        "text": text,
        "model_id": MODEL_ID,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "xi-api-key": API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            audio_bytes = resp.read()
            if len(audio_bytes) > 500:
                with open(target_path, "wb") as f:
                    f.write(audio_bytes)
                return f"/static/audio/{file_name}"
    except Exception as e:
        print(f"ElevenLabs TTS error: {e}")
        return None

    return None


def transcribe_audio(audio_bytes: bytes, filename: str = "recording.webm") -> Optional[str]:
    """
    Transcribes recorded audio via ElevenLabs Speech-to-Text API (scribe_v1).
    Returns transcribed plain text.
    """
    if not audio_bytes or not API_KEY:
        return None

    url = "https://api.elevenlabs.io/v1/speech-to-text"
    boundary = "----ElevenLabsBoundary7MA4YWxkTrZu0gW"
    body = []

    # File parameter
    body.append(f"--{boundary}".encode("utf-8"))
    body.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode("utf-8"))
    mime = "audio/mp4" if filename.endswith(".mp4") else "audio/ogg" if filename.endswith(".ogg") else "audio/webm"
    body.append(f"Content-Type: {mime}\r\n".encode("utf-8"))
    body.append(audio_bytes)

    # Model ID parameter
    body.append(f"--{boundary}".encode("utf-8"))
    body.append(b'Content-Disposition: form-data; name="model_id"\r\n')
    body.append(b"scribe_v1")

    body.append(f"--{boundary}--\r\n".encode("utf-8"))
    payload = b"\r\n".join(body)

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "xi-api-key": API_KEY,
            "Content-Type": f"multipart/form-data; boundary={boundary}"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("text", "").strip()
    except Exception as e:
        print(f"ElevenLabs STT error: {e}")
        return None

