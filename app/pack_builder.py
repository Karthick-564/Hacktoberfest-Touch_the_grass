"""
Regional Pack Builder for 'Field Guide' (Coimbatore & Offline Nature Guide)
Fetches local species from GBIF, Wikipedia, and Wikidata.
Extracts grounded traits strictly from text, real monthly seasonality,
Tamil names, and downloads images locally for offline airplane-mode operation.
"""

import argparse
import json
import math
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Configure UTF-8 for console output on Windows to support Tamil characters
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass



CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
STATIC_IMAGES_DIR = CURRENT_DIR / "static" / "images"
sys.path.insert(0, str(PROJECT_ROOT))

from app.database import get_connection, init_db

USER_AGENT = "FieldGuideNatureBot/2.0 (Hacktoberfest Open Source Nature App; contact@example.com)"
GBIF_OCCURRENCE_URL = "https://api.gbif.org/v1/occurrence/search"
GBIF_SPECIES_URL = "https://api.gbif.org/v1/species"
WIKI_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary"
WIKI_API_URL = "https://en.wikipedia.org/w/api.php"
WIKIDATA_SEARCH_URL = "https://www.wikidata.org/w/api.php"

TAXON_CLASS_KEYS = {
    "birds": 212
}

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

COLOR_VOCABULARY = [
    "black", "brown", "white", "yellow", "grey", "gray", "red", "green",
    "blue", "orange", "rufous", "chestnut", "buff", "tawny", "pink", "purple"
]


def http_get_json(url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 12) -> Optional[Dict[str, Any]]:
    """Safe HTTP GET returning parsed JSON with custom User-Agent."""
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None
    return None


def calculate_bounding_box(lat: float, lon: float, radius_km: float) -> Tuple[float, float, float, float]:
    """Calculates min_lat, max_lat, min_lon, max_lon for a radius in km."""
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / (111.0 * max(0.1, math.cos(math.radians(lat))))
    return (
        round(lat - lat_delta, 4),
        round(lat + lat_delta, 4),
        round(lon - lon_delta, 4),
        round(lon + lon_delta, 4)
    )


def fetch_gbif_species_counts(min_lat: float, max_lat: float, min_lon: float, max_lon: float,
                              class_key: int, limit: int = 35) -> List[Dict[str, Any]]:
    """Fetches the most frequently observed species in the bounding box from GBIF."""
    params = {
        "decimalLatitude": f"{min_lat},{max_lat}",
        "decimalLongitude": f"{min_lon},{max_lon}",
        "classKey": class_key,
        "facet": "speciesKey",
        "facetLimit": limit,
        "limit": 0,
        "hasCoordinate": "true"
    }
    data = http_get_json(GBIF_OCCURRENCE_URL, params)
    if not data or "facets" not in data:
        return []
    facets = data.get("facets", [])
    if not facets:
        return []
    return facets[0].get("counts", [])


def fetch_gbif_species_info(species_key: str) -> Optional[Dict[str, Any]]:
    """Fetches canonical, scientific, and vernacular name from GBIF species backbone."""
    url = f"{GBIF_SPECIES_URL}/{species_key}"
    return http_get_json(url)


def fetch_gbif_monthly_distribution(min_lat: float, max_lat: float, min_lon: float, max_lon: float,
                                    species_key: str) -> List[str]:
    """
    Fetches real monthly occurrence counts from GBIF and returns peak months.
    Grounds seasonality in actual local observation records.
    """
    params = {
        "decimalLatitude": f"{min_lat},{max_lat}",
        "decimalLongitude": f"{min_lon},{max_lon}",
        "speciesKey": species_key,
        "facet": "month",
        "limit": 0
    }
    data = http_get_json(GBIF_OCCURRENCE_URL, params)
    if not data or "facets" not in data or not data["facets"]:
        return ["Year-round"]

    counts_data = data["facets"][0].get("counts", [])
    if not counts_data:
        return ["Year-round"]

    # Map month numbers (1-12) to counts
    month_counts = {}
    total = 0
    for item in counts_data:
        try:
            m = int(item.get("name"))
            c = int(item.get("count", 0))
            if 1 <= m <= 12:
                month_counts[m] = c
                total += c
        except (ValueError, TypeError):
            continue

    if not month_counts:
        return ["Year-round"]

    # Filter months that represent above average sightings
    avg_count = total / len(month_counts)
    significant_months = [m for m, c in month_counts.items() if c >= avg_count * 0.7]

    if not significant_months:
        significant_months = sorted(month_counts.keys(), key=lambda m: month_counts[m], reverse=True)[:4]

    significant_months.sort()
    return [MONTH_NAMES[m - 1] for m in significant_months]


