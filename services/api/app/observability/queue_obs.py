import os

from .logging import get_logger
from .metrics import NS, Counter, Gauge, _registry

log = get_logger("queue")

EN = os.getenv("QOBS_ENABLED", "false").lower() in ("1", "true", "yes")

DEPTH = Gauge(f"{NS}_queue_depth", "Queue depth", ["name"], registry=_registry)
ENQ = Counter(f"{NS}_queue_enqueued_total", "Jobs enqueued", ["name"], registry=_registry)
DEQ = Counter(f"{NS}_queue_dequeued_total", "Jobs dequeued", ["name"], registry=_registry)


def set_depth(name: str, n: int):
    DEPTH.labels(name=name).set(n) if EN else None


def enqueued(name: str, n: int = 1):
    ENQ.labels(name=name).inc(n) if EN else None


def dequeued(name: str, n: int = 1):
    DEQ.labels(name=name).inc(n) if EN else None
