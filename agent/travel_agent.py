import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from typing import Any, Dict, List

from langchain_google_genai import ChatGoogleGenerativeAI

from agent.schemas import TravelItinerary
from services.discovery_service import discover_20_destination_places, search_live_hotels
from services.hub_resolver import get_catalog_flight, resolve_nearest_hub
from services.model_helper import get_available_flash_models
from tools.budget_tool import calculate_budget
from tools.weather_tool import get_weather


def _build_fast_structured_llm(api_key: str):
    """Build low-latency structured-output LLM with full multi-model failover."""
    models = get_available_flash_models(api_key)
    lite_models = [m for m in models if "lite" in m.lower()]
    primary_models = [m for m in models if "lite" not in m.lower()]

    ordered: list[str] = []
    for i in range(max(len(primary_models), len(lite_models))):
        if i < len(primary_models):
            ordered.append(primary_models[i])
        if i < len(lite_models):
            ordered.append(lite_models[i])

    chain = [
        ChatGoogleGenerativeAI(
            model=m,
            google_api_key=api_key,
            thinking_budget=0,
            timeout=25,
            max_retries=1,
        ).with_structured_output(TravelItinerary)
        for m in ordered
    ]
    return chain[0].with_fallbacks(chain[1:]) if len(chain) > 1 else chain[0]


def discover_route_and_places(
    origin: str,
    destination: str,
    custom_pref: str = "",
    force_refresh_places: bool = False,
    api_key: str | None = None,
) -> Dict[str, Any]:
    """Step 1: Resolve nearest airport hubs, catalog flight, and 20 attractions."""
    effective_key = (api_key or os.getenv("GOOGLE_API_KEY", "")).strip()
    if not effective_key:
        raise ValueError("GOOGLE_API_KEY is missing. Provide an api_key or set it in .env.")

    orig_hub = resolve_nearest_hub(origin)
    dest_hub = resolve_nearest_hub(destination, anchor_hub_city=orig_hub["city"])
    flight = get_catalog_flight(orig_hub["city"], dest_hub["city"])
    places, places_source = discover_20_destination_places(
        destination=destination,
        custom_pref=custom_pref,
        api_key=effective_key,
        force_refresh=force_refresh_places,
    )

    return {
        "orig_hub": orig_hub,
        "dest_hub": dest_hub,
        "flight": flight,
        "places": places,
        "places_source": places_source,
    }


