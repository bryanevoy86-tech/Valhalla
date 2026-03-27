import os

import httpx

from .logging import get_logger

EN = os.getenv("WARMER_ENABLED", "false").lower() in ("1", "true", "yes")
PATHS = [p.strip() for p in os.getenv("WARMER_PATHS", "").split(",") if p.strip()]
log = get_logger("warmer")


async def run(base="http://localhost:8000"):
    if not EN:
        return
    async with httpx.AsyncClient(timeout=10) as cli:
        for p in PATHS:
            try:
                r = await cli.get(base + p)
                log.info("warmer.hit", path=p, code=r.status_code)
            except Exception as e:
                log.error("warmer.fail", path=p, err=str(e))
