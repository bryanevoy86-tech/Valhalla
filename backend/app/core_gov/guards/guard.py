from __future__ import annotations

import logging

logger = logging.getLogger("valhalla.guards")

class GuardViolation(RuntimeError):
    pass

def require(condition: bool, message: str, **meta) -> None:
    if not condition:
        logger.error("GUARD_VIOLATION %s meta=%s", message, meta)
        raise GuardViolation(message)

def forbid(condition: bool, message: str, **meta) -> None:
    if condition:
        logger.error("GUARD_FORBIDDEN %s meta=%s", message, meta)
        raise GuardViolation(message)
