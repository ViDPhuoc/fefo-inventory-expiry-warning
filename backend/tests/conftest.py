"""SQLite kiểm tra nghiệp vụ; TEST_DATABASE_URL cho phép chạy lại trên PostgreSQL riêng.
Không trỏ TEST_DATABASE_URL vào DB thật: fixture tạo/xóa bảng trong schema test riêng.
"""

import os
import sys
from pathlib import Path
from datetime import date
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["APP_TODAY"] = "2026-09-07"
from app.database import Base, get_db
from app import models
from app.main import app
from scripts.mock_dataset import build_dataset
from app.cli import insert_dataset


@pytest.fixture(scope="session")
def dataset():
    return build_dataset(date(2026, 9, 7), products=6, days=14)


@pytest.fixture()
def env(dataset):
    url = os.getenv("TEST_DATABASE_URL")
    if url:
        # Schema có tên riêng; không DROP public hay bảng người dùng.
        from uuid import uuid4

        schema = "expiry_test_" + uuid4().hex
        admin = create_engine(url)
        with admin.begin() as c:
            c.exec_driver_sql(f"CREATE SCHEMA {schema}")
        engine = create_engine(url, connect_args={"options": f"-csearch_path={schema}"})
    else:
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )

        @event.listens_for(engine, "connect")
        def foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with Session.begin() as db:
        insert_dataset(db, dataset)

    def override_db():
        with Session() as db:
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise

    app.dependency_overrides[get_db] = override_db
    client = TestClient(app, raise_server_exceptions=False)
    yield client, Session
    client.close()
    app.dependency_overrides.clear()
    engine.dispose()
    if url:
        with admin.begin() as c:
            c.exec_driver_sql(f"DROP SCHEMA {schema} CASCADE")
        admin.dispose()


@pytest.fixture
def manager():
    return ("manager1", "Demo@2026")


@pytest.fixture
def staff():
    return ("staff1", "Demo@2026")
