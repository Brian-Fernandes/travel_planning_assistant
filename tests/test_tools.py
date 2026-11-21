import json
import pytest
from agent.schemas import TravelItinerary
from tools.flight_tool import search_flights
from tools.hotel_tool import search_hotels
from tools.places_tool import search_places
from tools.budget_tool import calculate_budget
from tools.weather_tool import get_weather
from datetime import date, timedelta

from tools.weather_tool import get_weather


def test_schema_validates():
    schema = TravelItinerary.model_json_schema()
    assert "properties" in schema
    assert {"destination", "duration_days", "flight", "hotel", "itinerary", "budget"}.issubset(
        schema["properties"].keys()
    )


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


def test_search_hotels_filters_and_sorts():
    raw = search_hotels.invoke({
        "city": "Goa",
        "max_price_per_night": 3000,
        "min_stars": 4,
    })
    data = json.loads(raw)
    assert data["count"] >= 1
    for hotel in data["hotels"]:
        assert hotel["price_per_night"] <= 3000
        assert hotel["stars"] >= 4


def test_search_places_filters_by_type_and_rating():
    raw = search_places.invoke({
        "city": "Goa",
        "place_type": "fort",
        "min_rating": 4.0,
    })
    data = json.loads(raw)
    assert data["count"] >= 1
    for place in data["places"]:
        assert place["type"].lower() == "fort"
        assert place["rating"] >= 4.0


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
    # 3304 + (1232 * 2) + (800 * 3) + (500 * 3) + 1000 = 10668
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