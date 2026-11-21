import os
from datetime import date, datetime, timedelta

import streamlit as st
from dotenv import load_dotenv

from agent.schemas import FlightOption, HotelOption, TravelItinerary
from agent.travel_agent import create_travel_agent
from tools.flight_tool import load_flights
from tools.hotel_tool import load_hotels

load_dotenv()

st.set_page_config(
    page_title="AI Travel Planning Assistant",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide sidebar completely for a clean, full-width product UI
st.markdown(
    """
    <style>
        [data-testid="stSidebar"], [data-testid="collapsedControl"] {
            display: none !important;
        }
        .block-container {
            padding-top: 2rem;
            max-width: 1200px;
        }
    </style>
    """,
    unsafe_allow_html=True,
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

TRANSIT_MODES = {
    "Metro / Auto / Local Bus (Budget)": 500,
    "Point-to-Point Cab / Uber / Ola (Balanced)": 1200,
    "Full-Day Private Cab Rental (Time-Optimized)": 2500,
}


def evaluate_itinerary_quality(itinerary: TravelItinerary, user_budget: float) -> tuple[int, list[str]]:
    """Deterministic itinerary quality audit ported from ADK evaluation_service."""
    score = 100
    notes: list[str] = []

    if len(itinerary.itinerary) != itinerary.duration_days:
        score -= 20
        notes.append("Day count mismatch")

    seen_places: set[str] = set()
    duplicates = False
    for day in itinerary.itinerary:
        for place in day.places:
            key = place.strip().lower()
            if key in seen_places:
                duplicates = True
            seen_places.add(key)

    if duplicates:
        score -= 15
        notes.append("Duplicate attractions detected")

    if itinerary.budget.total_estimated_cost > user_budget:
        score -= 10
        notes.append(f"Over budget by ₹{itinerary.budget.total_estimated_cost - user_budget:,.0f}")

    return max(0, score), notes


if "trip_history" not in st.session_state:
    st.session_state["trip_history"] = []
if "active_trip_idx" not in st.session_state:
    st.session_state["active_trip_idx"] = 0
if "planner_expanded" not in st.session_state:
    st.session_state["planner_expanded"] = True

# Header Bar
h_left, h_right = st.columns([3, 1])
with h_left:
    st.title("✈️ AI Travel Planning Assistant")
    st.caption(
        "Zone-clustered itineraries, live Open-Meteo forecasts, cab realism, and side-by-side option comparisons."
    )
with h_right:
    if st.session_state["trip_history"]:
        if st.button("➕ Plan Another Trip", use_container_width=True):
            st.session_state["planner_expanded"] = True
            st.rerun()

# Main-Canvas Trip Configuration Panel (No Sidebar)
server_key_available = bool(os.getenv("GOOGLE_API_KEY"))

with st.expander("🧭 Configure Trip & Preferences", expanded=st.session_state["planner_expanded"]):
    r1_c1, r1_c2, r1_c3, r1_c4 = st.columns([1.2, 1.2, 1, 1.2])
    with r1_c1:
        origin = st.selectbox("Origin City", CITIES, index=0)
    with r1_c2:
        destination = st.selectbox("Destination City", CITIES, index=1)
    with r1_c3:
        duration_days = st.number_input("Duration (Days)", min_value=1, max_value=7, value=3)
    with r1_c4:
        budget = st.number_input(
            "Total Budget (INR)", min_value=3000, max_value=200000, value=15000, step=1000
        )

    r2_c1, r2_c2, r2_c3 = st.columns([1.4, 1.2, 1.4])
    with r2_c1:
        interests = st.multiselect(
            "Interests",
            PLACE_CATEGORIES,
            default=["fort", "market", "museum"],
        )
    with r2_c2:
        hotel_pref = st.selectbox(
            "Hotel Tier",
            [
                "Best value affordable hotel",
                "Budget-friendly stay (2-3 stars)",
                "Comfortable mid-range (3-4 stars)",
                "Luxury 5-star stay",
            ],
        )
    with r2_c3:
        transit_mode = st.selectbox(
            "Local Cab & Transit Style",
            list(TRANSIT_MODES.keys()),
            index=1,
        )

    r3_c1, r3_c2, r3_c3 = st.columns([1.2, 1.4, 1.4])
    with r3_c1:
        use_specific_date = st.checkbox("Specific Departure Date", value=False)
        travel_date = ""
        if use_specific_date:
            picked_date = st.date_input("Departure Date", min_value=date.today())
            travel_date = picked_date.strftime("%Y-%m-%d")
    with r3_c2:
        # Never pre-fill server secret into the widget
        user_api_key = st.text_input(
            "Custom Gemini API Key (Optional)" if server_key_available else "Google Gemini API Key",
            value="",
            type="password",
            placeholder="Server key active — leave blank" if server_key_available else "Paste your Gemini API key",
        )
    with r3_c3:
        st.write("")
        st.write("")
        plan_clicked = st.button("🚀 Generate Itinerary", type="primary", use_container_width=True)

if plan_clicked:
    if origin == destination:
        st.warning("Origin and destination cities must be different.")
        st.stop()

    effective_api_key = user_api_key.strip() or os.getenv("GOOGLE_API_KEY", "")
    if not effective_api_key:
        st.error("No Gemini API key configured. Please enter your key above or set GOOGLE_API_KEY in Secrets.")
        st.stop()

    default_tomorrow = (date.today() + timedelta(days=1)).isoformat()
    date_clause = (
        f" starting on {travel_date} (pass start_date='{travel_date}' to get_weather; "
        f"do NOT pass travel_date to search_flights)"
        if travel_date
        else f" starting tomorrow ({default_tomorrow}, pass start_date='{default_tomorrow}' to get_weather)"
    )
    interests_clause = ", ".join(interests) if interests else "popular attractions"
    est_daily_cab = TRANSIT_MODES[transit_mode]

    prompt = (
        f"Plan a {duration_days}-day trip from {origin} to {destination}{date_clause}. "
        f"Total budget: ₹{budget:,}. "
        f"Interests: {interests_clause}. "
        f"Hotel preference: {hotel_pref}. "
        f"Local transit preference: {transit_mode} (~₹{est_daily_cab}/day for local cab/transit). "
        f"Group each day's attractions by neighborhood zone to minimize cab travel time. "
        f"Use all available tools to find a flight, hotel, places to visit, live weather forecast, "
        f"and calculate the full trip budget."
    )

    with st.spinner("Clustering attractions by zone, checking live weather, and building your itinerary..."):
        try:
            agent = create_travel_agent(api_key=effective_api_key)
            result = agent.invoke(
                {"messages": [{"role": "user", "content": prompt}]},
                config={"recursion_limit": 30},
            )
            itinerary: TravelItinerary | None = result.get("structured_response")

            if not itinerary:
                st.error("The agent could not generate a structured itinerary. Please try again.")
                st.stop()

            # Programmatic Guardrail 1: Verify flight & hotel IDs exist in datasets
            all_flights = load_flights()
            valid_flight_ids = {f["flight_id"] for f in all_flights}
            if itinerary.flight and itinerary.flight.flight_id not in valid_flight_ids:
                itinerary.flight = None
                itinerary.budget.total_estimated_cost -= itinerary.budget.flight_cost
                itinerary.budget.flight_cost = 0.0

            all_hotels = load_hotels()
            valid_hotel_ids = {h["hotel_id"] for h in all_hotels}
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

            # Append to Session Trip History
            trip_record = {
                "label": f"Trip #{len(st.session_state['trip_history']) + 1}: {origin} → {destination} ({duration_days}d)",
                "origin": origin,
                "destination": destination,
                "user_budget": float(budget),
                "transit_mode": transit_mode,
                "itinerary": itinerary,
            }
            st.session_state["trip_history"].append(trip_record)
            st.session_state["active_trip_idx"] = len(st.session_state["trip_history"]) - 1
            st.session_state["planner_expanded"] = False
            st.rerun()

        except Exception as exc:
            st.error(f"Error generating itinerary: {exc}")
            st.stop()

# Render Trip Workspace if History Exists
history = st.session_state["trip_history"]

if history:
    # History Switcher Bar
    if len(history) > 1:
        labels = [item["label"] for item in history]
        selected_label = st.radio(
            "Saved Session Trips",
            labels,
            index=st.session_state["active_trip_idx"],
            horizontal=True,
        )
        st.session_state["active_trip_idx"] = labels.index(selected_label)

    active_record = history[st.session_state["active_trip_idx"]]
    itinerary: TravelItinerary = active_record["itinerary"]
    rec_origin = active_record["origin"]
    rec_dest = active_record["destination"]
    user_budget = active_record["user_budget"]

    # Quality Audit Banner
    quality_score, audit_notes = evaluate_itinerary_quality(itinerary, user_budget)
    status_badge = f"Plan Audit: **{quality_score}/100**" + (
        f" ({', '.join(audit_notes)})" if audit_notes else " • All checks passed"
    )

    st.subheader(f"{rec_origin} → {itinerary.destination} ({itinerary.duration_days}-Day Itinerary)")
    st.caption(f"🚌 Transit Style: **{active_record['transit_mode']}** | ✅ {status_badge}")
    st.info(itinerary.trip_summary)

    # Top-Level Workspace Tabs: Itinerary | Compare Flights & Hotels | Compare Saved Trips
    tab_plan, tab_options, tab_compare = st.tabs(
        [
            "📅 Day-by-Day Itinerary & Budget",
            "⚖️ Compare & Swap Flights / Hotels",
            f"🗂️ Compare Saved Trips ({len(history)})",
        ]
    )

    with tab_plan:
        b = itinerary.budget
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("Total Estimated", f"₹{b.total_estimated_cost:,.0f}")
        col2.metric("Flight", f"₹{b.flight_cost:,.0f}")
        col3.metric("Hotel", f"₹{b.hotel_cost:,.0f}")
        col4.metric("Food (Est.)", f"₹{b.food_cost:,.0f}")
        col5.metric("Cab / Transit", f"₹{b.transport_cost:,.0f}")
        col6.metric("Activities", f"₹{b.activity_cost:,.0f}")
        st.caption(f"ℹ️ {b.budget_note}")

        st.divider()

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

        st.markdown("### 🗓️ Zone-Clustered Daily Schedule")
        day_tabs = st.tabs([f"Day {d.day} ({d.date})" for d in itinerary.itinerary])

        for d_tab, day_plan in zip(day_tabs, itinerary.itinerary):
            with d_tab:
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
            label="⬇️ Download Itinerary (JSON)",
            data=itinerary.model_dump_json(indent=2),
            file_name=f"{itinerary.destination.lower()}_itinerary.json",
            mime="application/json",
        )

    with tab_options:
        st.markdown("Compare all available catalog options for this route and swap selections with live budget recalculation.")
        nights = max(itinerary.duration_days - 1, 1)

        route_flights = [
            f for f in load_flights()
            if f["from"].strip().lower() == rec_origin.strip().lower()
            and f["to"].strip().lower() == rec_dest.strip().lower()
        ]
        route_flights.sort(key=lambda x: float(x["price"]))

        city_hotels = [
            h for h in load_hotels()
            if h["city"].strip().lower() == rec_dest.strip().lower()
        ]
        city_hotels.sort(key=lambda x: (-int(x["stars"]), float(x["price_per_night"])))

        opt_c1, opt_c2 = st.columns(2)
        with opt_c1:
            st.markdown(f"#### 🛫 Available Flights ({rec_origin} → {rec_dest})")
            if route_flights:
                st.dataframe(
                    [
                        {
                            "ID": f["flight_id"],
                            "Airline": f["airline"],
                            "Departure": f["departure_time"],
                            "Price (₹)": f["price"],
                        }
                        for f in route_flights
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
                flight_choices = {
                    f"{f['flight_id']} — {f['airline']} (₹{f['price']:,})": f
                    for f in route_flights
                }
                current_f_key = next(
                    (k for k, v in flight_choices.items() if itinerary.flight and v["flight_id"] == itinerary.flight.flight_id),
                    list(flight_choices.keys())[0],
                )
                picked_f_label = st.selectbox(
                    "Active Flight Selection",
                    list(flight_choices.keys()),
                    index=list(flight_choices.keys()).index(current_f_key),
                    key=f"flight_swap_{st.session_state['active_trip_idx']}",
                )
                chosen_f = flight_choices[picked_f_label]
                if not itinerary.flight or chosen_f["flight_id"] != itinerary.flight.flight_id:
                    itinerary.flight = FlightOption(
                        flight_id=chosen_f["flight_id"],
                        airline=chosen_f["airline"],
                        origin=chosen_f["from"],
                        destination=chosen_f["to"],
                        departure_time=chosen_f["departure_time"],
                        arrival_time=chosen_f["arrival_time"],
                        price=float(chosen_f["price"]),
                    )
                    itinerary.budget.flight_cost = float(chosen_f["price"])
                    itinerary.budget.total_estimated_cost = (
                        itinerary.budget.flight_cost
                        + itinerary.budget.hotel_cost
                        + itinerary.budget.food_cost
                        + itinerary.budget.transport_cost
                        + itinerary.budget.activity_cost
                    )
                    st.rerun()
            else:
                st.info("No catalog flights exist for this city pair.")

        with opt_c2:
            st.markdown(f"#### 🏨 Available Hotels in {rec_dest} ({nights} night{'s' if nights > 1 else ''})")
            if city_hotels:
                st.dataframe(
                    [
                        {
                            "ID": h["hotel_id"],
                            "Hotel": h["name"],
                            "Stars": "⭐" * int(h["stars"]),
                            "Per Night (₹)": h["price_per_night"],
                            "Stay Total (₹)": h["price_per_night"] * nights,
                        }
                        for h in city_hotels
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
                hotel_choices = {
                    f"{h['hotel_id']} — {h['name']} ({h['stars']}★, ₹{h['price_per_night']:,}/night)": h
                    for h in city_hotels
                }
                current_h_key = next(
                    (k for k, v in hotel_choices.items() if itinerary.hotel and v["hotel_id"] == itinerary.hotel.hotel_id),
                    list(hotel_choices.keys())[0],
                )
                picked_h_label = st.selectbox(
                    "Active Hotel Selection",
                    list(hotel_choices.keys()),
                    index=list(hotel_choices.keys()).index(current_h_key),
                    key=f"hotel_swap_{st.session_state['active_trip_idx']}",
                )
                chosen_h = hotel_choices[picked_h_label]
                if not itinerary.hotel or chosen_h["hotel_id"] != itinerary.hotel.hotel_id:
                    itinerary.hotel = HotelOption(
                        hotel_id=chosen_h["hotel_id"],
                        name=chosen_h["name"],
                        city=chosen_h["city"],
                        stars=int(chosen_h["stars"]),
                        price_per_night=float(chosen_h["price_per_night"]),
                        amenities=chosen_h["amenities"],
                    )
                    itinerary.budget.hotel_cost = float(chosen_h["price_per_night"]) * nights
                    itinerary.budget.total_estimated_cost = (
                        itinerary.budget.flight_cost
                        + itinerary.budget.hotel_cost
                        + itinerary.budget.food_cost
                        + itinerary.budget.transport_cost
                        + itinerary.budget.activity_cost
                    )
                    st.rerun()

    with tab_compare:
        st.markdown("#### Side-by-Side Comparison of Your Generated Trips")
        comparison_rows = []
        for idx, rec in enumerate(history, start=1):
            it = rec["itinerary"]
            comparison_rows.append(
                {
                    "Trip": f"#{idx}: {rec['origin']} → {it.destination}",
                    "Days": it.duration_days,
                    "Transit Mode": rec["transit_mode"].split(" (")[0],
                    "Flight": f"{it.flight.airline} (₹{it.budget.flight_cost:,.0f})" if it.flight else "None (₹0)",
                    "Hotel": f"{it.hotel.name} ({it.hotel.stars}★)" if it.hotel else "None",
                    "Cab/Transit (₹)": f"₹{it.budget.transport_cost:,.0f}",
                    "Total Est. (₹)": f"₹{it.budget.total_estimated_cost:,.0f}",
                    "Target Budget (₹)": f"₹{rec['user_budget']:,.0f}",
                }
            )
        st.dataframe(comparison_rows, use_container_width=True, hide_index=True)
else:
    st.info("Configure your trip above and click **🚀 Generate Itinerary** to build a zone-clustered travel plan.")