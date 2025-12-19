from __future__ import annotations

import argparse
import base64
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

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


def chunked(seq: List[dict], size: int) -> Iterable[Tuple[int, List[dict]]]:
    chunk_id = 0
    for i in range(0, len(seq), size):
        yield chunk_id, seq[i : i + size]
        chunk_id += 1


def parse_batch_key(key: str) -> Tuple[str | None, str | None, int | None]:
    """
    Expected format: profile:plan_name:index
    """
    parts = key.split(":")
    if len(parts) != 3:
        return None, None, None
    profile, plan_name, idx_str = parts
    try:
        return profile, plan_name, int(idx_str)
    except ValueError:
        return profile, plan_name, None


def get_state_name(batch_job: object) -> str:
    state = getattr(batch_job, "state", None) or getattr(batch_job, "status", None)
    if state is None:
        return "UNKNOWN"
    return getattr(state, "name", None) or str(state)


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
    parser.add_argument("--mode", choices=["sync", "batch"], default="sync", help="sync (default) or batch")
    parser.add_argument(
        "--batch-action", choices=["submit", "status", "collect"], help="Batch action: submit, status, collect"
    )
    parser.add_argument(
        "--batch-chunk-size",
        type=int,
        default=300,
        help="Chunk size for batch submit (default 300; smaller to avoid large files)",
    )
    parser.add_argument("--batch-force-submit", action="store_true", help="Force re-submit even if jobs exist")
    parser.add_argument(
        "--batch-mime-type",
        type=str,
        default="application/jsonl",
        help="MIME type for batch input upload (e.g., application/jsonl or text/plain)",
    )
    return parser.parse_args()


def load_jobs(jobs_path: Path) -> List[dict]:
    if not jobs_path.exists():
        return []
    jobs: List[dict] = []
    for line in jobs_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            jobs.append(json.loads(line))
        except Exception:
            continue
    return jobs


def append_job(jobs_path: Path, job: dict) -> None:
    jobs_path.parent.mkdir(parents=True, exist_ok=True)
    with open(jobs_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(job, ensure_ascii=False) + "\n")


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


def summarize_counts(plan: List[dict], manifest_cache: Dict[int, dict]) -> None:
    total = len(plan)
    success = 0
    failed = 0
    for meta in manifest_cache.values():
        status = meta.get("status")
        if status == "success":
            success += 1
        elif status in ("error", "failed", "failure"):
            failed += 1
    pending = total - success - failed
    print(f"[summary] total={total} success={success} failed={failed} pending={pending}")


