import json
from pathlib import Path

import yaml

from cropcare_ml.config import load_experiment
from cropcare_ml.manifest import read_jsonl
from cropcare_ml.prepare import PrepareBlocked, main, prepare_dataset
from tests.support import lowered_experiment, write_pattern


def test_missing_data_root_writes_a_report_and_no_labels(tmp_path: Path):
    output = tmp_path / "out"
    code = main(
        [
            "--config",
            str(Path(__file__).resolve().parents[1] / "config" / "classes.plantvillage.yaml"),
            "--data-root",
            str(tmp_path / "missing"),
            "--output-dir",
            str(output),
        ]
    )
    assert code == 2
    report = json.loads((output / "preparation_report.json").read_text(encoding="utf-8"))
    assert report["status"] == "blocked"
    assert report["manifest_written"] is False
    assert report["data_root_exists"] is False
    assert "accuracy" not in report
    assert not (output / "labels.json").exists()
    assert not (output / "manifest.jsonl").exists()


def test_missing_healthy_class_blocks_even_when_a_disease_is_present(tmp_path: Path):
    config_path = lowered_experiment("classes.plantvillage.yaml", tmp_path / "classes.yaml")
    root = tmp_path / "raw"
    _three("tomato", root / "color" / "Tomato___healthy")
    _three("blight", root / "color" / "Tomato___Early_blight")
    output = tmp_path / "out"
    with pytest_blocked() as caught:
        prepare_dataset(load_experiment(config_path), root, output)
    assert caught.report["manifest_written"] is False
    assert "soybean_healthy" in caught.report["blocked_reason"]
    assert "tomato_early_blight" in caught.report["eligible_classes"]
    assert not (output / "labels.json").exists()


def test_prepare_splits_are_reproducible_and_do_not_leak_leaf_copies(tmp_path: Path):
    config_path = lowered_experiment("classes.plantvillage.yaml", tmp_path / "classes.yaml")
    root = tmp_path / "raw"
    write_pattern(root / "train" / "Soybean___healthy" / "set___leafA.png", "horizontal")
    write_pattern(root / "valid" / "Soybean___healthy" / "set___leafA copy.png", "wide")
    write_pattern(root / "train" / "Soybean___healthy" / "set___leafB.png", "checker")
    write_pattern(root / "train" / "Soybean___healthy" / "set___leafC.png", "bars")
    write_pattern(root / "grayscale" / "Soybean___healthy" / "set___leafA.png", "horizontal")
    _three("tomato", root / "color" / "Tomato___healthy")
    _three("blight", root / "color" / "Tomato___Early_blight")
    (root / "color" / "Tomato___Target_Spot").mkdir(parents=True)
    (root / "color" / "Tomato___Target_Spot" / "notes.jpg").write_text("not an image", encoding="utf-8")
    write_pattern(root / "color" / "Pepper,_bell___healthy" / "pepper.png", "checker")

    config = load_experiment(config_path)
    first = prepare_dataset(config, root, tmp_path / "out-a")
    second = prepare_dataset(config, root, tmp_path / "out-b")
    rows_a = read_jsonl(tmp_path / "out-a" / "manifest.jsonl")
    rows_b = read_jsonl(tmp_path / "out-b" / "manifest.jsonl")
    assert [(row["relative_path"], row["split"], row["group_id"]) for row in rows_a] == [
        (row["relative_path"], row["split"], row["group_id"]) for row in rows_b
    ]
    assert first["manifest_written"] is True
    assert "tomato_target_spot" not in first["included_classes"]
    assert any(item["code"] == "tomato_target_spot" and item["reason"] == "no_valid_images" for item in first["excluded_classes"])
    assert any("Pepper,_bell___healthy" in path for path in first["unmapped_directories"])
    assert all("grayscale" not in row["relative_path"] for row in rows_a)
    assert sum(row["class_code"] == "soybean_healthy" for row in rows_a) == 4

    leaf_a = [row for row in rows_a if "leafA" in row["relative_path"]]
    assert len(leaf_a) == 2
    assert len({row["group_id"] for row in leaf_a}) == 1
    assert len({row["split"] for row in leaf_a}) == 1
    for code in first["included_classes"]:
        splits = {row["split"] for row in rows_a if row["class_code"] == code}
        assert splits == {"train", "val", "test"}
        groups: dict[str, set[str]] = {}
        for row in rows_a:
            if row["class_code"] != code:
                continue
            groups.setdefault(row["group_id"], set()).add(row["split"])
        assert all(len(found) == 1 for found in groups.values())

    labels = json.loads((tmp_path / "out-a" / "labels.json").read_text(encoding="utf-8"))
    codes = [item["code"] for item in labels["labels"]]
    assert codes == sorted(codes)
    assert codes[0] == "soybean_healthy"
    assert "tomato_target_spot" not in codes
    preprocessing = json.loads((tmp_path / "out-a" / "preprocessing.json").read_text(encoding="utf-8"))
    assert preprocessing["exported_model"] is None
    assert preprocessing["input"]["height"] == 224


