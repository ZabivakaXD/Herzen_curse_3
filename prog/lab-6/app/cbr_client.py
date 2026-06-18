"""Поставщики курсов валют.

Определяется протокол :class:`RateProvider` и две реализации:

* :class:`CBRClient` — обращается к реальному API ЦБ РФ (JSON-зеркало
  ``cbr-xml-daily.ru``, формат идентичен официальному ЦБ).
* :class:`SimulatedRateProvider` — генерирует случайные колебания курсов.
  Нужен для демонстрации и тестов: реальный курс ЦБ меняется лишь раз в
  сутки, а нам важно показать работу «Наблюдателя» в реальном времени.
"""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable

import httpx

from .models import CurrencyRate, RateSnapshot


@runtime_checkable
class RateProvider(Protocol):
    """Любой источник курсов умеет асинхронно отдавать снимок курсов."""

    async def fetch(self) -> RateSnapshot:  # pragma: no cover - протокол
        ...


class CBRClient:
    """Асинхронный клиент API Центробанка РФ."""

    #: JSON-зеркало официального API ЦБ (тот же формат, удобнее парсить).
    DEFAULT_URL = "https://www.cbr-xml-daily.ru/daily_json.js"

    def __init__(self, url: str | None = None, timeout: float = 10.0) -> None:
        self.url = url or self.DEFAULT_URL
        self.timeout = timeout

    async def fetch(self) -> RateSnapshot:
        """Запросить актуальные курсы и вернуть типизированный снимок."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.url)
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
        return self.parse(payload)

    @staticmethod
    def parse(payload: dict[str, Any]) -> RateSnapshot:
        """Преобразовать JSON ответа ЦБ в :class:`RateSnapshot`."""
        rates: dict[str, CurrencyRate] = {}
        for code, item in payload.get("Valute", {}).items():
            rates[code] = CurrencyRate(
                char_code=item["CharCode"],
                name=item["Name"],
                nominal=int(item["Nominal"]),
                value=float(item["Value"]),
                previous=(
                    float(item["Previous"]) if item.get("Previous") is not None else None
                ),
            )
        return RateSnapshot(
            date=str(payload.get("Date", "")),
            timestamp=str(payload.get("Timestamp", "")),
            rates=rates,
        )


class SimulatedRateProvider:
    """Имитатор источника курсов для демонстрации и тестов.

    При каждом вызове :meth:`fetch` курсы случайно смещаются в пределах
    ``volatility`` процентов. Это позволяет «оживить» наблюдателей, не
    дожидаясь суточного обновления настоящего ЦБ.
    """

    def __init__(
        self,
        base: dict[str, CurrencyRate] | None = None,
        volatility: float = 0.01,
        seed: int | None = None,
    ) -> None:
        self.volatility = volatility
        self._rng = random.Random(seed)
        self._rates: dict[str, CurrencyRate] = base or self._default_base()

    @staticmethod
    def _default_base() -> dict[str, CurrencyRate]:
        seed_values = {
            "USD": ("Доллар США", 1, 79.50),
            "EUR": ("Евро", 1, 92.30),
            "GBP": ("Фунт стерлингов Соединенного королевства", 1, 108.10),
            "CNY": ("Китайский юань", 1, 11.05),
            "JPY": ("Иена", 100, 52.40),
        }
        return {
            code: CurrencyRate(char_code=code, name=name, nominal=nominal, value=value)
            for code, (name, nominal, value) in seed_values.items()
        }

    async def fetch(self) -> RateSnapshot:
        """Сместить курсы случайным образом и вернуть новый снимок."""
        updated: dict[str, CurrencyRate] = {}
        for code, rate in self._rates.items():
            factor = 1 + self._rng.uniform(-self.volatility, self.volatility)
            new_value = round(rate.value * factor, 4)
            updated[code] = CurrencyRate(
                char_code=rate.char_code,
                name=rate.name,
                nominal=rate.nominal,
                value=new_value,
                previous=rate.value,
            )
        self._rates = updated
        now = datetime.now(timezone.utc).isoformat()
        return RateSnapshot(date=now[:10], timestamp=now, rates=updated)
