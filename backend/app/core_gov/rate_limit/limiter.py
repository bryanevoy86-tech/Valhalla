from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, Tuple

from fastapi import HTTPException, Request, status

@dataclass
class RateLimit:
    max_requests: int
    window_seconds: int

_BUCKETS: Dict[Tuple[str, str], Deque[float]] = {}

def _key(request: Request, bucket_name: str) -> Tuple[str, str]:
    # Simple IP-based key (good enough for dev + v1).
    # Later you can switch to user-id based when auth is real.
    ip = request.client.host if request.client else "unknown"
    return (bucket_name, ip)

def check_rate_limit(request: Request, bucket_name: str, rl: RateLimit) -> None:
    k = _key(request, bucket_name)
    now = time.time()
    q = _BUCKETS.setdefault(k, deque())

    # evict old
    cutoff = now - rl.window_seconds
    while q and q[0] < cutoff:
        q.popleft()

    if len(q) >= rl.max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for {bucket_name}. Try again later.",
        )

    q.append(now)
