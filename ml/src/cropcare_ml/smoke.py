"""Load an exported TensorFlow Lite model and run one image through it.

The result is a load check. Test-set accuracy stays in metrics.json.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cropcare_ml.manifest import read_labels
from cropcare_ml.metrics import write_json
from cropcare_ml.runtime import tensorflow_unavailable_reason


def run_smoke_test(
    model_path: Path,
    labels_path: Path,
    preprocessing_path: Path,
    image_path: Path,
    output_dir: Path,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / "smoke_test.json"
    if destination.exists():
        destination.unlink()
    if not model_path.is_file():
        raise FileNotFoundError(f"TensorFlow Lite model not found: {model_path}")
    if not labels_path.is_file():
        raise FileNotFoundError(f"Label file not found: {labels_path}")
    if not preprocessing_path.is_file():
        raise FileNotFoundError(f"Preprocessing file not found: {preprocessing_path}")
    if not image_path.is_file():
        raise FileNotFoundError(f"Smoke-test image not found: {image_path}")
    reason = tensorflow_unavailable_reason()
    if reason:
        raise RuntimeError(reason)

    import numpy as np
    import tensorflow as tf

    from cropcare_ml.train import load_resized_image

    labels = read_labels(labels_path)
    preprocessing = json.loads(preprocessing_path.read_text(encoding="utf-8"))
    image_size = int(preprocessing["input"]["height"])
    if image_size != int(preprocessing["input"]["width"]) or image_size != 224:
        raise ValueError("Smoke test expects the 224 by 224 preprocessing specification.")
    if preprocessing.get("backbone") != "MobileNetV3Small":
        raise ValueError("Smoke test expects a MobileNetV3Small preprocessing file.")
    if preprocessing.get("input", {}).get("color_order") != "RGB":
        raise ValueError("Smoke test expects RGB channel order.")

    interpreter = tf.lite.Interpreter(model_path=str(model_path))
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    if len(input_details) != 1 or len(output_details) != 1:
        raise ValueError("The exported model must have one input and one output.")
    if input_details[0]["dtype"] != np.float32:
        raise ValueError("The exported model input is not float32.")
    shape = [int(dim) for dim in input_details[0]["shape"]]
    if shape[-3:] != [image_size, image_size, 3]:
        raise ValueError(f"Exported input shape is {shape}.")

    image = load_resized_image(str(image_path), image_size)
    array = tf.expand_dims(image, 0).numpy().astype(np.float32)
    if list(array.shape) != shape:
        raise ValueError(f"Resized image shape {list(array.shape)} does not match {shape}.")
    interpreter.set_tensor(input_details[0]["index"], array)
    interpreter.invoke()
    probabilities = np.asarray(interpreter.get_tensor(output_details[0]["index"]), dtype=np.float32).reshape(-1)
    if probabilities.shape != (len(labels),):
        raise ValueError(
            f"The model returned {probabilities.shape[0]} values for {len(labels)} labels."
        )
    if not np.isfinite(probabilities).all():
        raise ValueError("The model returned a non-finite probability.")
    total = float(probabilities.sum())
    if abs(total - 1.0) > 1e-3:
        raise ValueError(f"Probabilities sum to {total}, which is outside the softmax range.")
    index = int(probabilities.argmax())
    payload = {
        "schema_version": 1,
        "status": "passed",
        "purpose": "export_load_check",
        "claims_accuracy": False,
        "model_file": model_path.name,
        "label_file": labels_path.name,
        "preprocessing_file": preprocessing_path.name,
        "image_name": image_path.name,
        "input_shape": shape,
        "output_length": int(probabilities.shape[0]),
        "probability_sum": total,
        "predicted_index": index,
        "predicted_code": labels[index]["code"],
        "predicted_probability": float(probabilities[index]),
        "finite_probabilities": True,
    }
    write_json(destination, payload)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Load an exported CropCare model and run one image.")
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--labels", required=True, type=Path)
    parser.add_argument("--preprocessing", required=True, type=Path)
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        payload = run_smoke_test(args.model, args.labels, args.preprocessing, args.image, args.output_dir)
    except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
        print(exc)
        return 2
    print(
        f"Smoke test passed. Predicted {payload['predicted_code']} "
        f"from {payload['image_name']}. This is a load check, not a test-set score."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
