"""Settings and database startup tests.

These tests do not open a connection to aadi_platform or the cropcare database.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import get_settings, reset_settings_cache
from app.database import (
    DatabaseUnavailable,
    assert_cropcare_migration_target,
    database_engine_created,
    database_name_from_url,
    get_db,
    get_engine,
)
from app.main import app


def test_health_starts_without_database_url() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert get_settings().database_url is None
    assert database_engine_created() is False


def test_database_url_name_is_cropcare(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://cropcare_user:local-only@localhost:5433/cropcare",
    )
    reset_settings_cache()

    url = get_settings().database_url
    assert url is not None
    assert database_name_from_url(url) == "cropcare"
    assert assert_cropcare_migration_target(url) == "cropcare"


def test_migrations_refuse_aadi_platform() -> None:
    url = "postgresql+psycopg://postgres:secret@localhost:5433/aadi_platform"
    with pytest.raises(DatabaseUnavailable, match="aadi_platform"):
        assert_cropcare_migration_target(url)


def test_migration_refusal_does_not_include_the_password() -> None:
    url = "postgresql+psycopg://postgres:secret-value@localhost:5433/aadi_platform"
    with pytest.raises(DatabaseUnavailable) as caught:
        assert_cropcare_migration_target(url)
    assert "secret-value" not in str(caught.value)


def test_ready_and_catalog_fail_when_database_url_is_missing() -> None:
    ready = TestClient(app).get("/health/ready")
    crops = TestClient(app).get("/api/v1/crops")

    assert ready.status_code == 503
    assert crops.status_code == 503
    assert ready.json() == {"detail": "Database is unavailable."}
    assert "postgresql" not in ready.text
    assert database_engine_created() is False


def test_ready_fails_for_an_unreachable_database(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://unused:unused@127.0.0.1:1/cropcare",
    )
    reset_settings_cache()

    response = TestClient(app).get("/health/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == "Database is unavailable."
    assert "unused" not in response.text


def test_engine_requires_database_url() -> None:
    with pytest.raises(DatabaseUnavailable, match="DATABASE_URL is not set"):
        get_engine()


def test_get_db_closes_the_session(monkeypatch: pytest.MonkeyPatch) -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine("sqlite://")
    factory = sessionmaker(bind=engine)
    closed: list[Session] = []
    original_close = Session.close

    def track_close(self: Session) -> None:
        closed.append(self)
        original_close(self)

    monkeypatch.setattr("app.database.get_session_factory", lambda: factory)
    monkeypatch.setattr(Session, "close", track_close)
    generator = get_db()
    session = next(generator)
    generator.close()
    engine.dispose()

    assert session in closed


def test_local_env_file_targets_cropcare_when_present() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        pytest.skip(".env is not present")

    url = ""
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("DATABASE_URL="):
            url = line.split("=", 1)[1].strip()
            break

    assert url
    assert database_name_from_url(url) == "cropcare"
    assert database_name_from_url(url) != "aadi_platform"
