import hashlib
import json
import os

from .logging import get_logger

log = get_logger("drift")

EN = os.getenv("DRIFT_ENABLED", "false").lower() in ("1", "true", "yes")
STATE = "/data/config_hash.json"


def _capture_env() -> dict:
    # choose a stable subset
    keys = [
        k
        for k in os.environ.keys()
        if k.startswith(
            (
                "LOG_",
                "OTEL_",
                "VECTOR_",
                "SLO_",
                "CANARY_",
                "BG_",
                "SCRUB_",
                "RETENTION_",
                "AM_",
                "PROM_",
            )
        )
    ]
    return {k: os.getenv(k) for k in sorted(keys)}


def check():
    if not EN:
        return
    cur = _capture_env()
    h = hashlib.sha256(json.dumps(cur, sort_keys=True).encode()).hexdigest()
    prev = {}
    if os.path.exists(STATE):
        try:
            prev = json.load(open(STATE))
        except Exception:
            prev = {}
    if prev.get("hash") != h:
        log.warn("config.drift", old=prev.get("hash"), new=h)
        json.dump({"hash": h, "snapshot": cur}, open(STATE, "w"))
