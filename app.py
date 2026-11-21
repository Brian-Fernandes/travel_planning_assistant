import os
from datetime import date, datetime, timedelta

import streamlit as st
from dotenv import load_dotenv

from agent.schemas import TravelItinerary
from agent.travel_agent import create_travel_agent
from tools.flight_tool import load_flights
from tools.hotel_tool import load_hotels

load_dotenv()

st.set_page_config(
    page_title="AI Travel Planning Assistant",
    page_icon="✈️",
    layout="wide",
)

CITIES = [
    "Mumbai",
    "Goa",
    "Delhi",
    "Bangalore",
    "Chennai",
    "Hyderabad",
    "Kolkata",
    "Jaipur",
]

PLACE_CATEGORIES = [
    "beach",
    "fort",
    "market",
    "museum",
    "park",
    "lake",
    "temple",
    "monument",
]

st.title("✈️ AI Travel Planning Assistant")
st.caption(
    "Agentic trip planner powered by LangChain, Gemini, and live Open-Meteo weather forecasts."
)

# Sidebar controls
with st.sidebar:
    st.header("Trip Preferences")

    api_key_input = st.text_input(
        "Google API Key",
        value=os.getenv("GOOGLE_API_KEY", ""),
        type="password",
        help="Required if not already set in your .env file.",
    )
    if api_key_input:
        os.environ["GOOGLE_API_KEY"] = api_key_input

    origin = st.selectbox("Origin City", CITIES, index=0)
    destination = st.selectbox("Destination City", CITIES, index=1)
    duration_days = st.slider("Trip Duration (Days)", min_value=1, max_value=7, value=3)
    budget = st.number_input(
        "Total Budget (INR)", min_value=3000, max_value=200000, value=15000, step=1000
    )

    use_specific_date = st.checkbox("Specify Departure Date", value=False)
    travel_date = ""
    if use_specific_date:
        picked_date = st.date_input("Departure Date", min_value=date.today())
        travel_date = picked_date.strftime("%Y-%m-%d")

    interests = st.multiselect(
        "Interests",
        PLACE_CATEGORIES,
        default=["fort", "market", "museum"],
    )

    hotel_pref = st.selectbox(
        "Hotel Preference",
        [
            "Best value affordable hotel",
            "Budget-friendly stay (2-3 stars)",
            "Comfortable mid-range (3-4 stars)",
            "Luxury 5-star stay",
        ],
    )

    plan_clicked = st.button("Generate Itinerary", type="primary", use_container_width=True)

if plan_clicked:
    if origin == destination:
        st.warning("Origin and destination cities must be different.")
        st.stop()

    if not os.getenv("GOOGLE_API_KEY"):
        st.error("Please provide a valid GOOGLE_API_KEY in the sidebar or your .env file.")
        st.stop()

    default_tomorrow = (date.today() + timedelta(days=1)).isoformat()
    date_clause = (
        f" starting on {travel_date} (pass start_date='{travel_date}' to get_weather; "
        f"do NOT pass travel_date to search_flights)"
        if travel_date
        else f" starting tomorrow ({default_tomorrow}, pass start_date='{default_tomorrow}' to get_weather)"
    )
    interests_clause = ", ".join(interests) if interests else "popular attractions"

    prompt = (
        f"Plan a {duration_days}-day trip from {origin} to {destination}{date_clause}. "
        f"Total budget: ₹{budget:,}. "
        f"Interests: {interests_clause}. "
        f"Hotel preference: {hotel_pref}. "
        f"Use all available tools to find a flight, hotel, places to visit, live weather forecast, "
        f"and calculate the full trip budget."
    )

    with st.spinner("Planning your itinerary and fetching live weather..."):
        try:
            agent = create_travel_agent()
            result = agent.invoke(
                {"messages": [{"role": "user", "content": prompt}]},
                config={"recursion_limit": 30},
            )
            itinerary: TravelItinerary | None = result.get("structured_response")

            if not itinerary:
                st.error("The agent could not generate a structured itinerary. Please try again.")
                st.stop()

            # Programmatic Guardrail 1: Verify flight & hotel IDs exist in datasets
            valid_flight_ids = {f["flight_id"] for f in load_flights()}
            if itinerary.flight and itinerary.flight.flight_id not in valid_flight_ids:
                itinerary.flight = None
                itinerary.budget.total_estimated_cost -= itinerary.budget.flight_cost
                itinerary.budget.flight_cost = 0.0

            valid_hotel_ids = {h["hotel_id"] for h in load_hotels()}
            if itinerary.hotel and itinerary.hotel.hotel_id not in valid_hotel_ids:
                itinerary.hotel = None
                itinerary.budget.total_estimated_cost -= itinerary.budget.hotel_cost
                itinerary.budget.hotel_cost = 0.0

            # Programmatic Guardrail 2: Enforce sequential dates & clamp out-of-window forecasts
            expected_start = (
                datetime.strptime(travel_date, "%Y-%m-%d").date()
                if travel_date
                else date.today() + timedelta(days=1)
            )
            max_live_weather_date = date.today() + timedelta(days=14)
            for idx, day_plan in enumerate(itinerary.itinerary):
                current_day = expected_start + timedelta(days=idx)
                day_plan.date = current_day.isoformat()
                if current_day > max_live_weather_date:
                    day_plan.weather = "Live forecast unavailable (beyond 14-day window)"
                    
            st.session_state["itinerary"] = itinerary

        except Exception as exc:
            st.error(f"Error generating itinerary: {exc}")
            st.stop()

