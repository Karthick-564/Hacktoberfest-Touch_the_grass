import urllib.request
import urllib.error
import json
from pathlib import Path

import os

url = "https://api.elevenlabs.io/v1/speech-to-text"
key = os.getenv("ELEVENLABS_API_KEY", "")
if not key and Path(".env").exists():
    for line in Path(".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("ELEVENLABS_API_KEY="):
            key = line.split("=", 1)[1].strip()

# Test with our existing generated mp3 audio file
audio_file = Path("app/static/audio/guide_010024c69871573c9ed4688bbfc6542c.mp3")

boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
body = []

# file parameter
body.append(f"--{boundary}".encode("utf-8"))
body.append(f'Content-Disposition: form-data; name="file"; filename="{audio_file.name}"'.encode("utf-8"))
body.append(b"Content-Type: audio/mpeg\r\n")
body.append(audio_file.read_bytes())

# model_id parameter
body.append(f"--{boundary}".encode("utf-8"))
body.append(b'Content-Disposition: form-data; name="model_id"\r\n')
body.append(b"scribe_v1")

body.append(f"--{boundary}--\r\n".encode("utf-8"))
payload = b"\r\n".join(body)

req = urllib.request.Request(
    url,
    data=payload,
    headers={
        "xi-api-key": key,
        "Content-Type": f"multipart/form-data; boundary={boundary}"
    }
)

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print("ElevenLabs STT Success! Transcribed text:", res.get("text"))
except urllib.error.HTTPError as e:
    print("Status:", e.code, "Body:", e.read().decode("utf-8"))
