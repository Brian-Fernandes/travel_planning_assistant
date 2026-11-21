import json
import os
import pytest
from tools.weather_tool import get_weather
from agent.travel_agent import create_travel_agent
from agent.schemas import TravelItinerary


@pytest.mark.integration
def test_weather_tool_live_open_meteo():
    raw = get_weather.invoke({"city": "Goa", "days": 3})
    data = json.loads(raw)
    assert "error" not in data
    assert data["city"].lower() == "goa"
    assert len(data["forecast"]["time"]) == 3


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("GOOGLE_API_KEY"), reason="GOOGLE_API_KEY not set")
def test_travel_agent_end_to_end():
    agent = create_travel_agent()
    request = (
        "Plan a 3-day trip from Mumbai to Goa with a budget of ₹15,000. "
        "I like forts, markets, and museums, and want a well-rated affordable hotel."
    )
    result = agent.invoke(
        {"messages": [{"role": "user", "content": request}]},
        config={"recursion_limit": 30},
    )
    structured = result.get("structured_response")
    assert isinstance(structured, TravelItinerary)
    assert structured.destination.lower() == "goa"
    assert structured.duration_days == 3
    assert len(structured.itinerary) == 3
    assert structured.budget.total_estimated_cost > 0