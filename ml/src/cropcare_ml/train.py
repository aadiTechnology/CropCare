"""Train the MobileNetV3Small baseline and export it when training finishes.

The script stops before creating metrics if the manifest is missing, sources
were mixed, or TensorFlow cannot be imported. It does not invent scores.
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path

from cropcare_ml.config import TrainConfig, load_preprocessing_spec, load_train_config
from cropcare_ml.evaluate import evaluate_predictions
from cropcare_ml.manifest import read_jsonl, read_labels, training_input_errors
from cropcare_ml.metrics import write_confusion_csv, write_json
from cropcare_ml.runtime import tensorflow_unavailable_reason


def train(config: TrainConfig, run_dir: Path | None = None) -> Path:
    manifest_path = config.prepared_dir / "manifest.jsonl"
    labels_path = config.prepared_dir / "labels.json"
    preprocessing_path = config.prepared_dir / "preprocessing.json"
    if not manifest_path.is_file() or not labels_path.is_file():
        raise FileNotFoundError(
            f"No prepared manifest at {config.prepared_dir}. Run cropcare_ml.prepare first."
        )
    rows = read_jsonl(manifest_path)
    labels = read_labels(labels_path)
    preprocessing = json.loads(preprocessing_path.read_text(encoding="utf-8"))
    errors = training_input_errors(
        rows,
        labels,
        preprocessing,
        config.image_size,
        config.allow_mixed_sources,
    )
    if errors:
        raise ValueError(" ".join(errors))
    reason = tensorflow_unavailable_reason()
    if reason:
        raise RuntimeError(reason)

    import numpy as np
    import tensorflow as tf

    random.seed(config.seed)
    np.random.seed(config.seed)
    tf.keras.utils.set_random_seed(config.seed)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = run_dir or (config.output_dir / f"{config.experiment}_{stamp}")
    destination.mkdir(parents=True, exist_ok=True)
    write_json(destination / "train_config.json", _config_dict(config))

    class_codes = [item["code"] for item in labels]
    model, base = build_baseline(len(class_codes), config.image_size, config.dropout, config.weights)
    base.trainable = False
    model.compile(
        optimizer=tf.keras.optimizers.Adam(config.learning_rate),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    train_ds = _dataset(rows, "train", config, training=True)
    val_ds = _dataset(rows, "val", config, training=False)
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=config.epochs,
        class_weight=_class_weights(rows),
        callbacks=_callbacks(destination / "checkpoint.weights.h5"),
    )
    history_payload = {key: list(values) for key, values in history.history.items()}
    if config.fine_tune_epochs:
        _unfreeze_tail(base, config.fine_tune_layers)
        model.compile(
            optimizer=tf.keras.optimizers.Adam(config.fine_tune_learning_rate),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )
        fine_history = model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=config.fine_tune_epochs,
            class_weight=_class_weights(rows),
            callbacks=_callbacks(destination / "checkpoint.weights.h5"),
        )
        for key, values in fine_history.history.items():
            history_payload.setdefault(key, [])
            history_payload[key].extend(values)

    checkpoint = destination / "checkpoint.weights.h5"
    if checkpoint.is_file():
        model.load_weights(checkpoint)
    model.save(destination / "model.keras")
    write_json(destination / "history.json", history_payload)

    y_true, y_pred = predict_split(model, rows, "test", config.image_size)
    metrics = evaluate_predictions(
        y_true,
        y_pred,
        class_codes,
        rows,
        source=rows[0]["source"],
        experiment=config.experiment,
    )
    write_json(destination / "metrics.json", metrics)
    write_confusion_csv(
        destination / "confusion_matrix.csv",
        class_codes,
        metrics["confusion_matrix"],
    )
    from cropcare_ml.export_model import export_saved_model

    export_saved_model(model, destination, labels_path, preprocessing)
    return destination


def build_baseline(num_classes: int, image_size: int, dropout: float, weights: str):
    import tensorflow as tf

    inputs = tf.keras.Input(shape=(image_size, image_size, 3), name="image_rgb_0_255")
    base = tf.keras.applications.MobileNetV3Small(
        input_tensor=inputs,
        include_top=False,
        weights=None if weights == "none" else weights,
        pooling="avg",
        include_preprocessing=True,
    )
    features = tf.keras.layers.Dropout(dropout)(base.output)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax", name="class_probabilities")(features)
    model = tf.keras.Model(inputs, outputs, name="cropcare_mobilenet_v3_small")
    return model, base


def predict_split(model, rows: list[dict], split: str, image_size: int) -> tuple[list[int], list[int]]:
    import tensorflow as tf

    selected = [row for row in rows if row["split"] == split]
    if not selected:
        raise ValueError(f"The manifest has no {split} rows.")
    paths = [row["path"] for row in selected]
    dataset = tf.data.Dataset.from_tensor_slices(paths)
    dataset = dataset.map(lambda path: load_resized_image(path, image_size), num_parallel_calls=tf.data.AUTOTUNE)
    dataset = dataset.batch(32).prefetch(tf.data.AUTOTUNE)
    probabilities = model.predict(dataset, verbose=0)
    predictions = probabilities.argmax(axis=1).astype(int).tolist()
    truth = [int(row["class_index"]) for row in selected]
    return truth, predictions


def load_resized_image(path, image_size: int):
    import tensorflow as tf

    image_bytes = tf.io.read_file(path)
    image = tf.io.decode_image(image_bytes, channels=3, expand_animations=False)
    image.set_shape([None, None, 3])
    image = tf.image.resize(image, [image_size, image_size], method="bilinear")
    return tf.cast(image, tf.float32)


def _dataset(rows: list[dict], split: str, config: TrainConfig, training: bool):
    import tensorflow as tf

    selected = [row for row in rows if row["split"] == split]
    paths = [row["path"] for row in selected]
    labels = [int(row["class_index"]) for row in selected]
    dataset = tf.data.Dataset.from_tensor_slices((paths, labels))
    if training:
        dataset = dataset.shuffle(len(paths), seed=config.seed, reshuffle_each_iteration=True)
    dataset = dataset.map(
        lambda path, label: (_train_image(path, config.image_size, training), label),
        num_parallel_calls=tf.data.AUTOTUNE,
    )
    return dataset.batch(config.batch_size).prefetch(tf.data.AUTOTUNE)


def _train_image(path, image_size: int, training: bool):
    import tensorflow as tf

    image = load_resized_image(path, image_size)
    if training:
        image = tf.image.random_flip_left_right(image)
        image = tf.image.random_flip_up_down(image)
    return image


def _class_weights(rows: list[dict]) -> dict[int, float]:
    counts: dict[int, int] = {}
    for row in rows:
        if row["split"] != "train":
            continue
        counts[int(row["class_index"])] = counts.get(int(row["class_index"]), 0) + 1
    total = sum(counts.values())
    class_count = len(counts)
    return {index: total / (class_count * count) for index, count in counts.items()}


def _unfreeze_tail(base, fine_tune_layers: int) -> None:
    base.trainable = True
    frozen_until = max(len(base.layers) - fine_tune_layers, 0)
    for layer in base.layers[:frozen_until]:
        layer.trainable = False
    for layer in base.layers:
        if layer.__class__.__name__ == "BatchNormalization":
            layer.trainable = False


def _callbacks(checkpoint_path: Path):
    import tensorflow as tf

    return [
        tf.keras.callbacks.ModelCheckpoint(
            checkpoint_path,
            monitor="val_loss",
            save_best_only=True,
            save_weights_only=True,
        ),
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True),
    ]


def _config_dict(config: TrainConfig) -> dict:
    return {
        "experiment": config.experiment,
        "prepared_dir": str(config.prepared_dir),
        "image_size": config.image_size,
        "batch_size": config.batch_size,
        "epochs": config.epochs,
        "fine_tune_epochs": config.fine_tune_epochs,
        "fine_tune_layers": config.fine_tune_layers,
        "learning_rate": config.learning_rate,
        "fine_tune_learning_rate": config.fine_tune_learning_rate,
        "seed": config.seed,
        "backbone": config.backbone,
        "weights": config.weights,
        "dropout": config.dropout,
        "allow_mixed_sources": config.allow_mixed_sources,
        "output_dir": str(config.output_dir),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train the CropCare MobileNetV3Small baseline.")
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)
    config_path = args.config or (Path(__file__).resolve().parents[2] / "config" / "train.yaml")
    try:
        config = load_train_config(config_path)
        load_preprocessing_spec()
        destination = train(config)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(exc)
        return 2
    print(f"Training finished. Artifacts: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
