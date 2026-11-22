import os
import time
from datetime import date, datetime, timedelta

import streamlit as st
from dotenv import load_dotenv

from agent.schemas import TravelItinerary
from agent.travel_agent import build_day0_itinerary, discover_route_and_places
from ui.components import (
    render_hero,
    render_landing_attractions,
    render_trip_workspace,
)
from ui.sample_data import build_sample_goa_itinerary
from ui.styles import inject_styles

load_dotenv()

SERVER_DEMO_LIMIT = 3

st.set_page_config(
    page_title="AI Travel Planning Assistant",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_styles()

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"], .stApp {
        opacity: 1 !important;
        filter: none !important;
        pointer-events: auto !important;
    }
    [data-stale="true"] {
        display: none !important;
    }
    div.stButton > button:active {
        filter: brightness(0.72) !important;
        transform: scale(0.98);
    }
    div.stButton > button:disabled {
        background-color: #262930 !important;
        color: #b8bec8 !important;
        border: 1px solid #1b1e24 !important;
        opacity: 0.92 !important;
        cursor: not-allowed !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

for key, default in [
    ("trip_history", []),
    ("active_trip_idx", 0),
    ("planner_expanded", True),
    ("busy_action", None),
    ("step1_discovery", None),
    ("server_runs_used", 0),
    ("demo_cap_notice", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default


def _using_server_key(custom_key_override: str | None = None) -> bool:
    raw_custom = (
        custom_key_override
        if custom_key_override is not None
        else st.session_state.get("in_api_key", "")
    )
    has_custom_key = bool(str(raw_custom).strip())
    has_server_key = bool(os.getenv("GOOGLE_API_KEY", "").strip())
    return (not has_custom_key) and has_server_key


def _trigger_find():
    if st.session_state["busy_action"] is None:
        if _using_server_key() and st.session_state["server_runs_used"] >= SERVER_DEMO_LIMIT:
            st.session_state["demo_cap_notice"] = True
            return
        st.session_state["demo_cap_notice"] = False
        dest_val = st.session_state.get("in_dest", "Goa").strip()
        st.session_state["busy_action"] = "find"
        st.session_state["locked_find"] = {
            "origin": st.session_state.get("in_origin", "Mumbai").strip(),
            "destination": dest_val,
            "duration_days": int(st.session_state.get("in_days", 3)),
            "budget": float(st.session_state.get("in_budget", 15000)),
            "custom_pref": st.session_state.get("in_custom_pref", ""),
            "hotel_pref": st.session_state.get("in_hotel_pref", "Best value affordable hotel"),
            "use_specific_date": bool(st.session_state.get("in_use_date", False)),
            "picked_date": st.session_state.get("in_picked_date", date.today() + timedelta(days=2)),
            "force_refresh": bool(st.session_state.get("in_force_refresh", False)),
            "user_api_key": st.session_state.get("in_api_key", ""),
        }


def _trigger_build():
    if st.session_state["busy_action"] is None and st.session_state.get("step1_discovery"):
        if _using_server_key() and st.session_state["server_runs_used"] >= SERVER_DEMO_LIMIT:
            st.session_state["demo_cap_notice"] = True
            return
        st.session_state["demo_cap_notice"] = False
        s1 = st.session_state["step1_discovery"]
        dest_key = s1["destination"].lower()
        st.session_state["busy_action"] = "build"
        st.session_state["locked_build"] = {
            "selected_labels": list(st.session_state.get(f"shortlist_{dest_key}", [])),
            "extra_pin": st.session_state.get(f"extra_spot_{dest_key}", ""),
            "hotel_pref": st.session_state.get("in_hotel_pref", "Best value affordable hotel"),
            "duration_days": int(st.session_state.get("in_days", s1["duration_days"])),
            "budget": float(st.session_state.get("in_budget", s1["budget"])),
            "user_api_key": st.session_state.get("in_api_key", ""),
        }


render_hero(has_history=bool(st.session_state["trip_history"]))
server_key_available = bool(os.getenv("GOOGLE_API_KEY", "").strip())


@st.fragment
def render_planner_fragment():
    busy = st.session_state["busy_action"]

    with st.expander("Configure Trip & Preferences", expanded=st.session_state["planner_expanded"]):
        if server_key_available and not st.session_state.get("in_api_key", "").strip():
            remaining = max(0, SERVER_DEMO_LIMIT - st.session_state["server_runs_used"])
            st.caption(
                f"Free Demo Mode: **{remaining} of {SERVER_DEMO_LIMIT}** server-key AI runs remaining this session "
                "(or enter your own Gemini API key for unlimited runs)."
            )

        if st.session_state.get("demo_cap_notice"):
            st.warning(
                f"You've reached the **{SERVER_DEMO_LIMIT} free server-key runs** demo cap for this session. "
                "Paste your own Google Gemini API key below to continue, or click **Load Sample**."
            )

        r1_c1, r1_c2, r1_c3, r1_c4 = st.columns([1.2, 1.2, 1, 1.2])
        with r1_c1:
            origin = st.text_input(
                "Origin City (Any City)",
                value="Mumbai",
                key="in_origin",
                placeholder="e.g. Udupi, Sindhudurg, Mumbai...",
            ).strip()
        with r1_c2:
            destination = st.text_input(
                "Destination City / Region",
                value="Goa",
                key="in_dest",
                placeholder="e.g. Ranchi, Ellora, Assam, Goa...",
            ).strip()
        with r1_c3:
            duration_days = st.number_input("Sightseeing Days (1–7)", min_value=1, max_value=7, value=3, key="in_days")
        with r1_c4:
            budget = st.number_input(
                "Flight + Hotel Budget (INR)",
                min_value=2000,
                max_value=250000,
                value=15000,
                step=1000,
                key="in_budget",
            )

        r2_c1, r2_c2 = st.columns([2.2, 1.3])
        with r2_c1:
            custom_pref = st.text_input(
                "Your Preferences (Optional)",
                value="",
                key="in_custom_pref",
                placeholder="Type preference (e.g., waterfalls, heritage sites, wildlife) or leave blank",
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
                key="in_hotel_pref",
            )

        r3_c1, r3_c2, r3_c3, r3_c4, r3_c5 = st.columns([1.05, 1.05, 1.25, 0.95, 0.9])
        with r3_c1:
            use_specific_date = st.checkbox("Specific Date", value=False, key="in_use_date")
            if use_specific_date:
                st.date_input(
                    "Day 1 Sightseeing Date",
                    min_value=date.today() + timedelta(days=1),
                    key="in_picked_date",
                )
        with r3_c2:
            st.checkbox(
                "Fresh Web Places",
                value=False,
                key="in_force_refresh",
                help="Bypass places.json cache and discover fresh attractions.",
            )
        with r3_c3:
            user_api_key = st.text_input(
                "Custom API Key (Optional)" if server_key_available else "Google Gemini API Key",
                value="",
                type="password",
                key="in_api_key",
                placeholder="Server key active" if server_key_available else "Paste Gemini API key",
            )
        with r3_c4:
            st.write("")
            st.write("")
            st.button(
                "Searching..." if busy == "find" else "Find Route & Places",
                key="btn_find_route",
                type="primary",
                width="stretch",
                disabled=(busy == "find"),
                on_click=_trigger_find,
            )
        with r3_c5:
            st.write("")
            st.write("")
            sample_clicked = st.button(
                "Load Sample",
                key="btn_load_sample",
                width="stretch",
                help="Preview a Mumbai → Goa itinerary instantly with zero API usage.",
            )

        if sample_clicked:
            sample_itinerary = build_sample_goa_itinerary()
            st.session_state["trip_history"].append(
                {
                    "label": f"Trip #{len(st.session_state['trip_history']) + 1}: Mumbai → Goa (3d • Sample)",
                    "origin": "Mumbai",
                    "destination": "Goa",
                    "user_budget": 15000.0,
                    "live_hotels": [
                        {
                            "hotel_id": "LIVE_H1",
                            "name": "Royal Heritage",
                            "city": "Goa",
                            "stars": 5,
                            "price_per_night": 1232.0,
                            "amenities": ["wifi", "parking", "breakfast", "pool"],
                            "source_note": "Sample rate",
                        }
                    ],
                    "itinerary": sample_itinerary,
                }
            )
            st.session_state["active_trip_idx"] = len(st.session_state["trip_history"]) - 1
            st.session_state["planner_expanded"] = False
            st.rerun()

        # -------- STEP 1 EXECUTION (INSIDE FRAGMENT — NO FULL PAGE FLICKER) --------
        if busy == "find":
            lf = st.session_state.get("locked_find", {})
            try:
                orig_in = lf.get("origin", origin)
                dest_in = lf.get("destination", destination)
                locked_custom_key = lf.get("user_api_key", user_api_key)
                eff_key = locked_custom_key.strip() or os.getenv("GOOGLE_API_KEY", "").strip()

                if not orig_in or not dest_in:
                    st.warning("Please enter both origin and destination.")
                elif orig_in.lower() == dest_in.lower():
                    st.warning("Origin and destination must be different.")
                elif not eff_key:
                    st.error("No Gemini API key configured.")
                else:
                    t0 = time.perf_counter()
                    t_date = (
                        lf["picked_date"].strftime("%Y-%m-%d")
                        if lf.get("use_specific_date") and lf.get("picked_date")
                        else ""
                    )
                    s1_res = discover_route_and_places(
                        origin=orig_in,
                        destination=dest_in,
                        custom_pref=lf.get("custom_pref", ""),
                        force_refresh_places=lf.get("force_refresh", False),
                        api_key=eff_key,
                    )
                    if _using_server_key(locked_custom_key):
                        st.session_state["server_runs_used"] += 1

                    st.session_state["step1_discovery"] = {
                        **s1_res,
                        "origin": orig_in,
                        "destination": dest_in,
                        "duration_days": lf.get("duration_days", duration_days),
                        "budget": lf.get("budget", budget),
                        "travel_date": t_date,
                        "elapsed": round(time.perf_counter() - t0, 2),
                    }
            except Exception as exc:
                st.error(f"Discovery failed: {exc}")
            finally:
                st.session_state["busy_action"] = None
                st.rerun(scope="fragment")

        # -------- NESTED STEP 2 SHORTLIST PANEL (INSIDE FRAGMENT) --------
        if st.session_state.get("step1_discovery"):
            s1 = st.session_state["step1_discovery"]
            st.divider()
            st.success(f"Route & 20 attractions ready in **{s1['elapsed']}s** | Source: `{s1['places_source']}`")

            c1, c2 = st.columns(2)
            with c1:
                st.info(
                    f"**Day-0 Transit Path:** {s1['orig_hub']['input_name']} → **{s1['orig_hub']['city']} ({s1['orig_hub']['code']})** "
                    f"✈️ **{s1['dest_hub']['city']} ({s1['dest_hub']['code']})** → Transfer to **{s1['destination']}** base"
                )
            with c2:
                fl = s1["flight"]
                if fl:
                    st.info(f"**Catalog Flight:** {fl['airline']} ({fl.get('flight_no', fl['flight_id'])}) | {fl.get('duration', '')} | **₹{fl['price']:,.0f}**")
                else:
                    st.warning("No direct catalog flight found (Book separately).")

            st.subheader(f"Shortlist Attractions in {s1['destination']}")
            places = s1["places"]
            options = [f"{p['name']} ({p['city']} · {p['zone']})" for p in places]
            selected_labels = st.multiselect(
                f"Pick from {len(places)} discovered attractions:",
                options=options,
                default=options[: min(6, len(options))],
                key=f"shortlist_{s1['destination'].lower()}",
            )

            selected_set = set(selected_labels)
            unselected_names = [
                places[idx]["name"]
                for idx, lbl in enumerate(options)
                if lbl not in selected_set
            ]
            if len(unselected_names) >= 2:
                dyn_placeholder = f"Type your own spot or add discovered options (e.g., {unselected_names[0]}, {unselected_names[1]})"
            elif len(unselected_names) == 1:
                dyn_placeholder = f"Type your own spot or add discovered option (e.g., {unselected_names[0]})"
            else:
                dyn_placeholder = f"Type any extra spot in {s1['destination']} or leave blank"

            extra_pin = st.text_input(
                "Add any extra custom spot (Optional)",
                value="",
                key=f"extra_spot_{s1['destination'].lower()}",
                placeholder=dyn_placeholder,
            )

            st.button(
                "Building..." if busy == "build" else "Build Itinerary",
                key="btn_build_itin",
                type="primary",
                disabled=(busy == "build"),
                on_click=_trigger_build,
            )

            if busy == "build":
                lb = st.session_state.get("locked_build", {})
                try:
                    locked_custom_key = lb.get("user_api_key", user_api_key)
                    eff_key = locked_custom_key.strip() or os.getenv("GOOGLE_API_KEY", "").strip()
                    chosen_labels = lb.get("selected_labels", selected_labels)
                    chosen_places = [places[options.index(lbl)] for lbl in chosen_labels if lbl in options]

                    for raw_pin in lb.get("extra_pin", extra_pin).split(","):
                        if raw_pin.strip():
                            chosen_places.append(
                                {
                                    "name": raw_pin.strip(),
                                    "city": s1["destination"],
                                    "zone": "Custom Pin",
                                    "type": "must-visit",
                                    "rating": 5.0,
                                }
                            )

                    dur_in = int(lb.get("duration_days", s1["duration_days"]))
                    bud_in = float(lb.get("budget", s1["budget"]))

                    bundle = build_day0_itinerary(
                        origin=s1["origin"],
                        destination=s1["destination"],
                        duration_days=dur_in,
                        budget=bud_in,
                        hotel_pref=lb.get("hotel_pref", hotel_pref),
                        selected_places=chosen_places,
                        orig_hub=s1["orig_hub"],
                        dest_hub=s1["dest_hub"],
                        flight=s1["flight"],
                        places_source=s1["places_source"],
                        travel_date=s1["travel_date"],
                        api_key=eff_key,
                    )
                    if _using_server_key(locked_custom_key):
                        st.session_state["server_runs_used"] += 1

                    itinerary: TravelItinerary = bundle["itinerary"]
                    discovered_hotels = bundle["live_hotels"]
                    weather_map = bundle.get("weather_summary_map", {})

                    nights = max(dur_in, 1)
                    if itinerary.hotel:
                        itinerary.budget.hotel_cost = round(itinerary.hotel.price_per_night * nights, 2)
                    itinerary.budget.food_cost = 0.0
                    itinerary.budget.transport_cost = 0.0
                    itinerary.budget.activity_cost = 0.0
                    itinerary.budget.total_estimated_cost = round(
                        itinerary.budget.flight_cost + itinerary.budget.hotel_cost, 2
                    )
                    itinerary.budget.budget_note = (
                        f"Combined Flight (₹{itinerary.budget.flight_cost:,.0f}) + "
                        f"{nights} Hotel Night{'s' if nights > 1 else ''} (₹{itinerary.budget.hotel_cost:,.0f}) "
                        f"| Places Source: {bundle['places_source']}."
                    )

                    expected_day1 = (
                        datetime.strptime(s1["travel_date"], "%Y-%m-%d").date()
                        if s1["travel_date"]
                        else date.today() + timedelta(days=2)
                    )
                    max_live_weather_date = date.today() + timedelta(days=14)

                    for day_plan in itinerary.itinerary:
                        if day_plan.day == 0:
                            day_plan.date = (expected_day1 - timedelta(days=1)).isoformat()
                            day_plan.weather = "Arrival & Staging Transit"
                        else:
                            current_day = expected_day1 + timedelta(days=day_plan.day - 1)
                            iso_d = current_day.isoformat()
                            day_plan.date = iso_d
                            if iso_d in weather_map:
                                day_plan.weather = weather_map[iso_d]
                            elif current_day > max_live_weather_date:
                                day_plan.weather = "Live forecast unavailable (beyond 14-day window)"
                            else:
                                day_plan.weather = "Live weather data unavailable"

                    st.session_state["trip_history"].append(
                        {
                            "label": f"Trip #{len(st.session_state['trip_history']) + 1}: {s1['origin']} → {s1['destination']} ({dur_in}d + Day 0)",
                            "origin": s1["origin"],
                            "destination": s1["destination"],
                            "user_budget": bud_in,
                            "live_hotels": discovered_hotels,
                            "itinerary": itinerary,
                        }
                    )
                    st.session_state["active_trip_idx"] = len(st.session_state["trip_history"]) - 1
                    st.session_state["planner_expanded"] = False
                    st.session_state["busy_action"] = None
                    st.rerun()  # Full app rerun ONLY when a completed trip is added to trip_history
                except Exception as exc:
                    st.error(f"Error building itinerary: {exc}")
                    st.session_state["busy_action"] = None
                    st.rerun(scope="fragment")


render_planner_fragment()

if st.session_state["trip_history"]:
    active_trip = st.session_state["trip_history"][st.session_state["active_trip_idx"]]
    active_itin: TravelItinerary = active_trip["itinerary"]
    if getattr(active_itin, "day_0_disclaimer", ""):
        st.info(f"ℹ️ **Schedule Note:** {active_itin.day_0_disclaimer}")
    render_trip_workspace(st.session_state["trip_history"])
    if getattr(active_itin, "optional_return_path", ""):
        st.info(f"🛫 **Optional Return Path (End of Day {active_itin.duration_days}):** {active_itin.optional_return_path}")
else:
    st.write("")
    render_landing_attractions()