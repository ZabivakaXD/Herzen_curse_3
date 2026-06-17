"""Подключение к БД SQLite и автоматическая миграция структуры при старте."""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Адрес БД можно переопределить переменной окружения DATABASE_URL.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/glossary.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Зависимость FastAPI: выдаёт сессию БД и закрывает её после запроса."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Автоматическая миграция: создаёт каталог БД и недостающие таблицы."""
    if DATABASE_URL.startswith("sqlite"):
        directory = os.path.dirname(DATABASE_URL.split("///", 1)[-1])
        if directory:
            os.makedirs(directory, exist_ok=True)
    from . import models  # импорт регистрирует модели в метаданных

    Base.metadata.create_all(bind=engine)
