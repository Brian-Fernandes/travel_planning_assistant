from agent.travel_agent import create_travel_agent

print("1. Creating agent...")

agent = create_travel_agent()

print("2. Agent created.")

request = """
Plan a 3-day trip from Mumbai to Goa.

Budget: ₹15,000.

Preferences:
- beaches
- forts
- markets
- good-rated places
- affordable hotel

Use the available tools to find a suitable flight,
hotel, places, weather forecast, and calculate the estimated
trip budget.

Return a complete structured itinerary.
"""

print("3. Sending request...")

try:
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": request,
                }
            ]
        },
        config={
            "recursion_limit": 10
        },
    )

    print("4. Response received.")
    print(result)

except Exception as e:
    print("ERROR:")
    print(type(e).__name__)
    print(e)