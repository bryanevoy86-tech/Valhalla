"""JSON file storage for governance state persistence."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_DATA_DIR = Path("data")
DEFAULT_DATA_DIR.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict[str, Any] | None:
    """Read JSON file, return None if not found."""
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON file with automatic directory creation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
