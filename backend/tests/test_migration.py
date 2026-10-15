"""Alembic checks against an isolated SQLite file.

These tests do not open the cropcare or aadi_platform PostgreSQL databases.
"""

import importlib.util
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from app.database import DatabaseUnavailable, database_name_from_url
from app.models import EXPERT_PROVENANCE_CHECK, VERIFICATION_STATUS_CHECK

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _migration_module():
    path = BACKEND_DIR / "alembic" / "versions" / "0002_knowledge_provenance.py"
    spec = importlib.util.spec_from_file_location("knowledge_provenance", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _alembic_config() -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("path_separator", "os")
    config.set_main_option("prepend_sys_path", str(BACKEND_DIR))
    return config


def test_provenance_migration_matches_model_checks_and_revises_initial_schema() -> None:
    module = _migration_module()
    assert module.revision == "0002_knowledge_provenance"
    assert module.down_revision == "0001_initial_schema"
    assert module.VERIFICATION_STATUS_CHECK == VERIFICATION_STATUS_CHECK
    assert module.EXPERT_PROVENANCE_CHECK == EXPERT_PROVENANCE_CHECK
    assert callable(module.upgrade)
    assert callable(module.downgrade)


def test_alembic_refuses_aadi_platform_online_and_offline(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:secret-value@127.0.0.1:1/aadi_platform",
    )
    config = _alembic_config()

    with pytest.raises(DatabaseUnavailable, match="aadi_platform"):
        command.upgrade(config, "head")
    with pytest.raises(DatabaseUnavailable, match="aadi_platform"):
        command.upgrade(config, "head", sql=True)

    captured = capsys.readouterr()
    assert "secret-value" not in captured.out
    assert "secret-value" not in captured.err


def test_upgrade_and_downgrade_use_an_isolated_sqlite_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///cropcare")
    assert database_name_from_url("sqlite:///cropcare") == "cropcare"

    config = _alembic_config()
    command.upgrade(config, "head")

    engine = create_engine("sqlite:///cropcare")
    crop_id = uuid.uuid4().hex
    disease_id = uuid.uuid4().hex
    with engine.begin() as connection:
        tables = set(inspect(connection).get_table_names())
        assert {"crops", "diseases", "remedies", "diagnosis_history", "cropcare_alembic_version"} <= tables
        disease_columns = {column["name"] for column in inspect(connection).get_columns("diseases")}
        remedy_columns = {column["name"] for column in inspect(connection).get_columns("remedies")}
        assert {"source", "verified_by", "verified_at"} <= disease_columns
        assert "source" in remedy_columns
        version = connection.execute(text("SELECT version_num FROM cropcare_alembic_version")).scalar_one()
        assert version == "0002_knowledge_provenance"
        connection.execute(
            text(
                "INSERT INTO crops (id, code, name_en, name_mr, created_at) "
                "VALUES (:id, 'tomato', 'Stored crop', 'साठवलेले पीक', CURRENT_TIMESTAMP)"
            ),
            {"id": crop_id},
        )
        connection.execute(
            text(
                "INSERT INTO diseases ("
                "id, crop_id, code, name_en, name_mr, verification_status, created_at"
                ") VALUES ("
                ":id, :crop_id, 'tomato_healthy', 'Stored disease', 'साठवलेला रोग', 'sample', CURRENT_TIMESTAMP"
                ")"
            ),
            {"id": disease_id, "crop_id": crop_id},
        )

    with engine.begin() as connection:
        with pytest.raises(IntegrityError):
            connection.execute(
                text(
                    "INSERT INTO diseases ("
                    "id, crop_id, code, name_en, name_mr, verification_status, source, verified_by, verified_at, created_at"
                    ") VALUES ("
                    ":id, :crop_id, 'tomato_early_blight', 'Stored disease', 'साठवलेला रोग', "
                    "'expert_verified', NULL, NULL, NULL, CURRENT_TIMESTAMP)"
                ),
                {"id": uuid.uuid4().hex, "crop_id": crop_id},
            )

    command.downgrade(config, "0001_initial_schema")
    with engine.connect() as connection:
        columns = {column["name"] for column in inspect(connection).get_columns("diseases")}
        assert "source" not in columns
        assert "verified_by" not in columns
        remaining = connection.execute(
            text("SELECT code FROM diseases WHERE id = :id"),
            {"id": disease_id},
        ).scalar_one()
        assert remaining == "tomato_healthy"
        version = connection.execute(text("SELECT version_num FROM cropcare_alembic_version")).scalar_one()
        assert version == "0001_initial_schema"

    command.downgrade(config, "base")
    with engine.connect() as connection:
        assert "crops" not in inspect(connection).get_table_names()

    command.upgrade(config, "head")
    with engine.connect() as connection:
        columns = {column["name"] for column in inspect(connection).get_columns("diseases")}
        assert {"source", "verified_by", "verified_at"} <= columns
    engine.dispose()
