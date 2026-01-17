"""Append-only audit log for governance decisions and state changes."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

AUDIT_PATH = Path("data") / "audit.log"


def audit(event: str, payload: dict[str, Any] | None = None) -> None:
    """Append immutable audit record to log."""
    record = {
        "ts_utc": dt.datetime.utcnow().isoformat() + "Z",
        "event": event,
        "payload": payload or {},
    }
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
