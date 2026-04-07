from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AUDIT_DIR = BASE_DIR / "audit"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_FILE = AUDIT_DIR / "legal_send_audit.jsonl"


def write_legal_audit(event_type: str, approval_id: str, payload: dict) -> None:
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "approval_id": approval_id,
        "payload": payload,
    }
    with AUDIT_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