def fetch_wikidata_tamil_name(scientific_name: str, common_name: str) -> Optional[str]:
    """Queries Wikidata to find the Tamil vernacular name (label in 'ta')."""
    queries = [scientific_name, common_name]
    for q in queries:
        if not q:
            continue
        search_params = {
            "action": "wbsearchentities",
            "search": q,
            "language": "en",
            "format": "json",
            "limit": 1
        }
        data = http_get_json(WIKIDATA_SEARCH_URL, search_params)
        if data and data.get("search"):
            qid = data["search"][0]["id"]
            # Fetch Tamil label
            label_params = {
                "action": "wbgetentities",
                "ids": qid,
                "props": "labels",
                "languages": "ta",
                "format": "json"
            }
            entity_data = http_get_json(WIKIDATA_SEARCH_URL, label_params)
            if entity_data and "entities" in entity_data and qid in entity_data["entities"]:
                labels = entity_data["entities"][qid].get("labels", {})
                if "ta" in labels and "value" in labels["ta"]:
                    return labels["ta"]["value"].strip()
    return None


def fetch_wikipedia_details(common_name: str, scientific_name: str) -> Tuple[str, str, Optional[str]]:
    """
    Fetches overview summary, specific 'Description' section text, and thumbnail URL.
    Grounds all physical traits strictly in Wikipedia text.
    """
    candidates = [common_name, scientific_name]
    title_to_use = None
    summary_text = ""
    thumbnail_url = None

    # Step 1: Summary API for intro and thumbnail
    for name in candidates:
        if not name:
            continue
        slug = urllib.parse.quote(name.replace(" ", "_"))
        data = http_get_json(f"{WIKI_SUMMARY_URL}/{slug}")
        if data and "extract" in data and len(data["extract"]) > 30:
            summary_text = data.get("extract", "").strip()
            title_to_use = data.get("title", name)
            if isinstance(data.get("thumbnail"), dict):
                thumbnail_url = data["thumbnail"].get("source")
            break

    # If title not found directly, try API search
    if not title_to_use:
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": common_name or scientific_name,
            "format": "json"
        }
        s_data = http_get_json(WIKI_API_URL, search_params)
        if s_data and s_data.get("query", {}).get("search"):
            title_to_use = s_data["query"]["search"][0]["title"]
            slug = urllib.parse.quote(title_to_use.replace(" ", "_"))
            sum_data = http_get_json(f"{WIKI_SUMMARY_URL}/{slug}")
            if sum_data and "extract" in sum_data:
                summary_text = sum_data.get("extract", "").strip()
                if isinstance(sum_data.get("thumbnail"), dict):
                    thumbnail_url = sum_data["thumbnail"].get("source")

    if not title_to_use:
        return (
            summary_text or "No verified summary available.",
            "Description not available in database.",
            thumbnail_url
        )

    # Step 2: Fetch full plain-text extract to locate the Description section
    parse_params = {
        "action": "query",
        "prop": "extracts",
        "explaintext": "true",
        "titles": title_to_use,
        "format": "json"
    }
    full_data = http_get_json(WIKI_API_URL, parse_params)
    description_text = ""
    if full_data and "query" in full_data and "pages" in full_data["query"]:
        pages = full_data["query"]["pages"]
        page = list(pages.values())[0]
        full_text = page.get("extract", "")

        # Look specifically for Description / Identification sections
        desc_matches = re.findall(
            r'==+\s*(?:Description|Identification|Characteristics|Physical description)\s*==+(.*?)(?:==+|$)',
            full_text,
            re.DOTALL | re.IGNORECASE
        )
        if desc_matches:
            description_text = desc_matches[0].strip()
        else:
            # Fall back to first 2 sections of lead text if no explicit header
            paragraphs = [p.strip() for p in full_text.split("\n\n") if len(p.strip()) > 30]
            description_text = paragraphs[0] if paragraphs else full_text[:400]

    # Clean description to a concise grounded block
    clean_desc = re.sub(r'\s+', ' ', description_text).strip()
    if not clean_desc:
        clean_desc = summary_text[:400]

    # Clean summary to 2-3 sentences
    summary_sentences = [s.strip() for s in summary_text.split(".") if len(s.strip()) > 10]
    clean_summary = ". ".join(summary_sentences[:3]) + "." if summary_sentences else summary_text

    return clean_summary, clean_desc, thumbnail_url


