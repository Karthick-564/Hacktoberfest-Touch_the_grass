"""
Field Detective / Pokemon Go Nature Encounter Engine
Multi-turn interactive dialogue that encourages users to LOOK AT THE REAL BIRD
instead of staring at static photos on a screen.
"""

import json
import re
from typing import Any, Dict, List, Optional
from app.database import get_connection
from app.matcher import prefilter_candidates
from app.voice import generate_speech


def evaluate_encounter_turn(
    category: str,
    user_input: str,
    turn: int = 1,
    target_id: Optional[int] = None,
    history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Handles multi-turn encounter dialogue:
    - Turn 1: User speaks initial observation. Engine identifies top suspect,
      keeps it hidden, and formulates a diagnostic question that forces the user to LOOK UP.
    - Turn 2+: User confirms/refutes diagnostic feature. Engine resolves to 'caught' or pivots.
    """
    history = history or []
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT id, scientific_name, common_name, tamil_name, rarity,
                      summary, description_text, key_traits, local_fact, image_local_path
               FROM species WHERE category = ? ORDER BY observation_count DESC""",
            (category,)
        ).fetchall()
        species_pool = [dict(r) for r in rows]
    finally:
        conn.close()

    species_by_id = {s["id"]: s for s in species_pool}

    # Case A: Turn 2 with a target candidate and user confirmation
    if turn >= 2 and target_id and target_id in species_by_id:
        target = species_by_id[target_id]
        clean_input = user_input.lower().strip()
        is_positive = any(w in clean_input for w in ["yes", "yeah", "yep", "true", "has", "crest", "forked", "yellow", "red", "spiky", "seen", "matches", "1", "one"])
        is_negative = any(w in clean_input for w in ["no", "nope", "not", "different", "smooth", "flat", "black", "none", "straight", "2", "two"])

        if is_positive or not is_negative:
            # Successfully Caught! Register in user collection
            conn = get_connection()
            try:
                conn.execute(
                    """INSERT INTO user_collection (species_id, notes) VALUES (?, ?)
                       ON CONFLICT(species_id) DO NOTHING""",
                    (target["id"], f"Spotted during wild field encounter: {user_input}")
                )
                conn.execute("UPDATE user_profile SET xp = xp + 50 WHERE id = 1")
                conn.commit()
            finally:
                conn.close()

            tamil_str = f" ({target.get('tamil_name')})" if target.get('tamil_name') else ""
            celebration = (
                f"Gotcha! You discovered a {target['common_name']}{tamil_str}! "
                f"{target.get('local_fact', target.get('summary', ''))[:110]}. "
                f"Registered to your Field Journal!"
            )
            audio_url = generate_speech(celebration)

            return {
                "phase": "caught",
                "status": "success",
                "species": target,
                "naturalist_speech": celebration,
                "audio_url": audio_url,
                "xp_gained": 50,
                "outdoor_prompt": "Now look up! Put your phone down and watch it move for 30 seconds."
            }

    # Case B: Turn 1 or Pivoting to a new candidate
    candidates = prefilter_candidates(species_pool, {"free_text": user_input}, max_candidates=5)
    if not candidates:
        speech = "I couldn't quite catch that. Look closely at the bird: what color are its feathers, and where is it sitting?"
        return {
            "phase": "question",
            "turn": 1,
            "target_id": None,
            "naturalist_speech": speech,
            "audio_url": generate_speech(speech),
            "diagnostic_prompt": "Look up at the creature: Describe its primary color or where it's perched.",
            "quick_choices": ["Perched on a wire or tree", "Hopping on the ground", "Near water / wetland"]
        }

    top_cand = candidates[0]
    runner_up = candidates[1] if len(candidates) > 1 else None

    # Extract diagnostic trait for the question
    traits = {}
    try:
        traits = json.loads(top_cand.get("key_traits", "{}")) if isinstance(top_cand.get("key_traits"), str) else top_cand.get("key_traits", {})
    except Exception:
        traits = {}

    # Extract diagnostic trait for the question
    traits = {}
    try:
        traits = json.loads(top_cand.get("key_traits", "{}")) if isinstance(top_cand.get("key_traits"), str) else top_cand.get("key_traits", {})
    except Exception:
        traits = {}

    distinctive = traits.get("distinctive_feature", "")
    beak = traits.get("beak_or_head", "")
    colors = traits.get("primary_colors", [])
    desc = top_cand.get("description_text", top_cand.get("summary", ""))

    # Formulate a sharp diagnostic question that forces the user to LOOK UP at the real bird!
    if "crest" in str(distinctive).lower() or "crest" in str(beak).lower():
        prompt = "Look up at its head right now: Does it have a spiky crest (like a little crown) on top of its head?"
        choices = ["Yes, spiky crest visible!", "No, smooth flat head", "Head is hidden"]
    elif "forked" in str(distinctive).lower() or "forked" in desc.lower() or "tail" in str(distinctive).lower():
        prompt = "Look at its tail right now: Is the tail deeply forked like a fish tail, or straight?"
        choices = ["Yes, deeply forked tail!", "No, straight / rounded tail", "Can't see tail clearly"]
    elif "yellow" in str(beak).lower() or "yellow patch" in desc.lower():
        prompt = "Look closely at its face: Does it have a bright yellow bill and yellow skin around the eyes?"
        choices = ["Yes, yellow beak and eye patch!", "No yellow on face", "Face not visible"]
    elif "curved" in str(beak).lower() or "decurved" in desc.lower():
        prompt = "Look closely at its bill: Is the beak long and curved downwards (like a sunbird)?"
        choices = ["Yes, curved beak!", "No, short straight beak", "Beak not clear"]
    elif "white" in colors and "black" in colors:
        prompt = "Look at its wings and belly: Does it have contrasting black and white plumage patterns?"
        choices = ["Yes, bold black & white!", "No, mostly plain colored", "Not sure"]
    elif distinctive and distinctive != "unknown" and len(distinctive) < 80:
        prompt = f"Look up at it right now: Can you spot its {distinctive}?"
        choices = ["Yes, matches that feature!", "No, looks different", "Hard to tell"]
    else:
        # Fallback to key field mark
        colors_clean = [c for c in colors if c != "unknown"]
        if colors_clean:
            prompt = f"Look closely at the plumage: Do you clearly see {' and '.join(colors_clean[:2])} feathers?"
            choices = [f"Yes, has {' & '.join(colors_clean[:2])}!", "No, different colors", "Lighting is dim"]
        else:
            prompt = "Look at its behavior right now: Is it hopping actively or perched still?"
            choices = ["Hopping actively", "Perched still on branch", "Flying around"]

    naturalist_speech = (
        f"Wild encounter detected! I have a strong suspect in mind from local Coimbatore records. "
        f"{prompt}"
    )
    audio_url = generate_speech(naturalist_speech)

    return {
        "phase": "question",
        "turn": 2,
        "target_id": top_cand["id"],
        "suspect_hint": f"{top_cand.get('rarity', 'Everyday')} sighting in Coimbatore",
        "naturalist_speech": naturalist_speech,
        "audio_url": audio_url,
        "diagnostic_prompt": prompt,
        "quick_choices": choices
    }
