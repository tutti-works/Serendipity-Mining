from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, Iterable, List, Set


def group_domains_by_bundle(domains: Iterable[dict]) -> Dict[str, List[dict]]:
    grouped: Dict[str, List[dict]] = {}
    for domain in domains:
        grouped.setdefault(domain["bundle"], []).append(domain)
    return grouped


def create_generation_plan(
    domains_by_bundle: Dict[str, List[dict]],
    axis_ids: List[str],
    bundle_ids: List[str],
    mix_count: int = 10,
    rerun_count: int = 10,
) -> List[dict]:
    plan: List[dict] = []
    idx = 0
    # Standard 480 (10 axes x 6 bundles x 8 each)
    for axis_id in axis_ids:
        for bundle in bundle_ids:
            domains = list(domains_by_bundle[bundle])
            random.shuffle(domains)
            for i in range(8):
                domain = domains[i % len(domains)]
                plan.append(
                    {
                        "index": idx,
                        "axis_id": axis_id,
                        "bundle": bundle,
                        "domain_id": domain["domain_id"],
                        "generation_type": "standard",
                    }
                )
                idx += 1

    standard_items = [item for item in plan if item["generation_type"] == "standard"]

    # Mix 10
    for _ in range(mix_count):
        pair = random.sample(axis_ids, 2)
        bundle = random.choice(bundle_ids)
        domain = random.choice(domains_by_bundle[bundle])
        plan.append(
            {
                "index": idx,
                "axis_id": f"mix__{pair[0]}__{pair[1]}",
                "bundle": bundle,
                "domain_id": domain["domain_id"],
                "generation_type": "mix",
                "axis_pair": pair,
            }
        )
        idx += 1

    # Rerun 10
    rerun_sources = random.sample(standard_items, k=min(rerun_count, len(standard_items)))
    for src in rerun_sources:
        plan.append(
            {
                "index": idx,
                "axis_id": src["axis_id"],
                "bundle": src["bundle"],
                "domain_id": src["domain_id"],
                "generation_type": "rerun",
                "source_index": src["index"],
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
    domains_by_bundle: Dict[str, List[dict]],
    axis_ids: List[str],
    bundle_ids: List[str],
) -> List[dict]:
    if path.exists():
        raw = path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in raw if line.strip()]
    plan = create_generation_plan(domains_by_bundle, axis_ids, bundle_ids)
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
