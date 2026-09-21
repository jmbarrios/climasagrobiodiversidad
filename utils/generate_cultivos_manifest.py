#!/usr/bin/env python3
"""Generate the static catalog used by the frontend."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
OUTPUT = FRONTEND / "data" / "cultivos.json"
FILENAME_PATTERN = re.compile(r"^(?P<name>.+)_(?P<id>[^.]+)\.(?P<extension>[^.]+)$")
ALLOWED_EXTENSIONS = {"gif", "jpeg", "jpg", "png", "webp"}


def display_name(name: str, category: str) -> str:
    """Convert the filename prefix to the label shown by the current PHP page."""
    label = re.sub(r"(?<! )[A-Z]", r" \g<0>", name)
    if category == "maices":
        label = re.sub(r"De", "de", label, flags=re.IGNORECASE)
    else:
        label = re.sub(r"Raza", "raza", label, flags=re.IGNORECASE)
    return label.strip()


def read_category(category: str, directory: Path) -> list[dict[str, str]]:
    entries = []
    for image_path in sorted(directory.iterdir(), key=lambda path: path.name):
        if not image_path.is_file() or image_path.name == ".DS_Store":
            continue
        if image_path.suffix.lower().lstrip(".") not in ALLOWED_EXTENSIONS:
            continue

        match = FILENAME_PATTERN.match(image_path.name)
        if match is None:
            raise ValueError(f"Unexpected image filename: {image_path}")

        entries.append(
            {
                "name": display_name(match["name"], category),
                "id": match["id"],
                "image": image_path.relative_to(FRONTEND).as_posix(),
            }
        )
    return entries


def main() -> None:
    manifest = {
        "maices": read_category("maices", FRONTEND / "maices" / "images"),
        "teocintles": read_category("teocintles", FRONTEND / "maices" / "teocintles"),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {OUTPUT.relative_to(ROOT)} ({sum(map(len, manifest.values()))} entries)")


if __name__ == "__main__":
    main()