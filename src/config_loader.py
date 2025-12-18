from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv


DEFAULT_CONFIG: Dict[str, Any] = {
    "output_dir": "./out",
    "save_thoughts": True,
    "dry_run": False,
    "retry": {"max_retries": 3, "base_delay": 2.0},
    "image_config": {"image_size": "2K"},
    "axis_ids": [
        "synesthesia",
        "biomimicry",
        "literal_interpretation",
        "macro_micro",
        "material_paradox",
        "glitch_contradiction",
        "affordance_inversion",
        "representation_shift",
        "manufacturing_first",
        "procedural_rules",
    ],
    "bundle_ids": [
        "bio_medical",
        "food_scent_chem",
        "legal_finance",
        "infra_industrial",
        "ritual_backstage",
        "human_ops",
    ],
}


def load_env() -> None:
    """Load environment variables from .env if present."""
    load_dotenv()


def load_yaml(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path: Path | None = None) -> Dict[str, Any]:
    config_path = path or Path("config/config.yaml")
    cfg = deepcopy(DEFAULT_CONFIG)
    if config_path.exists():
        file_cfg = load_yaml(config_path)
        if isinstance(file_cfg, dict):
            cfg = deep_merge(cfg, file_cfg)
    return cfg


def require_api_key(dry_run: bool = False) -> str | None:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key and not dry_run:
        raise RuntimeError("GOOGLE_API_KEY is required. Set it in .env or environment variables.")
    return api_key
