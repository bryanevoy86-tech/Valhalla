from __future__ import annotations

from collections import defaultdict
from typing import Callable, DefaultDict, List

Handler = Callable[[str, dict], None]


class EventBus:
    def __init__(self):
        self._subs: DefaultDict[str, List[Handler]] = defaultdict(list)

    def subscribe(self, event: str, handler: Handler):
        self._subs[event].append(handler)

    def publish(self, event: str, payload: dict):
        for h in list(self._subs.get(event, [])):
            try:
                h(event, payload)
            except Exception:
                pass


bus = EventBus()
