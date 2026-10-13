"""Export a trained Keras model to float32 TensorFlow Lite."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from cropcare_ml.metrics import write_json
from cropcare_ml.runtime import tensorflow_unavailable_reason


def export_saved_model(model, output_dir: Path, labels_path: Path, preprocessing: dict) -> Path:
    import tensorflow as tf

    output_dir.mkdir(parents=True, exist_ok=True)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    model_bytes = converter.convert()
    model_path = output_dir / "model.tflite"
    model_path.write_bytes(model_bytes)
    shutil.copyfile(labels_path, output_dir / "labels.json")
    exported = dict(preprocessing)
    exported["exported_model"] = model_path.name
    exported["quantization"] = "none"
    exported["input"] = dict(preprocessing["input"])
    write_json(output_dir / "preprocessing.json", exported)
    write_json(
        output_dir / "export_record.json",
        {
            "schema_version": 1,
            "format": "tflite",
            "quantization": "none",
            "model_file": model_path.name,
            "label_file": "labels.json",
            "preprocessing_file": "preprocessing.json",
        },
    )
    return model_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export a CropCare Keras model to TensorFlow Lite.")
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--labels", required=True, type=Path)
    parser.add_argument("--preprocessing", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    if not args.model.is_file():
        print(f"Keras model not found: {args.model}. No TensorFlow Lite file was written.")
        return 2
    reason = tensorflow_unavailable_reason()
    if reason:
        print(reason)
        return 2
    import tensorflow as tf

    model = tf.keras.models.load_model(args.model)
    preprocessing = json.loads(args.preprocessing.read_text(encoding="utf-8"))
    model_path = export_saved_model(model, args.output_dir, args.labels, preprocessing)
    print(f"Wrote {model_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
