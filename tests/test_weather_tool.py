from tools.weather_tool import get_weather


result = get_weather.invoke({
    "city": "Goa",
    "days": 3,
})

print(result)