from __future__ import annotations
from typing import Tuple
from . import store

def check(api_key: str) -> Tuple[bool, str]:
    k = (api_key or "").strip()
    if not k:
        return False, "missing api_key"
    keys = store.list_keys()
    if k not in [x.get("key") for x in keys]:
        return False, "invalid api_key"
    return True, "ok"
