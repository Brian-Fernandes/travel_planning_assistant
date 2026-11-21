# ✈️ AI Travel Planning Assistant

An agentic, tool-augmented travel planning application built with **LangChain**, **Google Gemini**, **Pydantic**, and **Streamlit**. The assistant generates structured, budget-aware multi-day Indian travel itineraries grounded in local JSON catalogs (`flights.json`, `hotels.json`, `places.json`) and live daily forecasts from the **Open-Meteo API**.

---

## ✨ Key Features

- **Tool-Augmented LangChain Agent:** Orchestrates five specialized tools (`search_flights`, `search_hotels`, `search_places`, `get_weather`, and `calculate_budget`) to assemble complete trip plans.
- **Strict Pydantic Structured Output:** Enforces validated schemas (`TravelItinerary`, `FlightOption`, `HotelOption`, `DayPlan`, `BudgetBreakdown`) with clean Streamlit rendering and one-click JSON export.
- **Deterministic Post-Generation Guardrails:**
  - **Catalog Grounding:** Cross-checks generated `flight_id` and `hotel_id` values against `data/flights.json` and `data/hotels.json`, stripping unverified records and adjusting budget totals automatically.
  - **Date & Forecast Horizon Enforcement:** Aligns itinerary dates sequentially from the user's chosen departure date (or tomorrow by default) and flags dates beyond Open-Meteo's 14-day live forecast window rather than displaying guessed weather.
- **Automated Test Suite:** Includes offline unit tests (`pytest -m "not integration"`) and live API / end-to-end agent integration tests.

---

## 🏗️ Project Structure

    travel-agent/
    ├── agent/
    │   ├── prompts.py          # System instructions & grounding rules
    │   ├── schemas.py          # Pydantic models for structured agent output
    │   └── travel_agent.py     # LangChain agent initialization & tool binding
    ├── data/
    │   ├── flights.json        # Domestic flight catalog
    │   ├── hotels.json         # City hotel catalog with star ratings & amenities
    │   └── places.json         # Attractions catalog categorized by interest
    ├── tests/
    │   ├── test_tools.py       # Fast offline unit tests for tools, schemas & edge cases
    │   └── test_integration.py # Live Open-Meteo & end-to-end Gemini agent tests
    ├── tools/
    │   ├── budget_tool.py      # Deterministic trip cost calculator
    │   ├── flight_tool.py      # Route & date flight lookup tool
    │   ├── hotel_tool.py       # City, budget & star-rating hotel filter tool
    │   ├── places_tool.py      # Interest & rating attraction lookup tool
    │   └── weather_tool.py     # Open-Meteo geocoding & 14-day forecast tool
    ├── app.py                  # Streamlit web interface & post-generation guardrails
    ├── pytest.ini              # Pytest configuration and markers
    ├── requirements.txt        # Pinned project dependencies
    └── README.md               # Project documentation

---

## 🚀 Getting Started

### 1. Clone & Create a Virtual Environment

    git clone [https://github.com/Brian-Fernandes/travel_planning_assistant.git](https://github.com/Brian-Fernandes/travel_planning_assistant.git)
    cd travel_planning_assistant
    python -m venv .venv

Activate the virtual environment:
- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
- **macOS / Linux:** `source .venv/bin/activate`

### 2. Install Dependencies

    pip install -r requirements.txt

### 3. Configure Environment Variables

Create a `.env` file in the project root (or enter your key directly in the Streamlit sidebar):

    GOOGLE_API_KEY=your_gemini_api_key_here

### 4. Run the Streamlit App

    streamlit run app.py

Open `http://localhost:8501` in your browser, configure your origin, destination, budget, dates, and interests, and click **Generate Itinerary**.

---

## 🧪 Running Tests

Run fast offline unit tests (no API key or internet required):

    pytest -v -m "not integration"

Run the full test suite (including live Open-Meteo and Gemini end-to-end tests):

    pytest -v

---

## 📌 Data & API Notes

- **Catalog Datasets (`data/*.json`):** Flights, hotels, and attractions are sourced from static local JSON datasets; if a route or preference has no matching entry, the agent gracefully sets the selection to `None` (`₹0`) rather than fabricating options.
- **Live Weather (`Open-Meteo`):** Live daily forecasts cover up to **14 days** ahead from the current date; trips scheduled beyond 14 days still generate full itineraries, accommodations, and budgets with an explicit forecast availability notice.
