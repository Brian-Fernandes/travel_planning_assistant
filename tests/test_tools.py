import json
from datetime import date, timedelta
from unittest.mock import patch

import pytest

from agent.schemas import TravelItinerary
from services.discovery_service import discover_20_destination_places, search_live_hotels
from services.hub_resolver import get_catalog_flight, resolve_nearest_hub
from tools.budget_tool import calculate_budget
from tools.flight_tool import search_flights
from tools.weather_tool import get_weather


def test_schema_validates():
    schema = TravelItinerary.model_json_schema()
    assert "properties" in schema
    assert {
        "destination",
        "duration_days",
        "day_0_disclaimer",
        "flight",
        "hotel",
        "itinerary",
        "optional_return_path",
        "budget",
    }.issubset(schema["properties"].keys())


def test_resolve_nearest_hub_and_catalog_flight():
    hub = resolve_nearest_hub("Udupi")
    assert hub["code"] == "IXE"
    assert hub["city"].lower() == "mangaluru"

    flight = get_catalog_flight("Mumbai", "Goa")
    assert flight is not None
    assert flight["from"].lower() == "mumbai"
    assert flight["to"].lower() == "goa"


def test_search_flights_valid_route():
    raw = search_flights.invoke({"origin": "Mumbai", "destination": "Goa"})
    data = json.loads(raw)
    assert data["count"] >= 1
    assert data["flights"][0]["from"].lower() == "mumbai"
    assert data["flights"][0]["to"].lower() == "goa"


def test_search_flights_invalid_date_format():
    raw = search_flights.invoke({
        "origin": "Mumbai",
        "destination": "Goa",
        "travel_date": "15-07-2025",
    })
    data = json.loads(raw)
    assert "error" in data


def test_discover_20_destination_places_from_cache():
    sample_cache = [
        {"name": f"Spot {i}", "city": "Goa", "state": "Goa", "zone": "North", "type": "landmark", "rating": 4.5}
        for i in range(15)
    ]
    with patch("services.discovery_service._load_json_list", return_value=sample_cache):
        places, source = discover_20_destination_places("Goa", custom_pref="", api_key="")
    assert len(places) == 15
    assert "Cache" in source


def test_search_live_hotels_from_cache():
    sample_hotels = [
        {
            "hotel_id": "HTL_0001",
            "name": "Coastal Stay",
            "city": "Goa",
            "nearest_hub": "Goa",
            "stars": 4,
            "price_per_night": 2800.0,
            "amenities": ["wifi", "ac"],
        },
        {
            "hotel_id": "HTL_0002",
            "name": "Palm Resort",
            "city": "Goa",
            "nearest_hub": "Goa",
            "stars": 3,
            "price_per_night": 2200.0,
            "amenities": ["wifi", "breakfast"],
        },
    ]
    with patch("services.discovery_service._load_json_list", return_value=sample_hotels):
        hotels = search_live_hotels(city="Goa", max_nightly_budget=3000.0, api_key="")
    assert len(hotels) == 2
    assert hotels[0]["city"] == "Goa"


def test_calculate_budget_math():
    raw = calculate_budget.invoke({
        "flight_cost": 3304,
        "hotel_price_per_night": 1232,
        "nights": 2,
        "daily_food_cost": 800,
        "daily_transport_cost": 500,
        "activity_cost": 1000,
    })
    data = json.loads(raw)
    assert data["hotel_cost"] == 2464
    assert data["food_cost"] == 2400
    assert data["transport_cost"] == 1500
    assert data["total_estimated_cost"] == 10668


def test_calculate_budget_rejects_negative_values():
    raw = calculate_budget.invoke({
        "flight_cost": -500,
        "hotel_price_per_night": 1000,
        "nights": 2,
    })
    data = json.loads(raw)
    assert "error" in data


@pytest.mark.integration
def test_weather_tool_live_open_meteo():
    raw = get_weather.invoke({"city": "Goa", "days": 3})
    data = json.loads(raw)
    assert "error" not in data
    assert data["city"].lower() == "goa"
    assert len(data["forecast"]["time"]) == 3
    assert len(data["daily_summary"]) == 3


def test_weather_beyond_14_days_returns_unavailable_notice():
    future_date = (date.today() + timedelta(days=20)).isoformat()
    raw = get_weather.invoke({
        "city": "Goa",
        "days": 3,
        "start_date": future_date,
    })
    data = json.loads(raw)
    assert data["forecast_available"] is False
    assert data["trip_start"] == future_date
    assert data["daily_summary"] == {}