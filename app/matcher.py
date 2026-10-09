"""
Matching Engine for 'Field Guide'
1. Pre-filters local species to top 8-10 candidates in pure Python code (colors, features, habitat).
2. Supports generic category-agnostic observation payload: { category, answers, free_text }.
3. Sends ONLY the top 8-10 candidates to the local LLM (Ollama).
4. Strictly validates LLM output, rejecting any hallucinated species_id.
5. Handles 'not_sure' gracefully to guide the user back to observation.
"""

import json
import re
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional, Tuple

OLLAMA_API_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "gemma2:2b"  # Or qwen2.5:1.5b / qwen2.5:3b


def prefilter_candidates(
    species_pool: List[Dict[str, Any]],
    observation: Dict[str, Any],
    max_candidates: int = 10
) -> List[Dict[str, Any]]:
    """
    Pre-filters a regional species list down to 8-10 candidates in plain Python.
    Prevents overwhelming small 1B-4B local LLMs with 80+ candidates.
    Supports generic payload shape: { "category": "...", "answers": { ... }, "free_text": "..." }
    """
    answers = observation.get("answers", observation)
    free_text = observation.get("free_text", observation.get("sound_description", ""))

    obs_colors = answers.get("colors", answers.get("primary_colors", []))
    if isinstance(obs_colors, str):
        obs_colors = [obs_colors]
    obs_colors = [c.lower().strip() for c in obs_colors if c]

    obs_text = " ".join([
        str(answers.get("size", answers.get("size_comparison", ""))),
        str(answers.get("beak_head", answers.get("beak_or_head", ""))),
        str(answers.get("where_seen", "")),
        str(answers.get("behavior", "")),
        str(answers.get("leaf_shape", "")),
        str(answers.get("leaf_arrangement", "")),
        str(answers.get("bark", "")),
        str(free_text or "")
    ]).lower()

    scored: List[Tuple[float, Dict[str, Any]]] = []

    for sp in species_pool:
        score = 0.0

        # Parse grounded traits
        traits = sp.get("key_traits")
        if isinstance(traits, str):
            try:
                traits = json.loads(traits)
            except Exception:
                traits = {}
        elif not isinstance(traits, dict):
            traits = {}

        # 1. Color overlap score
        sp_colors = [c.lower() for c in traits.get("primary_colors", []) if c != "unknown"]
        matched_colors = set(obs_colors).intersection(set(sp_colors))
        score += len(matched_colors) * 3.0

        # 2. Text keyword matches in Description and Traits
        desc_text = (sp.get("description_text", "") + " " + sp.get("summary", "")).lower()
        obs_words = set(re.findall(r'\b\w{4,}\b', obs_text))
        matched_words = [w for w in obs_words if w in desc_text]
        score += min(len(matched_words) * 0.5, 4.0)

        # 3. Frequency boost based on rarity
        rarity = sp.get("rarity")
        if rarity == "Everyday":
            score += 1.0
        elif rarity == "Regular":
            score += 0.5

        scored.append((score, sp))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:max_candidates]]


def build_matching_prompt(candidates: List[Dict[str, Any]], observation: Dict[str, Any]) -> str:
    """Constructs a strict grounding prompt for the local model."""
    candidate_summary = []
    for c in candidates:
        tamil_display = f" (Tamil: {c.get('tamil_name')})" if c.get('tamil_name') else ""
        candidate_summary.append({
            "species_id": c["id"],
            "name": f"{c['common_name']}{tamil_display} ({c['scientific_name']})",
            "rarity": c.get("rarity", "Everyday"),
            "grounded_description": c.get("description_text", c.get("summary", ""))[:300]
        })

    candidate_json = json.dumps(candidate_summary, indent=2, ensure_ascii=False)
    answers = observation.get("answers", observation)
    free_text = observation.get("free_text", observation.get("sound_description", ""))

    return f"""You are an educational field naturalist in an offline nature guide app.
Your job is to match the user's field observation against CANDIDATES, and help them OBSERVE.

STRICT RULES:
1. ONLY pick from the candidate list below. NEVER invent species or IDs outside this list.
2. Ground all reasoning strictly in the grounded description. Do NOT invent physical traits.
3. If the observation matches 1 to 3 candidates, return status "matched" with top candidates.
4. For each candidate, formulate a single actionable "confirm_question" pointing out ONE specific field mark the user can check right now with their eyes (e.g. beak color, eye patch, tail shape).
5. If observations are too vague (e.g. just 'small brown bird') or contradict the candidates:
   - Return status "not_sure".
   - Return "candidates": [].
   - Provide a "next_observation_question" asking them to look for a specific diagnostic mark.
6. Return ONLY valid JSON matching the exact schema. No extra text or markdown.

CANDIDATES:
{candidate_json}

USER OBSERVATION:
- Category: {observation.get('category', 'birds')}
- Answers: {json.dumps(answers, ensure_ascii=False)}
- Notes / Sound: {free_text}

RESPONSE SCHEMA:
{{
  "status": "matched" | "not_sure",
  "confidence_reasoning": "1-2 sentences strictly grounded in facts",
  "candidates": [
    {{
      "species_id": <int>,
      "common_name": "<str>",
      "why_it_fits": "<str>",
      "confirm_question": "<str>"
    }}
  ],
  "next_observation_question": "<str or null>",
  "observation_prompt": "Now look up. Watch it for a minute."
}}"""


