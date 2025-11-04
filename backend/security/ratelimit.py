from __future__ import annotations

import asyncio
import os
import time
from typing import Dict, Tuple

try:
    import redis.asyncio as aioredis
except Exception:
    aioredis = None

WINDOWS = {
    "min": 60,
    "sec": 1,
}


def _parse_limit(spec: str) -> Tuple[int, int]:
    n, per = spec.split("/")
    return int(n), WINDOWS["min"] if per.startswith("min") else WINDOWS["sec"]


class MemoryBucket:
    def __init__(self):
        self.store: Dict[str, Tuple[float, float, int, int]] = {}
        self.lock = asyncio.Lock()

    async def allow(self, key: str, cap: int, window: int) -> bool:
        now = time.monotonic()
        async with self.lock:
            tokens, last, _, _ = self.store.get(key, (cap, now, cap, window))
            elapsed = max(0.0, now - last)
            refill = (elapsed / window) * cap
            tokens = min(cap, tokens + refill)
            allowed = tokens >= 1.0
            tokens = tokens - 1.0 if allowed else tokens
            self.store[key] = (tokens, now, cap, window)
            return allowed


class RedisBucket:
    LUA = """
    local key = KEYS[1]
    local cap = tonumber(ARGV[1])
    local window = tonumber(ARGV[2])
    local now = tonumber(ARGV[3])
    local state = redis.call('HMGET', key, 'tokens', 'ts')
    local tokens = tonumber(state[1])
    local ts = tonumber(state[2])

    if tokens == nil then
      tokens = cap
      ts = now
    end

    local elapsed = now - ts
    local refill = (elapsed / window) * cap
    tokens = math.min(cap, tokens + refill)
    local allowed = 0
    if tokens >= 1 then
      tokens = tokens - 1
      allowed = 1
    end

    redis.call('HMSET', key, 'tokens', tokens, 'ts', now)
    redis.call('EXPIRE', key, window)
    return allowed
    """

    def __init__(self, url: str):
        self.redis = aioredis.from_url(url, encoding="utf-8", decode_responses=True)
        self.script = self.redis.register_script(self.LUA)

    async def allow(self, key: str, cap: int, window: int) -> bool:
        now = time.monotonic()
        res = await self.script(keys=[key], args=[cap, window, now])
        return res == 1


class RateLimiter:
    def __init__(self):
        backend = os.getenv("RATE_LIMIT_BACKEND", "memory").lower()
        self.global_ip = _parse_limit(os.getenv("RL_GLOBAL_PER_IP", "300/min"))
        self.download_user = _parse_limit(os.getenv("RL_DOWNLOAD_PER_USER", "60/min"))
        self.bulk_org = _parse_limit(os.getenv("RL_BULK_ENQUEUE_PER_ORG", "10/min"))
        self.retry_user = _parse_limit(os.getenv("RL_RETRY_PER_USER", "30/min"))
        self.upload_user = _parse_limit(os.getenv("RL_UPLOAD_PER_USER", "30/min"))
        if backend == "redis" and aioredis:
            self.impl = RedisBucket(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        else:
            self.impl = MemoryBucket()

    async def check(self, key: str, cap: int, window: int) -> bool:
        return await self.impl.allow(key, cap, window)


limiter = RateLimiter()
