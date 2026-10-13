"""Schema checks that do not connect to PostgreSQL."""

import importlib.util
from pathlib import Path

from app.models import Base


def test_metadata_contains_the_sprint_tables() -> None:
    assert set(Base.metadata.tables) == {
        "crops",
        "diseases",
        "remedies",
        "diagnosis_history",
    }
    image_reference = Base.metadata.tables["diagnosis_history"].columns["image_reference"]
    assert str(image_reference.type) == "VARCHAR(512)"


def test_initial_migration_can_be_reversed() -> None:
    path = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "0001_initial_schema.py"
    spec = importlib.util.spec_from_file_location("initial_schema", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.revision == "0001_initial_schema"
    assert module.down_revision is None
    assert callable(module.upgrade)
    assert callable(module.downgrade)
