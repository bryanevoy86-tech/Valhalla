import asyncio, logging, json
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy import create_engine, text
import httpx
from app.core.settings import settings

logger = logging.getLogger("valhalla")

async def ping(msg: dict):
    if not settings.notify_url:
        logger.warning("SLA breach: %s", msg); return
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            await c.post(settings.notify_url, json=msg)
    except Exception:
        logger.exception("notify failed")

async def run():
    engine = create_engine(settings.database_url, future=True)
    while True:
        try:
            with engine.begin() as conn:
                rows = conn.execute(text("""
                    SELECT id, status, sla_expires_at
                    FROM leads
                    WHERE sla_expires_at IS NOT NULL
                      AND sla_expires_at < NOW()
                      AND status NOT IN ('closed','dead')
                    ORDER BY sla_expires_at ASC
                    LIMIT 20
                """)).mappings().all()
            for r in rows:
                await ping({"type":"SLA_BREACH","lead_id":r["id"],"status":r["status"],"sla":r["sla_expires_at"].isoformat()})
        except Exception:
            logger.exception("sla worker loop error")
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(run())
