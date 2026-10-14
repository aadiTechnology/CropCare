import importlib.util
from pathlib import Path

import pytest

from cropcare_ml.smoke import main
from tests.support import write_pattern


def test_smoke_refuses_a_missing_model(tmp_path: Path):
    image = tmp_path / "leaf.png"
    write_pattern(image, "horizontal")
    code = main(
        [
            "--model",
            str(tmp_path / "missing.tflite"),
            "--labels",
            str(tmp_path / "labels.json"),
            "--preprocessing",
            str(tmp_path / "preprocessing.json"),
            "--image",
            str(image),
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )
    assert code == 2
    assert not (tmp_path / "out" / "smoke_test.json").exists()


def test_smoke_stops_when_tensorflow_is_not_installed(tmp_path: Path):
    if importlib.util.find_spec("tensorflow") is not None:
        pytest.skip("TensorFlow is installed, so this guard does not apply.")
    image = tmp_path / "leaf.png"
    write_pattern(image, "horizontal")
    (tmp_path / "model.tflite").write_bytes(b"not-a-model")
    (tmp_path / "labels.json").write_text('{"labels": []}', encoding="utf-8")
    (tmp_path / "preprocessing.json").write_text("{}", encoding="utf-8")
    code = main(
        [
            "--model",
            str(tmp_path / "model.tflite"),
            "--labels",
            str(tmp_path / "labels.json"),
            "--preprocessing",
            str(tmp_path / "preprocessing.json"),
            "--image",
            str(image),
            "--output-dir",
            str(tmp_path),
        ]
    )
    assert code == 2
    assert not (tmp_path / "smoke_test.json").exists()
