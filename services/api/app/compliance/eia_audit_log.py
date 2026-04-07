from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AUDIT_DIR = BASE_DIR / "audit"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_FILE = AUDIT_DIR / "eia_mode_audit.jsonl"


def write_eia_audit(event_type: str, payload: dict) -> None:
    row = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event_type": event_type,
        "payload": payload,
    }
    with AUDIT_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
