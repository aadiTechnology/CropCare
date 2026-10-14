"""Check dataset layout, licence text, split integrity, and run artifacts.

The checks read files the existing preparer and trainer already wrote.
They do not download images, train a model, or invent accuracy.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
from pathlib import Path

from cropcare_ml.config import ExperimentConfig, load_experiment, normalize_name
from cropcare_ml.discover import SKIP_DIRS, VARIANT_DIRS, _skip_variant
from cropcare_ml.images import is_image_path
from cropcare_ml.manifest import read_jsonl, read_labels, training_input_errors
from cropcare_ml.metrics import class_distribution, classification_report, write_json


class VerifyError(Exception):
    """Raised when a preparation or a training bundle fails a check."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("\n".join(problems))


REQUIRED_RUN_FILES = (
    "model.tflite",
    "model.keras",
    "labels.json",
    "preprocessing.json",
    "metrics.json",
    "confusion_matrix.csv",
    "export_record.json",
    "smoke_test.json",
    "history.json",
    "train_config.json",
)

PREPARED_BUNDLE_FILES = (
    "preparation_report.json",
    "class_distribution.json",
    "verification.json",
)

OPTIONAL_RUN_FILES = ("environment.json",)

SPRINT3_BUNDLE_TEXT = """CropCare AI Sprint 3 local artifacts
Experiment: plantvillage_tomato

Copy this folder to ml/artifacts/runs/plantvillage_tomato_colab/ on the development machine.
ml/artifacts/ is gitignored. Leave this folder and the PlantVillage images uncommitted.

Sprint 3 reads three files from that folder:
- model.tflite
- labels.json, where output index i is labels[i].code
- preprocessing.json

metrics.json and confusion_matrix.csv are the test-set report written by cropcare_ml.train.
Keep those files beside the model. smoke_test.json records one load of model.tflite.
The test-set scores stay in metrics.json.

preprocessing.json resizes outside the model to 224 by 224 RGB float32 pixels in the range 0-255.
MobileNetV3Small scaling runs inside the exported graph.
"""


def _normalize_licence_text(text: str) -> str:
    lowered = text.casefold().replace("_", " ").replace("-", " ")
    return " ".join(lowered.split())


def assess_licence_text(text: str, licence_name: str) -> dict:
    """Compare a dataset card with the licence named in the experiment config."""
    normalized = _normalize_licence_text(text)
    problems: list[str] = []
    if "cc0" in normalized or "public domain" in normalized:
        problems.append("The licence text also describes a public-domain release.")
    expected = _normalize_licence_text(licence_name)
    sharealike = expected in normalized or "attribution sharealike 3.0" in normalized
    if not sharealike:
        problems.append(f"The licence text does not state {licence_name}.")
    if "plantvillage" not in normalized:
        problems.append("The licence text does not name PlantVillage.")
    if any("public-domain" in problem for problem in problems):
        status = "conflict"
    elif problems:
        status = "rejected"
    else:
        status = "matches"
    return {
        "schema_version": 1,
        "status": status,
        "expected": licence_name,
        "problems": problems,
    }


def summarize_class_folders(data_root: Path, config: ExperimentConfig) -> dict:
    """Count image files in mapped class folders without decoding them."""
    data_root = data_root.resolve()
    aliases = config.alias_map()
    classes = [
        {
            "code": spec.code,
            "folder_names": list(spec.folder_names),
            "directories": [],
            "image_files": 0,
        }
        for spec in config.classes
    ]
    by_code = {row["code"]: row for row in classes}
    skipped: list[str] = []
    unmapped: list[str] = []
    if data_root.exists():
        for dirpath, dirnames, filenames in os.walk(data_root, followlinks=False):
            current = Path(dirpath)
            kept: list[str] = []
            for name in dirnames:
                if name in SKIP_DIRS:
                    continue
                if _skip_variant(name, config.image_variant):
                    skipped.append(str(current / name))
                    continue
                kept.append(name)
            dirnames[:] = kept
            spec = aliases.get(normalize_name(current.name))
            image_names = [name for name in filenames if is_image_path(current / name)]
            if spec is None:
                if image_names:
                    unmapped.append(str(current))
                continue
            dirnames[:] = []
            record = by_code[spec.code]
            record["directories"].append(str(current))
            record["image_files"] += len(image_names)
    return {
        "schema_version": 1,
        "data_root": str(data_root),
        "data_root_exists": data_root.exists(),
        "image_variant": config.image_variant,
        "classes": classes,
        "skipped_variant_directories": skipped,
        "unmapped_directories_with_images": unmapped[:20],
        "unmapped_directory_count": len(unmapped),
    }


