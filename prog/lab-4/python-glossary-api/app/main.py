"""FastAPI-приложение «Глоссарий терминов Python».

Пять операций (CRUD) над глоссарием, валидация через Pydantic, хранение в
SQLite, автоматическая миграция и наполнение базы при старте.
"""
from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models, schemas
from .database import SessionLocal, get_db, init_db

# Начальное наполнение: (термин, определение, категория).
SEED = [
    ("Variable", "Именованная ссылка на объект в памяти.", "Основы"),
    ("Function", "Именованный блок кода (def), выполняющий задачу.", "Основы"),
    ("Class", "Шаблон для создания объектов с атрибутами и методами.", "ООП"),
    ("Method", "Функция, определённая внутри класса.", "ООП"),
    ("Inheritance", "Получение классом атрибутов и методов родителя.", "ООП"),
    ("List", "Изменяемая упорядоченная коллекция: [1, 2, 3].", "Типы данных"),
    ("Tuple", "Неизменяемая упорядоченная коллекция: (1, 2, 3).", "Типы данных"),
    ("Dictionary", "Коллекция пар «ключ — значение».", "Типы данных"),
    ("Set", "Неупорядоченная коллекция уникальных элементов.", "Типы данных"),
    ("String", "Неизменяемая последовательность символов Unicode.", "Типы данных"),
    ("Module", "Файл с кодом Python (.py), который можно импортировать.", "Структура"),
    ("Package", "Каталог с модулями Python.", "Структура"),
    ("Decorator", "Функция, расширяющая поведение другой функции (@).", "Синтаксис"),
    ("Generator", "Функция с yield, выдающая значения лениво.", "Синтаксис"),
    ("List comprehension", "Краткий синтаксис создания списка.", "Синтаксис"),
    ("Lambda", "Анонимная функция в одну строку.", "Синтаксис"),
    ("F-string", "Форматированный литерал с префиксом f.", "Синтаксис"),
    ("Iterator", "Объект, выдающий элементы по одному (__next__).", "Концепции"),
    ("Closure", "Вложенная функция, запоминающая внешние переменные.", "Концепции"),
    ("Context manager", "Объект для конструкции with (__enter__/__exit__).", "Концепции"),
    ("Duck typing", "Тип определяется наличием методов, а не классом.", "Концепции"),
    ("Type hint", "Аннотация типа переменной или аргумента.", "Концепции"),
    ("Exception", "Объект, сигнализирующий об ошибке (try/except).", "Ошибки"),
    ("GIL", "Глобальная блокировка интерпретатора CPython.", "Внутреннее устройство"),
    ("PEP 8", "Руководство по стилю оформления кода Python.", "Стиль кода"),
    ("pip", "Менеджер пакетов Python для установки библиотек.", "Экосистема"),
    ("Virtual environment", "Изолированное окружение (venv).", "Экосистема"),
]


def seed(db: Session) -> None:
    """Наполняет таблицу, если она пуста."""
    if db.query(models.Term).count() == 0:
        db.add_all(models.Term(term=t, definition=d, category=c) for t, d, c in SEED)
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # автоматическая миграция структуры данных
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Python Glossary API",
    description="Глоссарий терминов Python: список, поиск, добавление, "
    "обновление и удаление терминов.",
    version="1.0.0",
    lifespan=lifespan,
)


def find(db: Session, term: str):
    """Поиск термина по ключевому слову без учёта регистра."""
    return (
        db.query(models.Term)
        .filter(func.lower(models.Term.term) == term.strip().lower())
        .first()
    )


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")


@app.get("/terms", response_model=List[schemas.TermOut], summary="Список всех терминов")
def list_terms(db: Session = Depends(get_db)):
    return db.query(models.Term).order_by(models.Term.term).all()


@app.get(
    "/terms/{term}",
    response_model=schemas.TermOut,
    summary="Получить термин по ключевому слову",
)
def get_term(term: str, db: Session = Depends(get_db)):
    obj = find(db, term)
    if obj is None:
        raise HTTPException(404, f"Термин '{term}' не найден")
    return obj


@app.post(
    "/terms",
    response_model=schemas.TermOut,
    status_code=201,
    summary="Добавить новый термин",
)
def create_term(data: schemas.TermCreate, db: Session = Depends(get_db)):
    if find(db, data.term) is not None:
        raise HTTPException(409, f"Термин '{data.term}' уже существует")
    obj = models.Term(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@app.put(
    "/terms/{term}",
    response_model=schemas.TermOut,
    summary="Обновить существующий термин",
)
def update_term(term: str, data: schemas.TermUpdate, db: Session = Depends(get_db)):
    obj = find(db, term)
    if obj is None:
        raise HTTPException(404, f"Термин '{term}' не найден")
    obj.definition = data.definition
    obj.category = data.category
    db.commit()
    db.refresh(obj)
    return obj


@app.delete("/terms/{term}", summary="Удалить термин")
def delete_term(term: str, db: Session = Depends(get_db)):
    obj = find(db, term)
    if obj is None:
        raise HTTPException(404, f"Термин '{term}' не найден")
    db.delete(obj)
    db.commit()
    return {"detail": f"Термин '{term}' удалён"}
