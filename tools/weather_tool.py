import json

import requests
from langchain.tools import tool


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


@tool
def get_weather(city: str, days: int = 3) -> str:
    """Get weather forecast for a city using Open-Meteo.

    Args:
        city: City name.
        days: Number of forecast days, from 1 to 7.

    Returns:
        Weather forecast as JSON.
    """
    city = city.strip()

    if not city:
        return json.dumps({"error": "City cannot be empty."})

    if days < 1 or days > 7:
        return json.dumps({
            "error": "days must be between 1 and 7."
        })

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

        geo_data = geo_response.json()
        results = geo_data.get("results", [])

        if not results:
            return json.dumps({
                "error": f"Could not find location: {city}"
            })

        location = results[0]

        if location.get("country_code") != "IN":
            return json.dumps({
                "error": f"Could not find an Indian location for: {city}"
            })

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
                "forecast_days": days,
                "timezone": "auto",
            },
            timeout=10,
        )
        weather_response.raise_for_status()

        weather_data = weather_response.json()

        return json.dumps({
            "city": location["name"],
            "country": location.get("country"),
            "forecast": weather_data.get("daily", {}),
        }, indent=2)

    except requests.RequestException as exc:
        return json.dumps({
            "error": f"Weather API request failed: {exc}"
        })

    except (KeyError, ValueError) as exc:
        return json.dumps({
            "error": f"Invalid weather API response: {exc}"
        })