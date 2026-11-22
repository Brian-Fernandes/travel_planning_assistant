import math
from typing import Any, Dict, List

import requests

from scripts.build_flights import MAJOR_AIRPORT_HUBS
from tools.flight_tool import load_flights

KNOWN_COORDS: Dict[str, tuple[float, float]] = {
    "sindhudurg": (16.0190, 73.6860),
    "kudal": (16.0135, 73.6897),
    "malvan": (16.0575, 73.4650),
    "konkan": (16.0190, 73.6860),
    "udupi": (13.3409, 74.7421),
    "hubbali": (15.3647, 75.1240),
    "hubli": (15.3647, 75.1240),
    "dharwad": (15.4589, 75.0078),
    "ratangarh": (28.0819, 74.6119),
    "ellora": (20.0258, 75.1780),
    "ajanta": (20.5519, 75.7033),
    "chhatrapati sambhajinagar": (19.8762, 75.3433),
    "aurangabad": (19.8762, 75.3433),
    "assam": (26.2006, 92.9376),
    "kaziranga": (26.5775, 93.1711),
    "nagaland": (25.6751, 94.1086),
    "kohima": (25.6751, 94.1086),
    "ladakh": (34.1526, 77.5771),
    "manali": (32.2432, 77.1892),
    "shimla": (31.1048, 77.1734),
    "darjeeling": (27.0410, 88.2663),
    "gangtok": (27.3314, 88.6138),
    "munnar": (10.0889, 77.0595),
    "alleppey": (9.4981, 76.3388),
    "rishikesh": (30.0869, 78.2676),
    "shillong": (25.5788, 91.8933),
}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _geocode_indian_location(location: str) -> tuple[float, float] | None:
    loc_norm = location.strip().lower()
    if loc_norm in KNOWN_COORDS:
        return KNOWN_COORDS[loc_norm]

    try:
        resp = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": location.strip(),
                "count": 5,
                "language": "en",
                "format": "json",
                "countryCode": "IN",
            },
            timeout=5,
        )
        resp.raise_for_status()
        results: List[Dict[str, Any]] = resp.json().get("results", [])
        indian_results = [r for r in results if r.get("country_code") == "IN"]
        if not indian_results:
            return None

        def _score(item: Dict[str, Any]) -> tuple[int, int]:
            exact = 1 if str(item.get("name", "")).strip().lower() == loc_norm else 0
            pop = int(item.get("population") or 0)
            return (exact, pop)

        best = max(indian_results, key=_score)
        return float(best["latitude"]), float(best["longitude"])
    except Exception:
        return None


def resolve_nearest_hub(
    location: str,
    anchor_hub_city: str | None = None,
) -> Dict[str, Any]:
    """
    Resolve any Indian city/state/town to its nearest sensible commercial airport hub.
    If `anchor_hub_city` is provided (for a destination), slightly prefers a nearby hub
    (within 350 km of the destination) that has a direct flight from `anchor_hub_city`,
    while never picking a hub > 500 km farther than the true nearest hub.
    """
    loc_clean = location.strip()
    loc_norm = loc_clean.lower()

    for hub in MAJOR_AIRPORT_HUBS:
        if hub["city"].lower() == loc_norm or hub["state"].lower() == loc_norm:
            return {**hub, "transfer_km": 0, "input_name": loc_clean}

    coords = _geocode_indian_location(loc_clean)
    if coords is None:
        return {**MAJOR_AIRPORT_HUBS[0], "transfer_km": 0, "input_name": loc_clean}

    lat, lon = coords
    ranked = sorted(
        MAJOR_AIRPORT_HUBS,
        key=lambda h: _haversine_km(lat, lon, h["lat"], h["lon"]),
    )
    nearest_hub = ranked[0]
    nearest_dist = _haversine_km(lat, lon, nearest_hub["lat"], nearest_hub["lon"])

    chosen = nearest_hub
    if anchor_hub_city:
        flights = load_flights()
        direct_targets = {
            f["to"].strip().lower()
            for f in flights
            if f["from"].strip().lower() == anchor_hub_city.strip().lower()
        }
        for candidate in ranked[:5]:
            cand_dist = _haversine_km(lat, lon, candidate["lat"], candidate["lon"])
            # Only consider hubs reasonably close to destination and within +500 km of nearest hub
            if cand_dist <= 350.0 and (cand_dist - nearest_dist) <= 500.0:
                if candidate["city"].strip().lower() in direct_targets:
                    chosen = candidate
                    break

    return {
        **chosen,
        "transfer_km": round(_haversine_km(lat, lon, chosen["lat"], chosen["lon"])),
        "input_name": loc_clean,
    }


def get_catalog_flight(origin_hub: str, dest_hub: str) -> Dict[str, Any] | None:
    """Find cheapest direct or 1-stop connecting hub flight from data/flights.json."""
    if origin_hub.strip().lower() == dest_hub.strip().lower():
        return None

    flights = load_flights()
    direct = [
        f for f in flights
        if f["from"].strip().lower() == origin_hub.strip().lower()
        and f["to"].strip().lower() == dest_hub.strip().lower()
    ]
    if direct:
        direct.sort(key=lambda x: float(x["price"]))
        best = dict(direct[0])
        best.setdefault("arrival_time", best.get("duration", "2h 15m"))
        return best

    for via in ("Delhi", "Mumbai", "Bengaluru", "Kolkata"):
        if via.lower() in (origin_hub.lower(), dest_hub.lower()):
            continue
        leg1 = [f for f in flights if f["from"].lower() == origin_hub.lower() and f["to"].lower() == via.lower()]
        leg2 = [f for f in flights if f["from"].lower() == via.lower() and f["to"].lower() == dest_hub.lower()]
        if leg1 and leg2:
            leg1.sort(key=lambda x: float(x["price"]))
            leg2.sort(key=lambda x: float(x["price"]))
            return {
                "flight_id": f"{leg1[0]['flight_id']}+{leg2[0]['flight_id']}",
                "airline": f"{leg1[0]['airline']} (via {via})",
                "flight_no": f"{leg1[0]['flight_no']} + {leg2[0]['flight_no']}",
                "from": origin_hub,
                "to": dest_hub,
                "departure_time": leg1[0].get("departure_time", "07:15"),
                "arrival_time": f"via {via} ({leg1[0]['duration']} + {leg2[0]['duration']})",
                "duration": f"{leg1[0]['duration']} + {leg2[0]['duration']}",
                "price": float(leg1[0]["price"]) + float(leg2[0]["price"]),
            }
    return None