import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st
from google import genai
from google.genai import types

from services.json_utils import safe_json_extract
from services.model_helper import get_available_flash_models

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PLACES_PATH = DATA_DIR / "places.json"
HOTEL_PATH = DATA_DIR / "hotel.json"
_CACHE_LOCK = threading.Lock()


def _load_json_list(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def _append_to_places_json(
    city: str,
    new_places: List[Dict[str, Any]],
    replace_city: bool = False,
) -> List[Dict[str, Any]]:
    """Atomically append (or refresh) discovered places for a destination inside data/places.json."""
    if not new_places:
        return []
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    city_norm = city.strip().lower()

    with _CACHE_LOCK:
        existing = _load_json_list(PLACES_PATH)
        if replace_city:
            existing = [
                p for p in existing
                if str(p.get("city", "")).strip().lower() != city_norm
                and str(p.get("state", "")).strip().lower() != city_norm
            ]

        seen = {
            (str(p.get("city", "")).strip().lower(), str(p.get("name", "")).strip().lower())
            for p in existing
        }

        for place in new_places:
            stay_city = str(place.get("city", city)).strip() or city.strip()
            key = (stay_city.lower(), str(place.get("name", "")).strip().lower())
            if key[1] and key not in seen:
                seen.add(key)
                existing.append({**place, "city": stay_city, "state": city.strip()})

        with open(PLACES_PATH, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())

        return [
            p for p in existing
            if city_norm in (
                str(p.get("city", "")).strip().lower(),
                str(p.get("state", "")).strip().lower(),
            )
        ]


def _single_shot_generate(
    api_key: str,
    prompt: str,
    use_search: bool = True,
    timeout_ms: int = 20000,
) -> str:
    """Single-attempt Gemini call with automatic multi-model 429/503 failover."""
    models = get_available_flash_models(api_key)
    standard = [m for m in models if "lite" not in m.lower()]
    lite = [m for m in models if "lite" in m.lower()]
    ordered = (standard + lite)[:4] if use_search else (lite + standard)[:4]

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=timeout_ms,
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )

    for model_name in ordered:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[{"google_search": {}}] if use_search else None,
                    temperature=0.2,
                ),
            )
            text = (response.text or "").strip()
            if text:
                return text
        except Exception as exc:
            err_str = str(exc)
            if any(code in err_str for code in ("503", "504", "429", "UNAVAILABLE", "DEADLINE")):
                logging.warning(f"Model {model_name} busy/rate-limited; failing over...")
                continue
            raise
    return ""


def discover_20_destination_places(
    destination: str,
    custom_pref: str = "",
    api_key: str | None = None,
    force_refresh: bool = False,
) -> tuple[List[Dict[str, Any]], str]:
    """
    Discover up to 20 attractions in and around `destination`:
    - Uses places.json cache immediately when >=12 spots exist and no custom preference/refresh is requested.
    - Otherwise queries Google Search (with direct Flash fallback) and persists to data/places.json.
    """
    dest_norm = destination.strip().lower()
    cached = [
        p for p in _load_json_list(PLACES_PATH)
        if dest_norm in (
            str(p.get("city", "")).strip().lower(),
            str(p.get("state", "")).strip().lower(),
            str(p.get("nearest_hub", "")).strip().lower(),
        )
    ]

    if len(cached) >= 12 and not custom_pref.strip() and not force_refresh:
        return cached[:20], f"places.json Cache ({len(cached[:20])} spots)"

    effective_key = (api_key or os.getenv("GOOGLE_API_KEY", "")).strip()
    if not effective_key:
        return cached[:20], "No API Key"

    pref_clause = (
        f"Prioritize attractions matching the user's preferences: '{custom_pref.strip()}'. "
        "If fewer than 20 spots match those preferences, fill the remaining slots with top notable landmarks "
        "in and around the area so the total is 20."
        if custom_pref.strip()
        else "Include a wide variety of the top 20 notable attractions, heritage sites, nature spots, and local experiences in and around the area."
    )

    prompt = (
        f"List 20 real tourist attractions in and around {destination}, India. {pref_clause}\n"
        "Tag each spot with its nearest stay town ('city') and local neighborhood/cluster ('zone').\n"
        "Return ONLY valid JSON (no markdown):\n"
        '{"places": [{"name": "Attraction Name", "city": "Stay Town", "type": "category", "zone": "Cluster/Area", "rating": 4.6}]}'
    )

    raw_text = _single_shot_generate(effective_key, prompt, use_search=True, timeout_ms=20000)
    source_tag = "Live Google Search -> Saved to places.json"
    data = safe_json_extract(raw_text, default={"places": []})
    raw_places = data if isinstance(data, list) else (data.get("places", []) if isinstance(data, dict) else [])

    if not raw_places:
        raw_text = _single_shot_generate(effective_key, prompt, use_search=False, timeout_ms=15000)
        source_tag = "Flash Knowledge Fallback -> Saved to places.json"
        data = safe_json_extract(raw_text, default={"places": []})
        raw_places = data if isinstance(data, list) else (data.get("places", []) if isinstance(data, dict) else [])

    cleaned: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for item in raw_places:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        try:
            rating = round(max(1.0, min(5.0, float(item.get("rating", 4.5)))), 1)
        except (TypeError, ValueError):
            rating = 4.5
        cleaned.append(
            {
                "name": name,
                "city": str(item.get("city", destination)).strip() or destination.strip(),
                "type": str(item.get("type", "landmark")).strip().lower(),
                "zone": str(item.get("zone", "Central Area")).strip(),
                "rating": rating,
            }
        )

    if cleaned:
        saved = _append_to_places_json(destination, cleaned, replace_city=force_refresh)
        result_list = (saved or cleaned)[:20]
        return result_list, f"{source_tag} ({len(result_list)} spots)"

    return cached[:20], ("places.json Fallback" if cached else "No Places Found")


