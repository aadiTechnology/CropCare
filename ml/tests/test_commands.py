import importlib.util
import json
from pathlib import Path

import pytest
import yaml

from cropcare_ml.config import load_train_config, ml_root
from cropcare_ml.export_model import main as export_main
from cropcare_ml.train import main as train_main
from cropcare_ml.train import train


def test_train_refuses_a_missing_manifest(tmp_path: Path):
    config = _train_config(tmp_path, tmp_path / "missing")
    with pytest.raises(FileNotFoundError):
        train(config)
    assert train_main(["--config", str(tmp_path / "train.yaml")]) == 2
    assert not list(tmp_path.rglob("metrics.json"))


def test_train_refuses_mixed_sources_before_writing_metrics(tmp_path: Path):
    prepared = _prepared(tmp_path, mixed=True)
    config = _train_config(tmp_path, prepared)
    with pytest.raises(ValueError, match="more than one dataset source"):
        train(config)
    assert not list(tmp_path.rglob("metrics.json"))
    assert not list(tmp_path.rglob("*.tflite"))


def test_train_stops_when_tensorflow_is_not_installed(tmp_path: Path):
    if importlib.util.find_spec("tensorflow") is not None:
        pytest.skip("TensorFlow is installed, so this guard does not apply.")
    prepared = _prepared(tmp_path, mixed=False)
    config = _train_config(tmp_path, prepared)
    with pytest.raises(RuntimeError, match="TensorFlow is not installed"):
        train(config)
    assert not list(tmp_path.rglob("metrics.json"))
    assert not list(tmp_path.rglob("model.keras"))
    assert not list(tmp_path.rglob("*.tflite"))


def test_export_refuses_a_missing_model(tmp_path: Path):
    code = export_main(
        [
            "--model",
            str(tmp_path / "missing.keras"),
            "--labels",
            str(tmp_path / "labels.json"),
            "--preprocessing",
            str(ml_root() / "config" / "preprocessing.json"),
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )
    assert code == 2
    assert not list(tmp_path.rglob("*.tflite"))


def _train_config(tmp_path: Path, prepared: Path):
    data = yaml.safe_load((ml_root() / "config" / "train.yaml").read_text(encoding="utf-8"))
    data["prepared_dir"] = prepared.as_posix()
    data["output_dir"] = (tmp_path / "runs").as_posix()
    path = tmp_path / "train.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return load_train_config(path)


def _prepared(tmp_path: Path, mixed: bool) -> Path:
    prepared = tmp_path / "prepared"
    prepared.mkdir()
    sources = ["plantvillage", "plantdoc", "plantvillage"] if mixed else ["plantvillage"] * 3
    rows = []
    labels = [
        {"index": 0, "code": "soybean_healthy", "crop": "soybean", "role": "healthy", "dataset_label": "Soybean___healthy"},
        {"index": 1, "code": "tomato_healthy", "crop": "tomato", "role": "healthy", "dataset_label": "Tomato___healthy"},
    ]
    specs = [
        ("train", 0, "soybean_healthy"),
        ("val", 1, "tomato_healthy"),
        ("test", 1, "tomato_healthy"),
    ]
    for (split, index, code), source in zip(specs, sources, strict=True):
        rows.append(
            {
                "split": split,
                "class_index": index,
                "class_code": code,
                "crop": "soybean" if code.startswith("soybean") else "tomato",
                "role": "healthy",
                "dataset_label": code,
                "source": source,
                "group_id": f"g-{split}",
                "leaf_key": split,
                "sha256": split,
                "phash": "0",
                "width": 64,
                "height": 64,
                "path": str(tmp_path / f"{split}.png"),
                "relative_path": f"{split}.png",
            }
        )
    (prepared / "manifest.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )
    (prepared / "labels.json").write_text(
        json.dumps({"experiment": "plantvillage_soybean_tomato", "source": "plantvillage", "labels": labels}),
        encoding="utf-8",
    )
    (prepared / "preprocessing.json").write_text(
        (ml_root() / "config" / "preprocessing.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return prepared
