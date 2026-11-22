from datetime import date, datetime, timedelta
import json

import requests
from langchain.tools import tool

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
MAX_FORECAST_HORIZON_DAYS = 14

# Official Open-Meteo WMO Weather Interpretation Codes (WW)
WMO_CODE_LABELS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def _format_daily_summaries(daily: dict) -> dict[str, str]:
    """Pair exact Open-Meteo min/max temperatures with official WMO condition labels per date."""
    dates = daily.get("time") or []
    codes = daily.get("weather_code") or []
    t_mins = daily.get("temperature_2m_min") or []
    t_maxs = daily.get("temperature_2m_max") or []

    summaries: dict[str, str] = {}
    for idx, d_str in enumerate(dates):
        code = codes[idx] if idx < len(codes) else None
        condition = WMO_CODE_LABELS.get(int(code), "") if code is not None else ""
        t_min = t_mins[idx] if idx < len(t_mins) else None
        t_max = t_maxs[idx] if idx < len(t_maxs) else None

        if t_min is not None and t_max is not None and condition:
            summaries[d_str] = f"{round(float(t_min))}°C–{round(float(t_max))}°C, {condition}"
        elif t_min is not None and t_max is not None:
            summaries[d_str] = f"{round(float(t_min))}°C–{round(float(t_max))}°C"
        elif condition:
            summaries[d_str] = condition
        else:
            summaries[d_str] = "Live weather data unavailable"
    return summaries


@tool
def get_weather(city: str, days: int = 3, start_date: str = "") -> str:
    """Get weather forecast for a city using Open-Meteo."""
    city = city.strip()

    if not city:
        return json.dumps({"error": "City cannot be empty."})

    if days < 1 or days > 7:
        return json.dumps({"error": "days must be between 1 and 7."})

    today = date.today()
    max_forecast_date = today + timedelta(days=MAX_FORECAST_HORIZON_DAYS)

    if start_date:
        try:
            trip_start = datetime.strptime(start_date.strip(), "%Y-%m-%d").date()
        except ValueError:
            return json.dumps({"error": "start_date must use YYYY-MM-DD format."})
    else:
        trip_start = today + timedelta(days=1)

    trip_end = trip_start + timedelta(days=days - 1)

    if trip_start > max_forecast_date:
        return json.dumps({
            "city": city.title(),
            "trip_start": trip_start.isoformat(),
            "trip_end": trip_end.isoformat(),
            "forecast_available": False,
            "daily_summary": {},
            "message": (
                f"No live weather forecast available for {trip_start.isoformat()} to "
                f"{trip_end.isoformat()} (live forecasts cover up to {MAX_FORECAST_HORIZON_DAYS} days ahead)."
            ),
        }, indent=2)

    api_end_date = min(trip_end, max_forecast_date)
    partial_cutoff = api_end_date < trip_end

    try:
        geo_response = requests.get(
            GEOCODING_URL,
            params={
                "name": city,
                "count": 1,
                "language": "en",
                "format": "json",
                "countryCode": "IN",
            },
            timeout=10,
        )
        geo_response.raise_for_status()

        results = geo_response.json().get("results", [])
        if not results:
            return json.dumps({"error": f"Could not find location: {city}"})

        location = results[0]
        if location.get("country_code") != "IN":
            return json.dumps({"error": f"Could not find an Indian location for: {city}"})

        weather_response = requests.get(
            WEATHER_URL,
            params={
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "daily": (
                    "weather_code,"
                    "temperature_2m_max,"
                    "temperature_2m_min,"
                    "precipitation_probability_max"
                ),
                "start_date": trip_start.isoformat(),
                "end_date": api_end_date.isoformat(),
                "timezone": "auto",
            },
            timeout=10,
        )
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        daily_raw = weather_data.get("daily", {})

        payload = {
            "city": location["name"],
            "country": location.get("country"),
            "trip_start": trip_start.isoformat(),
            "trip_end": trip_end.isoformat(),
            "forecast_available": True,
            "daily_summary": _format_daily_summaries(daily_raw),
            "forecast": daily_raw,
        }

        if partial_cutoff:
            payload["note"] = (
                f"Live forecast is only available through {api_end_date.isoformat()}. "
                f"Dates after {api_end_date.isoformat()} do not have live weather data yet."
            )

        return json.dumps(payload, indent=2)

    except requests.RequestException as exc:
        return json.dumps({"error": f"Weather API request failed: {exc}"})
    except (KeyError, ValueError) as exc:
        return json.dumps({"error": f"Invalid weather API response: {exc}"})