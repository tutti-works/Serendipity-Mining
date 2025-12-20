from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Set

from random import Random
from collections import deque


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


def normalize_vocab_category(cat: str, raw) -> tuple[Dict[str, List[str]], Dict[str, float], bool]:
    """
    Returns (tag_to_words, tag_weights, is_tagged)
    raw can be list[str] (old format) or dict[tag -> list[str]/_weights].
    """
    if isinstance(raw, list):
        return {"default": raw}, {}, False
    if not isinstance(raw, dict):
        raise ValueError(f"Unsupported vocab format for category {cat}")
    weights = {}
    if "_weights" in raw:
        weights = {k: float(v) for k, v in (raw.get("_weights") or {}).items()}
    tag_to_words: Dict[str, List[str]] = {}
    for tag, words in raw.items():
        if tag == "_weights":
            continue
        if not isinstance(words, list):
            raise ValueError(f"Vocab tag {tag} in category {cat} must be a list")
        tag_to_words[tag] = words
    if not tag_to_words:
        raise ValueError(f"Vocab category {cat} has no tags/words")
    return tag_to_words, weights, True


def flatten_words(tag_to_words: Dict[str, List[str]]) -> List[str]:
    words: List[str] = []
    for lst in tag_to_words.values():
        words.extend(lst)
    return words


