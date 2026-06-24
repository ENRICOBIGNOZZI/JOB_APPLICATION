from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

DEFAULT_TARGETS = Path("configs/targets.yaml")
DEFAULT_PROFILE = Path("configs/profile.yaml")


def load_yaml(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {p}")
    with p.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {p}")
    return data


def load_targets(path: str | Path = DEFAULT_TARGETS) -> dict[str, Any]:
    return load_yaml(path)


def load_profile(path: str | Path = DEFAULT_PROFILE) -> dict[str, Any]:
    return load_yaml(path)
