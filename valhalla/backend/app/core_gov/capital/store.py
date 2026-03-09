"""Capital usage tracker - manual tracking with caps enforcement."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

from ..storage.json_store import read_json, write_json

CAPITAL_PATH = Path("data") / "capital_usage.json"


def load_usage() -> Dict[str, float]:
    """Load capital usage from disk."""
    raw = read_json(CAPITAL_PATH)
    if not raw:
        return {}
    usage = raw.get("usage", {})
    # Ensure float values
    out: Dict[str, float] = {}
    for k, v in usage.items():
        try:
            out[k] = float(v)
        except Exception:
            out[k] = 0.0
    return out


def save_usage(usage: Dict[str, float]) -> None:
    """Save capital usage to disk."""
    write_json(CAPITAL_PATH, {"usage": usage})
