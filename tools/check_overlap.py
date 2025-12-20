#!/usr/bin/env python
"""
Plan overlap checker.
Usage:
    python tools/check_overlap.py path/to/plan_a.jsonl path/to/plan_b.jsonl [path/to/plan_c.jsonl ...]
Reports whether any axis_id+slots combination overlaps across 2+ plans.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def load_keys(path: Path) -> set[str]:
    keys: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        slots = data.get("slots") or {}
        key = "|".join([data.get("axis_id", "")] + [f"{k}={v}" for k, v in sorted(slots.items())])
        keys.add(key)
    return keys


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    paths = [Path(p) for p in sys.argv[1:]]
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        print("Missing plan file(s):")
        for p in missing:
            print(f"  {p}")
        sys.exit(1)

    key_sets: list[set[str]] = []
    key_to_sources: dict[str, list[int]] = {}

    for idx, path in enumerate(paths):
        keys = load_keys(path)
        key_sets.append(keys)
        for key in keys:
            key_to_sources.setdefault(key, []).append(idx)

    print("[FILES]")
    for idx, path in enumerate(paths):
        print(f"  {idx}: {path}")

    print("[COUNTS]")
    for idx, keys in enumerate(key_sets):
        print(f"  file_{idx}: keys={len(keys)}")

    all_unique = len(key_to_sources)
    overlap_any = {k: v for k, v in key_to_sources.items() if len(v) >= 2}
    overlap_all = set.intersection(*key_sets) if key_sets else set()

    print(f"  total_unique: {all_unique}")
    print(f"  overlap_any(>=2 files): {len(overlap_any)}")
    print(f"  overlap_all(all files): {len(overlap_all)}")

    if overlap_any:
        print("Overlapping keys (first 20):")
        for k in list(overlap_any.keys())[:20]:
            sources = ",".join(str(i) for i in overlap_any[k])
            print(f"{k}  [files:{sources}]")


if __name__ == "__main__":
    main()
