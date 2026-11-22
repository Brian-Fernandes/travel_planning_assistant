from functools import lru_cache
from typing import List
from google import genai


@lru_cache(maxsize=4)
def get_available_flash_models(api_key: str) -> List[str]:
    """Return all active Gemini Flash models for this key, newest first (no hardcoding)."""
    client = genai.Client(api_key=api_key)
    all_models = [
        m.name.removeprefix("models/")
        for m in client.models.list()
        if "generateContent" in (m.supported_actions or [])
        and "flash" in m.name.lower()
        and "image" not in m.name.lower()
        and "preview" not in m.name.lower()
        and "2.5" not in m.name.lower()
    ]

    # Prefer standard flash models first, then flash-lite models as high-availability fallbacks
    primary = sorted([m for m in all_models if "lite" not in m.lower()], reverse=True)
    lite = sorted([m for m in all_models if "lite" in m.lower()], reverse=True)
    ordered = primary + lite

    if not ordered:
        raise RuntimeError("No active Gemini Flash models found for the provided API key.")
    return ordered