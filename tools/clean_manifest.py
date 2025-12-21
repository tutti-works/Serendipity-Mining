#!/usr/bin/env python
"""
Clean manifest.jsonl by keeping a single best record per (plan_name, index).
Prefers success entries with existing image files and plan_name-prefixed filenames.
Creates a timestamped backup before writing.
Usage:
  python tools/clean_manifest.py --profile 4cats_pairmix --yes
  python tools/clean_manifest.py --profile 4cats_pairmix --plan-name explore_pairmix --plan-name explore_pairmix_r2 --yes
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple


def load_plan_map(plan_path: Path) -> Dict[int, dict]:
    mapping: Dict[int, dict] = {}
    if not plan_path.exists():
        return mapping
    for line in plan_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            idx = data.get("index")
            if isinstance(idx, int):
                mapping[idx] = data
        except Exception:
            continue
    return mapping


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean manifest.jsonl with best-per-index entries.")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--output", default="./out")
    parser.add_argument("--plan-name", action="append", default=[], help="Limit to plan_name(s).")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()

    output_root = Path(args.output)
    output_dir = output_root if output_root.name == args.profile else output_root / args.profile
    manifest_path = output_dir / "manifest.jsonl"
    images_root = output_dir / "images"

    if not manifest_path.exists():
        print(f"[error] manifest not found: {manifest_path}")
        return

    raw_lines = manifest_path.read_text(encoding="utf-8").splitlines()
    records: list[dict] = []
    for line in raw_lines:
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except Exception:
            continue

    plan_names = set(args.plan_name) if args.plan_name else {r.get("plan_name") for r in records if r.get("plan_name")}
    plan_maps: Dict[str, Dict[int, dict]] = {}
    for plan_name in plan_names:
        plan_path = output_dir / f"{plan_name}.jsonl"
        plan_maps[plan_name] = load_plan_map(plan_path)

    best: Dict[Tuple[str, int], Tuple[int, int, dict]] = {}
    skipped_missing_image = 0
    for order, rec in enumerate(records):
        plan_name = rec.get("plan_name")
        if plan_name not in plan_names:
            continue
        idx = rec.get("index")
        if not isinstance(idx, int):
            continue
        axis_id = rec.get("axis_id") or ""
        plan_map = plan_maps.get(plan_name, {})
        axis_match = bool(plan_map and idx in plan_map and plan_map[idx].get("axis_id") == axis_id)
        status = rec.get("status") or ""

        if status == "success":
            fname = rec.get("final_image_filename")
            if not fname:
                skipped_missing_image += 1
                continue
            img_path = images_root / axis_id / fname
            if not img_path.exists():
                skipped_missing_image += 1
                continue
            preferred = fname.startswith(f"batch_{plan_name}_")
            score = 10 + (5 if preferred else 0) + (1 if axis_match else 0)
        elif status in ("error", "failed", "failure") or rec.get("error"):
            score = 2 + (1 if axis_match else 0)
        else:
            score = 1 + (1 if axis_match else 0)

        key = (plan_name, idx)
        prev = best.get(key)
        if not prev or score > prev[0] or (score == prev[0] and order > prev[1]):
            best[key] = (score, order, rec)

    cleaned = [entry[2] for entry in sorted(best.values(), key=lambda x: (x[2].get("plan_name", ""), x[2].get("index", 0)))]

    print(
        f"[summary] total_lines={len(raw_lines)} parsed={len(records)} kept={len(cleaned)} "
        f"skipped_missing_image={skipped_missing_image}"
    )
    if args.dry_run or not args.yes:
        print("[info] dry-run only. Use --yes to write cleaned manifest.")
        return

    backup_path = manifest_path.with_suffix(f".jsonl.bak_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
    manifest_path.rename(backup_path)
    manifest_path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in cleaned) + "\n", encoding="utf-8")
    print(f"[done] backup={backup_path.name} written={manifest_path}")


if __name__ == "__main__":
    main()
