from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from ..storage.json_store import read_json, write_json

SESSION_PATH = Path("data") / "go_session.json"

def load_session() -> dict[str, Any] | None:
    raw = read_json(SESSION_PATH)
    if not raw:
        return None
    return raw.get("session")

def save_session(session: dict[str, Any] | None) -> None:
    write_json(SESSION_PATH, {"session": session})
