"""Реализация паттерна «Наблюдатель» (Observer).

* :class:`Subject` — абстрактный субъект: умеет подписывать, отписывать и
  уведомлять наблюдателей.
* :class:`Observer` — абстрактный наблюдатель с единственным методом
  :meth:`Observer.update`.
* :class:`CurrencyRateSubject` — конкретный субъект. Хранит последний снимок
  курсов, при обновлении вычисляет изменения и рассылает их наблюдателям.
* Конкретные наблюдатели: :class:`LoggingObserver` (пишет в лог) и
  :class:`CurrencyFilterObserver` (следит за одной валютой, например USD).

Наблюдатель-WebSocket (каждая открытая HTML-страница) живёт в
``app/server.py``, потому что он завязан на транспорт.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from .models import RateChange, RateSnapshot

logger = logging.getLogger("currency.observer")


class Observer(ABC):
    """Наблюдатель получает уведомления об изменении курсов."""

    @abstractmethod
    async def update(self, subject: "CurrencyRateSubject", changes: list[RateChange]) -> None:
        """Вызывается субъектом при изменении состояния.

        :param subject:  субъект-источник (даёт доступ к полному состоянию).
        :param changes:  список изменившихся курсов.
        """
        raise NotImplementedError


class Subject(ABC):
    """Субъект управляет подписками и рассылает уведомления."""

    @abstractmethod
    def attach(self, observer: Observer) -> None:
        """Подписать наблюдателя."""

    @abstractmethod
    def detach(self, observer: Observer) -> None:
        """Отписать наблюдателя."""

    @abstractmethod
    async def notify(self, changes: list[RateChange]) -> None:
        """Уведомить всех наблюдателей об изменениях."""


class CurrencyRateSubject(Subject):
    """Конкретный субъект: отслеживает курсы валют ЦБ РФ."""

    def __init__(self) -> None:
        self._observers: list[Observer] = []
        self._snapshot: RateSnapshot | None = None

    # --- управление подписками --------------------------------------------

    def attach(self, observer: Observer) -> None:
        if observer not in self._observers:
            self._observers.append(observer)
            logger.debug("Наблюдатель подписан: %s (всего %d)", observer, len(self._observers))

    def detach(self, observer: Observer) -> None:
        if observer in self._observers:
            self._observers.remove(observer)
            logger.debug("Наблюдатель отписан: %s (всего %d)", observer, len(self._observers))

    @property
    def observer_count(self) -> int:
        """Текущее число подписчиков."""
        return len(self._observers)

    @property
    def snapshot(self) -> RateSnapshot | None:
        """Последний известный снимок курсов (или ``None``, если опросов не было)."""
        return self._snapshot

    # --- логика субъекта --------------------------------------------------

    async def notify(self, changes: list[RateChange]) -> None:
        """Разослать изменения всем наблюдателям.

        Список копируется, чтобы безопасно переживать отписку наблюдателя
        прямо во время рассылки (например, при обрыве WebSocket).
        """
        for observer in list(self._observers):
            try:
                await observer.update(self, changes)
            except Exception:  # отказ одного наблюдателя не должен ронять рассылку
                logger.exception("Ошибка при уведомлении наблюдателя %s", observer)

    async def set_snapshot(self, snapshot: RateSnapshot) -> list[RateChange]:
        """Принять новый снимок, вычислить изменения и уведомить наблюдателей.

        Возвращает список изменений (пустой, если курсы не поменялись —
        в этом случае рассылка не выполняется).
        """
        changes = snapshot.diff(self._snapshot)
        self._snapshot = snapshot
        if changes:
            logger.info("Обнаружено изменений курсов: %d", len(changes))
            await self.notify(changes)
        return changes


class LoggingObserver(Observer):
    """Наблюдатель, который просто пишет изменения в лог (для отладки)."""

    def __init__(self, name: str = "logger") -> None:
        self.name = name

    async def update(self, subject: CurrencyRateSubject, changes: list[RateChange]) -> None:
        for change in changes:
            arrow = {"up": "▲", "down": "▼", "flat": "="}[change.direction]
            logger.info(
                "[%s] %s %s %.4f -> %.4f (%+.4f, %+.2f%%)",
                self.name,
                change.char_code,
                arrow,
                change.old_value if change.old_value is not None else float("nan"),
                change.new_value,
                change.delta,
                change.pct,
            )

    def __repr__(self) -> str:
        return f"LoggingObserver(name={self.name!r})"


class CurrencyFilterObserver(Observer):
    """Наблюдатель за одной конкретной валютой (USD, EUR, GBP ...).

    Демонстрирует идею «компонентов, отслеживающих конкретные валюты»:
    реагирует только если изменился курс отслеживаемого кода. Полученные
    изменения накапливаются в :attr:`history`, что удобно для тестов.
    """

    def __init__(self, char_code: str) -> None:
        self.char_code = char_code.upper()
        self.history: list[RateChange] = []

    async def update(self, subject: CurrencyRateSubject, changes: list[RateChange]) -> None:
        for change in changes:
            if change.char_code == self.char_code:
                self.history.append(change)
                logger.info(
                    "[watch:%s] новый курс %.4f (%+.4f)",
                    self.char_code,
                    change.new_value,
                    change.delta,
                )

    def __repr__(self) -> str:
        return f"CurrencyFilterObserver(char_code={self.char_code!r})"
