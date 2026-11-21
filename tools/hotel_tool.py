import json
from pathlib import Path

from langchain.tools import tool


DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "hotels.json"


def load_hotels():
    """Load hotel records from the JSON dataset."""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Hotel dataset not found: {DATA_FILE}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError("hotels.json contains invalid JSON.") from exc


@tool
def search_hotels(
    city: str,
    max_price_per_night: float = 0,
    min_stars: int = 0,
) -> str:
    """Search and rank hotels by city, price and minimum star rating.

    Args:
        city: Destination city.
        max_price_per_night: Maximum nightly price in INR. Use 0 for no limit.
        min_stars: Minimum hotel star rating. Use 0 for no minimum.

    Returns:
        Matching hotels sorted by price.
    """

    hotels = load_hotels()
    city = city.strip().lower()

    matches = []

    for hotel in hotels:
        if hotel["city"].strip().lower() != city:
            continue

        if (
            max_price_per_night > 0
            and float(hotel["price_per_night"]) > max_price_per_night
        ):
            continue

        if int(hotel["stars"]) < min_stars:
            continue

        matches.append(hotel)

    # Best value first: higher stars, then lower price.
    matches.sort(
        key=lambda hotel: (
            -int(hotel["stars"]),
            float(hotel["price_per_night"]),
        )
    )

    if not matches:
        return json.dumps({
            "message": "No matching hotels found.",
            "city": city.title(),
        })

    return json.dumps({
        "count": len(matches),
        "hotels": matches,
    }, indent=2)