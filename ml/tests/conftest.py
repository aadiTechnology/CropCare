from __future__ import annotations

from pathlib import Path

import pytest

from cropcare_ml.config import ml_root


@pytest.fixture
def ml_dir() -> Path:
    return ml_root()
