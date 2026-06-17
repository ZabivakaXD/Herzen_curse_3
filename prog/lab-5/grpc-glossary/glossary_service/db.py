"""Хранение глоссария: SQLite + SQLAlchemy, авто-миграция и наполнение."""
import os

from sqlalchemy import Column, Integer, String, Text, create_engine, func
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/glossary.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Term(Base):
    __tablename__ = "terms"
    id = Column(Integer, primary_key=True)
    term = Column(String(100), unique=True, nullable=False, index=True)
    definition = Column(Text, nullable=False)
    category = Column(String(80), nullable=True)


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
    ("Module", "Файл с кодом Python (.py) для импорта.", "Структура"),
    ("Package", "Каталог с модулями Python.", "Структура"),
    ("Decorator", "Функция, расширяющая поведение другой функции (@).", "Синтаксис"),
    ("Generator", "Функция с yield, выдающая значения лениво.", "Синтаксис"),
    ("List comprehension", "Краткий синтаксис создания списка.", "Синтаксис"),
    ("Lambda", "Анонимная функция в одну строку.", "Синтаксис"),
    ("F-string", "Форматированный литерал с префиксом f.", "Синтаксис"),
    ("Iterator", "Объект, выдающий элементы по одному (__next__).", "Концепции"),
    ("Closure", "Вложенная функция, запоминающая внешние переменные.", "Концепции"),
    ("Context manager", "Объект для конструкции with.", "Концепции"),
    ("Duck typing", "Тип определяется наличием методов, а не классом.", "Концепции"),
    ("Type hint", "Аннотация типа переменной или аргумента.", "Концепции"),
    ("Exception", "Объект, сигнализирующий об ошибке (try/except).", "Ошибки"),
    ("GIL", "Глобальная блокировка интерпретатора CPython.", "Внутреннее устройство"),
    ("PEP 8", "Руководство по стилю оформления кода Python.", "Стиль кода"),
    ("pip", "Менеджер пакетов Python для установки библиотек.", "Экосистема"),
    ("Virtual environment", "Изолированное окружение (venv).", "Экосистема"),
]


def init_db():
    """Авто-миграция: создаёт каталог и таблицы, затем наполняет, если пусто."""
    if DATABASE_URL.startswith("sqlite"):
        directory = os.path.dirname(DATABASE_URL.split("///", 1)[-1])
        if directory:
            os.makedirs(directory, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Term).count() == 0:
            db.add_all(Term(term=t, definition=d, category=c) for t, d, c in SEED)
            db.commit()
    finally:
        db.close()


def find(db, term: str):
    """Поиск термина по ключу без учёта регистра."""
    return db.query(Term).filter(func.lower(Term.term) == term.strip().lower()).first()
