import streamlit as st

from agent.schemas import FlightOption, HotelOption, TravelItinerary
from services.evaluation_service import evaluate_itinerary
from services.export_service import format_itinerary_txt
from tools.flight_tool import load_flights
from ui.sample_data import build_sample_goa_itinerary


def render_hero(has_history: bool) -> None:
    """Render the colorful SaaS navigation bar and deep-teal gradient hero banner."""
    st.html(
        """
        <div style="height: 22px; width: 100%;"></div>
        <div class="nav-bar">
            <div class="brand-group">
                <span class="brand-pill">AIR PLANNER</span>
                <span class="brand-title">AI Travel Planning Assistant</span>
            </div>
            <div class="nav-pills">
                <span class="nav-chip">Catalog Flights</span>
                <span class="nav-chip">Live Hotel &amp; Place Search</span>
                <span class="nav-chip">Open-Meteo Weather</span>
            </div>
        </div>
        <div class="hero-showcase">
            <div class="hero-badge">Hybrid Catalog + Real-Time Search Studio</div>
            <div class="hero-title">Plan Zone-Clustered Trips Across India in Seconds</div>
            <p class="hero-sub">
                Combine verified catalog flight fares with live Google Search hotel rates, real-time neighborhood-clustered
                attractions, 14-day Open-Meteo forecasts, and instant JSON + TXT exports.
            </p>
        </div>
        """
    )
    if has_history:
        _, btn_col = st.columns([4.2, 1])
        with btn_col:
            if st.button("＋ Plan Another Trip", use_container_width=True):
                st.session_state["planner_expanded"] = True
                st.rerun()


def render_landing_attractions() -> None:
    """Render the colorful landing sections: 3 Value Pillars & 3-Step Workflow."""
    st.markdown("### Why Plan With Air Travel Assistant")
    p1, p2, p3 = st.columns(3)

    with p1:
        st.html(
            """
            <div class="pillar-card">
                <div>
                    <div class="card-kicker">Pure Flight + Hotel Math</div>
                    <div class="card-heading">Zero Guesswork Budgeting</div>
                    <ul class="bullet-list">
                        <li>Combines exact catalog flight fares with live-searched hotel rates</li>
                        <li>No arbitrary cab, meal, or ticket guesses inflating your total</li>
                        <li>Instant recalculation whenever you swap flights or hotels</li>
                    </ul>
                </div>
                <div class="card-footer-strip">Flight + Hotel Only</div>
            </div>
            """
        )

    with p2:
        st.html(
            """
            <div class="pillar-card pillar-coral">
                <div>
                    <div class="card-kicker card-kicker-coral">Live Discovery + Zones</div>
                    <div class="card-heading">Any City, Zone-Clustered</div>
                    <ul class="bullet-list">
                        <li>Discover real-time attractions &amp; hotels for any destination</li>
                        <li>Pin your own must-visit landmarks right into the schedule</li>
                        <li>Grouped by neighborhood zone to avoid cross-city backtracking</li>
                    </ul>
                </div>
                <div class="card-footer-strip">Real-Time Google Search</div>
            </div>
            """
        )

    with p3:
        st.html(
            """
            <div class="pillar-card pillar-amber">
                <div>
                    <div class="card-kicker card-kicker-amber">Quality &amp; Dual Export</div>
                    <div class="card-heading">6-Point Audit &amp; JSON/TXT</div>
                    <ul class="bullet-list">
                        <li>Automated 100-point audit verifying pacing, uniqueness &amp; budget</li>
                        <li>Live Open-Meteo weather synced to your exact travel dates</li>
                        <li>Download both structured JSON and readable TXT travel briefs</li>
                    </ul>
                </div>
                <div class="card-footer-strip">Audit + Dual Export</div>
            </div>
            """
        )

    st.write("")
    st.write("")
    st.markdown("### Get Started in Just 3 Steps")
    s1, s2, s3 = st.columns(3)
    with s1:
        st.html(
            """
            <div class="step-box">
                <div class="step-circle">1</div>
                <div class="step-title">Enter Route, Budget &amp; Pins</div>
                <div class="step-text">Pick your origin, enter any destination city, set your Flight + Hotel budget, and add optional must-visit spots.</div>
            </div>
            """
        )
    with s2:
        st.html(
            """
            <div class="step-card step-box">
                <div class="step-circle">2</div>
                <div class="step-title">Live Search &amp; Zone Clustering</div>
                <div class="step-text">Our agent pairs catalog flights with live-searched hotel rates, zone-grouped attractions, and Open-Meteo forecasts.</div>
            </div>
            """
        )
    with s3:
        st.html(
            """
            <div class="step-box">
                <div class="step-circle">3</div>
                <div class="step-title">Audit, Swap &amp; Export</div>
                <div class="step-text">Inspect the 6-point quality audit, swap flights or live hotels side-by-side, and export JSON or TXT files.</div>
            </div>
            """
        )


