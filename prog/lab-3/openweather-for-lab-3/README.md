# openweather-simple

Простой клиент для [OpenWeatherMap API](https://openweathermap.org/api).

Исходный код: **https://github.com/ZabivakaXD/Herzen_curse_3/tree/main/prog/lab-3**

## Использование

```python
from weather import get_weather

data = get_weather("Stockholm")
print(data["main"]["temp"])
print(data["weather"][0]["description"])
```

