"""
Подключение к Redis.

Модуль вынесен отдельно от app.py, чтобы:
  * бизнес-логику счётчика было удобно тестировать (в тестах вместо
    реального Redis подставляется fakeredis);
  * параметры подключения читались из переменных окружения (.env),
    что важно для деплоя нескольких студентов на один сервер.
"""
import os
import time

from redis import Redis, RedisError

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") or None


def get_redis_client(retries: int = 5, wait: float = 1.0) -> Redis:
    """Создать клиент Redis с несколькими попытками подключения.

    Контейнер с Redis может стартовать чуть позже приложения, поэтому
    подключение выполняется с ретраями и проверкой ping().
    """
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            client = Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=True,
            )
            client.ping()
            return client
        except RedisError as exc:
            last_error = exc
            if attempt == retries - 1:
                break
            time.sleep(wait)
    raise RedisError(f"Cannot connect to Redis: {last_error}")
