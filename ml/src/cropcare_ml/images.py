"""Image checks, file hashes, and difference hashes used for grouping."""

from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, UnidentifiedImageError

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def is_image_path(path: Path) -> bool:
    return path.is_file() and path.suffix.casefold() in IMAGE_SUFFIXES


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def difference_hash(image: Image.Image, hash_size: int = 8) -> int:
    """Return a horizontal difference hash as an integer."""
    gray = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.BILINEAR)
    flattened = gray.get_flattened_data() if hasattr(gray, "get_flattened_data") else gray.getdata()
    pixels = list(flattened)
    width = hash_size + 1
    value = 0
    for row in range(hash_size):
        for col in range(hash_size):
            left = pixels[row * width + col]
            right = pixels[row * width + col + 1]
            value = (value << 1) | (1 if left > right else 0)
    return value


def hamming_distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def inspect_image(path: Path, min_side: int, hash_size: int) -> tuple[dict | None, str | None]:
    """Open one image. Return properties, or a short rejection reason."""
    try:
        with Image.open(path) as image:
            image.load()
            width, height = image.size
            if width < min_side or height < min_side:
                return None, "below_minimum_size"
            rgb = image.convert("RGB")
            perceptual = difference_hash(rgb, hash_size)
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
        return None, "unreadable"
    return {
        "width": width,
        "height": height,
        "sha256": sha256_file(path),
        "phash": perceptual,
    }, None


def plantvillage_leaf_identifier(file_name: str) -> str:
    """Match the PlantVillage filename key used to keep copies of one leaf together.

    The same rule is used by the public Hugging Face PlantVillage loader:
    drop a segmentation suffix, keep the text after the last triple underscore,
    and remove a trailing ``copy`` marker and the extension.
    """
    identifier = file_name.replace("_final_masked", "")
    if "___" in identifier:
        identifier = identifier.split("___")[-1]
    identifier = identifier.split("copy")[0]
    suffix = Path(identifier).suffix
    if suffix.casefold() in IMAGE_SUFFIXES:
        identifier = identifier[: -len(suffix)]
    return identifier.strip().casefold()