def test_plantdoc_folders_and_voc_source_stay_in_one_group(tmp_path: Path):
    config_path = lowered_experiment("classes.plantdoc.yaml", tmp_path / "classes.yaml")
    root = tmp_path / "raw"
    _three("soy", root / "train" / "Soyabean leaf")
    tomato = root / "train" / "Tomato leaf"
    write_pattern(tomato / "crop-a.png", "horizontal")
    write_pattern(tomato / "crop-b.png", "wide")
    write_pattern(tomato / "other.png", "checker")
    write_pattern(tomato / "third.png", "bars")
    for name in ("crop-a.png", "crop-b.png"):
        _xml(tomato / f"{Path(name).stem}.xml", "shared-photo.jpg")
    _three("blight", root / "train" / "Tomato Early blight leaf")
    output = tmp_path / "out"
    report = prepare_dataset(load_experiment(config_path), root, output)
    rows = read_jsonl(output / "manifest.jsonl")
    assert report["source"] == "plantdoc"
    assert {row["source"] for row in rows} == {"plantdoc"}
    crops = [row for row in rows if Path(row["relative_path"]).name in {"crop-a.png", "crop-b.png"}]
    assert len(crops) == 2
    assert len({row["group_id"] for row in crops}) == 1
    assert len({row["split"] for row in crops}) == 1
    assert all("Tomato___" not in row["relative_path"] for row in rows)


def test_sources_are_not_written_into_one_manifest(tmp_path: Path):
    plant_config = lowered_experiment("classes.plantvillage.yaml", tmp_path / "plant.yaml")
    doc_config = lowered_experiment("classes.plantdoc.yaml", tmp_path / "doc.yaml")
    plant_root = tmp_path / "plant"
    doc_root = tmp_path / "doc"
    _three("soy", plant_root / "Soybean___healthy")
    _three("tomato", plant_root / "Tomato___healthy")
    _three("soy", doc_root / "Soyabean leaf")
    _three("tomato", doc_root / "Tomato leaf")
    plant = prepare_dataset(load_experiment(plant_config), plant_root, tmp_path / "plant-out")
    doc = prepare_dataset(load_experiment(doc_config), doc_root, tmp_path / "doc-out")
    assert plant["source"] != doc["source"]
    plant_rows = read_jsonl(tmp_path / "plant-out" / "manifest.jsonl")
    doc_rows = read_jsonl(tmp_path / "doc-out" / "manifest.jsonl")
    assert {row["source"] for row in plant_rows} == {"plantvillage"}
    assert {row["source"] for row in doc_rows} == {"plantdoc"}


def _three(prefix: str, folder: Path) -> None:
    kinds = ("horizontal", "wide", "checker")
    for index, kind in enumerate(kinds):
        write_pattern(folder / f"{prefix}___leaf{index}.png", kind)


def _xml(path: Path, source_name: str) -> None:
    path.write_text(
        f"<annotation><filename>{source_name}</filename><object><name>Tomato leaf</name></object></annotation>",
        encoding="utf-8",
    )


class pytest_blocked:
    def __enter__(self):
        self.report = None
        return self

    def __exit__(self, exc_type, exc, traceback):
        if not isinstance(exc, PrepareBlocked):
            return False
        self.report = exc.report
        return True
