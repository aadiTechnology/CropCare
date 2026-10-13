"""Load and validate experiment, training, and preprocessing configuration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import yaml

SPLIT_NAMES = ("train", "val", "test")
ROLES = {"healthy", "disease"}


class ConfigError(ValueError):
    """Raised when a configuration file is incomplete or inconsistent."""


def ml_root() -> Path:
    """Return the ml/ directory that contains config, src, and tests."""
    return Path(__file__).resolve().parents[2]


def resolve_ml_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return ml_root() / path


@dataclass(frozen=True)
class ClassSpec:
    code: str
    crop: str
    role: str
    dataset_label: str
    folder_names: tuple[str, ...]


@dataclass(frozen=True)
class ExperimentConfig:
    experiment: str
    source: str
    description: str
    image_variant: str
    require_classes: tuple[str, ...]
    min_images_per_class: int
    min_groups_per_class: int
    min_side: int
    split_ratios: dict[str, float]
    seed: int
    filename_leaf_key: bool
    leaf_map: str | None
    phash_hash_size: int
    phash_max_distance: int
    use_voc_source: bool
    classes: tuple[ClassSpec, ...]
    licence_name: str
    licence_citation: str
    licence_url: str

    def class_by_code(self) -> dict[str, ClassSpec]:
        return {spec.code: spec for spec in self.classes}

    def alias_map(self) -> dict[str, ClassSpec]:
        mapping: dict[str, ClassSpec] = {}
        for spec in self.classes:
            for folder_name in spec.folder_names:
                mapping[normalize_name(folder_name)] = spec
        return mapping


@dataclass(frozen=True)
class TrainConfig:
    experiment: str
    prepared_dir: Path
    image_size: int
    batch_size: int
    epochs: int
    fine_tune_epochs: int
    fine_tune_layers: int
    learning_rate: float
    fine_tune_learning_rate: float
    seed: int
    backbone: str
    weights: str
    dropout: float
    allow_mixed_sources: bool
    output_dir: Path


def normalize_name(name: str) -> str:
    return " ".join(name.casefold().split())


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ConfigError(f"{path} must contain a YAML mapping.")
    return data


def _require_keys(data: dict, keys: set[str], label: str) -> None:
    missing = sorted(keys - data.keys())
    unknown = sorted(set(data) - keys)
    if missing or unknown:
        raise ConfigError(f"{label} keys are invalid. Missing: {missing or 'none'}. Unknown: {unknown or 'none'}.")


def load_experiment(path: Path) -> ExperimentConfig:
    data = load_yaml(path)
    _require_keys(
        data,
        {
            "experiment",
            "source",
            "description",
            "image_variant",
            "require_classes",
            "min_images_per_class",
            "min_groups_per_class",
            "min_side",
            "split",
            "grouping",
            "licence",
            "classes",
        },
        f"Experiment file {path}",
    )
    split = data["split"]
    grouping = data["grouping"]
    licence = data["licence"]
    _require_keys(split, {"train", "val", "test", "seed"}, "split")
    _require_keys(
        grouping,
        {"filename_leaf_key", "leaf_map", "phash_hash_size", "phash_max_distance", "use_voc_source"},
        "grouping",
    )
    _require_keys(licence, {"name", "citation", "url"}, "licence")

    ratios = {name: float(split[name]) for name in SPLIT_NAMES}
    if abs(sum(ratios.values()) - 1.0) > 1e-6:
        raise ConfigError(f"Split ratios must sum to 1. They sum to {sum(ratios.values())}.")
    if any(value <= 0 for value in ratios.values()):
        raise ConfigError("Every split ratio must be greater than zero.")

    classes: list[ClassSpec] = []
    seen_codes: set[str] = set()
    seen_folders: dict[str, str] = {}
    for entry in data["classes"]:
        _require_keys(entry, {"code", "crop", "role", "dataset_label", "folder_names"}, "class")
        if entry["role"] not in ROLES:
            raise ConfigError(f"Class {entry['code']} has role {entry['role']!r}.")
        if entry["code"] in seen_codes:
            raise ConfigError(f"Duplicate class code {entry['code']}.")
        seen_codes.add(entry["code"])
        folder_names = tuple(entry["folder_names"])
        if not folder_names:
            raise ConfigError(f"Class {entry['code']} needs at least one folder name.")
        for folder_name in folder_names:
            key = normalize_name(folder_name)
            owner = seen_folders.get(key)
            if owner is not None and owner != entry["code"]:
                raise ConfigError(f"Folder {folder_name!r} is listed for both {owner} and {entry['code']}.")
            seen_folders[key] = entry["code"]
        classes.append(
            ClassSpec(
                code=entry["code"],
                crop=entry["crop"],
                role=entry["role"],
                dataset_label=entry["dataset_label"],
                folder_names=folder_names,
            )
        )

    require_classes = tuple(data["require_classes"])
    known = {spec.code for spec in classes}
    unknown_required = [code for code in require_classes if code not in known]
    if unknown_required:
        raise ConfigError(f"require_classes includes unknown codes: {unknown_required}.")

    min_images = int(data["min_images_per_class"])
    min_groups = int(data["min_groups_per_class"])
    if min_groups < 3:
        raise ConfigError("min_groups_per_class must be at least 3 so a group is never split.")
    if min_images < min_groups:
        raise ConfigError("min_images_per_class cannot be lower than min_groups_per_class.")

    return ExperimentConfig(
        experiment=str(data["experiment"]),
        source=str(data["source"]),
        description=str(data["description"]).strip(),
        image_variant=str(data["image_variant"]).casefold(),
        require_classes=require_classes,
        min_images_per_class=min_images,
        min_groups_per_class=min_groups,
        min_side=int(data["min_side"]),
        split_ratios=ratios,
        seed=int(split["seed"]),
        filename_leaf_key=bool(grouping["filename_leaf_key"]),
        leaf_map=grouping["leaf_map"],
        phash_hash_size=int(grouping["phash_hash_size"]),
        phash_max_distance=int(grouping["phash_max_distance"]),
        use_voc_source=bool(grouping["use_voc_source"]),
        classes=tuple(classes),
        licence_name=str(licence["name"]),
        licence_citation=str(licence["citation"]),
        licence_url=str(licence["url"]),
    )


def load_train_config(path: Path) -> TrainConfig:
    data = load_yaml(path)
    _require_keys(
        data,
        {
            "experiment",
            "prepared_dir",
            "image_size",
            "batch_size",
            "epochs",
            "fine_tune_epochs",
            "fine_tune_layers",
            "learning_rate",
            "fine_tune_learning_rate",
            "seed",
            "backbone",
            "weights",
            "dropout",
            "allow_mixed_sources",
            "output_dir",
        },
        f"Training file {path}",
    )
    if data["backbone"] != "MobileNetV3Small":
        raise ConfigError("Sprint 2 trains MobileNetV3Small only.")
    if int(data["image_size"]) != 224:
        raise ConfigError("image_size must be 224 to match the preprocessing specification.")
    return TrainConfig(
        experiment=str(data["experiment"]),
        prepared_dir=resolve_ml_path(data["prepared_dir"]),
        image_size=int(data["image_size"]),
        batch_size=int(data["batch_size"]),
        epochs=int(data["epochs"]),
        fine_tune_epochs=int(data["fine_tune_epochs"]),
        fine_tune_layers=int(data["fine_tune_layers"]),
        learning_rate=float(data["learning_rate"]),
        fine_tune_learning_rate=float(data["fine_tune_learning_rate"]),
        seed=int(data["seed"]),
        backbone=str(data["backbone"]),
        weights=str(data["weights"]),
        dropout=float(data["dropout"]),
        allow_mixed_sources=bool(data["allow_mixed_sources"]),
        output_dir=resolve_ml_path(data["output_dir"]),
    )


def load_preprocessing_spec(path: Path | None = None) -> dict:
    spec_path = path or (ml_root() / "config" / "preprocessing.json")
    with spec_path.open("r", encoding="utf-8") as handle:
        spec = json.load(handle)
    if spec.get("backbone") != "MobileNetV3Small":
        raise ConfigError("Preprocessing specification must name MobileNetV3Small.")
    size = spec["input"]["height"]
    if size != spec["input"]["width"] or size != 224:
        raise ConfigError("Preprocessing specification must use a 224 by 224 input.")
    return spec
