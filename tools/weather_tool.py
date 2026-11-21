from datetime import date, datetime, timedelta
import json

import requests
from langchain.tools import tool

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
MAX_FORECAST_HORIZON_DAYS = 14


@tool
def get_weather(city: str, days: int = 3, start_date: str = "") -> str:
    """Get weather forecast for a city using Open-Meteo.

    Args:
        city: City name.
        days: Number of trip days, from 1 to 7.
        start_date: Optional trip start date in YYYY-MM-DD format. Defaults to tomorrow.

    Returns:
        Weather forecast or availability notice as JSON.
    """
    city = city.strip()

    if not city:
        return json.dumps({"error": "City cannot be empty."})

    if days < 1 or days > 7:
        return json.dumps({"error": "days must be between 1 and 7."})

    today = date.today()
    max_forecast_date = today + timedelta(days=MAX_FORECAST_HORIZON_DAYS)

    # Default to tomorrow if user did not specify a start date
    if start_date:
        try:
            trip_start = datetime.strptime(start_date.strip(), "%Y-%m-%d").date()
        except ValueError:
            return json.dumps({"error": "start_date must use YYYY-MM-DD format."})
    else:
        trip_start = today + timedelta(days=1)

    trip_end = trip_start + timedelta(days=days - 1)

    # Case 1: Entire trip is beyond the 14-day live forecast window
    if trip_start > max_forecast_date:
        return json.dumps({
            "city": city.title(),
            "trip_start": trip_start.isoformat(),
            "trip_end": trip_end.isoformat(),
            "forecast_available": False,
            "message": (
                f"No live weather forecast available for {trip_start.isoformat()} to "
                f"{trip_end.isoformat()} (live forecasts cover up to {MAX_FORECAST_HORIZON_DAYS} days ahead). "
                "Flight, hotel, and itinerary planning can still proceed."
            ),
        }, indent=2)

    # Case 2 & 3: Full or partial overlap with the 14-day window
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

        payload = {
            "city": location["name"],
            "country": location.get("country"),
            "trip_start": trip_start.isoformat(),
            "trip_end": trip_end.isoformat(),
            "forecast_available": True,
            "forecast": weather_data.get("daily", {}),
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