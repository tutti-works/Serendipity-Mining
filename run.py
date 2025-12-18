from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from tqdm import tqdm

from src.api_client import generate_with_retry, init_client
from src.config_loader import load_config, load_env, load_yaml, require_api_key
from src.data_manager import (
    find_domain,
    filter_plan,
    group_domains_by_bundle,
    load_manifest_by_index,
    load_manifest_indices,
    load_plan,
)
from src.image_extractor import extract_images_from_response, extract_response_metadata
from src.output_handler import append_to_manifest, save_images, save_metadata
from src.prompt_generator import build_mix_prompt, build_prompt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serendipity Mining image generator")
    parser.add_argument("--count", type=int, help="Generate only the first N items of the plan")
    parser.add_argument("--output", type=str, help="Output directory (default: config or ./out)")
    parser.add_argument("--axis", type=str, help="Filter by axis_id")
    parser.add_argument("--bundle", type=str, help="Filter by bundle id")
    parser.add_argument("--dry-run", action="store_true", help="Build prompts without calling the API or saving files")
    parser.add_argument("--no-save-thoughts", action="store_true", help="Do not save thinking images")
    parser.add_argument("--plan-path", type=str, help="Custom plan.jsonl path")
    parser.add_argument("--manifest-path", type=str, help="Custom manifest.jsonl path")
    return parser.parse_args()


def build_metadata_base(
    run_id: str,
    item: dict,
    domain: dict,
    prompt: str,
    prompt_meta: Dict[str, Any],
    image_size: str,
) -> Dict[str, Any]:
    return {
        "run_id": run_id,
        "index": item["index"],
        "created_at": datetime.now().isoformat(),
        "model": "gemini-3-pro-image-preview",
        "image_resolution": image_size,
        "axis_id": item["axis_id"],
        "bundle": item["bundle"],
        "domain_id": domain["domain_id"],
        "template_text": prompt_meta.get("template_text"),
        "final_prompt": prompt,
        "hints_used": prompt_meta.get("hints_used"),
        "vocab_used": prompt_meta.get("vocab_used"),
        "generation_type": item["generation_type"],
    }