def build_day0_itinerary(
    origin: str,
    destination: str,
    duration_days: int,
    budget: float,
    hotel_pref: str,
    selected_places: List[Dict[str, Any]],
    orig_hub: Dict[str, Any],
    dest_hub: Dict[str, Any],
    flight: Dict[str, Any] | None,
    places_source: str,
    travel_date: str = "",
    api_key: str | None = None,
) -> Dict[str, Any]:
    """Step 2: Fetch base hotels & Open-Meteo weather in parallel, then synthesize Day 0..N itinerary."""
    effective_key = (api_key or os.getenv("GOOGLE_API_KEY", "")).strip()
    if not effective_key:
        raise ValueError("GOOGLE_API_KEY is missing. Provide an api_key or set it in .env.")

    sightseeing_start = travel_date or (date.today() + timedelta(days=2)).isoformat()
    day0_date = (date.fromisoformat(sightseeing_start) - timedelta(days=1)).isoformat()

    stay_towns = list(dict.fromkeys([str(p.get("city", destination)).strip() for p in selected_places if p.get("city")]))
    if not stay_towns:
        stay_towns = [destination]

    nights = max(duration_days, 1)

    def _fetch_weather():
        return get_weather.invoke({"city": destination, "days": duration_days, "start_date": sightseeing_start})

    def _fetch_hotels():
        return search_live_hotels(
            city=stay_towns[0],
            hotel_pref=hotel_pref,
            max_nightly_budget=budget / nights,
            api_key=effective_key,
            stay_towns=stay_towns,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        w_fut = pool.submit(_fetch_weather)
        h_fut = pool.submit(_fetch_hotels)
        weather_raw = w_fut.result()
        hotels = h_fut.result()

    weather_summary_map: Dict[str, str] = {}
    try:
        parsed_w = json.loads(weather_raw)
        if parsed_w.get("forecast_available") and isinstance(parsed_w.get("daily_summary"), dict):
            weather_summary_map = parsed_w["daily_summary"]
    except Exception:
        weather_summary_map = {}

    best_hotel = hotels[0] if hotels else None
    if hotels:
        sorted_hotels = sorted(hotels, key=lambda h: float(h.get("price_per_night", 0)))
        best_hotel = sorted_hotels[0]
        flight_price = float(flight["price"]) if flight else 0.0
        for h in sorted_hotels:
            if flight_price + float(h["price_per_night"]) * nights <= budget:
                best_hotel = h

    flight_for_schema = None
    if flight:
        flight_for_schema = {
            "flight_id": str(flight.get("flight_id", "FL_CAT")),
            "airline": str(flight.get("airline", "IndiGo")),
            "origin": str(flight.get("from", orig_hub["city"])),
            "destination": str(flight.get("to", dest_hub["city"])),
            "departure_time": str(flight.get("departure_time", "07:15")),
            "arrival_time": str(flight.get("arrival_time", flight.get("duration", "2h 15m"))),
            "price": float(flight.get("price", 0.0)),
        }

    budget_json = calculate_budget.invoke(
        {
            "flight_cost": float(flight_for_schema["price"]) if flight_for_schema else 0.0,
            "hotel_price_per_night": float(best_hotel["price_per_night"]) if best_hotel else 0.0,
            "nights": nights,
            "daily_food_cost": 0.0,
            "daily_transport_cost": 0.0,
            "activity_cost": 0.0,
        }
    )

    disclaimer = (
        f"Day 0 ({day0_date}) is dedicated solely to arrival transit so all {duration_days} requested days "
        f"(Days 1–{duration_days}) are 100% sightseeing. Return transit at the end of Day {duration_days} is optional."
    )

    synthesis_prompt = f"""
Construct a realistic, zone-clustered travel itinerary from {origin} to {destination}.

VERIFIED INPUT DATA (USE ONLY THESE EXACT RECORDS — DO NOT FABRICATE):
1. Origin Hub: {json.dumps(orig_hub)}
2. Destination Hub: {json.dumps(dest_hub)}
3. Selected Flight: {json.dumps(flight_for_schema)}
4. Base Stay Hotel(s) (Use at most 1-2 base hotels): {json.dumps(hotels[:2])}
5. Verified Budget Breakdown: {budget_json}
6. Verified Open-Meteo Daily Weather Summary by Date (DO NOT INVENT TEMPERATURES): {json.dumps(weather_summary_map)}
7. User-Shortlisted Attractions (Cluster same 'city'/'zone' on the same day): {json.dumps(selected_places)}

STRICT STRUCTURE RULES:
- Set `day_0_disclaimer` to: "{disclaimer}"
- Include `day: 0` (date: "{day0_date}", weather: "Arrival & Staging Transit") as the FIRST entry in `itinerary`:
  * Morning: Travel from {origin} to {orig_hub['city']} Airport ({orig_hub['code']}) and board flight.
  * Afternoon: Arrive at {dest_hub['city']} Airport ({dest_hub['code']}) and take road transfer to base stay in {stay_towns[0]}.
  * Evening: Check-in at base hotel, rest, and acclimatize.
- Include `day: 1` through `day: {duration_days}` (starting on {sightseeing_start}) dedicated purely to sightseeing across the shortlisted attractions, grouping same 'city'/'zone' spots together without repeating attractions.
- For each sightseeing day, copy the exact matching date string from `Verified Open-Meteo Daily Weather Summary by Date` into `weather`; if a date is absent, set `weather` to `"Live forecast unavailable (beyond 14-day window)"`. Never invent temperatures.
- Set `optional_return_path` to a concise return route from {stay_towns[-1]} -> {dest_hub['city']} Airport ({dest_hub['code']}) -> {orig_hub['city']} Airport ({orig_hub['code']}) -> {origin} at the end of Day {duration_days} (do NOT add a Day {duration_days + 1}).
- Use the exact flight, hotel, and budget figures provided above.
"""

    structured_llm = _build_fast_structured_llm(effective_key)
    itinerary: TravelItinerary = structured_llm.invoke(synthesis_prompt)

    return {
        "itinerary": itinerary,
        "live_hotels": hotels,
        "places_source": places_source,
        "weather_summary_map": weather_summary_map,
    }