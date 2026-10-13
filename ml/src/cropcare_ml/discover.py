"""Find labelled images for one experiment without mixing image variants."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from cropcare_ml.config import ExperimentConfig, normalize_name
from cropcare_ml.grouping import Sample, load_leaf_map, resolve_leaf_key, voc_source_key
from cropcare_ml.images import inspect_image, is_image_path

VARIANT_DIRS = {"color", "colour", "grayscale", "greyscale", "segmented"}
SKIP_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "artifacts"}


@dataclass
class Discovery:
    samples: list[Sample] = field(default_factory=list)
    invalid_files: list[dict] = field(default_factory=list)
    unmapped_directories: list[str] = field(default_factory=list)
    matched_directories: dict[str, list[str]] = field(default_factory=dict)
    properties: dict[str, dict] = field(default_factory=dict)


def discover_images(
    data_root: Path,
    config: ExperimentConfig,
    leaf_map_path: Path | None,
    output_dir: Path | None = None,
) -> Discovery:
    discovery = Discovery()
    if not data_root.exists():
        return discovery

    aliases = config.alias_map()
    leaf_map = load_leaf_map(leaf_map_path)
    output_resolved = output_dir.resolve() if output_dir is not None else None
    invalid_limit = 100

    for dirpath, dirnames, filenames in os.walk(data_root, followlinks=False):
        current = Path(dirpath)
        if output_resolved is not None and current.resolve() == output_resolved:
            dirnames[:] = []
            continue
        dirnames[:] = [
            name
            for name in dirnames
            if name not in SKIP_DIRS and not _skip_variant(name, config.image_variant)
            and (output_resolved is None or (current / name).resolve() != output_resolved)
        ]
        folder_name = current.name
        spec = aliases.get(normalize_name(folder_name))
        image_names = [name for name in filenames if is_image_path(current / name)]
        if spec is None:
            if image_names:
                discovery.unmapped_directories.append(str(current))
            continue

        dirnames[:] = []
        discovery.matched_directories.setdefault(spec.code, []).append(str(current))
        for name in image_names:
            path = current / name
            properties, reason = inspect_image(path, config.min_side, config.phash_hash_size)
            relative = path.relative_to(data_root).as_posix()
            if properties is None:
                if len(discovery.invalid_files) < invalid_limit:
                    discovery.invalid_files.append({"path": relative, "reason": reason})
                continue
            leaf_key = resolve_leaf_key(name, folder_name, leaf_map, config.filename_leaf_key)
            if config.use_voc_source:
                source_key = voc_source_key(path)
                if source_key:
                    leaf_key = f"voc:{source_key}"
            sample = Sample(
                relative_path=relative,
                class_code=spec.code,
                folder_name=folder_name,
                file_name=name,
                sha256=properties["sha256"],
                phash=properties["phash"],
                leaf_key=leaf_key,
            )
            discovery.samples.append(sample)
            discovery.properties[relative] = properties
    discovery.unmapped_directories.sort()
    return discovery


def _skip_variant(name: str, selected: str) -> bool:
    folded = name.casefold()
    return folded in VARIANT_DIRS and folded != selected
