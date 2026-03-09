import json
from sqlalchemy.orm import Session
from app.providers.models import ProviderToken, ProviderWebhookEvent


def save_token(db: Session, **kw):
    tok = ProviderToken(**kw)
    db.add(tok)
    db.commit()
    db.refresh(tok)
    return tok


def list_tokens(db: Session, provider: str | None = None):
    q = db.query(ProviderToken)
    if provider:
        q = q.filter(ProviderToken.provider == provider)
    return q.order_by(ProviderToken.id.desc()).all()


def delete_token(db: Session, token_id: int):
    tok = db.query(ProviderToken).get(token_id)
    if tok:
        db.delete(tok)
        db.commit()
    return bool(tok)


def record_webhook(
    db: Session, provider: str, event_type: str, payload: dict, signature: str | None
):
    evt = ProviderWebhookEvent(
        provider=provider,
        event_type=event_type,
        payload=json.dumps(payload),
        signature=signature,
    )
    db.add(evt)
    db.commit()
    db.refresh(evt)
    return evt


def mark_processed(db: Session, event_id: int, error_msg: str | None = None):
    evt = db.query(ProviderWebhookEvent).get(event_id)
    if evt:
        evt.processed = True
        evt.error_msg = error_msg
        db.commit()
    return evt
