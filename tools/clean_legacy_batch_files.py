#!/usr/bin/env python
"""
Remove legacy batch files without plan_name prefix.
Usage:
  python tools/clean_legacy_batch_files.py --profile 4cats_pairmix --yes
  python tools/clean_legacy_batch_files.py --profile 4cats_pairmix --dry-run
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


LEGACY_PATTERN = re.compile(r"^batch_\d{4}_.+\.(png|json)$", re.IGNORECASE)


def collect_matches(root: Path) -> list[Path]:
    matches: list[Path] = []
    if not root.exists():
        return matches
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if LEGACY_PATTERN.match(path.name):
            matches.append(path)
    return matches


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove legacy batch images/meta without plan_name prefix.")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--output", default="./out")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()

    output_root = Path(args.output)
    output_dir = output_root if output_root.name == args.profile else output_root / args.profile
    images_root = output_dir / "images"
    meta_root = output_dir / "meta"

    image_matches = collect_matches(images_root)
    meta_matches = collect_matches(meta_root)

    print(f"[found] images={len(image_matches)} meta={len(meta_matches)}")
    for path in (image_matches + meta_matches)[:10]:
        print(f"  {path}")

    if args.dry_run or not args.yes:
        print("[info] dry-run only. Use --yes to delete.")
        return

    deleted = 0
    for path in image_matches + meta_matches:
        try:
            path.unlink()
            deleted += 1
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] failed to delete {path}: {exc}")

    print(f"[done] deleted={deleted}")


if __name__ == "__main__":
    main()
