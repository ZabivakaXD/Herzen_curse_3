"""
Flask-приложение «Счётчик».

API:
  GET  /api/counter            -> {"value": <int>}
  POST /api/counter/increment  -> {"value": <int>}
  POST /api/counter/decrement  -> {"value": <int>}  | 400 {"error": ...}
  POST /api/counter/reset      -> {"value": 0}

Бизнес-правила:
  * счётчик не может быть меньше 0;
  * при попытке уменьшить счётчик, равный 0, сервер возвращает HTTP 400
    и JSON {"error": "Counter cannot be negative"}.

Приложение собрано через фабрику create_app(redis_client=...), поэтому
в тестах можно подставить fakeredis вместо реального сервера Redis.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from redis import WatchError

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

COUNTER_KEY = "counter:value"
NEGATIVE_ERROR = "Counter cannot be negative"


def _read_value(redis_client) -> int:
    """Текущее значение счётчика (0, если ключа ещё нет)."""
    return int(redis_client.get(COUNTER_KEY) or 0)


def _decrement(redis_client) -> int:
    """Атомарно уменьшить счётчик на 1, не опускаясь ниже 0.

    Возвращает новое значение или поднимает ValueError, если счётчик
    уже равен 0. Атомарность обеспечивается оптимистической блокировкой
    (WATCH/MULTI), что корректно работает и с реальным Redis,
    и с fakeredis.
    """
    with redis_client.pipeline() as pipe:
        while True:
            try:
                pipe.watch(COUNTER_KEY)
                current = int(pipe.get(COUNTER_KEY) or 0)
                if current <= 0:
                    raise ValueError(NEGATIVE_ERROR)
                pipe.multi()
                pipe.decr(COUNTER_KEY)
                new_value = pipe.execute()[0]
                return int(new_value)
            except WatchError:
                # Значение изменили параллельно — повторяем попытку.
                continue
            finally:
                pipe.reset()


def create_app(redis_client=None) -> Flask:
    """Собрать Flask-приложение.

    redis_client можно передать явно (например, fakeredis в тестах).
    Если не передан — создаётся реальное подключение к Redis.
    """
    if redis_client is None:
        from redis_client import get_redis_client

        redis_client = get_redis_client()

    # Гарантируем существование ключа.
    if redis_client.get(COUNTER_KEY) is None:
        redis_client.set(COUNTER_KEY, 0)

    app = Flask(
        __name__,
        static_folder=str(BASE_DIR / "static"),
        static_url_path="/",
    )
    CORS(app)
    app.redis = redis_client  # доступ из тестов при желании

    @app.route("/api/counter", methods=["GET"])
    def get_counter():
        try:
            return jsonify({"value": _read_value(redis_client)})
        except Exception:
            return jsonify({"error": "Redis error"}), 500

    @app.route("/api/counter/increment", methods=["POST"])
    def increment():
        try:
            value = redis_client.incr(COUNTER_KEY)
            return jsonify({"value": int(value)})
        except Exception:
            return jsonify({"error": "Redis error"}), 500

    @app.route("/api/counter/decrement", methods=["POST"])
    def decrement():
        try:
            value = _decrement(redis_client)
            return jsonify({"value": value})
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception:
            return jsonify({"error": "Redis error"}), 500

    @app.route("/api/counter/reset", methods=["POST"])
    def reset():
        try:
            redis_client.set(COUNTER_KEY, 0)
            return jsonify({"value": 0})
        except Exception:
            return jsonify({"error": "Redis error"}), 500

    # Раздача собранного фронтенда (SPA).
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_spa(path):
        static_dir = BASE_DIR / "static"
        if path and (static_dir / path).exists():
            return send_from_directory(str(static_dir), path)
        return send_from_directory(str(static_dir), "index.html")

    return app


# Объект для gunicorn: `gunicorn app:app`.
# Создаётся только при реальном запуске, не при импорте в тестах.
if os.getenv("FLASK_SKIP_AUTO_APP") != "1":
    try:
        app = create_app()
    except Exception:  # noqa: BLE001 - при сборке без Redis не падаем на импорте
        app = None


if __name__ == "__main__":
    if app is None:
        app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
