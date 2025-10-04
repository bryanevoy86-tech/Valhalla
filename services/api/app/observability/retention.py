import glob
import os
import time

from .logging import get_logger

log = get_logger("retention")

EN = os.getenv("RETENTION_ENABLED", "false").lower() in ("1", "true", "yes")
LOG_PATH = os.getenv("LOG_JSON_PATH", "/data/app.jsonl")
TRACE_PATH = os.getenv("OTEL_JSON_PATH", "/data/traces.jsonl")
REPLAY_PATH = os.getenv("REPLAY_JSON_PATH", "/data/replay.jsonl")

D_LOG = int(os.getenv("RETENTION_LOG_DAYS", "14"))
D_TRACE = int(os.getenv("RETENTION_TRACE_DAYS", "7"))
D_REPLAY = int(os.getenv("RETENTION_REPLAY_DAYS", "7"))


def _purge(pattern: str, days: int):
    if not pattern or days <= 0:
        return
    cutoff = time.time() - days * 86400
    for f in glob.glob(pattern + "*"):
        try:
            if os.path.getmtime(f) < cutoff:
                log.info("retention.delete", file=f)
                os.remove(f)
        except Exception as e:
            log.error("retention.error", file=f, err=str(e))


async def run_once():
    if not EN:
        return
    _purge(LOG_PATH, D_LOG)
    _purge(TRACE_PATH, D_TRACE)
    _purge(REPLAY_PATH, D_REPLAY)
