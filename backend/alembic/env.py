"""Alembic environment.

The database URL is read from the environment or backend/.env at migration
time. The placeholder in alembic.ini is never used.

Migrations refuse to run against aadi_platform. The version table is
cropcare_alembic_version so CropCare does not share another application's
alembic_version history.
"""

import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from app.database import ALEMBIC_VERSION_TABLE, assert_cropcare_migration_target
from app.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
BACKEND_ENV = Path(__file__).resolve().parents[1] / ".env"


def get_database_url() -> str:
    load_dotenv(BACKEND_ENV, override=False)
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Add it to the environment or backend/.env "
            "before running Alembic."
        )
    return url


def run_migrations_offline() -> None:
    url = get_database_url()
    assert_cropcare_migration_target(url)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table=ALEMBIC_VERSION_TABLE,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = get_database_url()
    assert_cropcare_migration_target(url)
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = url
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table=ALEMBIC_VERSION_TABLE,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
