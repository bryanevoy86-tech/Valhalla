import json
from datetime import datetime, timezone
from pathlib import Path


def log_event(event_type: str, payload: dict):
    log_dir = Path("var/jarvis_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "payload": payload,
    }

    with open(log_dir / "audit.jsonl", "a") as f:
        f.write(json.dumps(event) + "\n")
