import os
from unittest.mock import MagicMock, patch

import pytest

from agent.schemas import BudgetBreakdown, DayPlan, HotelOption, TravelItinerary
from agent.travel_agent import build_day0_itinerary, discover_route_and_places


def test_discover_route_and_places_step1():
    mock_places = [
        {"name": "Aguada Fort", "city": "Goa", "type": "fort", "zone": "North Goa", "rating": 4.6}
    ]
    with patch(
        "agent.travel_agent.discover_20_destination_places",
        return_value=(mock_places, "places.json Cache (1 spots)"),
    ):
        res = discover_route_and_places(
            origin="Mumbai",
            destination="Goa",
            custom_pref="forts",
            api_key="test-key",
        )
    assert res["orig_hub"]["code"] == "BOM"
    assert res["dest_hub"]["code"] == "GOI"
    assert len(res["places"]) == 1
    assert "Cache" in res["places_source"]


def test_build_day0_itinerary_step2_mocked():
    mock_itinerary = TravelItinerary(
        destination="Goa",
        duration_days=3,
        day_0_disclaimer="Day 0 is arrival transit; Days 1-3 are sightseeing.",
        trip_summary="Mumbai to Goa via BOM to GOI.",
        flight=None,
        hotel=HotelOption(
            hotel_id="LIVE_H1",
            name="Goa Retreat",
            city="Goa",
            stars=4,
            price_per_night=2500.0,
            amenities=["wifi", "ac"],
        ),
        itinerary=[
            DayPlan(
                day=0,
                date="2026-11-23",
                morning=["Travel to BOM"],
                afternoon=["Arrive GOI and transfer"],
                evening=["Check-in and rest"],
                places=[],
                weather="Arrival & Staging Transit",
            ),
            DayPlan(
                day=1,
                date="2026-11-24",
                morning=["Aguada Fort"],
                afternoon=["Local market"],
                evening=["Sunset stroll"],
                places=["Aguada Fort"],
                weather="24°C–31°C, Clear sky",
            ),
        ],
        optional_return_path="Goa -> GOI -> BOM -> Mumbai at end of Day 3.",
        budget=BudgetBreakdown(
            flight_cost=0.0,
            hotel_cost=7500.0,
            food_cost=0.0,
            transport_cost=0.0,
            activity_cost=0.0,
            total_estimated_cost=7500.0,
            budget_note="Hotel only in test.",
        ),
    )

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = mock_itinerary

    with (
        patch("agent.travel_agent.search_live_hotels", return_value=[]),
        patch("agent.travel_agent.get_weather.func", return_value='{"forecast_available": false, "daily_summary": {}}'),
        patch("agent.travel_agent._build_fast_structured_llm", return_value=mock_llm),
    ):
        bundle = build_day0_itinerary(
            origin="Mumbai",
            destination="Goa",
            duration_days=3,
            budget=15000.0,
            hotel_pref="Best value affordable hotel",
            selected_places=[{"name": "Aguada Fort", "city": "Goa", "zone": "North Goa"}],
            orig_hub={"city": "Mumbai", "code": "BOM"},
            dest_hub={"city": "Goa", "code": "GOI"},
            flight=None,
            places_source="Cache",
            api_key="test-key",
        )

    itin = bundle["itinerary"]
    assert isinstance(itin, TravelItinerary)
    assert itin.itinerary[0].day == 0
    assert itin.optional_return_path != ""


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("GOOGLE_API_KEY"), reason="GOOGLE_API_KEY not set")
def test_two_step_live_smoke():
    s1 = discover_route_and_places(
        origin="Mumbai",
        destination="Goa",
        custom_pref="forts, markets",
        api_key=os.getenv("GOOGLE_API_KEY"),
    )
    assert len(s1["places"]) > 0