def layout_problems(summary: dict) -> list[str]:
    problems: list[str] = []
    if not summary["data_root_exists"]:
        problems.append(f"Data root does not exist: {summary['data_root']}")
        return problems
    for row in summary["classes"]:
        if not row["directories"]:
            problems.append(f"{row['code']}: no_directory")
        elif row["image_files"] == 0:
            problems.append(f"{row['code']}: no_image_files")
        elif len(row["directories"]) > 1:
            problems.append(
                f"{row['code']} matched {len(row['directories'])} directories. "
                "Point the data root at one dataset copy."
            )
    return problems


def verify_preparation(
    prepared_dir: Path,
    config: ExperimentConfig,
    *,
    require_all_configured: bool = False,
) -> dict:
    """Check the manifest, licence record, class counts, and split integrity."""
    prepared_dir = prepared_dir.resolve()
    problems: list[str] = []
    required = (
        "manifest.jsonl",
        "labels.json",
        "class_distribution.json",
        "preprocessing.json",
        "preparation_report.json",
    )
    for name in required:
        if not (prepared_dir / name).is_file():
            problems.append(f"Missing {name}.")
    if problems:
        _drop_verification(prepared_dir)
        raise VerifyError(problems)

    report = json.loads((prepared_dir / "preparation_report.json").read_text(encoding="utf-8"))
    rows = read_jsonl(prepared_dir / "manifest.jsonl")
    labels = read_labels(prepared_dir / "labels.json")
    preprocessing = json.loads((prepared_dir / "preprocessing.json").read_text(encoding="utf-8"))
    saved_distribution = json.loads((prepared_dir / "class_distribution.json").read_text(encoding="utf-8"))
    computed = class_distribution(rows)

    if report.get("status") != "ready" or report.get("manifest_written") is not True:
        problems.append("preparation_report.json is not a completed preparation.")
    if report.get("experiment") != config.experiment or report.get("source") != config.source:
        problems.append("Preparation report experiment or source does not match the config.")
    if report.get("image_variant") != config.image_variant:
        problems.append("Preparation report image variant does not match the config.")
    if report.get("seed") != config.seed:
        problems.append("Preparation report seed does not match the config.")
    licence = report.get("licence") or {}
    if (
        licence.get("name") != config.licence_name
        or licence.get("citation") != config.licence_citation
        or licence.get("url") != config.licence_url
    ):
        problems.append("Preparation report licence does not match the experiment config.")
    if preprocessing["input"]["height"] != 224 or preprocessing["input"]["width"] != 224:
        problems.append("Preprocessing input must be 224 by 224.")
    if report.get("sample_count") != len(rows):
        problems.append("sample_count does not match the manifest.")
    if saved_distribution != computed or report.get("class_distribution") != computed:
        problems.append("Class counts do not match the manifest.")

    included = list(report.get("included_classes") or [])
    configured = [spec.code for spec in config.classes]
    if require_all_configured and set(included) != set(configured):
        missing = [code for code in configured if code not in set(included)]
        problems.append("Configured classes were excluded: " + ", ".join(missing))
    for code in config.require_classes:
        if code not in included:
            problems.append(f"Required class {code} is not in the manifest.")

    problems.extend(
        training_input_errors(
            rows,
            labels,
            preprocessing,
            preprocessing["input"]["height"],
            allow_mixed_sources=False,
        )
    )
    expected_crop = {spec.code: spec.crop for spec in config.classes}
    aliases = config.alias_map()
    skipped_names = {name for name in VARIANT_DIRS if name != config.image_variant}
    hashes: dict[str, set[str]] = {}
    for row in rows:
        hashes.setdefault(row["sha256"], set()).add(row["split"])
        if row.get("source") != config.source:
            problems.append(f"{row['relative_path']} has source {row.get('source')}.")
            break
        if row.get("crop") != expected_crop.get(row["class_code"]):
            problems.append(f"{row['relative_path']} crop does not match the class map.")
            break
        parts = row["relative_path"].split("/")
        if any(part.casefold() in skipped_names for part in parts):
            problems.append(f"{row['relative_path']} is in a skipped image variant.")
            break
        matched = [aliases[normalize_name(part)].code for part in parts if normalize_name(part) in aliases]
        if not matched or matched[-1] != row["class_code"]:
            problems.append(f"{row['relative_path']} is outside the folder mapped for {row['class_code']}.")
            break
    leaked_hashes = [digest for digest, splits in hashes.items() if len(splits) > 1]
    if leaked_hashes:
        problems.append(f"{len(leaked_hashes)} file hashes appear in more than one split.")
    for code in sorted({row["class_code"] for row in rows}):
        splits = {row["split"] for row in rows if row["class_code"] == code}
        if splits != {"train", "val", "test"}:
            problems.append(f"{code} is missing a split: found {sorted(splits)}.")
    missing_files = [row["path"] for row in rows if not Path(row["path"]).is_file()]
    if missing_files:
        problems.append(f"{len(missing_files)} manifest paths are missing on disk. First: {missing_files[0]}")

    if problems:
        _drop_verification(prepared_dir)
        raise VerifyError(problems)

    payload = {
        "schema_version": 1,
        "status": "passed",
        "experiment": config.experiment,
        "source": config.source,
        "sample_count": len(rows),
        "class_count": len(labels),
        "class_distribution": computed,
        "licence": licence,
        "split_integrity": {
            "groups_in_one_split": True,
            "hashes_in_one_split": True,
            "every_class_has_train_val_test": True,
        },
        "problems": [],
    }
    write_json(prepared_dir / "verification.json", payload)
    return payload


