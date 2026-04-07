from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
QUEUE_DIR = BASE_DIR / "send_queue"


def get_queue_item(approval_id: str) -> dict:
    path = QUEUE_DIR / f"{approval_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Queue item not found: {approval_id}")
    return json.loads(path.read_text(encoding="utf-8"))