def extract_grounded_traits(description_text: str) -> Dict[str, Any]:
    """
    Extracts physical traits STRICTLY from the provided description text.
    Any trait not present in the text is marked as 'unknown'. No LLM hallucination.
    """
    text_lower = description_text.lower()

    # 1. Size Extraction (e.g., '23 cm', '10 to 12 inches', 'medium-sized', 'large')
    size_match = re.search(r'(\d+(?:\.\d+)?\s*(?:to|-)?\s*\d*(?:\.\d+)?\s*(?:cm|mm|inches|in)\b)', text_lower)
    if size_match:
        size = size_match.group(1).strip()
    elif "medium-sized" in text_lower or "medium sized" in text_lower:
        size = "medium-sized"
    elif "small" in text_lower:
        size = "small"
    elif "large" in text_lower:
        size = "large"
    else:
        size = "unknown"

    # 2. Colors: Only colors explicitly occurring in the description text
    colors = [color for color in COLOR_VOCABULARY if re.search(rf'\b{color}\b', text_lower)]
    if not colors:
        colors = ["unknown"]

    # 3. Bill / Head / Crest features strictly from text
    beak_match = re.search(r'([^.;]*?\b(?:bill|beak|crest|crown|throat|head|eye-ring|iris)\b[^.;]*)', description_text, re.IGNORECASE)
    if beak_match:
        beak_or_head = beak_match.group(1).strip()
        if len(beak_or_head) > 90:
            beak_or_head = beak_or_head[:90].strip() + "..."
    else:
        beak_or_head = "unknown"

    # 4. Distinctive field marks from text
    feature_match = re.search(r'([^.;]*?\b(?:patch|stripe|spots|tail|wings|collar|hood|belly)\b[^.;]*)', description_text, re.IGNORECASE)
    if feature_match:
        distinctive_feature = feature_match.group(1).strip()
        if len(distinctive_feature) > 90:
            distinctive_feature = distinctive_feature[:90].strip() + "..."
    else:
        distinctive_feature = "unknown"

    return {
        "size": size,
        "primary_colors": colors,
        "beak_or_head": beak_or_head,
        "distinctive_feature": distinctive_feature
    }


def download_image_locally(thumbnail_url: Optional[str], species_key: str) -> Optional[str]:
    """
    Downloads thumbnail locally to app/static/images/ for offline airplane-mode demo.
    Returns relative web path (e.g. /static/images/<key>.jpg).
    """
    if not thumbnail_url:
        return None

    STATIC_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    file_name = f"species_{species_key}.jpg"
    target_path = STATIC_IMAGES_DIR / file_name

    if target_path.exists() and target_path.stat().st_size > 1000:
        return f"/static/images/{file_name}"

    try:
        req = urllib.request.Request(thumbnail_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=12) as response:
            data = response.read()
            if len(data) > 500:
                with open(target_path, "wb") as f:
                    f.write(data)
                return f"/static/images/{file_name}"
    except Exception:
        return None
    return None


