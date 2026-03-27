from __future__ import annotations
from typing import Any, Dict, Tuple

def allow_mutation(reason: str = "") -> Tuple[bool, str]:
    # v1: if explore mode, deny mutations
    try:
        from .mode import get as get_mode
        m = (get_mode().get("mode") or "execute").lower()
        if m == "explore":
            return False, "Denied in explore mode"
    except Exception:
        pass
    return True, (reason or "")