def render_trip_workspace(history: list[dict]) -> None:
    """Render the active trip tabs: Itinerary & Budget, Option Swap, and Saved Trip Comparison."""
    if len(history) > 1:
        labels = [item["label"] for item in history]
        selected_label = st.radio(
            "Session Trips",
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
    live_hotels = active_record.get("live_hotels", [])

    audit = evaluate_itinerary(itinerary, user_budget)
    audit_badge = f"Quality Audit: {audit['score']}/100 ({'Passed' if audit['is_acceptable'] else 'Needs Review'})"

    st.markdown(f"### {rec_origin} → {itinerary.destination} ({itinerary.duration_days}-Day Itinerary)")
    st.html(
        f'<span class="pill-teal">Flight + Hotel Budget: ₹{user_budget:,.0f}</span>'
        f'<span class="pill-amber">{audit_badge}</span>'
    )
    st.html(
        f'<div class="pillar-card"><div class="card-kicker">Executive Summary</div>'
        f'<div style="font-size: 0.94rem; color: #243B3B; line-height: 1.6;">{itinerary.trip_summary}</div></div>'
    )

    with st.expander(f"View 6-Point Itinerary Quality Audit ({audit['score']}/100)", expanded=False):
        a_col1, a_col2 = st.columns(2)
        with a_col1:
            st.markdown("**Checks Passed**")
            for item in audit["passed"]:
                st.markdown(f"- ✅ {item}")
        with a_col2:
            st.markdown("**Warnings / Issues**")
            if audit["issues"]:
                for item in audit["issues"]:
                    st.markdown(f"- ⚠️ {item}")
            else:
                st.markdown("- None — all consistency checks passed.")

    st.write("")

    tab_plan, tab_options, tab_compare = st.tabs(
        [
            "Day-by-Day Itinerary & Budget",
            "Compare & Swap Flights / Live Hotels",
            f"Compare Saved Trips ({len(history)})",
        ]
    )

    with tab_plan:
        _render_plan_tab(itinerary, rec_origin, user_budget)

    with tab_options:
        _render_options_tab(itinerary, rec_origin, rec_dest, live_hotels)

    with tab_compare:
        _render_compare_tab(history)


def _render_plan_tab(itinerary: TravelItinerary, origin: str, user_budget: float) -> None:
    b = itinerary.budget
    m1, m2, m3 = st.columns(3)
    m1.metric(
        "Combined Total (Flight + Hotel)",
        f"₹{b.total_estimated_cost:,.0f}",
        delta=f"₹{user_budget - b.total_estimated_cost:,.0f} vs budget",
    )
    m2.metric("Flight Ticket (Catalog)", f"₹{b.flight_cost:,.0f}")
    m3.metric("Hotel Stay (Live Rate)", f"₹{b.hotel_cost:,.0f}")
    st.caption(f"{b.budget_note}")

    st.write("")

    f_col, h_col = st.columns(2)
    with f_col:
        if itinerary.flight:
            f = itinerary.flight
            st.html(
                f"""
                <div class="pillar-card">
                    <div>
                        <div class="card-kicker">Selected Flight • {f.flight_id}</div>
                        <div class="card-heading">{f.airline} — ₹{f.price:,.0f}</div>
                        <div style="font-size: 0.9rem; line-height: 1.6; color: #334E4E;">
                            <b>Route:</b> {f.origin} → {f.destination}<br/>
                            <b>Departs:</b> {f.departure_time.replace('T', ' ')}<br/>
                            <b>Arrives:</b> {f.arrival_time.replace('T', ' ')}
                        </div>
                    </div>
                </div>
                """
            )
        else:
            st.info("No direct catalog flight for this custom route — book flight separately (Flight cost = ₹0).")

    with h_col:
        if itinerary.hotel:
            h = itinerary.hotel
            amenities_html = "".join(f'<span class="pill-teal">{a}</span>' for a in h.amenities)
            st.html(
                f"""
                <div class="pillar-card pillar-coral">
                    <div>
                        <div class="card-kicker card-kicker-coral">Selected Hotel • Live Search</div>
                        <div class="card-heading">{h.name} ({'★' * h.stars}) — ₹{h.price_per_night:,.0f}/night</div>
                        <div style="font-size: 0.9rem; margin-bottom: 0.5rem; color: #334E4E;"><b>City:</b> {h.city}</div>
                        <div>{amenities_html}</div>
                    </div>
                </div>
                """
            )
        else:
            st.warning("No hotel selected. Hotel cost set to ₹0.")

    st.write("")
    st.markdown("#### Zone-Clustered Daily Schedule")
    day_tabs = st.tabs([f"Day {d.day} • {d.date}" for d in itinerary.itinerary])

    for d_tab, day_plan in zip(day_tabs, itinerary.itinerary):
        with d_tab:
            st.html(f'<span class="pill-amber">Weather: {day_plan.weather}</span>')
            c1, c2, c3 = st.columns(3)
            with c1:
                items_html = "".join(f"<li>{item}</li>" for item in day_plan.morning)
                st.html(
                    f'<div class="slot-box slot-morning"><div class="slot-label">Morning</div><ul>{items_html}</ul></div>'
                )
            with c2:
                items_html = "".join(f"<li>{item}</li>" for item in day_plan.afternoon)
                st.html(
                    f'<div class="slot-box slot-afternoon"><div class="slot-label">Afternoon</div><ul>{items_html}</ul></div>'
                )
            with c3:
                items_html = "".join(f"<li>{item}</li>" for item in day_plan.evening)
                st.html(
                    f'<div class="slot-box slot-evening"><div class="slot-label">Evening</div><ul>{items_html}</ul></div>'
                )

            if day_plan.places:
                st.write("")
                places_pills = "".join(f'<span class="pill-coral">{p}</span>' for p in day_plan.places)
                st.html(places_pills)

    st.divider()
    dl1, dl2, _ = st.columns([1.2, 1.2, 2.6])
    with dl1:
        st.download_button(
            label="Download Itinerary (.JSON)",
            data=itinerary.model_dump_json(indent=2),
            file_name=f"{itinerary.destination.lower().replace(' ', '_')}_itinerary.json",
            mime="application/json",
            use_container_width=True,
        )
    with dl2:
        st.download_button(
            label="Download Travel Brief (.TXT)",
            data=format_itinerary_txt(itinerary, origin=origin),
            file_name=f"{itinerary.destination.lower().replace(' ', '_')}_itinerary.txt",
            mime="text/plain",
            use_container_width=True,
        )


def _render_options_tab(
    itinerary: TravelItinerary,
    rec_origin: str,
    rec_dest: str,
    live_hotels: list[dict],
) -> None:
    st.markdown("Compare catalog flights and live-searched hotels, and swap selections with instant cost recalculation.")
    nights = max(itinerary.duration_days - 1, 1)

    route_flights = [
        f for f in load_flights()
        if f["from"].strip().lower() == rec_origin.strip().lower()
        and f["to"].strip().lower() == rec_dest.strip().lower()
    ]
    route_flights.sort(key=lambda x: float(x["price"]))

    opt_c1, opt_c2 = st.columns(2)
    with opt_c1:
        st.markdown(f"#### Catalog Flights ({rec_origin} → {rec_dest})")
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
                itinerary.budget.total_estimated_cost = itinerary.budget.flight_cost + itinerary.budget.hotel_cost
                st.rerun()
        else:
            st.info("No catalog flights exist for this custom route.")

    with opt_c2:
        st.markdown(f"#### Live-Searched Hotels in {rec_dest} ({nights} night{'s' if nights > 1 else ''})")
        if live_hotels:
            st.dataframe(
                [
                    {
                        "Hotel": h["name"],
                        "Stars": "★" * int(h["stars"]),
                        "Per Night (₹)": h["price_per_night"],
                        "Stay Total (₹)": round(float(h["price_per_night"]) * nights, 0),
                        "Note": h.get("source_note", ""),
                    }
                    for h in live_hotels
                ],
                use_container_width=True,
                hide_index=True,
            )
            hotel_choices = {
                f"{h['name']} ({h['stars']}★, ₹{h['price_per_night']:,.0f}/night)": h
                for h in live_hotels
            }
            current_h_key = next(
                (k for k, v in hotel_choices.items() if itinerary.hotel and v["name"].lower() == itinerary.hotel.name.lower()),
                list(hotel_choices.keys())[0],
            )
            picked_h_label = st.selectbox(
                "Active Hotel Selection",
                list(hotel_choices.keys()),
                index=list(hotel_choices.keys()).index(current_h_key),
                key=f"hotel_swap_{st.session_state['active_trip_idx']}",
            )
            chosen_h = hotel_choices[picked_h_label]
            if not itinerary.hotel or chosen_h["name"].lower() != itinerary.hotel.name.lower():
                itinerary.hotel = HotelOption(
                    hotel_id=chosen_h.get("hotel_id", "LIVE_H1"),
                    name=chosen_h["name"],
                    city=rec_dest,
                    stars=int(chosen_h["stars"]),
                    price_per_night=float(chosen_h["price_per_night"]),
                    amenities=chosen_h.get("amenities", ["wifi"]),
                )
                itinerary.budget.hotel_cost = float(chosen_h["price_per_night"]) * nights
                itinerary.budget.total_estimated_cost = itinerary.budget.flight_cost + itinerary.budget.hotel_cost
                st.rerun()
        else:
            st.info("Generate a live trip to compare multiple real-time hotel listings.")


def _render_compare_tab(history: list[dict]) -> None:
    st.markdown("#### Side-by-Side Comparison of Generated Trips")
    comparison_rows = []
    for idx, rec in enumerate(history, start=1):
        it = rec["itinerary"]
        comparison_rows.append(
            {
                "Trip": f"#{idx}: {rec['origin']} → {it.destination}",
                "Days": it.duration_days,
                "Flight": f"{it.flight.airline} (₹{it.budget.flight_cost:,.0f})" if it.flight else "Separate (₹0)",
                "Hotel": f"{it.hotel.name} ({it.hotel.stars}★)" if it.hotel else "None",
                "Hotel Stay (₹)": f"₹{it.budget.hotel_cost:,.0f}",
                "Combined Total (₹)": f"₹{it.budget.total_estimated_cost:,.0f}",
                "Target Budget (₹)": f"₹{rec['user_budget']:,.0f}",
            }
        )
    st.dataframe(comparison_rows, use_container_width=True, hide_index=True)