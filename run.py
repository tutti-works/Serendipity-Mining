from __future__ import annotations

import argparse
import random
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from tqdm import tqdm

from src.api_client import generate_with_retry, init_client
from src.config_loader import (
    load_env,
    load_profile_config,
    load_yaml,
    require_api_key,
)
from src.data_manager import filter_plan, load_manifest_by_index, load_plan
from src.image_extractor import extract_images_from_response, extract_response_metadata
from src.output_handler import append_to_manifest, save_images, save_metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serendipity Mining image generator")
    parser.add_argument("--count", type=int, help="Generate only the first N items of the plan")
    parser.add_argument("--output", type=str, help="Output directory (default: config or ./out)")
    parser.add_argument("--axis", type=str, help="Filter by axis_id")
    parser.add_argument("--dry-run", action="store_true", help="Build prompts without calling the API or saving files")
    parser.add_argument("--no-save-thoughts", action="store_true", help="Do not save thinking images")
    parser.add_argument("--plan-path", type=str, help="Custom plan.jsonl path")
    parser.add_argument("--manifest-path", type=str, help="Custom manifest.jsonl path")
    parser.add_argument("--profile", type=str, default="3labs", help="Profile name (e.g., 3labs, 4cats)")
    parser.add_argument("--seed", type=int, help="Seed for deterministic plan/prompt generation")
    parser.add_argument("--rerun", type=int, default=0, help="Rerun N successes from manifest (optional)")
    parser.add_argument("--plan-name", type=str, default="plan", help="Plan file name without extension (default: plan)")
    parser.add_argument("--regen-plan", action="store_true", help="Force regenerate plan even if it exists")
    parser.add_argument("--exclude-plan", action="append", help="Plan name(s) to exclude (comma separated or repeatable)")
    return parser.parse_args()


def build_metadata_base(
    run_id: str,
    item: dict,
    prompt: str,
    prompt_meta: Dict[str, Any],
    image_size: str,
    profile: str,
    plan_name: str,
) -> Dict[str, Any]:
    return {
        "run_id": run_id,
        "profile": profile,
        "domain_injection": prompt_meta.get("domain_injection"),
        "plan_name": plan_name,
        "index": item["index"],
        "created_at": datetime.now().isoformat(),
        "model": "gemini-3-pro-image-preview",
        "image_resolution": image_size,
        "axis_id": item["axis_id"],
        "bundle": None,
        "domain_id": None,
        "template_text": prompt_meta.get("template_text"),
        "final_prompt": prompt,
        "hints_used": None,
        "vocab_used": item.get("slots"),
        "slots": item.get("slots"),
        "slot_tags": item.get("slot_tags"),
        "generation_type": item.get("generation_type", "standard"),
        "status": "pending",
        "excluded_plans": item.get("excluded_plans"),
    }


def handle_error_metadata(metadata: Dict[str, Any], error_info: Dict[str, Any]) -> Dict[str, Any]:
    enriched = metadata.copy()
    enriched |= {
        "status": "error",
        "image_part_index": None,
        "total_image_parts": None,
        "is_thought": None,
        "thought_images_saved": [],
        "final_image_filename": None,
        "response_metadata": None,
        "error": error_info.get("error"),
        "error_type": error_info.get("error_type"),
        "http_status": error_info.get("http_status"),
        "retry_count": error_info.get("retry_count"),
    }
    return enriched


