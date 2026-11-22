import json
import math
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
FLIGHTS_PATH = DATA_DIR / "flights.json"

# 45 Major Commercial Airports with (lat, lon) for true distance-based duration & fare calculation
MAJOR_AIRPORT_HUBS: List[Dict[str, Any]] = [
    {"city": "Delhi", "code": "DEL", "state": "Delhi", "region": "North", "lat": 28.5562, "lon": 77.1000},
    {"city": "Noida", "code": "DXN", "state": "Uttar Pradesh", "region": "North", "lat": 28.1750, "lon": 77.5900},
    {"city": "Mumbai", "code": "BOM", "state": "Maharashtra", "region": "West", "lat": 19.0896, "lon": 72.8656},
    {"city": "Navi Mumbai", "code": "NMI", "state": "Maharashtra", "region": "West", "lat": 18.9902, "lon": 73.0680},
    {"city": "Pune", "code": "PNQ", "state": "Maharashtra", "region": "West", "lat": 18.5821, "lon": 73.9197},
    {"city": "Nagpur", "code": "NAG", "state": "Maharashtra", "region": "West", "lat": 21.0922, "lon": 79.0472},
    {"city": "Bengaluru", "code": "BLR", "state": "Karnataka", "region": "South", "lat": 13.1986, "lon": 77.7066},
    {"city": "Mangaluru", "code": "IXE", "state": "Karnataka", "region": "South", "lat": 12.9613, "lon": 74.8901},
    {"city": "Hyderabad", "code": "HYD", "state": "Telangana", "region": "South", "lat": 17.2403, "lon": 78.4294},
    {"city": "Chennai", "code": "MAA", "state": "Tamil Nadu", "region": "South", "lat": 12.9941, "lon": 80.1709},
    {"city": "Coimbatore", "code": "CJB", "state": "Tamil Nadu", "region": "South", "lat": 11.0300, "lon": 77.0434},
    {"city": "Madurai", "code": "IXM", "state": "Tamil Nadu", "region": "South", "lat": 9.8345, "lon": 78.0934},
    {"city": "Kolkata", "code": "CCU", "state": "West Bengal", "region": "East", "lat": 22.6547, "lon": 88.4467},
    {"city": "Bagdogra", "code": "IXB", "state": "West Bengal", "region": "East", "lat": 26.6812, "lon": 88.3286},
    {"city": "Ahmedabad", "code": "AMD", "state": "Gujarat", "region": "West", "lat": 23.0772, "lon": 72.6347},
    {"city": "Surat", "code": "STV", "state": "Gujarat", "region": "West", "lat": 21.1141, "lon": 72.7418},
    {"city": "Goa", "code": "GOI", "state": "Goa", "region": "West", "lat": 15.3808, "lon": 73.8314},
    {"city": "Jaipur", "code": "JAI", "state": "Rajasthan", "region": "North", "lat": 26.8242, "lon": 75.8122},
    {"city": "Udaipur", "code": "UDR", "state": "Rajasthan", "region": "West", "lat": 24.6177, "lon": 73.8961},
    {"city": "Jodhpur", "code": "JDH", "state": "Rajasthan", "region": "North", "lat": 26.2511, "lon": 73.0489},
    {"city": "Kochi", "code": "COK", "state": "Kerala", "region": "South", "lat": 10.1520, "lon": 76.4019},
    {"city": "Thiruvananthapuram", "code": "TRV", "state": "Kerala", "region": "South", "lat": 8.4821, "lon": 76.9201},
    {"city": "Kozhikode", "code": "CCJ", "state": "Kerala", "region": "South", "lat": 11.1368, "lon": 75.9553},
    {"city": "Guwahati", "code": "GAU", "state": "Assam", "region": "Northeast", "lat": 26.1061, "lon": 91.5859},
    {"city": "Dibrugarh", "code": "DIB", "state": "Assam", "region": "Northeast", "lat": 27.4839, "lon": 95.0169},
    {"city": "Dimapur", "code": "DMU", "state": "Nagaland", "region": "Northeast", "lat": 25.8839, "lon": 93.7711},
    {"city": "Imphal", "code": "IMF", "state": "Manipur", "region": "Northeast", "lat": 24.7600, "lon": 93.8967},
    {"city": "Agartala", "code": "IXA", "state": "Tripura", "region": "Northeast", "lat": 23.8870, "lon": 91.2404},
    {"city": "Bhubaneswar", "code": "BBI", "state": "Odisha", "region": "East", "lat": 20.2444, "lon": 85.8178},
    {"city": "Amritsar", "code": "ATQ", "state": "Punjab", "region": "North", "lat": 31.7096, "lon": 74.7973},
    {"city": "Chandigarh", "code": "IXC", "state": "Chandigarh", "region": "North", "lat": 30.6735, "lon": 76.7885},
    {"city": "Dehradun", "code": "DED", "state": "Uttarakhand", "region": "North", "lat": 30.1897, "lon": 78.1803},
    {"city": "Leh", "code": "IXL", "state": "Ladakh", "region": "North", "lat": 34.1359, "lon": 77.5465},
    {"city": "Srinagar", "code": "SXR", "state": "Jammu & Kashmir", "region": "North", "lat": 33.9871, "lon": 74.7742},
    {"city": "Jammu", "code": "IXJ", "state": "Jammu & Kashmir", "region": "North", "lat": 32.6891, "lon": 74.8374},
    {"city": "Lucknow", "code": "LKO", "state": "Uttar Pradesh", "region": "North", "lat": 26.7606, "lon": 80.8893},
    {"city": "Varanasi", "code": "VNS", "state": "Uttar Pradesh", "region": "North", "lat": 25.4524, "lon": 82.8593},
    {"city": "Visakhapatnam", "code": "VTZ", "state": "Andhra Pradesh", "region": "South", "lat": 17.7212, "lon": 83.2245},
    {"city": "Tirupati", "code": "TIR", "state": "Andhra Pradesh", "region": "South", "lat": 13.6325, "lon": 79.5433},
    {"city": "Indore", "code": "IDR", "state": "Madhya Pradesh", "region": "Central", "lat": 22.7218, "lon": 75.8011},
    {"city": "Bhopal", "code": "BHO", "state": "Madhya Pradesh", "region": "Central", "lat": 23.2875, "lon": 77.3374},
    {"city": "Patna", "code": "PAT", "state": "Bihar", "region": "East", "lat": 25.5913, "lon": 85.0880},
    {"city": "Ranchi", "code": "IXR", "state": "Jharkhand", "region": "East", "lat": 23.3143, "lon": 85.3217},
    {"city": "Raipur", "code": "RPR", "state": "Chhattisgarh", "region": "Central", "lat": 21.1804, "lon": 81.7388},
    {"city": "Port Blair", "code": "IXZ", "state": "Andaman & Nicobar", "region": "Islands", "lat": 11.6412, "lon": 92.7297},
]

