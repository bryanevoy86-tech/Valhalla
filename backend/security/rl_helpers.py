from backend.security.ratelimit import limiter
from fastapi import HTTPException, Request


def client_ip(req: Request) -> str:
    return (
        (req.headers.get("x-forwarded-for") or req.client.host or "unknown").split(",")[0].strip()
    )


async def enforce_limit(key: str, cap: int, window: int, reason: str):
    ok = await limiter.check(key, cap, window)
    if not ok:
        raise HTTPException(429, f"Rate limit exceeded ({reason})")
