from tools.places_tool import search_places


result = search_places.invoke({
    "city": "Goa",
    "place_type": "fort",
    "min_rating": 4.0,
})

print(result)