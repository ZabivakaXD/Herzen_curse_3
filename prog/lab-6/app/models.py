"""Типизированные структуры данных приложения.

Здесь собраны все доменные модели: курс валюты, факт изменения курса,
снимок (snapshot) всех курсов на конкретную дату, а также формы сообщений,
которые сервер отправляет наблюдателям через WebSocket.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypedDict

Direction = Literal["up", "down", "flat"]


@dataclass(frozen=True, slots=True)
class CurrencyRate:
    """Курс одной валюты на конкретную дату.

    :param char_code:  буквенный код валюты (``USD``, ``EUR``, ``GBP`` ...).
    :param name:       человекочитаемое название (``Доллар США``).
    :param nominal:    номинал — за сколько единиц валюты указан ``value``.
    :param value:      курс в рублях за ``nominal`` единиц.
    :param previous:   предыдущий курс по данным ЦБ (может отсутствовать).
    """

    char_code: str
    name: str
    nominal: int
    value: float
    previous: float | None = None

    @property
    def per_unit(self) -> float:
        """Курс за одну единицу валюты (нормализованный по номиналу)."""
        return self.value / self.nominal if self.nominal else self.value


@dataclass(frozen=True, slots=True)
class RateChange:
    """Факт изменения курса между двумя опросами источника."""

    char_code: str
    name: str
    old_value: float | None
    new_value: float
    nominal: int

    @property
    def delta(self) -> float:
        """Абсолютное изменение курса (новый минус старый)."""
        if self.old_value is None:
            return 0.0
        return round(self.new_value - self.old_value, 4)

    @property
    def pct(self) -> float:
        """Изменение в процентах относительно прошлого значения."""
        if not self.old_value:
            return 0.0
        return round((self.new_value - self.old_value) / self.old_value * 100, 4)

    @property
    def direction(self) -> Direction:
        """Направление движения курса."""
        if self.old_value is None or self.new_value == self.old_value:
            return "flat"
        return "up" if self.new_value > self.old_value else "down"


@dataclass(frozen=True, slots=True)
class RateSnapshot:
    """Снимок всех курсов на конкретную дату."""

    date: str
    timestamp: str
    rates: dict[str, CurrencyRate]

    def diff(self, previous: "RateSnapshot | None") -> list[RateChange]:
        """Сравнить себя с прошлым снимком и вернуть список изменений.

        Если ``previous`` равен ``None`` (первый опрос), изменением считается
        каждая валюта — это позволяет отдать новому наблюдателю полную картину.
        """
        changes: list[RateChange] = []
        for code, rate in self.rates.items():
            old = previous.rates.get(code) if previous else None
            old_value = old.value if old else None
            if old_value is None or old_value != rate.value:
                changes.append(
                    RateChange(
                        char_code=code,
                        name=rate.name,
                        old_value=old_value,
                        new_value=rate.value,
                        nominal=rate.nominal,
                    )
                )
        return changes


# --- Формы сообщений WebSocket (то, что уходит в браузер как JSON) ----------


class RateDTO(TypedDict):
    """Сериализуемое представление курса для фронтенда."""

    char_code: str
    name: str
    nominal: int
    value: float


class ChangeDTO(TypedDict):
    """Сериализуемое представление изменения курса для фронтенда."""

    char_code: str
    name: str
    old_value: float | None
    new_value: float
    delta: float
    pct: float
    direction: Direction


class ServerMessage(TypedDict):
    """Сообщение от сервера наблюдателю.

    ``type`` = ``welcome`` для первого сообщения (полная картина) и
    ``update`` для последующих уведомлений об изменениях.
    """

    type: Literal["welcome", "update"]
    client_id: str
    date: str
    timestamp: str
    rates: list[RateDTO]
    changes: list[ChangeDTO]


def rate_to_dto(rate: CurrencyRate) -> RateDTO:
    """Преобразовать доменную модель курса в DTO для отправки клиенту."""
    return RateDTO(
        char_code=rate.char_code,
        name=rate.name,
        nominal=rate.nominal,
        value=rate.value,
    )


def change_to_dto(change: RateChange) -> ChangeDTO:
    """Преобразовать факт изменения в DTO для отправки клиенту."""
    return ChangeDTO(
        char_code=change.char_code,
        name=change.name,
        old_value=change.old_value,
        new_value=change.new_value,
        delta=change.delta,
        pct=change.pct,
        direction=change.direction,
    )
