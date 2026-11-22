# ✈️ AI Travel Planning Assistant

A hybrid, tool-augmented travel planning application built with **LangChain**, **Google Gemini**, **Pydantic**, **Open-Meteo**, and **Streamlit**. The assistant uses a **two-step human-in-the-loop workflow** that pairs nearest-airport hub resolution and a distance-scaled domestic flight catalog with real-time Google Search discovery for hotels and attractions, live 14-day weather forecasts, and deterministic Flight + Hotel budgeting.

- **Live App:** [Live App](https://travel-planning-assistant.streamlit.app/)

---

## ✨ Key Features

- **Two-Step Discovery & Shortlist Workflow:**
  1. **Route & Attraction Discovery (`discover_route_and_places`):** Geocodes any Indian origin and destination (including towns without airports), resolves nearest commercial airport hubs via Haversine distance across 45 airports, finds direct or 1-stop connecting catalog flights, and discovers up to **20 neighborhood-tagged attractions** via live Google Search + `data/places.json` caching.
  2. **Shortlist Curation & Day-0 Synthesis (`build_day0_itinerary`):** Lets users curate discovered spots or pin custom landmarks, fetches base-stay hotels and live Open-Meteo weather in parallel, and synthesizes a zone-clustered `TravelItinerary`.
- **Day-0 Arrival Staging & Optional Return Path:** Dedicates **Day 0** to origin-to-hub transit, flight, and hotel check-in so 100% of requested days (**Days 1–N**) are pure sightseeing, paired with an optional return route at the end of the final day.
- **Pure Flight + Hotel Budgeting:** Uses `calculate_budget` to compute exact combined flight + accommodation costs without arbitrary meal, cab, or ticket guesses inflating totals.
- **6-Point Itinerary Quality Audit & Option Swapping:** Scores every generated plan out of 100 (day coverage, sequential numbering, zero duplicate attractions, populated blocks, daily pacing balance, and budget compliance) and supports instant flight/hotel swapping and multi-trip comparison.
- **Dual Export & Hosted Demo Safeguards:** Exports validated plans as `.JSON` and formatted `.TXT` travel briefs, includes a zero-API **Load Sample** preview, and caps server-key live runs at 3 per session (with unlimited runs when users supply their own Gemini API key).

---

## 🏗️ Project Structure

```text
travel-agent/
├── agent/
│   ├── prompts.py              # Grounding & workflow instructions
│   ├── schemas.py              # Pydantic models (TravelItinerary, DayPlan, BudgetBreakdown, etc.)
│   └── travel_agent.py         # 2-step discovery & Day-0 synthesis with multi-model failover
├── data/
│   ├── flights.json            # Distance-scaled domestic flight catalog across 45 airport hubs
│   ├── hotel.json              # Cached live-discovered hotel listings
│   └── places.json             # Cached zone-tagged destination attractions
├── scripts/
│   └── build_flights.py        # Generator for realistic distance-scaled domestic flight routes
├── services/
│   ├── discovery_service.py    # Live Google Search + Flash fallback & atomic JSON caching
│   ├── evaluation_service.py   # 6-point itinerary quality & pacing audit
│   ├── export_service.py       # Human-readable .TXT travel brief formatter
│   ├── hub_resolver.py         # Geocoding, Haversine airport matching & connecting flight lookup
│   ├── json_utils.py           # Resilient JSON extraction for LLM/search responses
│   └── model_helper.py         # Dynamic active Gemini Flash model discovery
├── tests/
│   ├── test_tools.py           # Fast offline unit tests for schemas, hubs, caching, weather & budget
│   └── test_integration.py     # Mocked 2-step pipeline & live API integration smoke tests
├── tools/
│   ├── budget_tool.py          # Deterministic Flight + Hotel cost calculator
│   ├── flight_tool.py          # Catalog flight lookup & date validation tool
│   └── weather_tool.py         # Open-Meteo geocoding, WMO weather labels & 14-day forecast tool
├── ui/
│   ├── components.py           # Hero banner, audit view, itinerary tabs, option swapper & comparison UI
│   ├── sample_data.py          # Zero-API Mumbai → Goa sample itinerary
│   └── styles.py               # Custom Streamlit CSS styling
├── .streamlit/
│   └── config.toml             # Light theme & minimal toolbar configuration
├── app.py                      # Streamlit web app, fragment-scoped runner & 3-run demo cap
├── pytest.ini                  # Pytest configuration and integration marker
└── requirements.txt            # Project dependencies
```

---

## 🚀 Getting Started

### Try the Hosted App

Visit the live deployment directly at [Live App](https://travel-planning-assistant.streamlit.app/).

### 1. Clone & Create a Virtual Environment

```bash
git clone https://github.com/Brian-Fernandes/travel_planning_assistant.git
cd travel_planning_assistant
python -m venv .venv
```

Activate the virtual environment:
- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
- **macOS / Linux:** `source .venv/bin/activate`

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root (or enter your key directly in the app's **Custom API Key** field):

```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 4. Run the Streamlit App Locally

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser, enter your route, budget, and preferences, click **Find Route & Places**, curate your shortlist, and click **Build Itinerary** (or click **Load Sample** for an instant zero-API preview).

---

## 🧪 Running Tests

Run the fast offline unit and mocked pipeline test suite (no API key or internet required):

```bash
pytest -m "not integration" -v
```

Run the full test suite (including live Open-Meteo and Gemini integration tests):

```bash
pytest -v
```

---

## 📌 Data & API Notes

- **Live Deployment:** Hosted on Streamlit Community Cloud at [Live App](https://travel-planning-assistant.streamlit.app/) with a 3-run per-session server-key demo cap, custom API key support, and zero-API sample mode.
- **Hybrid Data Sourcing:** Flights are matched from `data/flights.json` (generated via `scripts/build_flights.py`), while attractions and hotels combine local JSON caches (`data/places.json`, `data/hotel.json`) with live Google Search grounding and Gemini Flash failover.
- **Live Weather Horizon (`Open-Meteo`):** Live forecasts cover up to **14 days** ahead from the current date; sightseeing dates beyond the 14-day window are explicitly labeled `"Live forecast unavailable (beyond 14-day window)"` rather than guessing temperatures.
