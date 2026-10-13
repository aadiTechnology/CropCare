"""Read and check the JSONL manifest shared by training and evaluation."""

from __future__ import annotations

import json
from pathlib import Path


MANIFEST_FIELDS = (
    "split",
    "class_index",
    "class_code",
    "crop",
    "role",
    "dataset_label",
    "source",
    "group_id",
    "leaf_key",
    "sha256",
    "phash",
    "width",
    "height",
    "path",
    "relative_path",
)


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number} is not an object.")
            rows.append(row)
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            ordered = {field: row[field] for field in MANIFEST_FIELDS}
            handle.write(json.dumps(ordered, sort_keys=False) + "\n")


def read_labels(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    labels = payload["labels"]
    indexes = [item["index"] for item in labels]
    if indexes != list(range(len(labels))):
        raise ValueError("Label indexes must be contiguous and start at 0.")
    return labels


def training_input_errors(
    rows: list[dict],
    labels: list[dict],
    preprocessing: dict,
    image_size: int,
    allow_mixed_sources: bool,
) -> list[str]:
    errors: list[str] = []
    if not rows:
        errors.append("The manifest is empty.")
        return errors
    sources = sorted({row["source"] for row in rows})
    if len(sources) > 1 and not allow_mixed_sources:
        errors.append(
            "The manifest contains more than one dataset source "
            f"({', '.join(sources)}). PlantVillage and PlantDoc stay in separate experiments."
        )
    codes = [item["code"] for item in labels]
    if codes != sorted(codes):
        errors.append("Label codes must be sorted so the model output index stays stable.")
    manifest_codes = sorted({row["class_code"] for row in rows})
    if manifest_codes != codes:
        errors.append("Manifest class codes do not match labels.json.")
    for row in rows:
        expected = codes.index(row["class_code"])
        if row["class_index"] != expected:
            errors.append(f"{row['relative_path']} has class_index {row['class_index']} for {row['class_code']}.")
            break
    if preprocessing["input"]["height"] != image_size or preprocessing["input"]["width"] != image_size:
        errors.append("Training image_size does not match the preprocessing specification.")
    if preprocessing.get("backbone") != "MobileNetV3Small":
        errors.append("Preprocessing backbone must be MobileNetV3Small.")
    splits = {row["split"] for row in rows}
    if splits != {"train", "val", "test"}:
        errors.append(f"Manifest splits are {sorted(splits)}; train, val, and test are required.")
    grouped: dict[tuple[str, str], set[str]] = {}
    for row in rows:
        grouped.setdefault((row["class_code"], row["group_id"]), set()).add(row["split"])
    leaked = [key for key, found in grouped.items() if len(found) > 1]
    if leaked:
        errors.append(f"{len(leaked)} groups appear in more than one split.")
    return errors
