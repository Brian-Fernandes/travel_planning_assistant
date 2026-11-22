from agent.schemas import TravelItinerary


def format_itinerary_txt(itinerary: TravelItinerary, origin: str) -> str:
    """Format a TravelItinerary into a clean, human-readable .TXT travel brief."""
    lines: list[str] = [
        "FINAL TRAVEL ITINERARY",
        "=" * 48,
        f"Route       : {origin} -> {itinerary.destination}",
        f"Duration    : {itinerary.duration_days} Sightseeing Day(s) (+ Day 0 Transit)",
    ]

    if getattr(itinerary, "day_0_disclaimer", ""):
        lines.extend(["", f"NOTE: {itinerary.day_0_disclaimer}"])

    lines.extend(
        [
            "",
            "EXECUTIVE SUMMARY",
            "-" * 48,
            itinerary.trip_summary,
            "",
            "SELECTED FLIGHT (CATALOG)",
            "-" * 48,
        ]
    )

    if itinerary.flight:
        f = itinerary.flight
        lines.extend(
            [
                f"Flight      : {f.airline} ({f.flight_id})",
                f"Route       : {f.origin} -> {f.destination}",
                f"Departure   : {f.departure_time.replace('T', ' ')}",
                f"Duration/Arr: {f.arrival_time.replace('T', ' ')}",
                f"Fare        : INR {f.price:,.0f}",
            ]
        )
    else:
        lines.append("Flight      : None found in catalog (Book separately)")

    lines.extend(["", "SELECTED BASE HOTEL", "-" * 48])
    if itinerary.hotel:
        h = itinerary.hotel
        lines.extend(
            [
                f"Hotel       : {h.name} ({h.stars}-Star)",
                f"Nightly Rate: INR {h.price_per_night:,.0f} / night",
                f"Amenities   : {', '.join(h.amenities)}",
            ]
        )
    else:
        lines.append("Hotel       : None selected")

    lines.extend(["", "DAY-WISE SCHEDULE", "=" * 48])
    for d in itinerary.itinerary:
        day_label = "Day 0 — Arrival & Staging" if d.day == 0 else f"Day {d.day}"
        lines.extend(
            [
                "",
                f"{day_label} ({d.date}) | Weather: {d.weather}",
                f"  Morning   : {'; '.join(d.morning) if d.morning else 'Leisure'}",
                f"  Afternoon : {'; '.join(d.afternoon) if d.afternoon else 'Leisure'}",
                f"  Evening   : {'; '.join(d.evening) if d.evening else 'Leisure'}",
            ]
        )
        if d.places:
            lines.append(f"  Landmarks : {', '.join(d.places)}")

    if getattr(itinerary, "optional_return_path", ""):
        lines.extend(
            [
                "",
                "OPTIONAL RETURN PATH (END OF FINAL DAY)",
                "-" * 48,
                itinerary.optional_return_path,
            ]
        )

    b = itinerary.budget
    lines.extend(
        [
            "",
            "BUDGET SUMMARY (FLIGHT + HOTEL ONLY)",
            "=" * 48,
            f"Flight Ticket : INR {b.flight_cost:,.0f}",
            f"Hotel Stay    : INR {b.hotel_cost:,.0f}",
            "-" * 48,
            f"Combined Total: INR {b.total_estimated_cost:,.0f}",
            f"Note          : {b.budget_note}",
        ]
    )
    return "\n".join(lines) + "\n"