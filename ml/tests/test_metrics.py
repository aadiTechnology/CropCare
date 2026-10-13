import json

from cropcare_ml.evaluate import evaluate_predictions, main, write_distribution
from cropcare_ml.manifest import training_input_errors
from cropcare_ml.metrics import classification_report


def test_metrics_match_a_hand_counted_confusion_matrix():
    report = classification_report([0, 0, 1, 1, 2], [0, 1, 1, 1, 2], ["a", "b", "c"])
    assert report["accuracy"] == 0.8
    assert report["confusion_matrix"] == [[1, 1, 0], [0, 2, 0], [0, 0, 1]]
    by_code = {row["code"]: row for row in report["per_class"]}
    assert by_code["a"]["precision"] == 1
    assert by_code["a"]["recall"] == 0.5
    assert by_code["a"]["support"] == 2
    assert abs(by_code["a"]["f1"] - (2 / 3)) < 1e-12
    assert abs(by_code["b"]["precision"] - (2 / 3)) < 1e-12
    assert by_code["b"]["recall"] == 1
    assert by_code["b"]["f1"] == 0.8
    assert by_code["c"]["f1"] == 1
    expected_macro = ((2 / 3) + 0.8 + 1) / 3
    assert abs(report["macro_f1"] - expected_macro) < 1e-12


def test_distribution_file_has_counts_and_no_accuracy(tmp_path):
    rows = [
        {"split": "train", "class_code": "soybean_healthy", "source": "plantvillage"},
        {"split": "val", "class_code": "tomato_healthy", "source": "plantvillage"},
        {"split": "test", "class_code": "tomato_healthy", "source": "plantvillage"},
    ]
    payload = write_distribution(rows, tmp_path, "plantvillage_soybean_tomato", "plantvillage")
    assert "accuracy" not in payload
    assert "macro_f1" not in payload
    assert payload["generated_from"] == "manifest_counts"
    assert payload["class_distribution"]["train"] == {"soybean_healthy": 1}
    saved = json.loads((tmp_path / "class_distribution.json").read_text(encoding="utf-8"))
    assert saved == payload


def test_prediction_report_names_its_source():
    rows = [
        {"split": "test", "class_code": "a", "source": "plantvillage"},
        {"split": "test", "class_code": "a", "source": "plantvillage"},
    ]
    report = evaluate_predictions([0, 0], [0, 1], ["a", "b"], rows, "plantvillage", "demo")
    assert report["generated_from"] == "model_predictions"
    assert report["source"] == "plantvillage"
    assert report["accuracy"] == 0.5


def test_evaluate_distribution_only_command(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    labels = tmp_path / "labels.json"
    manifest.write_text(
        json.dumps(
            {
                "split": "train",
                "class_code": "soybean_healthy",
                "source": "plantvillage",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    labels.write_text(
        json.dumps(
            {
                "experiment": "plantvillage_soybean_tomato",
                "labels": [{"index": 0, "code": "soybean_healthy"}],
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "out"
    code = main(
        [
            "--manifest",
            str(manifest),
            "--labels",
            str(labels),
            "--output-dir",
            str(output),
            "--distribution-only",
        ]
    )
    assert code == 0
    saved = json.loads((output / "class_distribution.json").read_text(encoding="utf-8"))
    assert "accuracy" not in saved
    assert not (output / "metrics.json").exists()


def test_mixed_sources_and_leaked_groups_are_rejected():
    labels = [{"index": 0, "code": "soybean_healthy"}, {"index": 1, "code": "tomato_healthy"}]
    preprocessing = {"input": {"height": 224, "width": 224}, "backbone": "MobileNetV3Small"}
    rows = [
        _row("train", 0, "soybean_healthy", "g1", "plantvillage"),
        _row("val", 1, "tomato_healthy", "g2", "plantvillage"),
        _row("test", 1, "tomato_healthy", "g3", "plantdoc"),
    ]
    errors = training_input_errors(rows, labels, preprocessing, 224, allow_mixed_sources=False)
    assert any("more than one dataset source" in error for error in errors)

    leaked = [
        _row("train", 0, "soybean_healthy", "same", "plantvillage"),
        _row("val", 0, "soybean_healthy", "same", "plantvillage"),
        _row("test", 1, "tomato_healthy", "other", "plantvillage"),
    ]
    errors = training_input_errors(leaked, labels, preprocessing, 224, False)
    assert any("more than one split" in error for error in errors)


def _row(split: str, index: int, code: str, group_id: str, source: str) -> dict:
    return {
        "split": split,
        "class_index": index,
        "class_code": code,
        "source": source,
        "group_id": group_id,
        "relative_path": f"{split}-{code}-{group_id}.png",
    }