AIRLINES = [
    ("IndiGo", "6E", 1.00, "07:15"),
    ("Air India", "AI", 1.24, "13:40"),
]


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _format_duration(dist_km: float) -> str:
    # ~740 km/h cruise + 35 mins taxi/climb/descent buffer, rounded to nearest 5 mins
    total_mins = int(round((35 + (dist_km / 740.0) * 60) / 5.0) * 5)
    hrs, mins = divmod(max(55, total_mins), 60)
    return f"{hrs}h {mins:02d}m"


def build_flights_catalog() -> List[Dict[str, Any]]:
    """Generate realistic distance-scaled domestic routes across all 45 major airports."""
    flights: List[Dict[str, Any]] = []
    counter = 1
    metros = {"Mumbai", "Delhi", "Bengaluru", "Chennai", "Kolkata", "Hyderabad", "Pune", "Ahmedabad"}

    for src in MAJOR_AIRPORT_HUBS:
        for dst in MAJOR_AIRPORT_HUBS:
            if src["city"] == dst["city"]:
                continue
            if src["city"] not in metros and dst["city"] not in metros:
                continue

            dist_km = _haversine_km(src["lat"], src["lon"], dst["lat"], dst["lon"])
            # Skip twin-airport metro pairs < 150 km (e.g., Delhi-Noida, Mumbai-Pune/Navi Mumbai)
            if dist_km < 150:
                continue

            duration_str = _format_duration(dist_km)
            # Base fare scales realistically with distance (~INR 2,500 + INR 2.4/km, rounded to nearest 50)
            base_fare = 2500 + dist_km * 2.4

            for airline, prefix, multiplier, dep_time in AIRLINES:
                fare = round((base_fare * multiplier) / 50.0) * 50
                flights.append(
                    {
                        "flight_id": f"FL_{counter:04d}",
                        "airline": airline,
                        "flight_no": f"{prefix}-{100 + (counter % 899)}",
                        "from": src["city"],
                        "from_code": src["code"],
                        "to": dst["city"],
                        "to_code": dst["code"],
                        "distance_km": round(dist_km),
                        "departure_time": dep_time,
                        "duration": duration_str,
                        "price": float(max(2600, fare)),
                    }
                )
                counter += 1

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(FLIGHTS_PATH, "w", encoding="utf-8") as f:
        json.dump(flights, f, indent=2, ensure_ascii=False)

    print(f"[OK] Saved {len(flights)} realistic distance-scaled routes to {FLIGHTS_PATH}")
    return flights


if __name__ == "__main__":
    build_flights_catalog()