import json
from pathlib import Path

from langchain.tools import tool


DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "places.json"
)


def load_places():
    """Load places from the JSON dataset."""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Places dataset not found: {DATA_FILE}"
        ) from exc

    except json.JSONDecodeError as exc:
        raise ValueError(
            "places.json contains invalid JSON."
        ) from exc


@tool
def search_places(
    city: str,
    place_type: str = "",
    min_rating: float = 0,
) -> str:
    """Search places in a city by type and minimum rating.

    Args:
        city: Destination city.
        place_type: Optional type such as museum, fort, market, or park.
        min_rating: Optional minimum rating. Use 0 for no minimum.

    Returns:
        Matching places sorted by rating.
    """
    places = load_places()

    city = city.strip().lower()
    place_type = place_type.strip().lower()

    matches = []

    for place in places:
        if place["city"].strip().lower() != city:
            continue

        if (
            place_type
            and place["type"].strip().lower() != place_type
        ):
            continue

        if float(place["rating"]) < min_rating:
            continue

        matches.append(place)

    matches.sort(
        key=lambda place: float(place["rating"]),
        reverse=True,
    )

    if not matches:
        return json.dumps({
            "message": "No matching places found.",
            "city": city.title(),
            "place_type": place_type or None,
        })

    return json.dumps({
        "count": len(matches),
        "places": matches,
    }, indent=2)