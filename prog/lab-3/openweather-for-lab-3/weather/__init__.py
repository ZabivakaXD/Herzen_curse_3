import requests

__version__ = "0.1.3"

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
API_KEY = 'efdb4f3ca9906c8f3e4346fd6abdc5f7'

def get_weather(city, units="metric", lang="ru"):
    """Получить текущую погоду по названию города.

    :param city: название города, например "Stockholm"
    :param api_key: ключ OpenWeatherMap
    :return: словарь с погодой (ответ API)
    """
    params = {
        "q": city,
        "appid": API_KEY,
        "units": units,
        "lang": lang,
    }
    response = requests.get(BASE_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()
