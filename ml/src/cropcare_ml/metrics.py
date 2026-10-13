"""Classification metrics computed from stored predictions.

These functions do not load a model. A metrics file is written only after
an evaluation run supplies prediction indexes.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


def confusion_matrix(y_true: list[int], y_pred: list[int], class_count: int) -> list[list[int]]:
    if len(y_true) != len(y_pred):
        raise ValueError("True labels and predictions must have the same length.")
    matrix = [[0 for _ in range(class_count)] for _ in range(class_count)]
    for truth, prediction in zip(y_true, y_pred, strict=True):
        if not 0 <= truth < class_count or not 0 <= prediction < class_count:
            raise ValueError("A label index is outside the class list.")
        matrix[truth][prediction] += 1
    return matrix


def classification_report(y_true: list[int], y_pred: list[int], class_codes: list[str]) -> dict:
    matrix = confusion_matrix(y_true, y_pred, len(class_codes))
    total = sum(sum(row) for row in matrix)
    correct = sum(matrix[index][index] for index in range(len(class_codes)))
    per_class = []
    for index, code in enumerate(class_codes):
        true_positive = matrix[index][index]
        predicted_positive = sum(matrix[row][index] for row in range(len(class_codes)))
        support = sum(matrix[index])
        false_positive = predicted_positive - true_positive
        false_negative = support - true_positive
        precision = _ratio(true_positive, true_positive + false_positive)
        recall = _ratio(true_positive, true_positive + false_negative)
        per_class.append(
            {
                "code": code,
                "precision": precision,
                "recall": recall,
                "f1": _f1(precision, recall),
                "support": support,
            }
        )
    f1_values = [row["f1"] for row in per_class]
    return {
        "schema_version": 1,
        "split": "test",
        "sample_count": total,
        "accuracy": _ratio(correct, total),
        "macro_f1": sum(f1_values) / len(f1_values) if f1_values else 0.0,
        "per_class": per_class,
        "confusion_matrix": matrix,
        "label_codes": list(class_codes),
        "confusion_matrix_axes": {"rows": "true_class", "columns": "predicted_class"},
    }


def class_distribution(rows: list[dict]) -> dict[str, dict[str, int]]:
    distribution: dict[str, dict[str, int]] = {}
    for split in ("train", "val", "test"):
        counts = Counter(row["class_code"] for row in rows if row["split"] == split)
        distribution[split] = dict(sorted(counts.items()))
    return distribution


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(payload), indent=2) + "\n", encoding="utf-8")


def _jsonable(value):
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "item") and callable(value.item):
        try:
            return value.item()
        except ValueError:
            return value
    return value


def write_confusion_csv(path: Path, class_codes: list[str], matrix: list[list[int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["true_class", *class_codes])
        for code, row in zip(class_codes, matrix, strict=True):
            writer.writerow([code, *row])


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _f1(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)
