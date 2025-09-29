
import os, sys, pathlib

# Додаємо шлях до кореневої директорії проекту для імпорту модулів
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://postgres:mysecretpassword@localhost:5432/contacts_test")
os.environ.setdefault("REDIS_URL", "")        # Redis не обов'язковий у тестах
os.environ.setdefault("CLOUDINARY_URL", "")   # щоб не чіплявся SDK

# import tempfile, pathlib, sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, engine as app_engine
from app.models import Base
from app.settings import settings



# Використаємо SQLite для тестів
TEST_DB_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(autouse=True)
def _clean_db_before_each_test():
    # Страховка: убеждаемся, что это тестовая БД
    db_url = str(app_engine.url)
    assert any(tag in db_url for tag in ("contacts_test", "_test")), f"Refusing to TRUNCATE non-test DB: {db_url}"

    # Чистим СРАЗУ перед тестом
    with app_engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE public.contacts, public.users, public.app_meta RESTART IDENTITY CASCADE"))

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