def query_local_ollama(prompt: str, model_name: str = DEFAULT_MODEL, timeout: int = 25) -> Optional[Dict[str, Any]]:
    """Sends prompt to local Ollama instance with structured JSON output."""
    payload = {
        "model": model_name,
        "prompt": prompt,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }
    req = urllib.request.Request(
        OLLAMA_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw_response = data.get("response", "")
            return json.loads(raw_response)
    except Exception:
        return None


def match_observation(
    species_pool: List[Dict[str, Any]],
    observation: Dict[str, Any],
    model_name: str = DEFAULT_MODEL
) -> Dict[str, Any]:
    """
    Full pipeline:
    1. Pre-filter in Python to top 8-10 candidates.
    2. Query local LLM.
    3. Strictly validate output: reject any species_id not in the sent candidates!
    """
    filtered = prefilter_candidates(species_pool, observation, max_candidates=10)
    species_by_id = {c["id"]: c for c in filtered}
    prompt = build_matching_prompt(filtered, observation)
    llm_output = query_local_ollama(prompt, model_name=model_name, timeout=4)

    if not llm_output or not isinstance(llm_output, dict):
        results = []
        for c in filtered[:3]:
            traits = {}
            try:
                traits = json.loads(c.get("key_traits", "{}")) if isinstance(c.get("key_traits"), str) else c.get("key_traits", {})
            except Exception:
                pass
            feature = traits.get("distinctive_feature") or traits.get("beak_or_head")
            if not feature or feature == "unknown":
                feature = c.get("summary", "")[:70]
            confirm_q = f"Check closely: {feature}?"

            results.append({
                "species_id": c["id"],
                "common_name": c["common_name"],
                "tamil_name": c.get("tamil_name"),
                "scientific_name": c.get("scientific_name"),
                "rarity": c.get("rarity", "Everyday"),
                "why_it_fits": f"Matches field marks and regional Coimbatore records.",
                "confirm_question": confirm_q,
                "local_fact": c.get("local_fact"),
                "image_local_path": c.get("image_local_path")
            })

        return {
            "status": "matched" if results else "not_sure",
            "engine_used": "grounded_regional_matcher",
            "confidence_reasoning": "Offline grounded matching based on color, morphological features, and regional frequency.",
            "candidates": results,
            "observation_prompt": "Now look up. Watch it for a minute."
        }

    # Strict Validation: Reject hallucinated species IDs
    valid_candidates = []
    for cand in llm_output.get("candidates", []):
        cand_id = cand.get("species_id")
        if cand_id in allowed_ids:
            sp = species_by_id[cand_id]
            valid_candidates.append({
                "species_id": cand_id,
                "common_name": sp["common_name"],
                "tamil_name": sp.get("tamil_name"),
                "scientific_name": sp.get("scientific_name"),
                "rarity": sp.get("rarity", "Everyday"),
                "why_it_fits": cand.get("why_it_fits", "Matches observed traits in Coimbatore regional pack."),
                "confirm_question": cand.get("confirm_question", f"Check: {sp.get('summary', '')[:70]}?"),
                "local_fact": sp.get("local_fact"),
                "image_local_path": sp.get("image_local_path")
            })

    if not valid_candidates or llm_output.get("status") == "not_sure":
        return {
            "status": "not_sure",
            "engine_used": f"{model_name} (Local Gemma 2 LLM)",
            "confidence_reasoning": llm_output.get("confidence_reasoning", "Observations are not specific enough to separate candidates."),
            "candidates": [],
            "next_observation_question": llm_output.get(
                "next_observation_question",
                "Check the beak shape closely: is it thick and conical for seeds, or slender for insects? Also observe if it stays on the ground or in tree canopies."
            ),
            "observation_prompt": "Stay still and observe for another 15 seconds before tapping again."
        }

    return {
        "status": "matched",
        "engine_used": f"{model_name} (Local Gemma 2 LLM)",
        "confidence_reasoning": llm_output.get("confidence_reasoning", "Observations match local records."),
        "candidates": valid_candidates[:3],
        "observation_prompt": llm_output.get("observation_prompt", "Now look up. Watch it for a minute.")
    }
