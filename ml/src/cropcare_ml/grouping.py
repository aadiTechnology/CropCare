"""Group images that are the same leaf or near-duplicates.

Groups are assigned entirely to one split. Perceptual hashing is an
approximation: it can miss an edited copy and it can join different leaves
that look alike.
"""

from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from cropcare_ml.images import hamming_distance, plantvillage_leaf_identifier


@dataclass
class Sample:
    relative_path: str
    class_code: str
    folder_name: str
    file_name: str
    sha256: str
    phash: int
    leaf_key: str
    group_id: str = ""


@dataclass
class UnionFind:
    parent: dict[int, int] = field(default_factory=dict)

    def add(self, item: int) -> None:
        self.parent.setdefault(item, item)

    def find(self, item: int) -> int:
        self.add(item)
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left: int, right: int) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return
        if left_root < right_root:
            self.parent[right_root] = left_root
        else:
            self.parent[left_root] = right_root


def load_leaf_map(path: Path | None) -> dict[str, list[str]]:
    if path is None:
        return {}
    import json

    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, dict):
        raise ValueError(f"Leaf map {path} must be a JSON object.")
    mapping: dict[str, list[str]] = {}
    for key, value in raw.items():
        if isinstance(value, str):
            mapping[str(key).casefold()] = [value]
        elif isinstance(value, list):
            mapping[str(key).casefold()] = [str(item) for item in value]
        else:
            raise ValueError(f"Leaf map entry {key!r} must be a string or a list.")
    return mapping


def resolve_leaf_key(
    file_name: str,
    folder_name: str,
    leaf_map: dict[str, list[str]],
    enabled: bool,
) -> str:
    if not enabled:
        return ""
    identifier = plantvillage_leaf_identifier(file_name)
    suggestions = leaf_map.get(identifier, [])
    for suggestion in suggestions:
        if folder_name in suggestion or suggestion in folder_name:
            return suggestion.casefold()
    if len(suggestions) == 1:
        return suggestions[0].casefold()
    return identifier


def voc_source_key(image_path: Path) -> str | None:
    """Read a Pascal VOC file beside the image or in a sibling Annotations directory."""
    candidates = [
        image_path.with_suffix(".xml"),
        image_path.parent.parent / "Annotations" / f"{image_path.stem}.xml",
    ]
    for candidate in candidates:
        if not candidate.is_file():
            continue
        try:
            root = ET.parse(candidate).getroot()
        except ET.ParseError:
            return None
        filename = root.findtext("filename")
        if filename:
            return Path(filename).stem.casefold()
        return candidate.stem.casefold()
    return None


def assign_groups(
    samples: list[Sample],
    phash_max_distance: int,
    source: str,
) -> None:
    """Set ``group_id`` in place. Grouping never crosses class codes."""
    by_class: dict[str, list[int]] = {}
    for index, sample in enumerate(samples):
        by_class.setdefault(sample.class_code, []).append(index)

    for class_code, indexes in by_class.items():
        union = UnionFind()
        for index in indexes:
            union.add(index)
        _union_same_value(samples, indexes, union, lambda sample: sample.leaf_key)
        _union_same_value(samples, indexes, union, lambda sample: sample.sha256)
        if phash_max_distance >= 0:
            _union_phash(samples, indexes, union, phash_max_distance)

        clusters: dict[int, list[int]] = {}
        for index in indexes:
            clusters.setdefault(union.find(index), []).append(index)
        for members in clusters.values():
            anchor = min(samples[index].relative_path for index in members)
            group_id = "g_" + _token(source, class_code, anchor)
            for index in members:
                samples[index].group_id = group_id


def _union_same_value(samples: list[Sample], indexes: list[int], union: UnionFind, key) -> None:
    buckets: dict[str, list[int]] = {}
    for index in indexes:
        value = key(samples[index])
        if not value:
            continue
        buckets.setdefault(value, []).append(index)
    for members in buckets.values():
        first = members[0]
        for other in members[1:]:
            union.union(first, other)


def _union_phash(samples: list[Sample], indexes: list[int], union: UnionFind, max_distance: int) -> None:
    for position, left in enumerate(indexes):
        for right in indexes[position + 1 :]:
            distance = hamming_distance(samples[left].phash, samples[right].phash)
            if distance <= max_distance:
                union.union(left, right)


def _token(*parts: str) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()[:16]
