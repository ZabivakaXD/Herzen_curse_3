"""ORM-модель термина глоссария."""
from sqlalchemy import Column, Integer, String, Text

from .database import Base


class Term(Base):
    __tablename__ = "terms"

    id = Column(Integer, primary_key=True)
    term = Column(String(100), unique=True, nullable=False, index=True)
    definition = Column(Text, nullable=False)
    category = Column(String(80), nullable=True)
