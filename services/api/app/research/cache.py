import time
from typing import Any, Dict, Tuple

class TTLCache:
    def __init__(self, ttl_seconds: int = 900, max_items: int = 256):
        self.ttl = ttl_seconds
        self.max = max_items
        self._data: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str):
        now = time.time()
        if key in self._data:
            ts, val = self._data[key]
            if now - ts < self.ttl:
                return val
            self._data.pop(key, None)
        return None

    def set(self, key: str, value: Any):
        if len(self._data) >= self.max:
            # drop oldest
            oldest = sorted(self._data.items(), key=lambda kv: kv[1][0])[0][0]
            self._data.pop(oldest, None)
        self._data[key] = (time.time(), value)

    def clear(self):
        self._data.clear()
