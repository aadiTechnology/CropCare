"""Assign whole image groups to train, validation, and test."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass

from cropcare_ml.config import SPLIT_NAMES
from cropcare_ml.grouping import Sample


class SplitError(ValueError):
    """Raised when a class cannot fill every split without dividing a group."""


@dataclass(frozen=True)
class Group:
    group_id: str
    count: int


def assign_class_splits(
    samples: list[Sample],
    ratios: dict[str, float],
    seed: int,
    min_groups: int,
) -> dict[str, str]:
    """Return ``group_id -> split`` for one class."""
    counts: dict[str, int] = defaultdict(int)
    for sample in samples:
        counts[sample.group_id] += 1
    groups = [Group(group_id, count) for group_id, count in counts.items()]
    if len(groups) < min_groups:
        raise SplitError(
            f"Need at least {min_groups} groups to fill train, validation, and test. Found {len(groups)}."
        )

    total = sum(group.count for group in groups)
    ordered = sorted(groups, key=lambda group: (-group.count, _token(seed, group.group_id)))
    split_counts = {name: 0 for name in SPLIT_NAMES}
    assignment: dict[str, str] = {}
    for group in ordered:
        choice = min(
            SPLIT_NAMES,
            key=lambda name: (split_counts[name] / total - ratios[name], name),
        )
        assignment[group.group_id] = choice
        split_counts[choice] += group.count

    for split_name in SPLIT_NAMES:
        if split_counts[split_name] > 0:
            continue
        donor = max(SPLIT_NAMES, key=lambda name: (split_counts[name], name))
        movable = [group for group in ordered if assignment[group.group_id] == donor]
        movable.sort(key=lambda group: (group.count, group.group_id))
        if len(movable) < 2:
            raise SplitError("A split is empty and moving a group would empty another split.")
        moved = movable[0]
        assignment[moved.group_id] = split_name
        split_counts[donor] -= moved.count
        split_counts[split_name] += moved.count
    return assignment


def _token(seed: int, group_id: str) -> str:
    return hashlib.sha256(f"{seed}\0{group_id}".encode("utf-8")).hexdigest()