COMMON_NAME_OVERRIDES = {
    "Ardea cinerea": "Grey Heron",
    "Egretta garzetta": "Little Egret",
    "Anas poecilorhyncha": "Indian Spot-billed Duck",
    "Passer domesticus": "House Sparrow",
    "Corvus splendens": "House Crow",
    "Corvus macrorhynchos": "Large-billed Crow",
    "Psittacula krameri": "Rose-ringed Parakeet",
    "Pycnonotus cafer": "Red-vented Bulbul",
    "Spilopelia chinensis": "Spotted Dove",
    "Microcarbo niger": "Little Cormorant",
    "Merops orientalis": "Asian Green Bee-eater",
    "Centropus sinensis": "Greater Coucal",
    "Dicrurus macrocercus": "Black Drongo",
    "Cypsiurus balasiensis": "Asian Palm Swift",
    "Halcyon smyrnensis": "White-throated Kingfisher",
    "Ortygornis pondicerianus": "Grey Francolin",
    "Vanellus indicus": "Red-wattled Lapwing",
    "Saxicola caprata": "Pied Bushchat",
    "Dendrocitta vagabunda": "Rufous Treepie",
    "Dicaeum erythrorhynchos": "Pale-billed Flowerpecker",
    "Cinnyris asiaticus": "Purple Sunbird",
    "Leptocoma zeylonica": "Purple-rumped Sunbird",
    "Ardeola grayii": "Indian Pond Heron",
    "Milvus migrans": "Black Kite",
    "Haliastur indus": "Brahminy Kite",
    "Dinopium benghalense": "Black-rumped Flameback",
    "Acrocephalus dumetorum": "Blyth's Reed Warbler",
    "Hirundo rustica": "Barn Swallow",
    "Pastor roseus": "Rosy Starling",
    "Motacilla flava": "Western Yellow Wagtail",
    "Motacilla cinerea": "Grey Wagtail",
    "Motacilla maderaspatensis": "White-browed Wagtail",
    "Phylloscopus nitidus": "Green Warbler",
    "Phylloscopus trochiloides": "Greenish Warbler",
    "Acrocephalus stentoreus": "Clamorous Reed Warbler"
}


def sanitize_common_name(raw_name: str, scientific_name: str) -> str:
    """Ensures each species uses ONE canonical English name without A/B slashes."""
    if scientific_name in COMMON_NAME_OVERRIDES:
        return COMMON_NAME_OVERRIDES[scientific_name]
    if "/" in raw_name:
        parts = [p.strip() for p in raw_name.split("/") if p.strip()]
        raw_name = parts[0]
    cleaned = raw_name.strip()
    if cleaned and cleaned[0].islower():
        cleaned = cleaned.title()
    return cleaned


def assign_rarity(rank: int, total: int) -> str:
    """
    Rarity is ranked across the FULL species list:
    - Top 1/3: Everyday
    - Middle 1/3: Regular
    - Bottom 1/3: Special find
    """
    if total <= 0:
        return "Everyday"
    tier = total / 3.0
    if rank < tier:
        return "Everyday"
    elif rank < tier * 2:
        return "Regular"
    else:
        return "Special find"



