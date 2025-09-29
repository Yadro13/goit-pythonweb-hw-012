from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .settings import settings

# URL бази даних з .env
DATABASE_URL = settings.DATABASE_URL  # noqa: N816

# Ініціалізація синхронного двигуна SQLAlchemy
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Фабрика сесій
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator:
    """Повертає сесію БД для залежностей FastAPI. Закриває сесію після використання."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
