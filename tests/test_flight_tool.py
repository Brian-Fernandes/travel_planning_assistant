from tools.flight_tool import search_flights


result = search_flights.invoke({
    "origin": "Mumbai",
    "destination": "Goa",
})

print(result)