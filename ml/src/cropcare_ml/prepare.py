"""Build a reproducible manifest from a local labelled image directory."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from cropcare_ml.config import ExperimentConfig, load_experiment, load_preprocessing_spec, ml_root
from cropcare_ml.discover import discover_images
from cropcare_ml.grouping import Sample, assign_groups
from cropcare_ml.manifest import write_jsonl
from cropcare_ml.metrics import class_distribution, write_json
from cropcare_ml.splitting import SplitError, assign_class_splits


class PrepareBlocked(Exception):
    """Raised when required classes are not available. The report is already written."""

    def __init__(self, report: dict):
        self.report = report
        super().__init__(report["blocked_reason"])


def prepare_dataset(
    config: ExperimentConfig,
    data_root: Path,
    output_dir: Path,
    leaf_map_path: Path | None = None,
) -> dict:
    data_root = data_root.resolve()
    output_dir = output_dir.resolve()
    if output_dir == data_root:
        raise ValueError("The output directory must not be the same as the data root.")
    output_dir.mkdir(parents=True, exist_ok=True)

    configured_leaf_map = leaf_map_path
    if configured_leaf_map is None and config.leaf_map:
        configured_leaf_map = Path(config.leaf_map)
        if not configured_leaf_map.is_absolute():
            configured_leaf_map = ml_root() / configured_leaf_map

    discovery = discover_images(data_root, config, configured_leaf_map, output_dir)
    samples = discovery.samples
    assign_groups(samples, config.phash_max_distance, config.source)

    by_class: dict[str, list[Sample]] = defaultdict(list)
    for sample in samples:
        by_class[sample.class_code].append(sample)

    included: dict[str, list[Sample]] = {}
    excluded: list[dict] = []
    for spec in config.classes:
        class_samples = by_class.get(spec.code, [])
        group_count = len({sample.group_id for sample in class_samples})
        reason = _exclusion_reason(
            class_samples,
            group_count,
            config.min_images_per_class,
            config.min_groups_per_class,
            spec.code in discovery.matched_directories,
        )
        record = {
            "code": spec.code,
            "role": spec.role,
            "valid_images": len(class_samples),
            "groups": group_count,
            "directories": discovery.matched_directories.get(spec.code, []),
        }
        if reason is None:
            included[spec.code] = class_samples
            record["status"] = "included"
        else:
            record["status"] = "excluded"
            record["reason"] = reason
            excluded.append(record)

    missing_required = [
        spec.code
        for spec in config.classes
        if spec.code in config.require_classes and spec.code not in included
    ]
    eligible = sorted(included)
    base_report = {
        "schema_version": 1,
        "experiment": config.experiment,
        "source": config.source,
        "status": "ready",
        "blocked_reason": None,
        "manifest_written": False,
        "data_root": str(data_root),
        "data_root_exists": data_root.exists(),
        "image_variant": config.image_variant,
        "seed": config.seed,
        "licence": {
            "name": config.licence_name,
            "citation": config.licence_citation,
            "url": config.licence_url,
        },
        "eligible_classes": eligible,
        "included_classes": [],
        "excluded_classes": excluded,
        "unmapped_directories": discovery.unmapped_directories,
        "invalid_files": discovery.invalid_files,
        "duplicate_folder_warnings": _duplicate_folder_warnings(discovery.matched_directories),
        "grouping": {
            "filename_leaf_key": config.filename_leaf_key,
            "phash_max_distance": config.phash_max_distance,
            "use_voc_source": config.use_voc_source,
            "leaf_map": str(configured_leaf_map) if configured_leaf_map else None,
        },
    }

    if not data_root.exists() or missing_required:
        if not data_root.exists():
            reason = f"Data root does not exist: {data_root}"
        else:
            reason = (
                "Required classes are unavailable: "
                + ", ".join(missing_required)
                + ". No manifest or label file was written."
            )
        base_report["status"] = "blocked"
        base_report["blocked_reason"] = reason
        base_report["class_distribution"] = {}
        _block(output_dir, base_report)

    label_specs = [spec for spec in config.classes if spec.code in included]
    label_specs.sort(key=lambda spec: spec.code)
    index_by_code = {spec.code: index for index, spec in enumerate(label_specs)}
    rows: list[dict] = []
    for spec in label_specs:
        try:
            assignment = assign_class_splits(
                included[spec.code],
                config.split_ratios,
                config.seed,
                config.min_groups_per_class,
            )
        except SplitError as exc:
            blocked = {
                **base_report,
                "status": "blocked",
                "blocked_reason": f"{spec.code}: {exc}",
                "class_distribution": {},
            }
            _block(output_dir, blocked)
        for sample in included[spec.code]:
            properties = discovery.properties[sample.relative_path]
            rows.append(
                {
                    "split": assignment[sample.group_id],
                    "class_index": index_by_code[spec.code],
                    "class_code": spec.code,
                    "crop": spec.crop,
                    "role": spec.role,
                    "dataset_label": spec.dataset_label,
                    "source": config.source,
                    "group_id": sample.group_id,
                    "leaf_key": sample.leaf_key,
                    "sha256": sample.sha256,
                    "phash": f"{sample.phash:0{(config.phash_hash_size * config.phash_hash_size) // 4}x}",
                    "width": properties["width"],
                    "height": properties["height"],
                    "path": str((data_root / sample.relative_path).resolve()),
                    "relative_path": sample.relative_path,
                }
            )

    rows.sort(key=lambda row: (row["split"], row["class_code"], row["relative_path"]))
    labels = {
        "schema_version": 1,
        "experiment": config.experiment,
        "source": config.source,
        "model_output": "softmax",
        "labels": [
            {
                "index": index,
                "code": spec.code,
                "crop": spec.crop,
                "role": spec.role,
                "dataset_label": spec.dataset_label,
            }
            for index, spec in enumerate(label_specs)
        ],
    }
    distribution = class_distribution(rows)
    base_report["status"] = "ready"
    base_report["manifest_written"] = True
    base_report["included_classes"] = eligible
    base_report["class_distribution"] = distribution
    base_report["sample_count"] = len(rows)
    base_report["group_count"] = len({row["group_id"] for row in rows})
    write_jsonl(output_dir / "manifest.jsonl", rows)
    write_json(output_dir / "labels.json", labels)
    write_json(output_dir / "class_distribution.json", distribution)
    preprocessing = load_preprocessing_spec()
    preprocessing["experiment"] = config.experiment
    preprocessing["source"] = config.source
    write_json(output_dir / "preprocessing.json", preprocessing)
    write_json(output_dir / "preparation_report.json", base_report)
    return base_report


def _exclusion_reason(
    samples: list[Sample],
    group_count: int,
    min_images: int,
    min_groups: int,
    directory_found: bool,
) -> str | None:
    if not directory_found and not samples:
        return "no_directory"
    if not samples:
        return "no_valid_images"
    if len(samples) < min_images:
        return "below_min_images"
    if group_count < min_groups:
        return "below_min_groups"
    return None


def _duplicate_folder_warnings(matched: dict[str, list[str]]) -> list[str]:
    warnings = []
    for code, directories in sorted(matched.items()):
        if len(directories) > 1:
            warnings.append(f"{code} matched {len(directories)} directories. Point --data-root at one dataset copy.")
    return warnings


def _block(output_dir: Path, report: dict) -> None:
    write_json(output_dir / "preparation_report.json", report)
    _remove_success_files(output_dir)
    raise PrepareBlocked(report)


def _remove_success_files(output_dir: Path) -> None:
    for name in ("manifest.jsonl", "labels.json", "class_distribution.json", "preprocessing.json"):
        path = output_dir / name
        if path.exists():
            path.unlink()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare a CropCare image-classification manifest.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--leaf-map", type=Path, default=None)
    args = parser.parse_args(argv)
    config = load_experiment(args.config)
    try:
        report = prepare_dataset(config, args.data_root, args.output_dir, args.leaf_map)
    except PrepareBlocked as exc:
        print(exc.report["blocked_reason"])
        print(f"Report: {args.output_dir.resolve() / 'preparation_report.json'}")
        return 2
    print(
        f"Prepared {report['sample_count']} images in {len(report['included_classes'])} classes "
        f"from {config.source}. Report: {args.output_dir.resolve() / 'preparation_report.json'}"
    )
    print(json.dumps(report["class_distribution"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
