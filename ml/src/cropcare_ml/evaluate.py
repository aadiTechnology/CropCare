"""Write class distribution, and model metrics when predictions exist."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cropcare_ml.manifest import read_jsonl, read_labels
from cropcare_ml.metrics import class_distribution, classification_report, write_confusion_csv, write_json


def evaluate_predictions(
    y_true: list[int],
    y_pred: list[int],
    class_codes: list[str],
    rows: list[dict],
    source: str,
    experiment: str,
) -> dict:
    report = classification_report(y_true, y_pred, class_codes)
    report["experiment"] = experiment
    report["source"] = source
    report["class_distribution"] = class_distribution(rows)
    report["generated_from"] = "model_predictions"
    return report


def write_distribution(rows: list[dict], output_dir: Path, experiment: str, source: str) -> dict:
    payload = {
        "schema_version": 1,
        "experiment": experiment,
        "source": source,
        "generated_from": "manifest_counts",
        "class_distribution": class_distribution(rows),
        "sample_count": len(rows),
    }
    write_json(output_dir / "class_distribution.json", payload)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate a prepared split or a saved Keras model.")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--labels", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--model", type=Path, default=None)
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--distribution-only", action="store_true")
    args = parser.parse_args(argv)

    if not args.manifest.is_file():
        print(f"Manifest not found: {args.manifest}")
        return 2
    if not args.labels.is_file():
        print(f"Label file not found: {args.labels}")
        return 2
    rows = read_jsonl(args.manifest)
    label_payload = json.loads(args.labels.read_text(encoding="utf-8"))
    labels = read_labels(args.labels)
    experiment = label_payload.get("experiment", "")
    source = rows[0]["source"] if rows else ""
    if args.distribution_only:
        payload = write_distribution(rows, args.output_dir, experiment, source)
        print(json.dumps(payload["class_distribution"], indent=2))
        return 0
    if args.model is None or not args.model.is_file():
        print("A saved Keras model is required. No accuracy or F1 was written.")
        return 2

    from cropcare_ml.runtime import tensorflow_unavailable_reason
    from cropcare_ml.train import predict_split

    reason = tensorflow_unavailable_reason()
    if reason:
        print(reason)
        return 2
    import tensorflow as tf

    model = tf.keras.models.load_model(args.model)
    class_codes = [item["code"] for item in labels]
    y_true, y_pred = predict_split(model, rows, "test", args.image_size)
    report = evaluate_predictions(y_true, y_pred, class_codes, rows, source, experiment)
    write_json(args.output_dir / "metrics.json", report)
    write_confusion_csv(args.output_dir / "confusion_matrix.csv", class_codes, report["confusion_matrix"])
    print(
        f"Test accuracy {report['accuracy']:.4f}, macro-F1 {report['macro_f1']:.4f}. "
        f"Wrote {args.output_dir / 'metrics.json'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