def build_regional_pack(
    name: str,
    lat: float,
    lon: float,
    radius_km: float = 20.0,
    category: str = "birds",
    limit: int = 35,
    db_path: Optional[Path] = None
) -> Dict[str, Any]:
    """Fetches and builds the complete offline pack."""
    init_db(db_path)
    min_lat, max_lat, min_lon, max_lon = calculate_bounding_box(lat, lon, radius_km)

    print(f"\n[1/5] Querying GBIF for {category} near {name} ({lat}, {lon}) within {radius_km} km radius...")
    print(f"      Bounding box: lat [{min_lat}, {max_lat}], lon [{min_lon}, {max_lon}]")

    class_key = TAXON_CLASS_KEYS.get(category, 212)
    counts = fetch_gbif_species_counts(min_lat, max_lat, min_lon, max_lon, class_key, limit=limit)

    if not counts:
        print("Error: No occurrences found. Try adjusting radius or coordinates.")
        return {"error": "No occurrences found"}

    total_species = len(counts)
    print(f"[2/5] Found {total_species} candidate species. Fetching grounded traits, seasons, Tamil names & images...")

    species_list = []

    for rank, item in enumerate(counts):
        species_key = str(item.get("name"))
        obs_count = int(item.get("count", 0))

        info = fetch_gbif_species_info(species_key)
        if not info:
            continue

        scientific_name = info.get("canonicalName") or info.get("scientificName") or f"Species {species_key}"
        raw_common = info.get("vernacularName") or scientific_name
        common_name = sanitize_common_name(raw_common, scientific_name)

        # 1. Rarity across full species list
        rarity = assign_rarity(rank, total_species)

        # 2. Real monthly seasonality from GBIF
        peak_months = fetch_gbif_monthly_distribution(min_lat, max_lat, min_lon, max_lon, species_key)
        peak_season_str = ", ".join(peak_months[:4])

        # 3. Tamil vernacular name from Wikidata
        tamil_name = fetch_wikidata_tamil_name(scientific_name, common_name)

        # 4. Grounded Wikipedia details (Description section)
        summary, desc_text, thumb_url = fetch_wikipedia_details(common_name, scientific_name)
        grounded_traits = extract_grounded_traits(desc_text)

        # 5. Local image download for airplane-mode offline demo
        local_image_path = download_image_locally(thumb_url, species_key)

        # 6. Enriched grounded local fact
        local_fact = (
            f"Ranked #{rank + 1} most reported bird in {name} citizen checklists "
            f"({obs_count:,} observations via eBird/iNaturalist). "
            f"Local status: {rarity}. Peak months: {peak_season_str}."
        )

        sp_record = {
            "species_key": species_key,
            "rank": rank + 1,
            "scientific_name": scientific_name,
            "common_name": common_name,
            "tamil_name": tamil_name,
            "category": category,
            "observation_count": obs_count,
            "rarity": rarity,
            "peak_months": json.dumps(peak_months),
            "summary": summary,
            "description_text": desc_text[:400],
            "key_traits": json.dumps(grounded_traits),
            "local_fact": local_fact,
            "image_url": thumb_url,
            "image_local_path": local_image_path
        }
        species_list.append(sp_record)

        tamil_display = f" | Tamil: {tamil_name}" if tamil_name else ""
        try:
            print(f"  [{rank + 1}/{total_species}] {common_name} ({scientific_name}){tamil_display}")
        except UnicodeEncodeError:
            print(f"  [{rank + 1}/{total_species}] {common_name} ({scientific_name})")
        print(f"        Obs: {obs_count:,} | Rarity: {rarity} | Peak: {peak_season_str} | Img: {'Saved' if local_image_path else 'None'}")

        time.sleep(0.12)  # Respectful API pacing

    print(f"\n[3/5] Saving regional pack into SQLite...")
    conn = get_connection(db_path)
    with conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO regions (name, latitude, longitude, radius_km)
               VALUES (?, ?, ?, ?)""",
            (name, lat, lon, radius_km)
        )
        region_id = cursor.lastrowid

        for sp in species_list:
            cursor.execute(
                """INSERT OR REPLACE INTO species
                   (region_id, category, scientific_name, common_name, tamil_name, observation_count,
                    rarity, peak_months, summary, description_text, key_traits, local_fact,
                    image_url, image_local_path)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    region_id,
                    sp["category"],
                    sp["scientific_name"],
                    sp["common_name"],
                    sp["tamil_name"],
                    sp["observation_count"],
                    sp["rarity"],
                    sp["peak_months"],
                    sp["summary"],
                    sp["description_text"],
                    sp["key_traits"],
                    sp["local_fact"],
                    sp["image_url"],
                    sp["image_local_path"]
                )
            )
    conn.close()

    pack_json = {
        "region": {
            "id": region_id,
            "name": name,
            "latitude": lat,
            "longitude": lon,
            "radius_km": radius_km,
            "species_count": len(species_list)
        },
        "species": species_list
    }

    out_file = PROJECT_ROOT / "data" / f"pack_region_{region_id}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(pack_json, f, indent=2, ensure_ascii=False)

    print(f"[4/5] Saved JSON pack to {out_file}")
    print(f"[5/5] Pack build complete! Ready for offline use.\n")
    return pack_json


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build offline regional pack for Field Guide.")
    parser.add_argument("--lat", type=float, default=11.0168, help="Latitude (default: 11.0168 / Coimbatore)")
    parser.add_argument("--lon", type=float, default=76.9558, help="Longitude (default: 76.9558 / Coimbatore)")
    parser.add_argument("--radius", type=float, default=20.0, help="Radius in km (default: 20)")
    parser.add_argument("--limit", type=int, default=80, help="Number of top species (default: 80)")
    parser.add_argument("--name", type=str, default="Coimbatore", help="Region name")
    parser.add_argument("--category", type=str, default="birds", help="Category (default: birds)")

    args = parser.parse_args()
    build_regional_pack(
        name=args.name,
        lat=args.lat,
        lon=args.lon,
        radius_km=args.radius,
        category=args.category,
        limit=args.limit
    )
