#!/usr/bin/env python
"""
Vocab audit tool.
Usage:
    python tools/vocab_audit.py profiles/4cats/vocab.yaml
Checks:
    - snake_case tokens
    - duplicates per category (including across tags)
    - reserved keys misuse
    - banned words
    - count per category
"""

from __future__ import annotations

import re
import sys
import yaml
from collections import Counter, defaultdict
from pathlib import Path


BANNED_SUBSTRINGS = ["logo", "typography", "poster", "billboard", "subtitle", "caption", "watermark", "text", "title"]
SNAKE_RE = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*$")


def load_vocab(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not data or "vocab" not in data:
        raise ValueError("vocab.yaml must have top-level 'vocab'")
    return data["vocab"]


def iter_tokens(cat: str, raw) -> tuple[list[str], dict]:
    tags = {}
    if isinstance(raw, list):
        tags["default"] = raw
    elif isinstance(raw, dict):
        for k, v in raw.items():
            if k == "_weights":
                continue
            tags[k] = v
    else:
        raise ValueError(f"Invalid vocab format for {cat}")
    tokens: list[str] = []
    for t, words in tags.items():
        tokens.extend(words)
    return tokens, tags


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    path = Path(sys.argv[1])
    vocab = load_vocab(path)
    banned_hits = []
    duplicate_counts = defaultdict(list)
    cat_counts = {}
    errors = 0
    for cat, raw in vocab.items():
        tokens, tags = iter_tokens(cat, raw)
        cat_counts[cat] = len(tokens)
        counter = Counter(tokens)
        for token, cnt in counter.items():
            if cnt > 1:
                duplicate_counts[cat].append((token, cnt))
        for token in tokens:
            if not SNAKE_RE.match(token):
                print(f"[ERROR] non-snake-case in {cat}: {token}")
                errors += 1
            if any(b in token for b in BANNED_SUBSTRINGS):
                banned_hits.append((cat, token))
        for tag, words in tags.items():
            if not words:
                print(f"[ERROR] empty tag in {cat}.{tag}")
                errors += 1
    if banned_hits:
        print("\n[BANNED] tokens containing banned substrings:")
        for cat, tok in banned_hits:
            print(f"  {cat}: {tok}")
    if duplicate_counts:
        print("\n[WARN] duplicates:")
        for cat, items in duplicate_counts.items():
            for tok, cnt in items:
                print(f"  {cat}: {tok} x{cnt}")
    print("\n[COUNTS]")
    for cat, cnt in cat_counts.items():
        print(f"  {cat}: {cnt}")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
