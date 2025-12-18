#!/usr/bin/env python
"""
Plan overlap checker.
Usage:
    python tools/check_overlap.py path/to/plan_a.jsonl path/to/plan_b.jsonl
Reports whether any axis_id+slots combination overlaps.
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
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    a = Path(sys.argv[1])
    b = Path(sys.argv[2])
    if not a.exists() or not b.exists():
        print("One of the plan files does not exist.")
        sys.exit(1)
    keys_a = load_keys(a)
    keys_b = load_keys(b)
    overlap = keys_a & keys_b
    print(f"A keys: {len(keys_a)}, B keys: {len(keys_b)}, overlap: {len(overlap)}")
    if overlap:
        print("Overlapping keys (first 20):")
        for k in list(overlap)[:20]:
            print(k)


if __name__ == "__main__":
    main()
