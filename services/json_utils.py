import json
import logging
import re
from typing import Any, List


def safe_json_extract(text: Any, default: Any) -> Any:
    """Safely extract JSON from messy LLM or search responses without raising."""
    try:
        if isinstance(text, (dict, list)):
            return text

        if not isinstance(text, str):
            logging.warning("safe_json_extract: non-string input; returning default.")
            return default

        stripped = text.strip()
        if not stripped:
            return default

        # Strip markdown code fences if present
        stripped = re.sub(r"^```(?:json)?\s*|\s*```$", "", stripped, flags=re.IGNORECASE).strip()

        try:
            return json.loads(stripped)
        except Exception:
            pass

        candidates: List[str] = []
        for opening, closing in [("{", "}"), ("[", "]")]:
            start = stripped.find(opening)
            end = stripped.rfind(closing)
            if start != -1 and end != -1 and end > start:
                candidates.append(stripped[start : end + 1])

        for chunk in candidates:
            try:
                return json.loads(chunk)
            except Exception:
                continue

        lines = [ln.strip(" \t,-*") for ln in stripped.splitlines() if ln.strip()]
        items: List[str] = []
        for ln in lines:
            m = re.match(r"^\d+\.\s*(.+)$", ln)
            if m:
                ln = m.group(1).strip()
            ln = ln.strip('"').strip("'").strip()
            if ln:
                items.append(ln)

        if items:
            return {"items": items}

        return default
    except Exception as exc:
        logging.error(f"safe_json_extract: unexpected error: {exc}")
        return default