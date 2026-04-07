"""Background jobs for indexing, training, and long-running tasks."""

from typing import Dict, Callable, Any, Deque
from collections import deque
import asyncio


def run_indexing(payload: Dict) -> Dict:
    """Run a naive indexing job (synchronous stub)."""
    # TODO: offload to background worker
    return {"indexed": True, "items": len(payload.get("items", []))}


class JobQueue:
    def __init__(self) -> None:
        self.q: Deque[Callable[[], Any]] = deque()
        self.running = False

    def add(self, fn: Callable[[], Any]) -> None:
        self.q.append(fn)

    async def run_forever(self) -> None:
        self.running = True
        while self.running:
            if self.q:
                job = self.q.popleft()
                try:
                    res = job()
                    if asyncio.iscoroutine(res):
                        await res
                except Exception:
                    pass
            else:
                await asyncio.sleep(0.2)


GLOBAL_JOBS = JobQueue()
