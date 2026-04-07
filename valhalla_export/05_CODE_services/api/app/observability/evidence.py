import json
import os
import time

from .logging import get_logger

log = get_logger("evidence")

EN = os.getenv("EVIDENCE_ENABLED", "false").lower() in ("1", "true", "yes")
PATH = os.getenv("EVIDENCE_PATH", "/data/evidence.jsonl")


def record(kind: str, **fields):
    if not EN:
        return
    rec = {"ts": int(time.time() * 1000), "kind": kind, **fields}
    try:
        os.makedirs(os.path.dirname(PATH), exist_ok=True)
        with open(PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as e:
        log.error("evidence.error", err=str(e))
