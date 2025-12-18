from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Set

from random import Random


def weighted_choice(items: List[str], weights: List[float], rng: Random) -> str:
    assert len(items) == len(weights)
    total = sum(weights)
    if total <= 0:
        return rng.choice(items)
    r = rng.uniform(0, total)
    cum = 0.0
    for item, w in zip(items, weights):
        cum += w
        if r <= cum:
            return item
    return items[-1]


def dedupe_key(axis_id: str, slots: Dict[str, str]) -> str:
    parts = [axis_id] + [f"{k}={v}" for k, v in sorted(slots.items())]
    return "|".join(parts)


def create_slot_plan(
    axis_templates: Dict[str, dict],
    vocab: Dict[str, List[str]],
    axis_ids: List[str],
    target_count: int,
    global_suffix: str,
    axis_weights: Dict[str, float] | None,
    dedupe_mode: str,
    seed: int | None,
    profile: str,
) -> List[dict]:
    rng = Random(seed) if seed is not None else Random()
    plan: List[dict] = []
    seen: Set[str] = set()

    weights = []
    for ax in axis_ids:
        weights.append(float(axis_weights.get(ax, 1.0) if axis_weights else 1.0))

    idx = 0
    while len(plan) < target_count:
        axis_id = weighted_choice(axis_ids, weights, rng)
        tmpl = axis_templates[axis_id]
        placeholders = tmpl.get("placeholders") or []
        slots: Dict[str, str] = {}
        for ph in placeholders:
            words = vocab.get(ph, [])
            if not words:
                raise ValueError(f"Vocab missing for placeholder {ph}")
            slots[ph] = rng.choice(words)

        key = dedupe_key(axis_id, slots)
        if dedupe_mode == "strict" and key in seen:
            continue
        seen.add(key)

        prompt_body = tmpl["template"].format(context="", h1="", h2="", **slots)
        final_prompt = f"{prompt_body} {global_suffix}".strip()

        plan.append(
            {
                "index": idx,
                "profile": profile,
                "axis_id": axis_id,
                "slots": slots,
                "final_prompt": final_prompt,
                "seed_used": seed,
                "generation_type": "standard",
            }
        )
        idx += 1
    return plan


def save_plan(plan: List[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(item, ensure_ascii=False) for item in plan]
    path.write_text("\n".join(lines), encoding="utf-8")


def load_plan(
    path: Path,
    axis_templates: Dict[str, dict],
    vocab: Dict[str, List[str]],
    axis_ids: List[str],
    target_count: int,
    global_suffix: str,
    axis_weights: Dict[str, float] | None,
    dedupe_mode: str,
    seed: int | None,
    profile: str,
    regen_plan: bool,
) -> List[dict]:
    if path.exists() and not regen_plan:
        raw = path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in raw if line.strip()]
    plan = create_slot_plan(
        axis_templates,
        vocab,
        axis_ids,
        target_count,
        global_suffix,
        axis_weights,
        dedupe_mode,
        seed,
        profile,
    )
    save_plan(plan, path)
    return plan


def load_manifest_indices(path: Path) -> Set[int]:
    if not path.exists():
        return set()
    indices: Set[int] = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                indices.add(int(data["index"]))
            except Exception:
                continue
    return indices


def load_manifest_by_index(path: Path) -> Dict[int, dict]:
    if not path.exists():
        return {}
    mapping: Dict[int, dict] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                mapping[int(data["index"])] = data
            except Exception:
                continue
    return mapping


def filter_plan(
    plan: List[dict],
    axis: str | None = None,
    bundle: str | None = None,
    count: int | None = None,
) -> List[dict]:
    filtered = []
    for item in plan:
        if axis and item["axis_id"] != axis:
            continue
        if bundle and item.get("bundle") != bundle:
            continue
        filtered.append(item)
        if count is not None and len(filtered) >= count:
            break
    return filtered


def find_domain(domains_by_bundle: Dict[str, List[dict]], bundle: str, domain_id: str) -> dict | None:
    for domain in domains_by_bundle.get(bundle, []):
        if domain["domain_id"] == domain_id:
            return domain
    return None
