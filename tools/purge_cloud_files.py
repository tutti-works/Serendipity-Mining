#!/usr/bin/env python
"""
Purge Gemini Files API inputs/outputs for specific profiles.
Usage:
  python tools/purge_cloud_files.py --profiles 3labs 4cats 4cats_pairmix --yes
  python tools/purge_cloud_files.py --profiles 4cats --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.api_client import init_client
from src.config_loader import load_env, require_api_key


def _get_attr(obj: object, *names: str) -> Any | None:
    for name in names:
        if isinstance(obj, dict) and name in obj:
            return obj[name]
        if hasattr(obj, name):
            return getattr(obj, name)
    return None


def iter_files(client: object) -> Iterable[object]:
    try:
        resp = client.files.list()
    except TypeError:
        resp = client.files.list(page_size=1000)
    if isinstance(resp, list):
        return resp
    if hasattr(resp, "__iter__"):
        return list(resp)
    files = _get_attr(resp, "files")
    if files is None:
        return []
    return files


def file_name(file_obj: object) -> str | None:
    return _get_attr(file_obj, "name", "file", "file_name", "fileName")


def resolve_output_file_name(batch_info: object) -> str | None:
    dest = _get_attr(batch_info, "dest")
    if dest:
        name = _get_attr(dest, "file_name") or _get_attr(dest, "fileName")
        if name:
            return name
    output_ref = _get_attr(batch_info, "output")
    if output_ref:
        name = _get_attr(output_ref, "name") or _get_attr(output_ref, "file")
        name = name or _get_attr(output_ref, "file_name") or _get_attr(output_ref, "fileName")
        if name:
            return name
        if isinstance(output_ref, str):
            return output_ref
    return None


def delete_file(client: object, file_id: str) -> tuple[bool, str | None]:
    candidates = [file_id]
    if file_id.startswith("files/"):
        candidates.append(file_id.replace("files/", "", 1))
    for name in candidates:
        try:
            client.files.delete(name=name)
            return True, None
        except TypeError:
            try:
                client.files.delete(file=name)
                return True, None
            except Exception as exc:  # noqa: BLE001
                last_err = str(exc)
                continue
        except Exception as exc:  # noqa: BLE001
            last_err = str(exc)
            continue
    return False, last_err if "last_err" in locals() else None


def gather_batch_outputs(client: object, output_dir: Path) -> list[tuple[str, str | None]]:
    outputs: list[tuple[str, str | None]] = []
    batches_dir = output_dir / "batches"
    if not batches_dir.exists():
        return outputs
    for jobs_path in batches_dir.glob("*.jobs.jsonl"):
        for line in jobs_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except Exception:
                continue
            bname = data.get("batch_name")
            if not bname:
                continue
            try:
                info = client.batches.get(name=bname)
            except Exception:
                continue
            out_name = resolve_output_file_name(info)
            outputs.append((bname, out_name))
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Purge Gemini files for specific profiles.")
    parser.add_argument("--profiles", nargs="+", required=True, help="Profile names.")
    parser.add_argument("--output", default="./out")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()

    load_env()
    api_key = require_api_key(dry_run=False)
    client = init_client(api_key=api_key)

    output_root = Path(args.output)
    profiles = args.profiles

    input_ids: set[str] = set()
    for item in iter_files(client):
        name = file_name(item)
        display_name = _get_attr(item, "display_name", "displayName") or ""
        if not name:
            continue
        for profile in profiles:
            prefix = f"{profile}-"
            if display_name.startswith(prefix):
                input_ids.add(name)
                break

    output_pairs: list[tuple[str, str | None]] = []
    for profile in profiles:
        output_dir = output_root if output_root.name == profile else output_root / profile
        output_pairs.extend(gather_batch_outputs(client, output_dir))

    output_ids = {out for _, out in output_pairs if out}
    all_ids = sorted(set(input_ids) | output_ids)
    print(f"[summary] inputs={len(input_ids)} outputs={len(output_ids)} total={len(all_ids)}")
    for fid in all_ids[:10]:
        print(f"  {fid}")

    if args.dry_run or not args.yes:
        print("[info] dry-run only. Use --yes to delete.")
        return

    deleted = 0
    for fid in all_ids:
        ok, err = delete_file(client, fid)
        if ok:
            deleted += 1
            print(f"[deleted] {fid}")
        else:
            if err and "NOT_FOUND" in err.upper():
                print(f"[skip] not found {fid}")
                continue
            print(f"[warn] failed to delete {fid}: {err}")
            if err and "INVALID_ARGUMENT" in err.upper() and "cannot be more than 40" in err:
                # Attempt to delete corresponding batch job (may release output file).
                for bname, out_name in output_pairs:
                    if out_name == fid:
                        try:
                            client.batches.delete(name=bname)
                            print(f"[deleted] batch {bname} (output too long to delete via Files API)")
                        except Exception as exc:  # noqa: BLE001
                            print(f"[warn] failed to delete batch {bname}: {exc}")
                        break
    print(f"[done] deleted={deleted}")


if __name__ == "__main__":
    main()
