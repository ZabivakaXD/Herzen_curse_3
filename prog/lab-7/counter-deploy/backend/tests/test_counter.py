"""
Тесты бизнес-логики счётчика.

Redis не запускается по-настоящему — вместо него используется fakeredis
(in-memory эмулятор), что делает тесты быстрыми и независимыми от окружения.
Приложение собирается через create_app(redis_client=...) с подставленным
fake-клиентом.
"""
import os

import fakeredis
import pytest

os.environ["FLASK_SKIP_AUTO_APP"] = "1"

from app import COUNTER_KEY, NEGATIVE_ERROR, create_app  # noqa: E402


@pytest.fixture
def client():
    """Тестовый клиент Flask с чистым fakeredis на каждый тест."""
    fake = fakeredis.FakeStrictRedis(decode_responses=True)
    app = create_app(redis_client=fake)
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        test_client.fake = fake  # доступ к Redis из теста при необходимости
        yield test_client


def test_initial_value_is_zero(client):
    """1. Инициализация: при первом запросе значение счётчика равно 0."""
    resp = client.get("/api/counter")
    assert resp.status_code == 200
    assert resp.get_json() == {"value": 0}


def test_increment_adds_one(client):
    """2. Увеличение: после /increment значение увеличивается на 1."""
    resp = client.post("/api/counter/increment")
    assert resp.status_code == 200
    assert resp.get_json()["value"] == 1

    # Повторный вызов снова увеличивает на 1.
    resp = client.post("/api/counter/increment")
    assert resp.get_json()["value"] == 2


def test_decrement_below_zero_returns_400(client):
    """3. Защита от отрицательных значений.

    При попытке уменьшить счётчик, равный 0, сервер возвращает HTTP 400
    и JSON с сообщением об ошибке. Значение в Redis не уходит в минус.
    """
    resp = client.post("/api/counter/decrement")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": NEGATIVE_ERROR}

    # Счётчик остался равен 0, а не -1.
    assert int(client.fake.get(COUNTER_KEY)) == 0


def test_decrement_after_increment(client):
    """Доп.: корректное уменьшение, когда счётчик больше 0."""
    client.post("/api/counter/increment")
    client.post("/api/counter/increment")  # value == 2

    resp = client.post("/api/counter/decrement")
    assert resp.status_code == 200
    assert resp.get_json()["value"] == 1


def test_reset_sets_zero(client):
    """Доп.: /reset обнуляет счётчик."""
    client.post("/api/counter/increment")
    client.post("/api/counter/increment")

    resp = client.post("/api/counter/reset")
    assert resp.status_code == 200
    assert resp.get_json() == {"value": 0}
