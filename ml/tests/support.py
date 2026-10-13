from __future__ import annotations

from pathlib import Path

import yaml
from PIL import Image

from cropcare_ml.config import ml_root


def write_pattern(path: Path, kind: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (64, 64))
    pixels = image.load()
    for y in range(64):
        for x in range(64):
            if kind == "horizontal":
                pixels[x, y] = (255, 255, 255) if x < 32 else (0, 0, 0)
            elif kind == "wide":
                pixels[x, y] = (255, 255, 255) if x < 16 else (0, 0, 0)
            elif kind == "checker":
                pixels[x, y] = (255, 255, 0) if ((x // 8) + (y // 8)) % 2 == 0 else (0, 0, 128)
            elif kind == "bars":
                pixels[x, y] = (255, 255, 255) if (x // 8) % 2 == 0 else (0, 0, 0)
            else:
                raise ValueError(kind)
    image.save(path, format="PNG")


def lowered_experiment(source_name: str, destination: Path) -> Path:
    data = yaml.safe_load((ml_root() / "config" / source_name).read_text(encoding="utf-8"))
    data["min_images_per_class"] = 3
    data["min_groups_per_class"] = 3
    data["grouping"]["phash_max_distance"] = 0
    destination.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return destination