@st.cache_data(ttl=1800, show_spinner=False)
def _cached_hotel_search(
    towns_key: str,
    stay_towns_display: str,
    hotel_pref: str,
    budget_bucket: int,
    api_key: str,
) -> List[Dict[str, Any]]:
    budget_clause = (
        f"Prefer hotels around or under ₹{budget_bucket:,} per night."
        if budget_bucket > 0
        else ""
    )
    prompt = (
        f"Find 3 real, well-rated 3-star+ hotels in {stay_towns_display}, India "
        f"matching: '{hotel_pref}'. {budget_clause}\n"
        "Return ONLY valid JSON:\n"
        '{"hotels": [{"hotel_id": "LIVE_H1", "name": "Hotel Name", "city": "Town Name", '
        '"stars": 4, "price_per_night": 3500, "amenities": ["wifi", "breakfast"], "source_note": "Base stay"}]}'
    )

    raw_text = _single_shot_generate(api_key, prompt, use_search=True, timeout_ms=18000)
    if not raw_text:
        raw_text = _single_shot_generate(api_key, prompt, use_search=False, timeout_ms=15000)
    if not raw_text:
        return []

    data = safe_json_extract(raw_text, default={"hotels": []})
    raw_hotels = data if isinstance(data, list) else (data.get("hotels", []) if isinstance(data, dict) else [])

    cleaned: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for idx, item in enumerate(raw_hotels, start=1):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        try:
            price = float(item.get("price_per_night", 3200))
        except (TypeError, ValueError):
            price = 3200.0
        if price <= 0:
            price = 3200.0
        try:
            stars = max(3, min(5, int(item.get("stars", 3))))
        except (TypeError, ValueError):
            stars = 3
        amenities = item.get("amenities")
        if not isinstance(amenities, list) or not amenities:
            amenities = ["wifi", "ac", "breakfast"]

        cleaned.append(
            {
                "hotel_id": f"LIVE_H{idx}",
                "name": name,
                "city": str(item.get("city", stay_towns_display.split(",")[0])).strip(),
                "stars": stars,
                "price_per_night": round(price, 2),
                "amenities": [str(a) for a in amenities[:5]],
                "source_note": str(item.get("source_note", "Base stay rate")).strip(),
            }
        )
    return cleaned[:4]


def search_live_hotels(
    city: str,
    hotel_pref: str = "Best value affordable hotel",
    max_nightly_budget: float | None = None,
    api_key: str | None = None,
    stay_towns: List[str] | None = None,
) -> List[Dict[str, Any]]:
    """Check data/hotel.json first; fall back to cached live/Flash hotel lookup for primary stay towns."""
    towns = [t.strip() for t in (stay_towns or [city]) if t.strip()]
    towns_norm = {t.lower() for t in towns}

    cached_hotels = _load_json_list(HOTEL_PATH)
    matched = [
        h for h in cached_hotels
        if str(h.get("city", "")).strip().lower() in towns_norm
        or str(h.get("nearest_hub", "")).strip().lower() in towns_norm
    ]
    if len(matched) >= 2:
        return matched[:4]

    effective_key = (api_key or os.getenv("GOOGLE_API_KEY", "")).strip()
    if not effective_key or not towns:
        return matched

    bucket = int(round((max_nightly_budget or 0) / 500.0) * 500)
    towns_display = ", ".join(towns[:2])
    fetched = _cached_hotel_search(
        "|".join(sorted(towns_norm)),
        towns_display,
        hotel_pref.strip(),
        bucket,
        effective_key,
    )
    if fetched:
        with _CACHE_LOCK:
            current = _load_json_list(HOTEL_PATH)
            existing_names = {str(h.get("name", "")).strip().lower() for h in current}
            for item in fetched:
                if item["name"].lower() not in existing_names:
                    current.append(item)
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(HOTEL_PATH, "w", encoding="utf-8") as f:
                json.dump(current, f, indent=2, ensure_ascii=False)
    return fetched or matched