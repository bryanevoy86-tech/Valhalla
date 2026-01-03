from __future__ import annotations

from app.core_gov.cone.models import ConeBand
try:
    from app.core_gov.cone.engine_registry import ENGINE_REGISTRY
except (ImportError, AttributeError):
    ENGINE_REGISTRY = {}

try:
    from app.core_gov.config.store import load_thresholds
except (ImportError, AttributeError):
    def load_thresholds():
        return None

try:
    from app.core_gov.capital.store import load_usage
except (ImportError, AttributeError):
    def load_usage():
        return None


def _safe_engine_registry() -> dict:
    """
    Returns registry in a stable shape even if internal representation changes.
    """
    reg = {}
    try:
        for k, v in ENGINE_REGISTRY.items():
            # v may be dict or dataclass-like
            if isinstance(v, dict):
                reg[k] = v
            else:
                reg[k] = v.__dict__
    except Exception:
        reg = {}
    return reg


def canon_snapshot() -> dict:
    thresholds = None
    try:
        th = load_thresholds()
        if th:
            thresholds = th.model_dump() if hasattr(th, 'model_dump') else th.__dict__
    except Exception:
        thresholds = None

    usage = None
    try:
        usage = load_usage()
    except Exception:
        usage = None

    # Band policy summary (high level)
    band_policy = {
        "A": {"intent": "Expansion / Normal", "notes": "Most actions allowed within caps."},
        "B": {"intent": "Caution", "notes": "Run core engines; scale opportunistic denied; reduce variance."},
        "C": {"intent": "Stabilization", "notes": "Only stabilizers + essential ops; no scaling."},
        "D": {"intent": "Survival", "notes": "Freeze expansion; preserve runway; resolve failures first."},
    }

    return {
        "canon_version": "1.0.0",
        "locked_model": "UA-1 Full Authority Aggressive (but Safe)",
        "boring_engines_locked": ["storage", "cleaning", "landscaping"],
        "engine_registry": _safe_engine_registry(),
        "band_policy": band_policy,
        "thresholds": thresholds,
        "capital_usage": usage,
        "notes": [
            "Canon is authoritative SSOT. UI should read canon rather than hardcode rules.",
            "Anything not in canon should be treated as non-existent until added.",
        ],
    }
