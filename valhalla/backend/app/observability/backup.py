import os
import time

from .logging import get_logger
from .metrics import NS, Counter, Gauge, _registry

EN = os.getenv("BACKUP_ENABLED", "false").lower() in ("1", "true", "yes")
log = get_logger("backup")

RUNS = Counter(f"{NS}_backup_runs_total", "Backup runs", ["kind", "status"], registry=_registry)
BYTES = Counter(f"{NS}_backup_bytes_total", "Backup bytes", ["kind"], registry=_registry)
DUR_S = Gauge(
    f"{NS}_backup_last_seconds",
    "Last backup duration seconds",
    ["kind", "status"],
    registry=_registry,
)


class BackupTimer:
    def __init__(self, kind: str):
        self.kind = kind
        self.t0 = None

    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, et, ev, tb):
        dur = time.perf_counter() - self.t0
        ok = "OK" if et is None else "ERROR"
        if EN:
            RUNS.labels(kind=self.kind, status=ok).inc()
            DUR_S.labels(kind=self.kind, status=ok).set(dur)
        if et:
            log.error("backup.error", kind=self.kind, err=str(ev))
        return False


def add_bytes(kind: str, n: int):
    if EN:
        BYTES.labels(kind=kind).inc(n)
