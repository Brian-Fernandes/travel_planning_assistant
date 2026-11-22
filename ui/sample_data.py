from datetime import date, timedelta

from agent.schemas import (
    BudgetBreakdown,
    DayPlan,
    FlightOption,
    HotelOption,
    TravelItinerary,
)


def build_sample_goa_itinerary() -> TravelItinerary:
    """Return a pre-built sample itinerary (Flight + Hotel budget only, 0 API calls)."""
    start = date.today() + timedelta(days=1)
    return TravelItinerary(
        destination="Goa",
        duration_days=3,
        trip_summary=(
            "A zone-clustered 3-day Mumbai to Goa itinerary pairing SpiceJet FL0024 (₹3,304) and "
            "live-sourced 5-star Royal Heritage (₹1,232/night for 2 nights) for a combined flight + hotel "
            "total of ₹5,768—well within your ₹15,000 budget."
        ),
        flight=FlightOption(
            flight_id="FL0024",
            airline="SpiceJet",
            origin="Mumbai",
            destination="Goa",
            departure_time="2025-07-15T14:38:00",
            arrival_time="2025-07-15T18:38:00",
            price=3304.0,
        ),
        hotel=HotelOption(
            hotel_id="LIVE_H1",
            name="Royal Heritage",
            city="Goa",
            stars=5,
            price_per_night=1232.0,
            amenities=["wifi", "parking", "breakfast", "pool"],
        ),
        itinerary=[
            DayPlan(
                day=1,
                date=start.isoformat(),
                morning=["Arrive in Goa and check in at Royal Heritage (North Goa base)."],
                afternoon=["Explore Fort Aguada overlooking the Arabian Sea (Candolim zone)."],
                evening=["Sunset walk along Baga & Calangute Beach."],
                places=["Fort Aguada", "Baga & Calangute Beach"],
                weather="31°C / 25°C — Mostly sunny with coastal breeze",
            ),
            DayPlan(
                day=2,
                date=(start + timedelta(days=1)).isoformat(),
                morning=["Visit Chapora Fort for panoramic coastal views (Vagator zone)."],
                afternoon=["Browse local stalls at Anjuna Flea Market."],
                evening=["Relaxed evening along the North Goa coast."],
                places=["Chapora Fort", "Anjuna Flea Market"],
                weather="30°C / 24°C — Partly cloudy, pleasant evening",
            ),
            DayPlan(
                day=3,
                date=(start + timedelta(days=2)).isoformat(),
                morning=["Head to Panjim / Old Goa zone; visit Goa State Museum."],
                afternoon=["Tour UNESCO-listed Basilica of Bom Jesus in Old Goa."],
                evening=["Depart Goa for Mumbai."],
                places=["Goa State Museum", "Basilica of Bom Jesus"],
                weather="31°C / 25°C — Clear skies",
            ),
        ],
        budget=BudgetBreakdown(
            flight_cost=3304.0,
            hotel_cost=2464.0,
            food_cost=0.0,
            transport_cost=0.0,
            activity_cost=0.0,
            total_estimated_cost=5768.0,
            currency="INR",
            budget_note="Combined Flight (₹3,304) + 2 Hotel Nights (₹2,464). Local transit & personal expenses excluded.",
        ),
    )