def run_artifact_problems(run_dir: Path) -> list[str]:
    """Return problems when a finished run does not agree with its own matrix."""
    problems: list[str] = []
    for name in REQUIRED_RUN_FILES:
        if not (run_dir / name).is_file():
            problems.append(f"Missing {name}.")
    if problems:
        return problems

    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    labels_payload = json.loads((run_dir / "labels.json").read_text(encoding="utf-8"))
    labels = read_labels(run_dir / "labels.json")
    preprocessing = json.loads((run_dir / "preprocessing.json").read_text(encoding="utf-8"))
    smoke = json.loads((run_dir / "smoke_test.json").read_text(encoding="utf-8"))
    export_record = json.loads((run_dir / "export_record.json").read_text(encoding="utf-8"))
    history = json.loads((run_dir / "history.json").read_text(encoding="utf-8"))
    train_config = json.loads((run_dir / "train_config.json").read_text(encoding="utf-8"))
    codes = [item["code"] for item in labels]

    if not isinstance(history, dict):
        problems.append("history.json must be a JSON object.")
    if train_config.get("backbone") != "MobileNetV3Small":
        problems.append("train_config.json backbone must be MobileNetV3Small.")
    if train_config.get("allow_mixed_sources") is not False:
        problems.append("train_config.json must keep allow_mixed_sources false.")
    if metrics.get("generated_from") != "model_predictions":
        problems.append("metrics.json was not written from model predictions.")
    if metrics.get("split") != "test":
        problems.append("metrics.json is not a test-split report.")
    if metrics.get("experiment") != train_config.get("experiment"):
        problems.append("metrics.json experiment does not match train_config.json.")
    if metrics.get("label_codes") != codes:
        problems.append("metrics label_codes do not match labels.json.")
    if labels_payload.get("model_output") != "softmax":
        problems.append("labels.json model_output must be softmax.")

    matrix = metrics.get("confusion_matrix")
    per_class = metrics.get("per_class")
    if not isinstance(matrix, list) or not matrix or any(not isinstance(row, list) or len(row) != len(matrix) for row in matrix):
        problems.append("confusion matrix is missing or not square.")
        return problems
    if len(matrix) != len(codes) or not isinstance(per_class, list):
        problems.append("confusion matrix size does not match the label file.")
        return problems

    y_true: list[int] = []
    y_pred: list[int] = []
    for truth, row in enumerate(matrix):
        for prediction, count in enumerate(row):
            if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                problems.append("confusion matrix contains a negative or non-integer count.")
                return problems
            y_true.extend([truth] * count)
            y_pred.extend([prediction] * count)
    if not y_true:
        problems.append("confusion matrix is empty.")
        return problems

    recomputed = classification_report(y_true, y_pred, codes)
    if abs(float(metrics.get("accuracy", -1)) - recomputed["accuracy"]) > 1e-9:
        problems.append("Stored accuracy does not match the confusion matrix.")
    if abs(float(metrics.get("macro_f1", -1)) - recomputed["macro_f1"]) > 1e-9:
        problems.append("Stored macro-F1 does not match the confusion matrix.")
    stored = {row.get("code"): row for row in per_class}
    for row in recomputed["per_class"]:
        other = stored.get(row["code"])
        if not isinstance(other, dict):
            problems.append(f"per_class is missing {row['code']}.")
            continue
        for key in ("precision", "recall", "f1", "support"):
            if key not in other or abs(float(other[key]) - float(row[key])) > 1e-9:
                problems.append(f"{row['code']} {key} does not match the confusion matrix.")
                break

    with (run_dir / "confusion_matrix.csv").open("r", encoding="utf-8", newline="") as handle:
        table = list(csv.reader(handle))
    if not table or table[0] != ["true_class", *codes]:
        problems.append("confusion_matrix.csv header does not match labels.json.")
    elif len(table) != len(matrix) + 1:
        problems.append("confusion_matrix.csv row count does not match the matrix.")
    else:
        for code, csv_row, matrix_row in zip(codes, table[1:], matrix, strict=True):
            try:
                parsed = [int(value) for value in csv_row[1:]]
            except ValueError:
                parsed = []
            if csv_row[0] != code or parsed != matrix_row:
                problems.append("confusion_matrix.csv does not match metrics.json.")
                break

    if preprocessing.get("exported_model") != "model.tflite":
        problems.append("preprocessing.json exported_model must be model.tflite.")
    if preprocessing.get("quantization") != "none":
        problems.append("preprocessing.json quantization must be none.")
    if preprocessing.get("backbone") != "MobileNetV3Small":
        problems.append("preprocessing.json backbone must be MobileNetV3Small.")
    if preprocessing.get("internal_scaling", {}).get("formula") != "pixel / 127.5 - 1.0":
        problems.append("preprocessing.json scaling formula does not match the training pipeline.")
    if smoke.get("status") != "passed" or smoke.get("claims_accuracy") is not False:
        problems.append("smoke_test.json must record a passed load check and must not claim accuracy.")
    if smoke.get("output_length") != len(codes):
        problems.append("smoke_test.json output_length does not match labels.json.")
    predicted_index = smoke.get("predicted_index")
    if isinstance(predicted_index, bool) or not isinstance(predicted_index, int) or not 0 <= predicted_index < len(codes):
        problems.append("smoke_test.json predicted_index is outside the label file.")
    elif smoke.get("predicted_code") != codes[predicted_index]:
        problems.append("smoke_test.json predicted_code does not match predicted_index.")
    if export_record.get("format") != "tflite" or export_record.get("model_file") != "model.tflite":
        problems.append("export_record.json must name model.tflite.")
    if export_record.get("quantization") != "none":
        problems.append("export_record.json quantization must be none.")
    if export_record.get("label_file") != "labels.json" or export_record.get("preprocessing_file") != "preprocessing.json":
        problems.append("export_record.json must name labels.json and preprocessing.json.")
    return problems


