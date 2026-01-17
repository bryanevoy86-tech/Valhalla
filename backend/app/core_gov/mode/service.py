from __future__ import annotations
from typing import Any, Dict
from . import store

def get() -> Dict[str, Any]:
    return store.get_state()

def set(mode: str, reason: str = "") -> Dict[str, Any]:
    return store.set_state(mode=mode, reason=reason)