def create_slot_plan(
    axis_templates: Dict[str, dict],
    vocab: Dict[str, List[str]],
    axis_ids: List[str],
    target_count: int,
    global_suffix: str,
    axis_weights: Dict[str, float] | None,
    axis_distribution: str | None,
    dedupe_mode: str,
    seed: int | None,
    profile: str,
    exclude_keys: Set[str] | None = None,
    excluded_plans: List[str] | None = None,
    tag_sampling: Dict[str, object] | None = None,
    sampling_controls: Dict[str, int] | None = None,
) -> List[dict]:
    rng = Random(seed) if seed is not None else Random()
    plan: List[dict] = []
    seen: Set[str] = set()
    axis_distribution = (axis_distribution or "weighted").lower()
    exclude_keys = exclude_keys or set()
    excluded_plans = excluded_plans or []
    tag_sampling = tag_sampling or {}
    sampling_controls = sampling_controls or {}
    max_repeat_window = int(sampling_controls.get("max_repeat_window", 0))
    max_repeat_per_token = int(sampling_controls.get("max_repeat_per_token", 0))
    recent_tokens = deque(maxlen=max_repeat_window) if max_repeat_window > 0 else None
    token_counts: Dict[str, int] = {}

    # preprocess vocab categories
    vocab_struct: Dict[str, dict] = {}
    tag_cursors: Dict[str, int] = {}
    for cat, raw in vocab.items():
        tags, weights, is_tagged = normalize_vocab_category(cat, raw)
        vocab_struct[cat] = {"tags": tags, "weights": weights, "is_tagged": is_tagged}
        tag_cursors[cat] = 0

    def choose_token(cat: str) -> tuple[str, str | None]:
        cat_cfg = vocab_struct.get(cat)
        if not cat_cfg:
            raise ValueError(f"Vocab category missing: {cat}")
        tags = cat_cfg["tags"]
        weights = cat_cfg["weights"]
        is_tagged = cat_cfg["is_tagged"]
        mode = (tag_sampling.get("per_category", {}) or {}).get(cat, tag_sampling.get("mode", "off"))
        if not is_tagged:
            mode = "off"
        if mode == "uniform":
            tag_list = list(tags.keys())
            cursor = tag_cursors.get(cat, 0)
            chosen_tag = tag_list[cursor % len(tag_list)]
            tag_cursors[cat] = cursor + 1
            words = tags[chosen_tag]
            word = rng.choice(words)
            return word, chosen_tag
        if mode == "weighted":
            tag_list = list(tags.keys())
            tag_weights = [weights.get(t, 1.0) for t in tag_list]
            chosen_tag = weighted_choice(tag_list, tag_weights, rng)
            word = rng.choice(tags[chosen_tag])
            return word, chosen_tag
        # off
        word = rng.choice(flatten_words(tags))
        return word, None

    def should_avoid(token: str) -> bool:
        if recent_tokens is None:
            return False
        return token in recent_tokens

    weights = [float(axis_weights.get(ax, 1.0) if axis_weights else 1.0) for ax in axis_ids]

    def build_slots_for_axis(axis_id: str) -> tuple[Dict[str, str], Dict[str, str | None]]:
        tmpl = axis_templates[axis_id]
        placeholders = tmpl.get("placeholders") or []
        slots: Dict[str, str] = {}
        slot_tags: Dict[str, str | None] = {}
        for ph in placeholders:
            attempts = 0
            chosen = None
            chosen_tag = None
            while attempts < 5:
                token, ttag = choose_token(ph)
                if should_avoid(token):
                    attempts += 1
                    continue
                chosen = token
                chosen_tag = ttag
                break
            if chosen is None:
                token, ttag = choose_token(ph)
                chosen = token
                chosen_tag = ttag
            slots[ph] = chosen
            if chosen_tag:
                slot_tags[ph] = chosen_tag
            token_counts[chosen] = token_counts.get(chosen, 0) + 1
            if recent_tokens is not None:
                recent_tokens.append(chosen)
            if max_repeat_per_token and token_counts[chosen] > max_repeat_per_token:
                print(f"[warn] token '{chosen}' exceeded max_repeat_per_token={max_repeat_per_token}")
        return slots, slot_tags

    def append_item(axis_id: str, slots: Dict[str, str], slot_tags: Dict[str, str | None], idx: int) -> None:
        tmpl = axis_templates[axis_id]
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
                "excluded_plans": excluded_plans,
                "slot_tags": slot_tags or None,
            }
        )

    idx = 0
    if axis_distribution == "balanced":
        total_weight = sum(weights)
        if total_weight <= 0:
            weights = [1.0 for _ in axis_ids]
            total_weight = sum(weights)
        raw = [target_count * w / total_weight for w in weights]
        base = [int(x) for x in raw]
        remainder = target_count - sum(base)
        if remainder > 0:
            frac = [(raw[i] - base[i], i) for i in range(len(axis_ids))]
            frac.sort(key=lambda x: (-x[0], axis_ids[x[1]]))
            for _, i in frac[:remainder]:
                base[i] += 1
        axis_queue: List[str] = []
        for axis_id, count in zip(axis_ids, base):
            axis_queue.extend([axis_id] * count)
        rng.shuffle(axis_queue)
        for axis_id in axis_queue:
            while True:
                slots, slot_tags = build_slots_for_axis(axis_id)
                key = dedupe_key(axis_id, slots)
                if key in exclude_keys:
                    continue
                if dedupe_mode == "strict" and key in seen:
                    continue
                seen.add(key)
                append_item(axis_id, slots, slot_tags, idx)
                idx += 1
                break
    else:
        while len(plan) < target_count:
            axis_id = weighted_choice(axis_ids, weights, rng)
            slots, slot_tags = build_slots_for_axis(axis_id)
            key = dedupe_key(axis_id, slots)
            if key in exclude_keys:
                continue
            if dedupe_mode == "strict" and key in seen:
                continue
            seen.add(key)
            append_item(axis_id, slots, slot_tags, idx)
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
    axis_distribution: str | None,
    dedupe_mode: str,
    seed: int | None,
    profile: str,
    regen_plan: bool,
    exclude_keys: Set[str] | None = None,
    excluded_plans: List[str] | None = None,
    tag_sampling: Dict[str, object] | None = None,
    sampling_controls: Dict[str, int] | None = None,
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
        axis_distribution,
        dedupe_mode,
        seed,
        profile,
        exclude_keys,
        excluded_plans,
        tag_sampling,
        sampling_controls,
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
