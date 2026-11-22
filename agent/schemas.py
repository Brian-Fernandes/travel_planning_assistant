from typing import List, Optional

from pydantic import BaseModel


class FlightOption(BaseModel):
    flight_id: str
    airline: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    price: float


class HotelOption(BaseModel):
    hotel_id: str
    name: str
    city: str
    stars: int
    price_per_night: float
    amenities: List[str]


class Place(BaseModel):
    place_id: str
    name: str
    city: str
    type: str
    rating: float


class DayPlan(BaseModel):
    day: int
    date: str
    morning: List[str]
    afternoon: List[str]
    evening: List[str]
    places: List[str]
    weather: str


class BudgetBreakdown(BaseModel):
    flight_cost: float
    hotel_cost: float
    food_cost: float
    transport_cost: float
    activity_cost: float
    total_estimated_cost: float
    currency: str = "INR"
    budget_note: str


class TravelItinerary(BaseModel):
    destination: str
    duration_days: int
    day_0_disclaimer: str = (
        "Day 0 is dedicated solely to arrival transit so all requested days are 100% sightseeing; "
        "return transit at the end of the final day is optional."
    )
    trip_summary: str
    flight: Optional[FlightOption] = None
    hotel: Optional[HotelOption] = None
    itinerary: List[DayPlan]
    optional_return_path: str = ""
    budget: BudgetBreakdown