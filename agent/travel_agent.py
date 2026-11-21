from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from agent.prompts import SYSTEM_PROMPT
from agent.schemas import TravelItinerary

from tools.flight_tool import search_flights
from tools.hotel_tool import search_hotels
from tools.places_tool import search_places
from tools.weather_tool import get_weather
from tools.budget_tool import calculate_budget
from dotenv import load_dotenv
import os
load_dotenv()

def create_travel_agent():
    """Create and configure the LangChain travel planning agent."""

    model = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )

    tools = [
        search_flights,
        search_hotels,
        search_places,
        get_weather,
        calculate_budget,
    ]

    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        response_format=TravelItinerary,
    )

    return agent