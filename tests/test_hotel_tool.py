from tools.hotel_tool import search_hotels


result = search_hotels.invoke({
    "city": "Goa",
    "max_price_per_night": 3000,
    "min_stars": 4,
})

print(result)