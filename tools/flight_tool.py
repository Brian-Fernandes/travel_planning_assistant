import json
from datetime import datetime
from pathlib import Path

from langchain.tools import tool


DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "flights.json"


def load_flights():
    """Load flight records from the JSON dataset."""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Flight dataset not found: {DATA_FILE}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError("flights.json contains invalid JSON.") from exc


@tool
def search_flights(
    origin: str,
    destination: str,
    travel_date: str = "",
    max_price: float = 0,
) -> str:
    """Search available flights by origin, destination, date and maximum price.

    Args:
        origin: Departure city, for example Mumbai.
        destination: Arrival city, for example Goa.
        travel_date: Optional date in YYYY-MM-DD format.
        max_price: Optional maximum ticket price in INR. Use 0 for no limit.

    Returns:
        Matching flights sorted by price.
    """

    flights = load_flights()

    origin = origin.strip().lower()
    destination = destination.strip().lower()

    if travel_date:
        try:
            datetime.strptime(travel_date, "%Y-%m-%d")
        except ValueError:
            return json.dumps({
                "error": "travel_date must use YYYY-MM-DD format."
            })

    matches = []

    for flight in flights:
        if flight["from"].strip().lower() != origin:
            continue

        if flight["to"].strip().lower() != destination:
            continue

        flight_date = flight["departure_time"][:10]

        if travel_date and flight_date != travel_date:
            continue

        if max_price > 0 and float(flight["price"]) > max_price:
            continue

        matches.append(flight)

    matches.sort(key=lambda flight: float(flight["price"]))

    if not matches:
        return json.dumps({
            "message": "No matching flights found.",
            "origin": origin.title(),
            "destination": destination.title(),
            "travel_date": travel_date or None,
        })

    return json.dumps({
        "count": len(matches),
        "flights": matches,
    }, indent=2)