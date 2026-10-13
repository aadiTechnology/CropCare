"""Interpreter checks that do not import TensorFlow."""

from __future__ import annotations

import importlib.util


def tensorflow_unavailable_reason() -> str | None:
    if importlib.util.find_spec("tensorflow") is None:
        return (
            "TensorFlow is not installed for this Python. "
            "From ml/, install requirements-train.txt with Python 3.12."
        )
    return None