def handle_error_metadata(metadata: Dict[str, Any], error_info: Dict[str, Any]) -> Dict[str, Any]:
    enriched = metadata.copy()
    enriched |= {
        "image_part_index": None,
        "total_image_parts": None,
        "is_thought": None,
        "thought_images_saved": [],
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
    cfg = load_config()

    output_dir = Path(args.output or cfg.get("output_dir", "./out"))
    plan_path = Path(args.plan_path) if args.plan_path else output_dir / "plan.jsonl"
    manifest_path = Path(args.manifest_path) if args.manifest_path else output_dir / "manifest.jsonl"
    dry_run = bool(cfg.get("dry_run")) or args.dry_run
    save_thoughts = bool(cfg.get("save_thoughts", True)) and not args.no_save_thoughts
    image_size = str(cfg.get("image_config", {}).get("image_size", "2K"))

    api_key = require_api_key(dry_run=dry_run)
    client = None if dry_run else init_client(api_key)

    domains = load_yaml("data/domains.yaml").get("domains", [])
    vocab = load_yaml("data/vocab.yaml").get("vocab", {})
    axis_templates = load_yaml("data/axis_templates.yaml").get("axis_templates", {})
    domains_by_bundle = group_domains_by_bundle(domains)

    plan = load_plan(plan_path, domains_by_bundle, cfg.get("axis_ids", []), cfg.get("bundle_ids", []))
    plan = filter_plan(plan, axis=args.axis, bundle=args.bundle, count=args.count)

    if not plan:
        print("No plan items to process. Check filters or plan file.")
        return

    completed_indices = load_manifest_indices(manifest_path)
    manifest_cache = load_manifest_by_index(manifest_path)

    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    for item in tqdm(plan, desc="Generating images"):
        idx = item["index"]
        if idx in completed_indices:
            continue

        domain = find_domain(domains_by_bundle, item["bundle"], item["domain_id"])
        if domain is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"{ts}_{idx:04d}_{item['axis_id']}_{item['bundle']}_{item['domain_id']}_error"
            error_meta = {
                "error": f"Domain not found: bundle={item['bundle']}, domain_id={item['domain_id']}",
                "error_type": "MISSING_DOMAIN",
                "http_status": None,
                "retry_count": 0,
            }
            metadata = build_metadata_base(run_id, item, {"domain_id": item["domain_id"]}, "", {}, image_size)
            metadata = handle_error_metadata(metadata, error_meta)
            save_metadata(output_dir / item["axis_id"] / item["bundle"] / item["domain_id"], base_name, metadata)
            append_to_manifest(manifest_path, metadata)
            manifest_cache[idx] = metadata
            continue

        prompt: str
        prompt_meta: Dict[str, Any]

        if item["generation_type"] == "rerun":
            source_meta = manifest_cache.get(item.get("source_index"))
            if not source_meta:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = f"{ts}_{idx:04d}_{item['axis_id']}_{item['bundle']}_{domain['domain_id']}_error"
                error_meta = {
                    "error": f"source_index {item.get('source_index')} not found for rerun",
                    "error_type": "MISSING_SOURCE",
                    "http_status": None,
                    "retry_count": 0,
                }
                metadata = build_metadata_base(run_id, item, domain, "", {}, image_size)
                metadata = handle_error_metadata(metadata, error_meta)
                save_metadata(output_dir / item["axis_id"] / item["bundle"] / domain["domain_id"], base_name, metadata)
                append_to_manifest(manifest_path, metadata)
                manifest_cache[idx] = metadata
                continue
            prompt = source_meta.get("final_prompt", "")
            prompt_meta = {
                "template_text": source_meta.get("template_text"),
                "hints_used": source_meta.get("hints_used"),
                "vocab_used": source_meta.get("vocab_used"),
            }
            if not prompt:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = f"{ts}_{idx:04d}_{item['axis_id']}_{item['bundle']}_{domain['domain_id']}_error"
                error_meta = {
                    "error": f"Empty final_prompt for source_index {item.get('source_index')}",
                    "error_type": "MISSING_SOURCE_PROMPT",
                    "http_status": None,
                    "retry_count": 0,
                }
                metadata = build_metadata_base(run_id, item, domain, prompt, prompt_meta, image_size)
                metadata = handle_error_metadata(metadata, error_meta)
                save_metadata(output_dir / item["axis_id"] / item["bundle"] / domain["domain_id"], base_name, metadata)
                append_to_manifest(manifest_path, metadata)
                manifest_cache[idx] = metadata
                continue
        elif item["generation_type"] == "mix":
            prompt, prompt_meta = build_mix_prompt(item["axis_pair"], axis_templates, domain, vocab)
        else:
            prompt, prompt_meta = build_prompt(item["axis_id"], axis_templates, domain, vocab)

        if dry_run:
            print(f"[DRY RUN] index={idx} axis={item['axis_id']} bundle={item['bundle']} domain={domain['domain_id']}")
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
        base_name = f"{ts}_{idx:04d}_{item['axis_id']}_{item['bundle']}_{domain['domain_id']}"
        img_dir = output_dir / item["axis_id"] / item["bundle"] / domain["domain_id"]

        metadata = build_metadata_base(run_id, item, domain, prompt, prompt_meta, image_size)

        if error_info and response is None:
            metadata = handle_error_metadata(metadata, error_info)
            save_metadata(img_dir, base_name, metadata)
            append_to_manifest(manifest_path, metadata)
            manifest_cache[idx] = metadata
            continue

        try:
            resp_meta = extract_response_metadata(response)
            extracted = extract_images_from_response(response)
            saved_paths = save_images(extracted, img_dir, base_name, save_thoughts=save_thoughts)
            metadata |= {
                "image_part_index": extracted["final_image_index"],
                "total_image_parts": extracted["total_parts"],
                "is_thought": False,
                "thought_images_saved": [Path(p).name for p in saved_paths.get("thoughts", [])],
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

        save_metadata(img_dir, base_name, metadata)
        append_to_manifest(manifest_path, metadata)
        manifest_cache[idx] = metadata


if __name__ == "__main__":
    main()
