import os

from .metrics import NS, Counter, _registry

EN = os.getenv("CACHE_ENABLED", "false").lower() in ("1", "true", "yes")

HITS = Counter(f"{NS}_cache_hits_total", "Cache hits", ["name"], registry=_registry)
MISSES = Counter(f"{NS}_cache_misses_total", "Cache misses", ["name"], registry=_registry)


def hit(name: str):
    HITS.labels(name=name).inc() if EN else None


def miss(name: str):
    MISSES.labels(name=name).inc() if EN else None
