#!/usr/bin/env python
"""
Move error meta JSON files into an archive folder.
Usage:
    python tools/move_error_meta.py out/4cats/meta out/4cats/meta_errors --dry-run
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def is_error_meta(meta: dict) -> bool:
    status = meta.get("status")
    if status == "success":
        return False
    if status in ("error", "failed", "failure"):
        return True
    if meta.get("error"):
        return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Move error meta JSON files to an archive folder.")
    parser.add_argument("meta_root", type=Path, help="Meta root directory (e.g., out/4cats/meta)")
    parser.add_argument("dest_root", type=Path, help="Destination root directory (e.g., out/4cats/meta_errors)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be moved without changes")
    args = parser.parse_args()

    meta_root = args.meta_root
    dest_root = args.dest_root
    if not meta_root.exists():
        raise FileNotFoundError(f"Meta root not found: {meta_root}")

    moved = 0
    for path in meta_root.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not is_error_meta(data):
            continue
        rel = path.relative_to(meta_root)
        dest = dest_root / rel
        if args.dry_run:
            print(f"[dry-run] {path} -> {dest}")
            moved += 1
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(dest))
        moved += 1

    print(f"moved={moved}")


if __name__ == "__main__":
    main()
