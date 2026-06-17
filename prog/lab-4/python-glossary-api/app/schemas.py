"""Pydantic-схемы для валидации входных данных и OpenAPI."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TermBase(BaseModel):
    # str_strip_whitespace убирает пробелы, после чего пустые строки не проходят.
    model_config = ConfigDict(str_strip_whitespace=True)

    term: str = Field(..., min_length=1, max_length=100, examples=["decorator"])
    definition: str = Field(
        ..., min_length=1, examples=["Функция, расширяющая поведение другой функции."]
    )
    category: Optional[str] = Field(None, max_length=80, examples=["Синтаксис"])


class TermCreate(TermBase):
    """Схема создания термина."""


class TermUpdate(BaseModel):
    """Схема обновления (термин определяется по пути)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    definition: str = Field(..., min_length=1)
    category: Optional[str] = Field(None, max_length=80)


class TermOut(TermBase):
    """Схема ответа."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    id: int