def main() -> None:
    load_env()
    args = parse_args()
    profile = args.profile
    cfg = load_profile_config(profile)
    rng = random.Random(args.seed) if args.seed is not None else random
    domain_injection = cfg.get("domain_injection", "context_and_hints")

    output_root = Path(args.output or cfg.get("output_dir", "./out"))
    output_dir = output_root if output_root.name == profile else output_root / profile
    images_root = output_dir / "images"
    meta_root = output_dir / "meta"
    plan_name = args.plan_name
    plan_path = Path(args.plan_path) if args.plan_path else output_dir / f"{plan_name}.jsonl"
    manifest_path = Path(args.manifest_path) if args.manifest_path else output_dir / "manifest.jsonl"
    dry_run = bool(cfg.get("dry_run")) or args.dry_run
    save_thoughts = bool(cfg.get("save_thoughts", True)) and not args.no_save_thoughts
    image_size = str(cfg.get("image_config", {}).get("image_size", "2K"))
    global_suffix = str(cfg.get("global_prompt_suffix", "")).strip()

    api_key = require_api_key(dry_run=dry_run)
    client = None if dry_run else init_client(api_key)

    profile_dir = Path("profiles") / profile

    def load_with_fallback(name: str, key: str):
        prof_path = profile_dir / name
        if prof_path.exists():
            return load_yaml(prof_path).get(key, {})
        return load_yaml(f"data/{name}").get(key, {})

    vocab = load_with_fallback("vocab.yaml", "vocab")
    axis_templates = load_with_fallback("axis_templates.yaml", "axis_templates")

    axis_weights = cfg.get("axis_weights", {})
    target_count = int(cfg.get("target_count", cfg.get("standard_per_combo", 0) or 0))
    dedupe_mode = str(cfg.get("dedupe_mode", "strict"))
    tag_sampling = cfg.get("tag_sampling", {})
    sampling_controls = cfg.get("sampling_controls", {})

    # Exclude plan keys
    exclude_plan_names: list[str] = []
    if args.exclude_plan:
        for entry in args.exclude_plan:
            exclude_plan_names.extend([name.strip() for name in entry.split(",") if name.strip()])
    exclude_keys: set[str] = set()
    if exclude_plan_names and not args.regen_plan and plan_path.exists():
        print(f"[info] plan exists at {plan_path}, exclude_plan ignored (use --regen-plan to regenerate).")
    if exclude_plan_names and args.regen_plan:
        for name in exclude_plan_names:
            ex_path = output_dir / f"{name}.jsonl"
            if not ex_path.exists():
                raise FileNotFoundError(f"exclude plan not found: {ex_path}")
            lines = ex_path.read_text(encoding="utf-8").splitlines()
            for line in lines:
                if not line.strip():
                    continue
                data = json.loads(line)
                slots = data.get("slots") or {}
                key = "|".join(
                    [data.get("axis_id", "")]
                    + [f"{k}={v}" for k, v in sorted(slots.items())]
                )
                exclude_keys.add(key)

    plan = load_plan(
        plan_path,
        axis_templates,
        vocab,
        cfg.get("axis_ids", []),
        target_count,
        global_suffix,
        axis_weights,
        dedupe_mode,
        args.seed,
        profile,
        args.regen_plan,
        exclude_keys=exclude_keys,
        excluded_plans=exclude_plan_names if args.regen_plan else [],
        tag_sampling=tag_sampling,
        sampling_controls=sampling_controls,
    )
    if args.seed is not None and plan_path.exists() and not args.regen_plan:
        print(f"[info] plan exists at {plan_path}, seed {args.seed} ignored; using existing plan.")
    for item in plan:
        item.setdefault("profile", profile)
        item.setdefault("generation_type", "standard")
    plan = filter_plan(plan, axis=args.axis, bundle=None, count=args.count)

    if not plan:
        print("No plan items to process. Check filters or plan file.")
        return

    manifest_cache = load_manifest_by_index(manifest_path)

    def is_completed(meta: Dict[str, Any]) -> bool:
        if not meta:
            return False
        status = meta.get("status")
        if status == "success":
            fname = meta.get("final_image_filename")
            if fname:
                fpath = images_root / meta.get("axis_id", "") / fname
                return fpath.exists()
            return True
        # 後方互換: status 無しでも error_type が None かつ final_image_filename が存在すれば成功扱い
        if status is None and meta.get("error_type") in (None, "null"):
            fname = meta.get("final_image_filename")
            if fname:
                fpath = images_root / meta.get("axis_id", "") / fname
                return fpath.exists()
            return True
        return False

    completed_indices = {idx for idx, meta in manifest_cache.items() if is_completed(meta)}

    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    for item in tqdm(plan, desc="Generating images"):
        idx = item["index"]
        if idx in completed_indices:
            continue

        prompt = item["final_prompt"]
        prompt_meta: Dict[str, Any] = {
            "template_text": item.get("template_text"),
            "domain_injection": domain_injection,
        }

        if dry_run:
            print(f"[DRY RUN] index={idx} axis={item['axis_id']}")
            print(prompt)
            continue

        response, error_info = generate_with_retry(
            client,
            prompt,
            max_retries=int(cfg.get("retry", {}).get("max_retries", 3)),
            base_delay=float(cfg.get("retry", {}).get("base_delay", 2.0)),
            image_size=image_size,
        )

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{ts}_{idx:04d}_{item['axis_id']}"
        img_dir = images_root / item["axis_id"]
        meta_dir = meta_root / item["axis_id"]

        metadata = build_metadata_base(run_id, item, prompt, prompt_meta, image_size, profile, plan_name)

        if error_info and response is None:
            metadata = handle_error_metadata(metadata, error_info)
            save_metadata(meta_dir, base_name, metadata)
            append_to_manifest(manifest_path, metadata)
            manifest_cache[idx] = metadata
            continue

        try:
            resp_meta = extract_response_metadata(response)
            extracted = extract_images_from_response(response)
            saved_paths = save_images(extracted, img_dir, base_name, save_thoughts=save_thoughts)
            metadata |= {
                "status": "success",
                "image_part_index": extracted["final_image_index"],
                "total_image_parts": extracted["total_parts"],
                "is_thought": False,
                "thought_images_saved": [Path(p).name for p in saved_paths.get("thoughts", [])],
                "final_image_filename": saved_paths.get("final"),
                "response_metadata": resp_meta,
                "error": None,
                "error_type": None,
                "http_status": None,
                "retry_count": error_info.get("retry_count") if error_info else 0,
            }
        except ValueError as exc:
            resp_meta = extract_response_metadata(response)
            metadata = handle_error_metadata(
                metadata,
                {
                    "error": str(exc),
                    "error_type": "NO_IMAGE_DATA",
                    "http_status": None,
                    "retry_count": error_info.get("retry_count") if error_info else 0,
                },
            )
            metadata["response_metadata"] = resp_meta
        except Exception as exc:  # noqa: BLE001
            metadata = handle_error_metadata(
                metadata,
                {
                    "error": str(exc),
                    "error_type": "UNEXPECTED_ERROR",
                    "http_status": None,
                    "retry_count": error_info.get("retry_count") if error_info else 0,
                },
            )

        save_metadata(meta_dir, base_name, metadata)
        append_to_manifest(manifest_path, metadata)
        manifest_cache[idx] = metadata


if __name__ == "__main__":
    main()
