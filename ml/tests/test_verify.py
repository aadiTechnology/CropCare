import json
from pathlib import Path

import pytest

from cropcare_ml.config import load_experiment, load_preprocessing_spec, ml_root
from cropcare_ml.manifest import read_jsonl
from cropcare_ml.metrics import classification_report, write_confusion_csv, write_json
from cropcare_ml.prepare import prepare_dataset
from cropcare_ml.verify import (
    VerifyError,
    assess_licence_text,
    layout_problems,
    main,
    stage_sprint3_bundle,
    summarize_class_folders,
    verify_preparation,
)
from tests.support import lowered_experiment, write_pattern


def test_layout_names_missing_tomato_folders_and_skips_grayscale(tmp_path: Path):
    config = load_experiment(ml_root() / "config" / "classes.plantvillage.tomato.yaml")
    root = tmp_path / "raw"
    write_pattern(root / "color" / "Tomato___healthy" / "leaf.png", "horizontal")
    write_pattern(root / "grayscale" / "Tomato___healthy" / "gray.png", "bars")
    write_pattern(root / "color" / "Pepper,_bell___healthy" / "pepper.png", "checker")
    summary = summarize_class_folders(root, config)
    problems = layout_problems(summary)
    healthy = next(row for row in summary["classes"] if row["code"] == "tomato_healthy")
    assert healthy["image_files"] == 1
    assert any(problem == "tomato_early_blight: no_directory" for problem in problems)
    assert all("tomato_healthy" not in problem for problem in problems)
    assert any("grayscale" in path for path in summary["skipped_variant_directories"])
    assert summary["unmapped_directory_count"] == 1
    assert main(
        [
            "layout",
            "--config",
            str(ml_root() / "config" / "classes.plantvillage.tomato.yaml"),
            "--data-root",
            str(root),
            "--require-complete",
        ]
    ) == 2


def test_complete_layout_accepts_one_folder_per_mapped_class(tmp_path: Path):
    config = load_experiment(ml_root() / "config" / "classes.plantvillage.tomato.yaml")
    root = tmp_path / "raw"
    for spec in config.classes:
        write_pattern(root / "color" / spec.folder_names[0] / "leaf.png", "horizontal")
    summary = summarize_class_folders(root, config)
    assert layout_problems(summary) == []
    assert sum(row["image_files"] for row in summary["classes"]) == 10


def test_licence_text_must_state_the_configured_plantvillage_licence():
    assert assess_licence_text("license: cc-by-sa-3.0\nPlantVillage Dataset", "CC BY-SA 3.0")["status"] == "matches"
    assert assess_licence_text("Attribution-ShareAlike 3.0\nPlantVillage", "CC BY-SA 3.0")["status"] == "matches"
    missing = assess_licence_text("CC0\nPlantVillage", "CC BY-SA 3.0")
    assert missing["status"] == "conflict"
    unrelated = assess_licence_text("CC BY-SA 3.0", "CC BY-SA 3.0")
    assert unrelated["status"] == "rejected"
    conflict = assess_licence_text("CC BY-SA 3.0 and CC0\nPlantVillage", "CC BY-SA 3.0")
    assert conflict["status"] == "conflict"


def test_licence_command_writes_a_match_and_rejects_a_conflict(tmp_path: Path):
    config = ml_root() / "config" / "classes.plantvillage.tomato.yaml"
    card = tmp_path / "card.md"
    card.write_text("license: cc-by-sa-3.0\n# PlantVillage Dataset\n", encoding="utf-8")
    output = tmp_path / "licence_check.json"
    assert main(["licence", "--config", str(config), "--text-file", str(card), "--output", str(output)]) == 0
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved["status"] == "matches"
    card.write_text("license: cc0\nPlantVillage\n", encoding="utf-8")
    assert main(["licence", "--config", str(config), "--text-file", str(card), "--output", str(output)]) == 2


def test_verify_preparation_checks_counts_licence_and_split_integrity(tmp_path: Path):
    config_path = lowered_experiment("classes.plantvillage.tomato.yaml", tmp_path / "classes.yaml")
    config = load_experiment(config_path)
    root = tmp_path / "raw"
    _three("healthy", root / "color" / "Tomato___healthy")
    write_pattern(root / "grayscale" / "Tomato___healthy" / "healthy___gray.png", "bars")
    output = tmp_path / "out"
    prepare_dataset(config, root, output)
    verified = verify_preparation(output, config)
    assert verified["status"] == "passed"
    assert verified["licence"]["name"] == "CC BY-SA 3.0"
    assert verified["class_count"] == 1
    assert verified["sample_count"] == 3
    assert set(verified["class_distribution"]) == {"train", "val", "test"}
    rows = read_jsonl(output / "manifest.jsonl")
    assert all("grayscale" not in row["relative_path"] for row in rows)
    assert len({row["split"] for row in rows}) == 3
    with pytest.raises(VerifyError, match="Configured classes were excluded"):
        verify_preparation(output, config, require_all_configured=True)
    assert not (output / "verification.json").exists()

    leaked = read_jsonl(output / "manifest.jsonl")
    leaked[0]["split"] = "test" if leaked[0]["split"] != "test" else "train"
    (output / "manifest.jsonl").write_text("".join(json.dumps(row) + "\n" for row in leaked), encoding="utf-8")
    with pytest.raises(VerifyError, match="split"):
        verify_preparation(output, config)


