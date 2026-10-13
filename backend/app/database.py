"""Lazy SQLAlchemy engine and session factory.

The engine connects on first use. Catalog routes request a session, so those
calls need PostgreSQL. Importing the module does not open a connection.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

# Kept separate from any other application's alembic_version table.
ALEMBIC_VERSION_TABLE = "cropcare_alembic_version"
CROPCARE_DATABASE_NAME = "cropcare"

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


class DatabaseUnavailable(Exception):
    """PostgreSQL cannot be used. Messages must not include credentials."""


def database_name_from_url(url: str) -> str | None:
    """Return the database name from a SQLAlchemy URL."""

    try:
        return make_url(url).database
    except Exception as exc:
        raise DatabaseUnavailable("DATABASE_URL is not a valid database URL.") from exc


def assert_cropcare_migration_target(url: str) -> str:
    """Refuse to migrate any database other than the dedicated CropCare database."""

    name = database_name_from_url(url)
    if name == "aadi_platform":
        raise DatabaseUnavailable("Refusing to run CropCare migrations against aadi_platform.")
    if name != CROPCARE_DATABASE_NAME:
        raise DatabaseUnavailable("CropCare migrations must target the cropcare database.")
    return CROPCARE_DATABASE_NAME


def get_engine() -> Engine:
    """Return a cached engine, creating it on first use."""

    global _engine
    if _engine is None:
        database_url = get_settings().database_url
        if not database_url:
            raise DatabaseUnavailable(
                "DATABASE_URL is not set. Copy backend/.env.example to backend/.env "
                "and provide a PostgreSQL URL before using the database."
            )
        connect_args: dict[str, int] = {}
        if database_url.startswith("postgresql"):
            connect_args["connect_timeout"] = 5
        _engine = create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
    return _session_factory


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that opens a session only when a route requests it."""

    try:
        session = get_session_factory()()
    except DatabaseUnavailable:
        raise
    except Exception as exc:
        raise DatabaseUnavailable("Database is unavailable.") from exc
    try:
        yield session
    finally:
        session.close()


def database_engine_created() -> bool:
    """True only after a caller has asked for an engine."""

    return _engine is not None


def reset_database_state() -> None:
    """Drop cached engine state. Used by tests so they never keep a live pool."""

    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
