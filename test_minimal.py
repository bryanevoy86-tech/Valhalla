#!/usr/bin/env python
"""Minimal FastAPI test matching cone router structure."""
from fastapi import APIRouter, Depends, Request

def require_dev_key(request: Request) -> None:
    """Minimal dev key check."""
    pass

def require_other(request: Request):
    """Another dependency."""
    pass

def rate_limit(name: str, max_requests: int, window_seconds: int):
    """Minimal rate limiter."""
    def dep(request: Request):
        pass
    return Depends(dep)

router = APIRouter(prefix="/test", tags=["Test"])

@router.post("/state")
def write_state(
    reason: str,
    _key=Depends(require_dev_key),
    _sub=Depends(require_other),
    _rl=rate_limit("test", 10, 60),
):
    return {"ok": True}

print("✅ Minimal router created successfully!")
