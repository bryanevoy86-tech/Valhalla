import asyncio
import os
import random
import re

from fastapi import Request
from fastapi.responses import JSONResponse

EN = os.getenv("CHAOS_ENABLED", "false").lower() in ("1", "true", "yes")
LAT = int(os.getenv("CHAOS_LATENCY_MS", "0"))
ER = float(os.getenv("CHAOS_ERROR_RATE", "0.0"))
REX = re.compile(os.getenv("CHAOS_PATHS_REGEX", r"^/"))


async def middleware(request: Request, call_next):
    if EN and REX.search(request.url.path):
        if LAT > 0:
            await asyncio.sleep(LAT / 1000.0)
        if ER > 0 and random.random() < ER:
            return JSONResponse({"error": "chaos"}, status_code=500)
    return await call_next(request)