def is_completed(meta: Dict[str, Any], images_root: Path) -> bool:
    if not meta:
        return False
    status = meta.get("status")
    if status == "success":
        fname = meta.get("final_image_filename")
        if fname:
            fpath = images_root / meta.get("axis_id", "") / fname
            return fpath.exists()
        return True
    # legacy fallback
    if status is None and meta.get("error_type") in (None, "null"):
        fname = meta.get("final_image_filename")
        if fname:
            fpath = images_root / meta.get("axis_id", "") / fname
            return fpath.exists()
        return True
    return False


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
    model_name = cfg.get("model", "gemini-3-pro-image-preview")

    if args.mode == "batch" and dry_run:
        raise ValueError("Batch mode does not support --dry-run.")

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
    plan_by_index = {item["index"]: item for item in plan}
    filtered_plan = filter_plan(plan, axis=args.axis, bundle=None, count=args.count)

    manifest_cache = load_manifest_by_index(manifest_path)
    completed_indices = {idx for idx, meta in manifest_cache.items() if is_completed(meta, images_root)}

    # batch mode handling
    if args.mode == "batch":
        if args.batch_action is None:
            raise ValueError("In batch mode, --batch-action is required (submit|status|collect).")
        batch_inputs_dir = output_dir / "batch_inputs"
        batch_outputs_dir = output_dir / "batch_outputs"
        jobs_path = output_dir / "batches" / f"{plan_name}.jobs.jsonl"

        if args.batch_action == "submit":
            target_plan = sorted(filtered_plan, key=lambda item: item["index"])
            if not target_plan:
                print("No plan items to submit. Check filters or plan file.")
                return
            if not any(item["index"] not in completed_indices for item in target_plan):
                print("All filtered plan items already succeeded; nothing to submit.")
                return
            existing_jobs = load_jobs(jobs_path)
            existing_keys = set()
            existing_chunk_ids = set()
            for job in existing_jobs:
                if job.get("profile") != profile or job.get("plan_name") != plan_name:
                    continue
                chunk_id = int(job.get("chunk_id", -1))
                index_range = job.get("index_range") or []
                if len(index_range) == 2:
                    existing_keys.add((chunk_id, (index_range[0], index_range[1])))
                existing_chunk_ids.add(chunk_id)

            for chunk_id, chunk_items in chunked(target_plan, max(args.batch_chunk_size, 1)):
                index_range = (chunk_items[0]["index"], chunk_items[-1]["index"])
                pending_items = [item for item in chunk_items if item["index"] not in completed_indices]
                if not pending_items:
                    print(f"[skip] chunk {chunk_id} already all success; nothing to submit.")
                    continue
                if (chunk_id, index_range) in existing_keys and not args.batch_force_submit:
                    print(
                        f"[skip] chunk {chunk_id} already submitted (jobs.jsonl). Use --batch-force-submit to resubmit."
                    )
                    continue
                if chunk_id in existing_chunk_ids and not args.batch_force_submit:
                    print(
                        f"[warn] chunk {chunk_id} exists with different index_range; submitting new job for {index_range}."
                    )
                input_path = batch_inputs_dir / f"{plan_name}__chunk{chunk_id:04d}.jsonl"
                input_path.parent.mkdir(parents=True, exist_ok=True)
                lines = []
                for it in pending_items:
                    key = f"{profile}:{plan_name}:{it['index']}"
                    req = {
                        "contents": [{"role": "user", "parts": [{"text": it["final_prompt"]}]}],
                        "generation_config": {
                            "response_modalities": ["IMAGE"],
                        },
                    }
                    lines.append(json.dumps({"key": key, "request": req}, ensure_ascii=False))
                input_path.write_text("\n".join(lines), encoding="utf-8")
                try:
                    uploaded = client.files.upload(path=str(input_path), mime_type=args.batch_mime_type)
                except Exception as exc:  # noqa: BLE001
                    print(
                        f"[error] upload failed for chunk {chunk_id}: {exc}\n"
                        "Try adjusting --batch-mime-type (e.g., text/plain)."
                    )
                    continue
                uploaded_name = getattr(uploaded, "name", None) or getattr(uploaded, "file", None)
                try:
                    batch_job = client.batches.create(
                        model=model_name,
                        src=uploaded_name,
                        config={"display_name": f"{profile}-{plan_name}-chunk{chunk_id:04d}"},
                    )
                    print(f"[info] batch create primary src={uploaded_name}")
                except Exception as exc:  # noqa: BLE001
                    try:
                        batch_job = client.batches.create(
                            model=model_name,
                            src={"file_name": uploaded_name},
                            config={"display_name": f"{profile}-{plan_name}-chunk{chunk_id:04d}"},
                        )
                        print(f"[info] batch create fallback src dict for chunk {chunk_id}")
                    except Exception as exc2:  # noqa: BLE001
                        try:
                            batch_job = client.batches.create(
                                model=model_name,
                                input=uploaded,
                                config={"display_name": f"{profile}-{plan_name}-chunk{chunk_id:04d}"},
                            )
                            print(f"[info] fallback create() signature used for chunk {chunk_id}")
                        except Exception as exc3:  # noqa: BLE001
                            print(
                                f"[error] batch create failed for chunk {chunk_id}: {exc3} (orig: {exc}/{exc2})"
                            )
                            continue
                job_rec = {
                    "profile": profile,
                    "plan_name": plan_name,
                    "chunk_id": chunk_id,
                    "index_range": [index_range[0], index_range[1]],
                    "chunk_count": len(pending_items),
                    "input_jsonl_path": str(input_path),
                    "uploaded_file_name": uploaded_name,
                    "batch_name": getattr(batch_job, "name", None),
                    "created_at": datetime.utcnow().isoformat(),
                    "model": model_name,
                    "mime_type": args.batch_mime_type,
                }
                append_job(jobs_path, job_rec)
                print(f"[submit] chunk {chunk_id} -> batch {job_rec['batch_name']}")
            return

        if args.batch_action == "status":
            jobs = load_jobs(jobs_path)
            if not jobs:
                print(f"No jobs found at {jobs_path}")
                return
            state_counts: Dict[str, int] = {}
            for job in jobs:
                bname = job.get("batch_name")
                if not bname:
                    print(f"[warn] job missing batch_name: {job}")
                    continue
                try:
                    batch_info = client.batches.get(name=bname)
                except Exception as exc:  # noqa: BLE001
                    print(f"[error] status fetch failed for {bname}: {exc}")
                    continue
                state_name = get_state_name(batch_info)
                state_counts[state_name] = state_counts.get(state_name, 0) + 1
                print(f"[status] chunk={job.get('chunk_id')} batch={bname} state={state_name}")
            if state_counts:
                summary = ", ".join(f"{k}={v}" for k, v in sorted(state_counts.items()))
                print(f"[status-summary] {summary}")
            return

        if args.batch_action == "collect":
            jobs = load_jobs(jobs_path)
            if not jobs:
                print(f"No jobs found at {jobs_path}")
                return
            run_id = f"batch_collect_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            success_new = 0
            failed_new = 0
            for job in jobs:
                bname = job.get("batch_name")
                if not bname:
                    print(f"[warn] job missing batch_name: {job}")
                    continue
                try:
                    batch_info = client.batches.get(name=bname)
                except Exception as exc:  # noqa: BLE001
                    print(f"[error] status fetch failed for {bname}: {exc}")
                    continue
                state_name = get_state_name(batch_info)
                if state_name != "JOB_STATE_SUCCEEDED":
                    print(f"[info] batch {bname} not completed (state={state_name}), skipping collect.")
                    continue
                output_ref = getattr(batch_info, "output", None)
                output_name = None
                if output_ref:
                    output_name = getattr(output_ref, "name", None) or getattr(output_ref, "file", None)
                if not output_name:
                    print(f"[warn] batch {bname} has no output reference.")
                    continue
                out_path = batch_outputs_dir / f"{plan_name}__chunk{job.get('chunk_id', 0):04d}.jsonl"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    client.files.download(name=output_name, path=str(out_path))
                except Exception as exc:  # noqa: BLE001
                    print(f"[error] download failed for {bname}: {exc}")
                    continue

                with open(out_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            data = json.loads(line)
                        except Exception:
                            continue
                        key = data.get("key", "")
                        k_profile, k_plan, k_idx = parse_batch_key(key)
                        if k_idx is None:
                            print(f"[warn] invalid key in output: {key}")
                            continue
                        if k_profile and k_profile != profile:
                            print(f"[warn] profile mismatch for key {key}, skipping")
                            continue
                        if k_plan and k_plan != plan_name:
                            print(f"[warn] plan mismatch for key {key}, skipping")
                            continue
                        item = plan_by_index.get(k_idx)
                        if not item:
                            print(f"[warn] index {k_idx} not in plan, skipping")
                            continue
                        if k_idx in completed_indices:
                            print(f"[skip] index {k_idx} already success, not overwriting.")
                            continue
                        prompt_meta: Dict[str, Any] = {
                            "template_text": item.get("template_text"),
                            "domain_injection": domain_injection,
                        }
                        metadata = build_metadata_base(
                            run_id, item, item["final_prompt"], prompt_meta, image_size, profile, plan_name
                        )
                        metadata["batch_name"] = bname
                        metadata["chunk_id"] = job.get("chunk_id")
                        metadata["batch_key"] = key
                        img_dir = images_root / item["axis_id"]
                        meta_dir = meta_root / item["axis_id"]
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
                            save_metadata(meta_dir, f"batch_{k_idx:04d}_{item['axis_id']}", metadata)
                            append_to_manifest(manifest_path, metadata)
                            manifest_cache[k_idx] = metadata
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
                            save_metadata(meta_dir, f"batch_{k_idx:04d}_{item['axis_id']}", metadata)
                            append_to_manifest(manifest_path, metadata)
                            manifest_cache[k_idx] = metadata
                            failed_new += 1
                            continue
                        extracted = {"final_image": img_bytes, "thought_images": []}
                        base_name = f"batch_{k_idx:04d}_{item['axis_id']}"
                        saved_paths = save_images(extracted, img_dir, base_name, save_thoughts=False)
                        metadata |= {
                            "status": "success",
                            "image_part_index": 0,
                            "total_image_parts": 1,
                            "is_thought": False,
                            "thought_images_saved": [],
                            "final_image_filename": saved_paths.get("final"),
                            "response_metadata": {"batch_name": bname, "key": key},
                            "error": None,
                            "error_type": None,
                            "http_status": None,
                            "retry_count": 0,
                        }
                        save_metadata(meta_dir, base_name, metadata)
                        append_to_manifest(manifest_path, metadata)
                        manifest_cache[k_idx] = metadata
                        completed_indices.add(k_idx)
                        success_new += 1
            summarize_counts(plan, manifest_cache)
            print(f"[collect] new_success={success_new} new_failed={failed_new}")
            return

        raise ValueError(f"Unsupported batch action: {args.batch_action}")

    # sync mode
    plan = filtered_plan

    if not plan:
        print("No plan items to process. Check filters or plan file.")
        return

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
