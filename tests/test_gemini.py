from google import genai
from dotenv import load_dotenv
import os
import time

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY"),
    http_options={"timeout": 15000},
)

models = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
]

for model in models:
    print(f"\nTesting: {model}")
    start = time.time()

    try:
        response = client.models.generate_content(
            model=model,
            contents="Reply with exactly: OK",
        )

        elapsed = time.time() - start
        print(f"SUCCESS ({elapsed:.1f}s): {response.text}")

    except Exception as e:
        elapsed = time.time() - start
        print(f"FAILED ({elapsed:.1f}s)")
        print(type(e).__name__)
        print(e)