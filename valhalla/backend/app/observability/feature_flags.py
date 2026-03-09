import os

from .logging import get_logger
from .metrics import NS, Counter, _registry

EN = os.getenv("FF_ENABLED", "false").lower() in ("1", "true", "yes")
log = get_logger("ff")
FF_EXPOSURES = Counter(
    f"{NS}_ff_exposures_total", "Feature flag exposures", ["flag", "variant"], registry=_registry
)
FF_DECISIONS = Counter(
    f"{NS}_ff_decisions_total",
    "Feature flag decisions",
    ["flag", "variant", "reason"],
    registry=_registry,
)


def expose(flag: str, variant: str):
    if not EN:
        return
    log.info("ff.expose", flag=flag, variant=variant)
    FF_EXPOSURES.labels(flag=flag, variant=variant).inc()


def decide(flag: str, variant: str, reason: str = "rule"):
    if not EN:
        return
    log.info("ff.decide", flag=flag, variant=variant, reason=reason)
    FF_DECISIONS.labels(flag=flag, variant=variant, reason=reason).inc()
    return variant
