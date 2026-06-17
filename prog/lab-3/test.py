from weather import get_weather

data = get_weather("Saint Petersburg")
print(data["main"]["temp"])
print(data["weather"][0]["description"])