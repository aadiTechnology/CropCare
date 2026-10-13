"""Optional check that catalog routes query the dedicated cropcare database.

The test rolls back its transaction. It never connects to aadi_platform.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.database import database_name_from_url, get_db
from app.main import app
from app.models import Crop


def _cropcare_url() -> str | None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("DATABASE_URL="):
            url = line.split("=", 1)[1].strip()
            if database_name_from_url(url) == "cropcare":
                return url
            return None
    return None


def test_catalog_reads_postgresql_and_rolls_back() -> None:
    url = _cropcare_url()
    if url is None:
        pytest.skip("backend/.env does not target the cropcare database")

    engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 5})
    try:
        connection = engine.connect()
    except Exception as exc:
        engine.dispose()
        pytest.skip(f"cropcare database is not reachable: {exc.__class__.__name__}")

    transaction = connection.begin()
    session = Session(bind=connection, autoflush=False, autocommit=False)

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        session.add(Crop(code="postgres_probe", name_en="Probe", name_mr="तपास"))
        session.flush()

        response = TestClient(app).get("/api/v1/crops")
        assert response.status_code == 200
        assert any(crop["code"] == "postgres_probe" for crop in response.json()["crops"])
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        transaction.rollback()
        connection.close()

    with engine.connect() as check:
        remaining = check.execute(
            text("select count(*) from crops where code = 'postgres_probe'")
        ).scalar_one()
    engine.dispose()
    assert remaining == 0
