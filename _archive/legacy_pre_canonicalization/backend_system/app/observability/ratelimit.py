import os
import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse

from .metrics import NS, Counter, _registry

EN = os.getenv("RL_ENABLED", "false").lower() in ("1", "true", "yes")
MAX_PM = int(os.getenv("RL_MAX_PER_MINUTE", "600"))

HITS = Counter(f"{NS}_rl_hits_total", "Rate-limit hits", ["key"], registry=_registry)
ALLOW = Counter(f"{NS}_rl_allow_total", "Requests allowed", ["key"], registry=_registry)
BLOCK = Counter(f"{NS}_rl_block_total", "Requests blocked", ["key"], registry=_registry)

_window = defaultdict(lambda: deque())


def key_from(req: Request) -> str:
    return req.client.host or "unknown"


async def middleware(request: Request, call_next):
    if not EN:
        return await call_next(request)
    k = key_from(request)
    now = time.time()
    dq = _window[k]
    dq.append(now)
    while dq and now - dq[0] > 60:
        dq.popleft()
    if len(dq) > MAX_PM:
        BLOCK.labels(key=k).inc()
        return JSONResponse({"error": "rate_limited"}, status_code=429)
    ALLOW.labels(key=k).inc()
    return await call_next(request)
