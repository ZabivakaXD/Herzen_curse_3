"""Веб-сервер FastAPI — роль «Объекта» (Subject) из паттерна.

Сервер:

1. в фоне опрашивает источник курсов (:class:`RateProvider`) с заданным
   интервалом и передаёт снимок субъекту :class:`CurrencyRateSubject`;
2. на каждое WebSocket-подключение создаёт наблюдателя
   :class:`WebSocketObserver` со своим ``client_id`` и подписывает его на
   субъект; при обрыве соединения — отписывает;
3. отдаёт HTML-страницу наблюдателя по адресу ``/``.

Параметры через переменные окружения:

* ``POLL_INTERVAL`` — интервал опроса в секундах (по умолчанию 300 = 5 минут);
* ``SIMULATE`` — ``1``/``true`` включает :class:`SimulatedRateProvider`
  (случайные колебания курсов вместо реального ЦБ — удобно для демонстрации);
* ``CBR_URL`` — переопределить URL API ЦБ.
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .cbr_client import CBRClient, RateProvider, SimulatedRateProvider
from .models import RateChange, ServerMessage, change_to_dto, rate_to_dto
from .observer import (
    CurrencyFilterObserver,
    CurrencyRateSubject,
    LoggingObserver,
    Observer,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("currency.server")

STATIC_DIR = Path(__file__).parent / "static"


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").lower() in {"1", "true", "yes", "on"}


def build_provider() -> RateProvider:
    """Выбрать источник курсов исходя из переменных окружения."""
    if _env_flag("SIMULATE"):
        logger.info("Источник курсов: ИМИТАТОР (случайные колебания)")
        return SimulatedRateProvider(volatility=0.01)
    logger.info("Источник курсов: API ЦБ РФ")
    return CBRClient(url=os.getenv("CBR_URL") or None)


class WebSocketObserver(Observer):
    """Наблюдатель, обёрнутый вокруг одного WebSocket-подключения.

    Каждая открытая HTML-страница — это отдельный наблюдатель со своим
    уникальным ``client_id``, который и отображается на странице.
    """

    def __init__(self, websocket: WebSocket, client_id: str) -> None:
        self.websocket = websocket
        self.client_id = client_id

    async def update(self, subject: CurrencyRateSubject, changes: list[RateChange]) -> None:
        snapshot = subject.snapshot
        if snapshot is None:
            return
        message: ServerMessage = {
            "type": "update",
            "client_id": self.client_id,
            "date": snapshot.date,
            "timestamp": snapshot.timestamp,
            "rates": [rate_to_dto(r) for r in snapshot.rates.values()],
            "changes": [change_to_dto(c) for c in changes],
        }
        await self.websocket.send_json(message)

    async def send_welcome(self, subject: CurrencyRateSubject) -> None:
        """Отправить новому клиенту полную текущую картину курсов."""
        snapshot = subject.snapshot
        message: ServerMessage = {
            "type": "welcome",
            "client_id": self.client_id,
            "date": snapshot.date if snapshot else "",
            "timestamp": snapshot.timestamp if snapshot else "",
            "rates": [rate_to_dto(r) for r in snapshot.rates.values()] if snapshot else [],
            "changes": [],
        }
        await self.websocket.send_json(message)

    def __repr__(self) -> str:
        return f"WebSocketObserver(client_id={self.client_id!r})"


async def poll_loop(
    subject: CurrencyRateSubject, provider: RateProvider, interval: float
) -> None:
    """Фоновая задача: опрашивать источник и обновлять субъект."""
    logger.info("Запущен опрос курсов с интервалом %.0f сек.", interval)
    while True:
        try:
            snapshot = await provider.fetch()
            await subject.set_snapshot(snapshot)
        except asyncio.CancelledError:
            logger.info("Опрос курсов остановлен")
            raise
        except Exception:
            logger.exception("Не удалось обновить курсы — повтор через интервал")
        await asyncio.sleep(interval)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Жизненный цикл приложения: поднять субъект и фоновый опрос."""
    subject = CurrencyRateSubject()
    # серверные наблюдатели-примеры «компонентов под конкретные валюты»
    subject.attach(LoggingObserver())
    for code in ("USD", "EUR", "GBP"):
        subject.attach(CurrencyFilterObserver(code))

    provider = build_provider()
    interval = float(os.getenv("POLL_INTERVAL", "300"))  # 300 сек = 5 минут

    app.state.subject = subject
    task = asyncio.create_task(poll_loop(subject, provider, interval))
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="Currency Observer", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def index() -> FileResponse:
    """Отдать HTML-страницу наблюдателя."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/healthz")
async def healthz() -> dict[str, object]:
    """Простой health-check: число подписчиков и наличие данных."""
    subject: CurrencyRateSubject = app.state.subject
    return {
        "status": "ok",
        "observers": subject.observer_count,
        "has_data": subject.snapshot is not None,
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Точка подключения наблюдателя (HTML-страницы)."""
    await websocket.accept()
    subject: CurrencyRateSubject = websocket.app.state.subject
    client_id = uuid.uuid4().hex[:8]
    observer = WebSocketObserver(websocket, client_id)
    subject.attach(observer)
    logger.info("Клиент %s подключён (всего %d)", client_id, subject.observer_count)
    try:
        await observer.send_welcome(subject)
        # держим соединение открытым; входящие сообщения нам не нужны,
        # но receive позволяет поймать отключение клиента.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        subject.detach(observer)
        logger.info("Клиент %s отключён (всего %d)", client_id, subject.observer_count)
