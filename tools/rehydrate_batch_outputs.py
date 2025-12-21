#!/usr/bin/env python
"""
Rehydrate images/meta/manifest from local batch_outputs JSONL.
Usage:
  python tools/rehydrate_batch_outputs.py --profile 4cats_pairmix --plan-name explore_pairmix_r3
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.config_loader import load_profile_config
from src.output_handler import append_to_manifest, save_images, save_metadata


def parse_batch_key(key: str) -> tuple[str | None, str | None, int | None]:
    parts = key.split(":")
    if len(parts) != 3:
        return None, None, None
    profile, plan_name, idx_str = parts
    try:
        return profile, plan_name, int(idx_str)
    except ValueError:
        return profile, plan_name, None


def decode_image_from_response(response: dict) -> bytes:
    candidates = response.get("candidates") or []
    if not candidates:
        raise ValueError("No candidates in response")
    parts = candidates[0].get("content", {}).get("parts", [])
    for part in parts:
        inline = part.get("inline_data") or part.get("inlineData")
        if inline and inline.get("data"):
            return base64.b64decode(inline["data"])
    raise ValueError("No inline image data found in response")


def build_metadata_base(
    run_id: str,
    item: dict,
    prompt: str,
    image_size: str,
    model_name: str,
    profile: str,
    plan_name: str,
    domain_injection: str,
) -> Dict[str, Any]:
    return {
        "run_id": run_id,
        "profile": profile,
        "domain_injection": domain_injection,
        "plan_name": plan_name,
        "index": item["index"],
        "created_at": datetime.now().isoformat(),
        "model": model_name,
        "image_resolution": image_size,
        "axis_id": item["axis_id"],
        "bundle": None,
        "domain_id": None,
        "template_text": item.get("template_text"),
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


def load_plan(plan_path: Path) -> dict[int, dict]:
    plan_by_index: dict[int, dict] = {}
    for line in plan_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        idx = item.get("index")
        if isinstance(idx, int):
            plan_by_index[idx] = item
    return plan_by_index


def load_latest_success(manifest_path: Path, plan_name: str) -> dict[int, str]:
    latest: dict[int, str] = {}
    if not manifest_path.exists():
        return latest
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("plan_name") != plan_name:
            continue
        if rec.get("status") != "success":
            continue
        idx = rec.get("index")
        fname = rec.get("final_image_filename")
        if isinstance(idx, int) and isinstance(fname, str):
            latest[idx] = fname
    return latest


def main() -> None:
    parser = argparse.ArgumentParser(description="Rehydrate images from local batch_outputs JSONL.")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--plan-name", required=True)
    parser.add_argument("--output-dir", default="out")
    parser.add_argument("--batch-outputs-dir", default=None)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    profile = args.profile
    plan_name = args.plan_name
    output_root = Path(args.output_dir)
    output_dir = output_root if output_root.name == profile else output_root / profile
    batch_outputs_dir = (
        Path(args.batch_outputs_dir) if args.batch_outputs_dir else output_dir / "batch_outputs"
    )
    plan_path = output_dir / f"{plan_name}.jsonl"
    manifest_path = output_dir / "manifest.jsonl"
    images_root = output_dir / "images"
    meta_root = output_dir / "meta"

    if not plan_path.exists():
        print(f"[error] plan not found: {plan_path}")
        return
    if not batch_outputs_dir.exists():
        print(f"[error] batch_outputs not found: {batch_outputs_dir}")
        return

    cfg = load_profile_config(profile)
    image_size = str(cfg.get("image_config", {}).get("image_size", "2K"))
    domain_injection = str(cfg.get("domain_injection", "context_and_hints"))
    model_name_meta = "models/gemini-3-pro-image-preview"

    plan_by_index = load_plan(plan_path)
    existing_success = load_latest_success(manifest_path, plan_name)
    base_prefix = f"batch_{plan_name}_"

    output_files = sorted(batch_outputs_dir.glob(f"{plan_name}__chunk*.jsonl"))
    if not output_files:
        print(f"[error] no batch outputs found for {plan_name}")
        return

    run_id = f"rehydrate_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    success_new = 0
    failed_new = 0
    skipped = 0
    total_lines = 0

    for out_path in output_files:
        with open(out_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                total_lines += 1
                data = json.loads(line)
                key = data.get("key")
                if not isinstance(key, str):
                    continue
                k_profile, k_plan, k_idx = parse_batch_key(key)
                if k_plan != plan_name or k_profile != profile or k_idx is None:
                    continue
                item = plan_by_index.get(k_idx)
                if not item:
                    continue
                existing_name = existing_success.get(k_idx)
                base_name = f"{base_prefix}{k_idx:04d}_{item['axis_id']}"
                img_path = images_root / item["axis_id"] / f"{base_name}.png"
                if not args.overwrite:
                    if existing_name and existing_name.startswith(base_prefix) and img_path.exists():
                        skipped += 1
                        continue
                    if img_path.exists():
                        skipped += 1
                        continue

                metadata = build_metadata_base(
                    run_id,
                    item,
                    item["final_prompt"],
                    image_size,
                    model_name_meta,
                    profile,
                    plan_name,
                    domain_injection,
                )
                metadata["batch_key"] = key
                metadata["batch_output"] = out_path.name

                if data.get("error"):
                    err = data.get("error")
                    metadata = handle_error_metadata(
                        metadata,
                        {
                            "error": err,
                            "error_type": "BATCH_ERROR",
                            "http_status": None,
                            "retry_count": 0,
                        },
                    )
                    if not args.dry_run:
                        save_metadata(meta_root / item["axis_id"], base_name, metadata)
                        append_to_manifest(manifest_path, metadata)
                    failed_new += 1
                    continue

                try:
                    img_bytes = decode_image_from_response(data.get("response") or {})
                except Exception as exc:  # noqa: BLE001
                    metadata = handle_error_metadata(
                        metadata,
                        {
                            "error": str(exc),
                            "error_type": "NO_IMAGE_DATA",
                            "http_status": None,
                            "retry_count": 0,
                        },
                    )
                    if not args.dry_run:
                        save_metadata(meta_root / item["axis_id"], base_name, metadata)
                        append_to_manifest(manifest_path, metadata)
                    failed_new += 1
                    continue

                extracted = {"final_image": img_bytes, "thought_images": []}
                if not args.dry_run:
                    saved_paths = save_images(extracted, images_root / item["axis_id"], base_name, save_thoughts=False)
                    metadata |= {
                        "status": "success",
                        "image_part_index": 0,
                        "total_image_parts": 1,
                        "is_thought": False,
                        "thought_images_saved": [],
                        "final_image_filename": saved_paths.get("final"),
                        "response_metadata": {"batch_key": key, "batch_output": out_path.name},
                        "error": None,
                        "error_type": None,
                        "http_status": None,
                        "retry_count": 0,
                    }
                    save_metadata(meta_root / item["axis_id"], base_name, metadata)
                    append_to_manifest(manifest_path, metadata)
                success_new += 1

    print(
        f"[done] outputs={len(output_files)} lines={total_lines} "
        f"new_success={success_new} new_failed={failed_new} skipped={skipped} dry_run={args.dry_run}"
    )


if __name__ == "__main__":
    main()
