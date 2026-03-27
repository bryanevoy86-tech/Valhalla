import os
from contextvars import ContextVar

from fastapi import Request

EN = os.getenv("TENANT_TAG_ENABLED", "false").lower() in ("1", "true", "yes")
HEADER = os.getenv("TENANT_HEADER", "X-Tenant-Id")

_current = ContextVar("tenant_id", default="")


def get_tenant():
    return _current.get("")


async def middleware(request: Request, call_next):
    tid = request.headers.get(HEADER, "").strip() if EN else ""
    _current.set(tid or "")
    resp = await call_next(request)
    if tid:
        resp.headers[HEADER] = tid
    return resp
