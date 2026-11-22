from typing import Any, Dict, List

from agent.schemas import TravelItinerary


def evaluate_itinerary(itinerary: TravelItinerary, user_budget: float) -> Dict[str, Any]:
    """6-point itinerary quality & pacing audit merged from ADK evaluation_service."""
    issues: List[str] = []
    passed: List[str] = []
    score = 100

    schedule = itinerary.itinerary
    if not schedule:
        return {
            "score": 0,
            "is_acceptable": False,
            "issues": ["No day-wise schedule generated."],
            "passed": [],
        }

    # 1. Day count match
    if len(schedule) != itinerary.duration_days:
        issues.append(f"Scheduled {len(schedule)} days instead of requested {itinerary.duration_days} days.")
        score -= 20
    else:
        passed.append(f"Exact {itinerary.duration_days}-day schedule coverage")

    # 2. Duplicate day numbers
    day_nums = [d.day for d in schedule]
    if len(day_nums) != len(set(day_nums)):
        issues.append("Duplicate day numbers detected.")
        score -= 10
    else:
        passed.append("Sequential non-duplicate day numbering")

    # 3. Duplicate attractions across days
    seen_places: set[str] = set()
    dup_found = False
    for d in schedule:
        for place in d.places:
            key = place.strip().lower()
            if key in seen_places:
                dup_found = True
            seen_places.add(key)

    if dup_found:
        issues.append("Repeated attractions found across multiple days.")
        score -= 15
    else:
        passed.append(f"{len(seen_places)} unique attractions with zero repeats")

    # 4. Empty days check
    empty_days = [d.day for d in schedule if not d.places and not (d.morning or d.afternoon or d.evening)]
    if empty_days:
        issues.append(f"Unexpected empty schedule on Day(s): {empty_days}.")
        score -= min(10, len(empty_days) * 5)
    else:
        passed.append("All days populated with activities")

    # 5. Pacing balance across days
    counts = [len(d.places) for d in schedule]
    if counts and (max(counts) - min(counts) > 4):
        issues.append("Attractions are unevenly distributed across days.")
        score -= 5
    else:
        passed.append("Balanced daily sightseeing density")

    # 6. Flight + Hotel budget compliance
    total = itinerary.budget.total_estimated_cost
    if user_budget > 0 and total > user_budget:
        issues.append(f"Flight + Hotel total (₹{total:,.0f}) exceeds target budget by ₹{total - user_budget:,.0f}.")
        score -= 10
    else:
        passed.append(f"Within budget (₹{total:,.0f} / ₹{user_budget:,.0f})")

    score = max(0, min(score, 100))
    return {
        "score": score,
        "is_acceptable": score >= 60,
        "issues": issues,
        "passed": passed,
    }