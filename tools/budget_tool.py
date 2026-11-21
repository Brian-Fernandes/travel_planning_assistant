import json

from langchain.tools import tool


@tool
def calculate_budget(
    flight_cost: float,
    hotel_price_per_night: float,
    nights: int,
    daily_food_cost: float = 0,
    daily_transport_cost: float = 0,
    activity_cost: float = 0,
) -> str:
    """Calculate the estimated total trip budget.

    Args:
        flight_cost: Total flight cost in INR.
        hotel_price_per_night: Hotel cost per night in INR.
        nights: Number of hotel nights.
        daily_food_cost: Estimated food cost per day in INR.
        daily_transport_cost: Estimated transport cost per day in INR.
        activity_cost: Total activity cost in INR.

    Returns:
        Budget breakdown as JSON.
    """
    if flight_cost < 0:
        return json.dumps({"error": "flight_cost cannot be negative."})

    if hotel_price_per_night < 0:
        return json.dumps({
            "error": "hotel_price_per_night cannot be negative."
        })

    if nights < 0:
        return json.dumps({"error": "nights cannot be negative."})

    if daily_food_cost < 0 or daily_transport_cost < 0:
        return json.dumps({
            "error": "Daily costs cannot be negative."
        })

    if activity_cost < 0:
        return json.dumps({
            "error": "activity_cost cannot be negative."
        })

    hotel_total = hotel_price_per_night * nights
    food_total = daily_food_cost * (nights + 1)
    transport_total = daily_transport_cost * (nights + 1)

    total = (
        flight_cost
        + hotel_total
        + food_total
        + transport_total
        + activity_cost
    )

    return json.dumps({
    "flight_cost": flight_cost,
    "hotel_cost": hotel_total,
    "food_cost": food_total,
    "transport_cost": transport_total,
    "activity_cost": activity_cost,
    "total_estimated_cost": total,
    "currency": "INR",
    "budget_note": (
        "Flight and hotel costs are based on the available dataset. "
        "Food, local transportation, and activity costs are estimated "
        "and may vary based on actual spending."
    ),
}, indent=2)