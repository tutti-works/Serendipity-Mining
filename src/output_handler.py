from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_images(extracted: Dict[str, object], img_dir: Path, base_name: str, save_thoughts: bool = True) -> Dict[str, List[str]]:
    ensure_directory(img_dir)
    final_path = img_dir / f"{base_name}.png"
    with open(final_path, "wb") as f:
        f.write(extracted["final_image"])

    thought_paths: List[str] = []
    if save_thoughts:
        for idx, img in enumerate(extracted["thought_images"], start=1):
            thought_path = img_dir / f"{base_name}_thought_{idx:02d}.png"
            with open(thought_path, "wb") as f:
                f.write(img)
            thought_paths.append(str(thought_path))

    return {"final": str(final_path), "thoughts": thought_paths}


def save_metadata(img_dir: Path, base_name: str, metadata: Dict[str, object]) -> Path:
    ensure_directory(img_dir)
    meta_path = img_dir / f"{base_name}.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    return meta_path


def append_to_manifest(manifest_path: Path, metadata: Dict[str, object]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(metadata, ensure_ascii=False) + "\n")


def load_manifest_indices(path: Path) -> set[int]:
    from src.data_manager import load_manifest_indices as _load  # lazy import to avoid cycle

    return _load(path)


def load_manifest_by_index(path: Path) -> dict:
    from src.data_manager import load_manifest_by_index as _load  # lazy import to avoid cycle

    return _load(path)
