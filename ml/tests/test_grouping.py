from cropcare_ml.grouping import Sample, assign_groups
from cropcare_ml.images import difference_hash, plantvillage_leaf_identifier
from cropcare_ml.splitting import SplitError, assign_class_splits
from PIL import Image

from tests.support import write_pattern


def test_plantvillage_filename_key_keeps_copies_of_one_leaf():
    assert plantvillage_leaf_identifier("set___leafA.png") == "leafa"
    assert plantvillage_leaf_identifier("set___leafA copy.png") == "leafa"
    assert plantvillage_leaf_identifier("leafA_final_masked.png") == "leafa"


def test_groups_join_on_leaf_key_hash_and_phash_without_crossing_classes():
    samples = [
        _sample("a/one.png", "tomato_healthy", "leaf-a", "hash-1", 1),
        _sample("a/two.png", "tomato_healthy", "leaf-a", "hash-2", 50),
        _sample("b/one.png", "tomato_healthy", "leaf-b", "hash-3", 1),
        _sample("c/one.png", "soybean_healthy", "leaf-a", "hash-1", 1),
        _sample("d/one.png", "tomato_healthy", "leaf-c", "same-file", 9),
        _sample("d/two.png", "tomato_healthy", "leaf-d", "same-file", 40),
    ]
    assign_groups(samples, phash_max_distance=0, source="plantvillage")
    groups = {sample.relative_path: sample.group_id for sample in samples}
    assert groups["a/one.png"] == groups["a/two.png"]
    assert groups["a/one.png"] == groups["b/one.png"]
    assert groups["d/one.png"] == groups["d/two.png"]
    assert groups["c/one.png"] != groups["a/one.png"]


def test_pattern_hashes_are_separable(tmp_path):
    hashes = {}
    for kind in ("horizontal", "wide", "checker", "bars"):
        path = tmp_path / f"{kind}.png"
        write_pattern(path, kind)
        with Image.open(path) as image:
            hashes[kind] = difference_hash(image.convert("RGB"), 8)
    values = list(hashes.values())
    assert len(set(values)) == 4


def test_split_keeps_a_group_intact_and_is_reproducible():
    samples = []
    for group_id, count in (("large", 10), ("small-a", 1), ("small-b", 1)):
        for index in range(count):
            samples.append(_sample(f"{group_id}-{index}.png", "tomato_healthy", group_id, str(index), index))
            samples[-1].group_id = group_id
    ratios = {"train": 0.7, "val": 0.15, "test": 0.15}
    first = assign_class_splits(samples, ratios, seed=42, min_groups=3)
    second = assign_class_splits(samples, ratios, seed=42, min_groups=3)
    assert first == second
    assert set(first.values()) == {"train", "val", "test"}
    assert len(set(first.values())) == 3
    large_split = first["large"]
    assert sum(group_id == "large" for group_id in first) == 1
    assert large_split in {"train", "val", "test"}
    equal_groups = []
    for name in ("g1", "g2", "g3"):
        for index in range(4):
            sample = _sample(f"{name}-{index}.png", "tomato_healthy", name, name, index)
            sample.group_id = name
            equal_groups.append(sample)
    seed_assignments = {
        seed: tuple(sorted(assign_class_splits(equal_groups, ratios, seed=seed, min_groups=3).items()))
        for seed in range(12)
    }
    assert len(set(seed_assignments.values())) > 1
    with pytest_split_error():
        assign_class_splits(samples[:2], ratios, seed=42, min_groups=3)


def _sample(relative_path: str, class_code: str, leaf_key: str, sha256: str, phash: int) -> Sample:
    return Sample(
        relative_path=relative_path,
        class_code=class_code,
        folder_name=class_code,
        file_name=relative_path,
        sha256=sha256,
        phash=phash,
        leaf_key=leaf_key,
    )


class pytest_split_error:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        if exc_type is None:
            raise AssertionError("SplitError was not raised")
        return issubclass(exc_type, SplitError)