def stage_sprint3_bundle(
    run_dir: Path,
    prepared_dir: Path,
    destination: Path,
    licence_check: Path | None = None,
) -> Path:
    """Copy the verified run files into a folder that can be downloaded.

    The copy includes the model and the metric files. It leaves the dataset behind.
    """
    problems = run_artifact_problems(run_dir)
    for name in PREPARED_BUNDLE_FILES:
        if not (prepared_dir / name).is_file():
            problems.append(f"Prepared directory is missing {name}.")
    if licence_check is not None and not licence_check.is_file():
        problems.append(f"Licence check file is missing: {licence_check}")
    if problems:
        raise VerifyError(problems)

    report = json.loads((prepared_dir / "preparation_report.json").read_text(encoding="utf-8"))
    verification = json.loads((prepared_dir / "verification.json").read_text(encoding="utf-8"))
    distribution = json.loads((prepared_dir / "class_distribution.json").read_text(encoding="utf-8"))
    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    if report.get("status") != "ready" or report.get("manifest_written") is not True:
        problems.append("preparation_report.json is not a completed preparation.")
    if verification.get("status") != "passed":
        problems.append("verification.json status must be passed.")
    if verification.get("licence") != report.get("licence"):
        problems.append("verification.json licence does not match the preparation report.")
    if verification.get("class_distribution") != distribution or report.get("class_distribution") != distribution:
        problems.append("Class-count files do not match inside the prepared directory.")
    if metrics.get("class_distribution") != distribution:
        problems.append("metrics.json class counts do not match class_distribution.json.")
    if metrics.get("experiment") != report.get("experiment") or metrics.get("source") != report.get("source"):
        problems.append("metrics.json experiment does not match the preparation report.")
    if licence_check is not None:
        licence_payload = json.loads(licence_check.read_text(encoding="utf-8"))
        if licence_payload.get("status") != "matches":
            problems.append("licence_check.json status must be matches.")
        if licence_payload.get("expected") != (report.get("licence") or {}).get("name"):
            problems.append("licence_check.json does not name the preparation licence.")
    if problems:
        raise VerifyError(problems)
    if destination.exists():
        raise VerifyError([f"Bundle destination already exists: {destination}"])

    destination.mkdir(parents=True)
    try:
        for name in REQUIRED_RUN_FILES:
            shutil.copyfile(run_dir / name, destination / name)
        for name in OPTIONAL_RUN_FILES:
            source = run_dir / name
            if source.is_file():
                shutil.copyfile(source, destination / name)
        for name in PREPARED_BUNDLE_FILES:
            shutil.copyfile(prepared_dir / name, destination / name)
        if licence_check is not None:
            shutil.copyfile(licence_check, destination / "licence_check.json")
        (destination / "SPRINT3_README.txt").write_text(SPRINT3_BUNDLE_TEXT, encoding="utf-8")
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    return destination


