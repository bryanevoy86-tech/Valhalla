import hashlib
import hmac
import json
from typing import Any, Dict

import httpx
from sqlalchemy.orm import Session

from ..models.notification import Notification, OutboundEvent, UserNotifPref, WebhookEndpoint


def _topic_enabled(prefs: dict | None, topic: str, channel: str) -> bool:
    if not prefs:
        return True
    t = prefs.get(topic)
    if t is None:
        return True
    return bool(t.get(channel, True))


def notify_user(
    db: Session,
    *,
    user_id: int,
    title: str,
    body: str | None = None,
    topic: str = "general",
    org_id: int | None = None,
    channel: str = "in-app",
    meta: Dict[str, Any] | None = None,
) -> Notification:
    pref = db.query(UserNotifPref).filter(UserNotifPref.user_id == user_id).first()
    if not _topic_enabled(pref.topics if pref else None, topic, channel):
        return None
    n = Notification(
        user_id=user_id,
        org_id=org_id,
        channel=channel,
        topic=topic,
        title=title,
        body=body,
        meta=meta or {},
    )
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


def queue_webhook(db: Session, *, org_id: int | None, topic: str, payload: dict):
    evt = OutboundEvent(org_id=org_id, topic=topic, payload=payload, status="pending")
    db.add(evt)
    db.commit()
    db.refresh(evt)
    return evt


def _sign(secret: str, raw_body: bytes) -> str:
    mac = hmac.new(secret.encode("utf-8"), msg=raw_body, digestmod=hashlib.sha256).hexdigest()
    return f"sha256={mac}"


async def deliver_pending_webhooks(db: Session, *, limit: int = 25):
    rows = (
        db.query(OutboundEvent)
        .filter(OutboundEvent.status == "pending")
        .order_by(OutboundEvent.id.asc())
        .limit(limit)
        .all()
    )
    if not rows:
        return 0

    count = 0
    async with httpx.AsyncClient(timeout=10) as client:
        for ev in rows:
            endpoints = (
                db.query(WebhookEndpoint)
                .filter(WebhookEndpoint.active == True)
                .filter((WebhookEndpoint.org_id == ev.org_id) | (ev.org_id == None))
                .all()
            )
            to_send = []
            for ep in endpoints:
                if ep.topics and (ev.topic not in ep.topics):
                    continue
                to_send.append(ep)

            raw = json.dumps(
                {
                    "topic": ev.topic,
                    "org_id": ev.org_id,
                    "payload": ev.payload,
                }
            ).encode("utf-8")

            ok_any = False
            last_err = None
            for ep in to_send:
                try:
                    sig = _sign(ep.secret, raw)
                    r = await client.post(
                        ep.url,
                        content=raw,
                        headers={
                            "Content-Type": "application/json",
                            "X-Valhalla-Topic": ev.topic,
                            "X-Valhalla-Signature": sig,
                        },
                    )
                    if r.status_code // 100 == 2:
                        ok_any = True
                    else:
                        last_err = f"{r.status_code} {r.text}"
                except Exception as e:
                    last_err = str(e)

            ev.attempts += 1
            if ok_any:
                ev.status = "sent"
                ev.last_error = None
            else:
                ev.status = "failed" if ev.attempts >= 3 else "pending"
                ev.last_error = last_err
            db.commit()
            count += 1
    return count
