import asyncio

from backend.db.webhooks_dao import get_active_webhooks
from backend.utils.webhooks import post_webhook, sign_payload
from app.core.engines.dispatch_guard import guard_outreach
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

DISPATCH_POLL_SECONDS = 3
WEBHOOK_MAX_ATTEMPTS = 6


def _next_delay(attempts: int) -> int:
    base = 10
    delay = base * (2 ** max(0, attempts - 1))
    return min(delay, 300)


async def dispatch_once(session: AsyncSession):
    guard_outreach()
    row = (
        (
            await session.execute(
                text(
                    """
      SELECT id, event_type, job_id, payload, attempts
      FROM export_events
      WHERE status='queued'
      ORDER BY created_at ASC
      FOR UPDATE SKIP LOCKED
      LIMIT 1
    """
                )
            )
        )
        .mappings()
        .first()
    )
    if not row:
        return

    event_id = row["id"]
    payload = dict(row["payload"])
    event_type = row["event_type"]
    attempts = row["attempts"]

    await session.execute(
        text("UPDATE export_events SET status='sending', updated_at=NOW() WHERE id=:id"),
        {"id": event_id},
    )
    await session.commit()

    hooks = await get_active_webhooks(session, event_type)
    if not hooks:
        await session.execute(
            text("UPDATE export_events SET status='sent', updated_at=NOW() WHERE id=:id"),
            {"id": event_id},
        )
        await session.commit()
        return

    errors = []
    for h in hooks:
        headers = sign_payload(h["secret"], {"type": event_type, "data": payload})
        ok, err = await post_webhook(h["url"], headers, {"type": event_type, "data": payload})
        if not ok:
            errors.append(f"{h['name']}: {err}")

    if not errors:
        await session.execute(
            text("UPDATE export_events SET status='sent', updated_at=NOW() WHERE id=:id"),
            {"id": event_id},
        )
        await session.commit()
        return

    attempts += 1
    if attempts >= WEBHOOK_MAX_ATTEMPTS:
        await session.execute(
            text(
                """
          UPDATE export_events
          SET status='failed', attempts=:a, last_error=:e, updated_at=NOW()
          WHERE id=:id
        """
            ),
            {"id": event_id, "a": attempts, "e": "; ".join(errors)},
        )
        await session.commit()
        return

    delay = _next_delay(attempts)
    await session.execute(
        text(
            """
      UPDATE export_events
      SET status='queued', attempts=:a, last_error=:e,
          updated_at=NOW()
      WHERE id=:id
    """
        ),
        {"id": event_id, "a": attempts, "e": "; ".join(errors)},
    )
    await session.commit()
    await asyncio.sleep(delay)


async def run_webhook_dispatcher(session_factory):
    while True:
        try:
            async with session_factory() as s:
                await dispatch_once(s)
        except Exception:
            pass
        await asyncio.sleep(DISPATCH_POLL_SECONDS)
