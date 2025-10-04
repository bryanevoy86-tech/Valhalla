import os
import time

from .logging import get_logger
from .metrics import NS, Counter, Histogram, _registry

log = get_logger("db")

EN = os.getenv("DBOBS_ENABLED", "false").lower() in ("1", "true", "yes")
SLOW = float(os.getenv("DBOBS_SLOW_SEC", "0.3"))

QUERY_DUR = Histogram(
    f"{NS}_db_query_seconds", "DB query duration seconds", ["name"], registry=_registry
)
QUERY_ERR = Counter(f"{NS}_db_query_errors_total", "DB query errors", ["name"], registry=_registry)


async def run_query(name: str, exec_fn):
    if not EN:
        return await exec_fn()
    t0 = time.perf_counter()
    try:
        res = await exec_fn()
        dur = time.perf_counter() - t0
        QUERY_DUR.labels(name=name).observe(dur)
        if dur > SLOW:
            log.warn("db.slow", name=name, seconds=dur)
        return res
    except Exception as e:
        QUERY_ERR.labels(name=name).inc()
        log.error("db.error", name=name, err=str(e))
        raise
