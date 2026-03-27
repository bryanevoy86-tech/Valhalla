import os
import time

from .logging import get_logger

EN = os.getenv("AUDIT_ENABLED", "false").lower() in ("1", "true", "yes")
log = get_logger("audit")


def emit(event: str, **fields):
    if not EN:
        return
    log.info("audit." + event, **fields, ts_ms=int(time.time() * 1000))
