from tools.budget_tool import calculate_budget


result = calculate_budget.invoke({
    "flight_cost": 3304,
    "hotel_price_per_night": 1232,
    "nights": 4,
    "daily_food_cost": 800,
    "daily_transport_cost": 500,
    "activity_cost": 1000,
})

print(result)