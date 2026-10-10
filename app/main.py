"""
Field Guide FastAPI Web Application
Mobile-first, category-agnostic offline nature guide.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.database import get_connection

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
CONFIG_PATH = APP_DIR / "config" / "categories.json"
STATIC_DIR = APP_DIR / "static"
TEMPLATES_DIR = APP_DIR / "templates"

app = FastAPI(title="Field Guide", description="Touch Grass Nature Guide")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static directories exist
STATIC_DIR.mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "css").mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "js").mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "images").mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class ObservationPayload(BaseModel):
    category: str = "birds"
    answers: Dict[str, Any] = {}
    free_text: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def serve_home():
    index_file = TEMPLATES_DIR / "index.html"
    if index_file.exists():
        response = HTMLResponse(content=index_file.read_text(encoding="utf-8"))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return HTMLResponse("<h1>Field Guide</h1><p>UI loading...</p>")


@app.get("/sw.js")
async def serve_service_worker():
    sw_file = STATIC_DIR / "js" / "sw.js"
    if sw_file.exists():
        return FileResponse(sw_file, media_type="application/javascript")
    return JSONResponse(status_code=404, content={"error": "Service worker not found"})


@app.get("/api/categories")
async def get_categories():
    """Returns question definitions for each category from config."""
    if not CONFIG_PATH.exists():
        return JSONResponse(status_code=404, content={"error": "Config not found"})
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


@app.get("/api/stats")
async def get_stats(category: str = "birds"):
    """Returns total local species and unlocked count for home screen."""
    conn = get_connection()
    try:
        region_row = conn.execute("SELECT id, name FROM regions ORDER BY id DESC LIMIT 1").fetchone()
        region_name = region_row["name"] if region_row else "Local Region"
        region_id = region_row["id"] if region_row else 1

        total_row = conn.execute(
            "SELECT COUNT(*) as count FROM species WHERE region_id = ? AND category = ?",
            (region_id, category)
        ).fetchone()
        total_species = total_row["count"] if total_row else 0

        unlocked_row = conn.execute(
            """SELECT COUNT(*) as count FROM user_collection uc
               JOIN species s ON uc.species_id = s.id
               WHERE s.region_id = ? AND s.category = ?""",
            (region_id, category)
        ).fetchone()
        unlocked_species = unlocked_row["count"] if unlocked_row else 0

        return {
            "region_name": region_name,
            "category": category,
            "total_species": total_species,
            "unlocked_species": unlocked_species
        }
    finally:
        conn.close()


from app.voice import generate_speech, transcribe_audio

class SpeakRequest(BaseModel):
    text: str


@app.post("/api/speak")
async def speak_text_endpoint(payload: SpeakRequest):
    """Generates audio for given text via ElevenLabs turbo model."""
    audio_url = generate_speech(payload.text)
    return {"audio_url": audio_url}


@app.post("/api/transcribe")
async def transcribe_audio_endpoint(request: Request):
    """Transcribes uploaded audio blob using ElevenLabs Speech-to-Text."""
    body = await request.body()
    if not body:
        return JSONResponse(status_code=400, content={"error": "Empty audio data"})

    content_type = request.headers.get("content-type", "audio/webm").lower()
    ext = "mp4" if "mp4" in content_type else "ogg" if "ogg" in content_type else "webm"
    text = transcribe_audio(body, filename=f"speech.{ext}")
    return {"text": text or ""}


from app.encounter import evaluate_encounter_turn

class EncounterPayload(BaseModel):
    category: str = "birds"
    user_input: str
    turn: int = 1
    target_id: Optional[int] = None

@app.post("/api/encounter/turn")
async def encounter_turn_endpoint(payload: EncounterPayload):
    """
    Pokemon Go style wild nature encounter.
    Drives 2-way detective dialogue forcing user to look up at the real creature.
    """
    result = evaluate_encounter_turn(
        category=payload.category,
        user_input=payload.user_input,
        turn=payload.turn,
        target_id=payload.target_id
    )
    return result

class PocketWalkPayload(BaseModel):
    duration_seconds: int = 0
    steps: int = 0
    xp_earned: int = 0

@app.post("/api/pocket/complete")
async def complete_pocket_walk(payload: PocketWalkPayload):
    """
    Saves Touch Grass Pocket Mode walk session and awards XP.
    """
    conn = get_connection()
    try:
        if payload.xp_earned > 0:
            conn.execute(
                "UPDATE user_profile SET xp = xp + ? WHERE id = 1",
                (payload.xp_earned,)
            )
            conn.commit()
        profile_row = conn.execute("SELECT xp FROM user_profile WHERE id = 1").fetchone()
        new_xp = profile_row["xp"] if profile_row else 0
        return {"success": True, "total_xp": new_xp, "xp_earned": payload.xp_earned}
    finally:
        conn.close()


@app.get("/api/quests")
async def get_daily_quests():
    """
    Returns user profile (XP, level, rank title, streak) and daily quests.
    """
    conn = get_connection()
    try:
        profile_row = conn.execute("SELECT * FROM user_profile WHERE id = 1").fetchone()
        xp = profile_row["xp"] if profile_row else 0
        streak = profile_row["streak_days"] if profile_row else 1

        # Calculate Level & Rank
        if xp < 100:
            level = 1
            rank_title = "Seedling Scout"
            rank_title_ta = "தொடக்க சாரணர்"
            xp_next = 100
            xp_curr = xp
        elif xp < 250:
            level = 2
            rank_title = "Field Tracker"
            rank_title_ta = "களக் கண்டுபிடிப்பாளர்"
            xp_next = 150
            xp_curr = xp - 100
        elif xp < 500:
            level = 3
            rank_title = "Bushcraft Ranger"
            rank_title_ta = "காட்டுப் பாதுகாவலர்"
            xp_next = 250
            xp_curr = xp - 250
        else:
            level = 4
            rank_title = "Master Naturalist"
            rank_title_ta = "முதன்மை இயற்கை ஆய்வாளர்"
            xp_next = 500
            xp_curr = 500

        # Check today's unlocks for quests
        today_unlocks = conn.execute(
            """SELECT s.common_name, s.key_traits, s.summary
               FROM user_collection uc
               JOIN species s ON uc.species_id = s.id
               WHERE DATE(uc.unlocked_at) = CURRENT_DATE"""
        ).fetchall()

        has_touch_grass = len(today_unlocks) > 0
        has_perched = any("wire" in (r["summary"] or "").lower() or "branch" in (r["summary"] or "").lower() for r in today_unlocks)
        has_color = any("yellow" in (r["key_traits"] or "").lower() or "red" in (r["key_traits"] or "").lower() for r in today_unlocks)

        quests = [
            {
                "id": "touch_grass",
                "icon": "🌱",
                "title": "Touch Grass Today",
                "title_ta": "இன்று இயற்கையை உணருங்கள்",
                "desc": "Step outside and log 1 wild sighting",
                "desc_ta": "வெளியே சென்று 1 உயிரினத்தைக் கண்டறியவும்",
                "completed": has_touch_grass,
                "reward_xp": 50
            },
            {
                "id": "perched_watcher",
                "icon": "🔭",
                "title": "Perched Watcher",
                "title_ta": "கிளைக் கண்காணிப்பாளர்",
                "desc": "Find a bird perched on a branch or wire",
                "desc_ta": "கம்பியில் அல்லது கிளையில் அமர்ந்த பறவை",
                "completed": has_perched,
                "reward_xp": 50
            },
            {
                "id": "color_hunter",
                "icon": "🎨",
                "title": "Vibrant Plumage",
                "title_ta": "வண்ண இறகுகள்",
                "desc": "Observe a bird with yellow or red accents",
                "desc_ta": "மஞ்சள் அல்லது சிவப்பு அடையாளங்கள் கொண்ட பறவை",
                "completed": has_color,
                "reward_xp": 50
            }
        ]

        pct = min(100, int((xp_curr / xp_next) * 100)) if xp_next > 0 else 100

        return {
            "profile": {
                "level": level,
                "rank_title": rank_title,
                "rank_title_ta": rank_title_ta,
                "total_xp": xp,
                "xp_current_level": xp_curr,
                "xp_next": xp_next,
                "progress_pct": pct,
                "streak_days": streak
            },
            "quests": quests
        }
    finally:
        conn.close()


from app.matcher import match_observation


@app.post("/api/match")
async def match_observation_endpoint(payload: ObservationPayload):
    """
    Accepts natural speech or structured field observations.
    Runs grounded matching (with local Gemma 2 if available),
    extracts diagnostic field traits, and generates ElevenLabs audio narration.
    """
    category = payload.category
    answers = payload.answers
    free_text = payload.free_text or ""
    spoken_observation = answers.get("spoken_text") or free_text

    conn = get_connection()
    try:
        species_rows = conn.execute(
            """SELECT id, scientific_name, common_name, tamil_name, rarity,
                      summary, description_text, key_traits, local_fact, image_local_path, audio_url
               FROM species WHERE category = ? ORDER BY observation_count DESC""",
            (category,)
        ).fetchall()
        pool = [dict(r) for r in species_rows]
    finally:
        conn.close()

    if not pool:
        return {
            "status": "not_sure",
            "confidence_reasoning": "No species loaded for this category.",
            "candidates": [],
            "next_observation_question": "Verify your regional pack.",
            "observation_prompt": "Look up and observe the surrounding landscape."
        }

    # Run matching pipeline (evaluates local Gemma 2 or uses grounded ranker)
    match_result = match_observation(pool, {
        "category": category,
        "answers": answers,
        "free_text": spoken_observation
    })

    candidates = match_result.get("candidates", [])
    engine_used = match_result.get("engine_used", "Gemma 2 9B (Open-Weight)")

    # Extract keywords, colors, and features for visual trait breakdown
    combined_query = f"{spoken_observation} {free_text} {answers.get('beak_head', '')} {' '.join(answers.get('colors', []))}".lower()
    known_colors = ["black", "brown", "white", "yellow", "grey", "gray", "red", "green", "blue", "orange", "rufous"]
    detected_colors = [c for c in known_colors if c in combined_query]
    known_features = ["crest", "beak", "bill", "tail", "wings", "throat", "head", "eye", "belly", "legs", "patch"]
    detected_features = [f for f in known_features if f in combined_query]

    extracted_traits = {
        "raw_text": spoken_observation or free_text or "Field observation",
        "detected_colors": detected_colors if detected_colors else ["Natural plumage/tones"],
        "detected_features": detected_features if detected_features else ["General silhouette"],
        "keywords": [w for w in combined_query.split() if len(w) > 3][:6]
    }

    # Generate ElevenLabs spoken audio for the top candidate
    audio_url = None
    if candidates:
        top_cand = candidates[0]
        narrator_line = f"That sounds like a {top_cand['common_name']}. {top_cand.get('confirm_question', 'Look closely at its markings.')}"
        audio_url = generate_speech(narrator_line)

    return {
        "status": match_result.get("status", "matched"),
        "engine_used": engine_used,
        "confidence_reasoning": match_result.get("confidence_reasoning", "Top regional species aligning with spoken observation."),
        "extracted_traits": extracted_traits,
        "candidates": candidates,
        "audio_url": audio_url,
        "observation_prompt": match_result.get("observation_prompt", "Now look up. Watch it for a minute.")
    }


class UnlockPayload(BaseModel):
    species_id: int
    notes: Optional[str] = ""


@app.post("/api/collection/unlock")
async def unlock_species_card(payload: UnlockPayload):
    """
    Unlocks a species card in the user's offline collection.
    Generates ElevenLabs celebration narration.
    """
    conn = get_connection()
    try:
        # Insert or update collection
        conn.execute(
            """INSERT INTO user_collection (species_id, notes)
               VALUES (?, ?)
               ON CONFLICT(species_id) DO UPDATE SET notes = coalesce(excluded.notes, user_collection.notes)""",
            (payload.species_id, payload.notes)
        )
        conn.commit()

        sp = conn.execute(
            """SELECT s.*, uc.unlocked_at, uc.notes as user_notes
               FROM species s
               JOIN user_collection uc ON s.id = uc.species_id
               WHERE s.id = ?""",
            (payload.species_id,)
        ).fetchone()

        if not sp:
            return JSONResponse(status_code=404, content={"error": "Species not found"})

        species_data = dict(sp)
    finally:
        conn.close()

    # ElevenLabs voice celebration for card discovery
    celebration_speech = f"Congratulations! You unlocked the {species_data['common_name']}. {species_data.get('local_fact', '')[:120]}"
    audio_url = generate_speech(celebration_speech)

    return {
        "success": True,
        "species": species_data,
        "audio_url": audio_url,
        "message": f"Successfully unlocked {species_data['common_name']} in your Field Journal!"
    }


@app.get("/api/collection")
async def get_user_collection(category: str = "birds"):
    """
    Returns full regional deck with unlocked status and collection statistics.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT s.id, s.scientific_name, s.common_name, s.tamil_name, s.rarity,
                      s.summary, s.description_text, s.key_traits, s.local_fact,
                      s.image_local_path, s.peak_months, s.audio_url,
                      CASE WHEN uc.id IS NOT NULL THEN 1 ELSE 0 END as is_unlocked,
                      uc.unlocked_at, uc.notes as user_notes
               FROM species s
               LEFT JOIN user_collection uc ON s.id = uc.species_id
               WHERE s.category = ?
               ORDER BY s.observation_count DESC""",
            (category,)
        ).fetchall()

        species_list = [dict(r) for r in rows]

        total = len(species_list)
        unlocked = sum(1 for s in species_list if s["is_unlocked"])
        everyday_unlocked = sum(1 for s in species_list if s["is_unlocked"] and s["rarity"] == "Everyday")
        regular_unlocked = sum(1 for s in species_list if s["is_unlocked"] and s["rarity"] == "Regular")
        special_unlocked = sum(1 for s in species_list if s["is_unlocked"] and s["rarity"] == "Special find")

        return {
            "category": category,
            "total_species": total,
            "unlocked_count": unlocked,
            "stats_by_rarity": {
                "Everyday": {
                    "unlocked": everyday_unlocked,
                    "total": sum(1 for s in species_list if s["rarity"] == "Everyday")
                },
                "Regular": {
                    "unlocked": regular_unlocked,
                    "total": sum(1 for s in species_list if s["rarity"] == "Regular")
                },
                "Special find": {
                    "unlocked": special_unlocked,
                    "total": sum(1 for s in species_list if s["rarity"] == "Special find")
                }
            },
            "deck": species_list
        }
    finally:
        conn.close()


