"""Shared fixtures. Catalog tests use SQLite so they never touch PostgreSQL."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import reset_settings_cache
from app.database import get_db, reset_database_state
from app.main import app
from app.models import Base


@pytest.fixture
def sqlite_client() -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db() -> Generator[Session, None, None]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app), session_factory
    finally:
        app.dependency_overrides.clear()
        reset_database_state()
        engine.dispose()


@pytest.fixture(autouse=True)
def isolate_database_settings(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Keep tests from reading the developer .env or a live DATABASE_URL."""

    monkeypatch.setenv("DATABASE_URL", "")
    reset_settings_cache()
    reset_database_state()
    yield
    app.dependency_overrides.clear()
    reset_settings_cache()
    reset_database_state()
