import os

import httpx

from .logging import get_logger

log = get_logger("synthetic")

EN = os.getenv("SYN_ENABLED", "false").lower() in ("1", "true", "yes")
TARGETS = [t.strip() for t in os.getenv("SYN_TARGETS", "").split(",") if t.strip()]


async def check_url(u):
    try:
        async with httpx.AsyncClient(timeout=5) as cli:
            r = await cli.get(u)
            log.info("synthetic.ok", url=u, code=r.status_code)
    except Exception as e:
        log.error("synthetic.fail", url=u, err=str(e))


async def run():
    if not EN:
        return
    for u in TARGETS:
        await check_url(u)