def test_bundle_copies_verified_files_and_leaves_images_behind(tmp_path: Path):
    prepared, run_dir, licence = _consistent_bundle(tmp_path)
    (run_dir / "leaf.jpg").write_bytes(b"image-bytes")
    destination = tmp_path / "bundle"
    stage_sprint3_bundle(run_dir, prepared, destination, licence)
    assert (destination / "model.tflite").read_bytes() == b"tflite"
    assert (destination / "labels.json").is_file()
    assert (destination / "preprocessing.json").is_file()
    assert (destination / "metrics.json").is_file()
    assert (destination / "confusion_matrix.csv").is_file()
    assert (destination / "smoke_test.json").is_file()
    assert (destination / "licence_check.json").is_file()
    assert (destination / "SPRINT3_README.txt").is_file()
    assert not (destination / "leaf.jpg").exists()
    readme = (destination / "SPRINT3_README.txt").read_text(encoding="utf-8")
    assert "model.tflite" in readme
    assert "labels.json" in readme
    assert "preprocessing.json" in readme
    assert "ml/artifacts/" in readme

    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    metrics["accuracy"] = 1
    write_json(run_dir / "metrics.json", metrics)
    with pytest.raises(VerifyError, match="accuracy"):
        stage_sprint3_bundle(run_dir, prepared, tmp_path / "other", licence)


def test_bundle_command_exits_when_the_smoke_file_claims_accuracy(tmp_path: Path):
    prepared, run_dir, licence = _consistent_bundle(tmp_path)
    smoke = json.loads((run_dir / "smoke_test.json").read_text(encoding="utf-8"))
    smoke["claims_accuracy"] = True
    write_json(run_dir / "smoke_test.json", smoke)
    assert main(
        [
            "bundle",
            "--run-dir",
            str(run_dir),
            "--prepared-dir",
            str(prepared),
            "--destination",
            str(tmp_path / "bundle"),
            "--licence-check",
            str(licence),
        ]
    ) == 2
    assert not (tmp_path / "bundle").exists()


def _three(prefix: str, folder: Path) -> None:
    for index, kind in enumerate(("horizontal", "wide", "checker")):
        write_pattern(folder / f"{prefix}___leaf{index}.png", kind)


def _consistent_bundle(tmp_path: Path) -> tuple[Path, Path, Path]:
    codes = ["tomato_early_blight", "tomato_healthy"]
    report = classification_report([0, 0, 1, 1], [0, 1, 1, 1], codes)
    distribution = {
        "train": {"tomato_early_blight": 2, "tomato_healthy": 2},
        "val": {"tomato_early_blight": 1, "tomato_healthy": 1},
        "test": {"tomato_early_blight": 2, "tomato_healthy": 2},
    }
    licence = {
        "name": "CC BY-SA 3.0",
        "citation": "Hughes and Salathé, arXiv:1511.08060 (2015)",
        "url": "https://arxiv.org/abs/1511.08060",
    }
    report.update(
        {
            "experiment": "plantvillage_tomato",
            "source": "plantvillage",
            "class_distribution": distribution,
            "generated_from": "model_predictions",
        }
    )
    prepared = tmp_path / "prepared"
    prepared.mkdir()
    write_json(
        prepared / "preparation_report.json",
        {
            "status": "ready",
            "manifest_written": True,
            "experiment": "plantvillage_tomato",
            "source": "plantvillage",
            "licence": licence,
            "class_distribution": distribution,
        },
    )
    write_json(prepared / "class_distribution.json", distribution)
    write_json(
        prepared / "verification.json",
        {"status": "passed", "licence": licence, "class_distribution": distribution},
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    write_json(run_dir / "metrics.json", report)
    write_confusion_csv(run_dir / "confusion_matrix.csv", codes, report["confusion_matrix"])
    (run_dir / "model.tflite").write_bytes(b"tflite")
    (run_dir / "model.keras").write_bytes(b"keras")
    write_json(
        run_dir / "labels.json",
        {
            "schema_version": 1,
            "experiment": "plantvillage_tomato",
            "source": "plantvillage",
            "model_output": "softmax",
            "labels": [
                {
                    "index": 0,
                    "code": "tomato_early_blight",
                    "crop": "tomato",
                    "role": "disease",
                    "dataset_label": "Tomato___Early_blight",
                },
                {
                    "index": 1,
                    "code": "tomato_healthy",
                    "crop": "tomato",
                    "role": "healthy",
                    "dataset_label": "Tomato___healthy",
                },
            ],
        },
    )
    preprocessing = load_preprocessing_spec()
    preprocessing["exported_model"] = "model.tflite"
    preprocessing["quantization"] = "none"
    write_json(run_dir / "preprocessing.json", preprocessing)
    write_json(
        run_dir / "export_record.json",
        {
            "schema_version": 1,
            "format": "tflite",
            "quantization": "none",
            "model_file": "model.tflite",
            "label_file": "labels.json",
            "preprocessing_file": "preprocessing.json",
        },
    )
    write_json(
        run_dir / "smoke_test.json",
        {
            "schema_version": 1,
            "status": "passed",
            "claims_accuracy": False,
            "output_length": 2,
            "predicted_index": 1,
            "predicted_code": "tomato_healthy",
        },
    )
    write_json(run_dir / "history.json", {"loss": [1.0], "accuracy": [0.25]})
    write_json(
        run_dir / "train_config.json",
        {"experiment": "plantvillage_tomato", "backbone": "MobileNetV3Small", "allow_mixed_sources": False},
    )
    licence_path = tmp_path / "licence_check.json"
    write_json(licence_path, {"status": "matches", "expected": "CC BY-SA 3.0", "problems": []})
    return prepared, run_dir, licence_path
