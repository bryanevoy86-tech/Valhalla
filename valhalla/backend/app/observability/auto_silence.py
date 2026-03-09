import os
import time

from .logging import get_logger

log = get_logger("silence")

EN = os.getenv("AUTO_SILENCE_ENABLED", "false").lower() in ("1", "true", "yes")
TTL = int(os.getenv("AUTO_SILENCE_TTL", "3600"))
_silences = {}  # id->ts


def add_silence(sid: str):
    if not EN:
        return
    _silences[sid] = time.time()


def cleanup():
    if not EN:
        return
    now = time.time()
    expired = [k for k, v in _silences.items() if now - v > TTL]
    for k in expired:
        del _silences[k]
        log.info("silence.expired", id=k)
