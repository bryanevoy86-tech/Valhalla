from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

from ..storage.json_store import read_json, write_json

GO_PATH = Path("data") / "go_progress.json"

def load_progress() -> dict[str, dict[str, Any]]:
    """
    Returns:
      { step_id: { "done": bool, "notes": str|None } }
    """
    raw = read_json(GO_PATH)
    if not raw:
        return {}
    progress = raw.get("progress", {})
    if isinstance(progress, dict):
        return progress
    return {}

def save_progress(progress: dict[str, dict[str, Any]]) -> None:
    write_json(GO_PATH, {"progress": progress})