# Render results
itinerary: TravelItinerary | None = st.session_state.get("itinerary")

if itinerary:
    st.subheader(f"{itinerary.destination} — {itinerary.duration_days}-Day Itinerary")
    st.info(itinerary.trip_summary)

    # Budget Metrics Row
    b = itinerary.budget
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total Estimated", f"₹{b.total_estimated_cost:,.0f}")
    col2.metric("Flight", f"₹{b.flight_cost:,.0f}")
    col3.metric("Hotel", f"₹{b.hotel_cost:,.0f}")
    col4.metric("Food (Est.)", f"₹{b.food_cost:,.0f}")
    col5.metric("Transport (Est.)", f"₹{b.transport_cost:,.0f}")
    col6.metric("Activities (Est.)", f"₹{b.activity_cost:,.0f}")
    st.caption(f"ℹ️ {b.budget_note}")

    st.divider()

    # Flight & Hotel Cards
    f_col, h_col = st.columns(2)
    with f_col:
        st.markdown("### 🛫 Selected Flight")
        if itinerary.flight:
            f = itinerary.flight
            st.write(f"**{f.airline}** (`{f.flight_id}`)")
            st.write(f"**Route:** {f.origin} → {f.destination}")
            st.write(f"**Departure:** {f.departure_time} | **Arrival:** {f.arrival_time}")
            st.write(f"**Ticket Price:** ₹{f.price:,.0f}")
        else:
            st.warning("No direct flights found in the catalog for this route. Flight cost set to ₹0.")

    with h_col:
        st.markdown("### 🏨 Selected Hotel")
        if itinerary.hotel:
            h = itinerary.hotel
            st.write(f"**{h.name}** ({'⭐' * h.stars}) — `{h.hotel_id}`")
            st.write(f"**City:** {h.city} | **Rate:** ₹{h.price_per_night:,.0f} / night")
            st.write(f"**Amenities:** {', '.join(h.amenities)}")
        else:
            st.warning("No suitable hotels found in the catalog. Hotel cost set to ₹0.")

    st.divider()

    # Day-by-Day Itinerary Tabs
    st.markdown("### 📅 Day-by-Day Plan")
    tabs = st.tabs([f"Day {d.day} ({d.date})" for d in itinerary.itinerary])

    for tab, day_plan in zip(tabs, itinerary.itinerary):
        with tab:
            st.caption(f"🌤️ **Forecast:** {day_plan.weather}")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("**Morning**")
                for item in day_plan.morning:
                    st.markdown(f"- {item}")
            with c2:
                st.markdown("**Afternoon**")
                for item in day_plan.afternoon:
                    st.markdown(f"- {item}")
            with c3:
                st.markdown("**Evening**")
                for item in day_plan.evening:
                    st.markdown(f"- {item}")

            if day_plan.places:
                st.markdown(f"**Featured Places:** {', '.join(day_plan.places)}")

    st.divider()
    st.download_button(
        label="Download Itinerary (JSON)",
        data=itinerary.model_dump_json(indent=2),
        file_name=f"{itinerary.destination.lower()}_itinerary.json",
        mime="application/json",
    )
else:
    st.markdown(
        "👈 Configure your trip in the sidebar and click **Generate Itinerary** to build a grounded, budget-aware travel plan."
    )