def _drop_verification(prepared_dir: Path) -> None:
    path = prepared_dir / "verification.json"
    if path.exists():
        path.unlink()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a CropCare preparation or training bundle.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    layout = subparsers.add_parser("layout", help="Count mapped class folders without decoding images.")
    layout.add_argument("--config", required=True, type=Path)
    layout.add_argument("--data-root", required=True, type=Path)
    layout.add_argument("--require-complete", action="store_true")

    licence = subparsers.add_parser("licence", help="Compare a dataset card with the experiment licence.")
    licence.add_argument("--config", required=True, type=Path)
    licence.add_argument("--text-file", required=True, type=Path)
    licence.add_argument("--output", required=True, type=Path)

    prepared = subparsers.add_parser("prepared", help="Check manifest counts, licence, and split integrity.")
    prepared.add_argument("--config", required=True, type=Path)
    prepared.add_argument("--prepared-dir", required=True, type=Path)
    prepared.add_argument("--require-all-configured", action="store_true")

    bundle = subparsers.add_parser("bundle", help="Copy verified artifacts for the local Sprint 3 folder.")
    bundle.add_argument("--run-dir", required=True, type=Path)
    bundle.add_argument("--prepared-dir", required=True, type=Path)
    bundle.add_argument("--destination", required=True, type=Path)
    bundle.add_argument("--licence-check", type=Path, default=None)

    args = parser.parse_args(argv)
    try:
        if args.command == "layout":
            config = load_experiment(args.config)
            summary = summarize_class_folders(args.data_root, config)
            problems = layout_problems(summary) if args.require_complete or not summary["data_root_exists"] else []
            print(json.dumps({**summary, "problems": problems}, indent=2))
            return 2 if problems else 0
        if args.command == "licence":
            config = load_experiment(args.config)
            if not args.text_file.is_file():
                print(f"Licence text not found: {args.text_file}")
                return 2
            result = assess_licence_text(args.text_file.read_text(encoding="utf-8"), config.licence_name)
            result["text_file"] = str(args.text_file.resolve())
            write_json(args.output, result)
            print(json.dumps(result, indent=2))
            return 0 if result["status"] == "matches" else 2
        if args.command == "prepared":
            config = load_experiment(args.config)
            payload = verify_preparation(
                args.prepared_dir,
                config,
                require_all_configured=args.require_all_configured,
            )
            print(json.dumps(payload, indent=2))
            return 0
        destination = stage_sprint3_bundle(
            args.run_dir,
            args.prepared_dir,
            args.destination,
            args.licence_check,
        )
    except VerifyError as exc:
        print(exc)
        return 2
    except (FileNotFoundError, ValueError, json.JSONDecodeError, OSError) as exc:
        print(exc)
        return 2
    print(f"Sprint 3 bundle: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
