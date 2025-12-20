#!/usr/bin/env python
"""
Gemini Files API helper.
Usage:
  python tools/files_manager.py --list
  python tools/files_manager.py --delete files/xxxx --yes
  python tools/files_manager.py --delete-older-hours 48 --yes
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
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


def _parse_time(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            return None
    return None


def _format_size(num_bytes: int | None) -> str:
    if num_bytes is None:
        return "-"
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            return f"{size:.2f}{unit}"
        size /= 1024.0
    return f"{size:.2f}B"


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


def list_files(client: object) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in iter_files(client):
        name = file_name(item)
        display_name = _get_attr(item, "display_name", "displayName")
        size_bytes = _get_attr(item, "size_bytes", "sizeBytes", "size")
        create_time = _get_attr(item, "create_time", "createTime")
        expire_time = _get_attr(item, "expiration_time", "expirationTime", "expire_time", "expireTime")
        rows.append(
            {
                "name": name or "-",
                "display_name": display_name or "-",
                "size_bytes": int(size_bytes) if str(size_bytes).isdigit() else None,
                "create_time": _parse_time(create_time),
                "expiration_time": _parse_time(expire_time),
            }
        )
    return rows


def delete_file(client: object, file_id: str) -> bool:
    try:
        client.files.delete(name=file_id)
        return True
    except TypeError:
        try:
            client.files.delete(file=file_id)
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"[error] delete failed file={file_id}: {exc}")
            return False
    except Exception as exc:  # noqa: BLE001
        print(f"[error] delete failed file={file_id}: {exc}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Gemini Files API helper.")
    parser.add_argument("--list", action="store_true", help="List files (default).")
    parser.add_argument("--delete", action="append", default=[], help="Delete file id (repeatable).")
    parser.add_argument("--delete-older-hours", type=float, help="Delete files older than N hours.")
    parser.add_argument(
        "--delete-display-prefix",
        action="append",
        default=[],
        help="Delete files whose display_name starts with prefix (repeatable).",
    )
    parser.add_argument("--yes", action="store_true", help="Confirm deletion.")
    args = parser.parse_args()

    load_env()
    api_key = require_api_key(dry_run=False)
    client = init_client(api_key=api_key)

    rows = list_files(client)
    if not rows:
        print("[info] no files found.")
        return

    if not args.list and not args.delete and args.delete_older_hours is None:
        args.list = True

    if args.list:
        print("[FILES]")
        total = 0
        for row in rows:
            size_bytes = row["size_bytes"]
            if size_bytes:
                total += size_bytes
            created = row["create_time"].isoformat() if row["create_time"] else "-"
            exp = row["expiration_time"].isoformat() if row["expiration_time"] else "-"
            print(
                f"- {row['name']} | size={_format_size(size_bytes)} | created={created} | "
                f"expires={exp} | display={row['display_name']}"
            )
        print(f"[SUMMARY] count={len(rows)} total={_format_size(total)}")

    to_delete: list[str] = []
    if args.delete:
        to_delete.extend(args.delete)

    prefixes = [p for p in args.delete_display_prefix if p]
    use_time_filter = args.delete_older_hours is not None
    use_prefix_filter = bool(prefixes)
    if use_time_filter or use_prefix_filter:
        cutoff = None
        if use_time_filter:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=args.delete_older_hours)
        for row in rows:
            name = row["name"]
            if name == "-":
                continue
            if use_time_filter:
                created = row["create_time"]
                if created and created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                if not created or created >= cutoff:
                    continue
            if use_prefix_filter:
                display_name = row["display_name"]
                if display_name == "-" or not any(display_name.startswith(p) for p in prefixes):
                    continue
            to_delete.append(name)

    if to_delete:
        unique_ids = sorted(set(to_delete))
        if not args.yes:
            print("[warn] delete requested but --yes not set. Showing candidates only.")
            for file_id in unique_ids:
                print(f"- {file_id}")
            return
        for file_id in unique_ids:
            ok = delete_file(client, file_id)
            if ok:
                print(f"[deleted] {file_id}")


if __name__ == "__main__":
    main()
