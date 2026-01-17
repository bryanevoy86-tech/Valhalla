from ..core.events import bus
from ..services.mailer import send_email
from ..services.webhooks import send_webhook


def _on_any(event: str, payload: dict):
    send_webhook(event, payload)
    if event in {"lead.created", "deal.created", "lead.note.created"}:
        recipients = [payload.get("notify_email")] if payload.get("notify_email") else []
        if recipients:
            subj = f"[Valhalla] {event}"
            txt = f"Event: {event}\nPayload: {payload}"
            send_email(recipients, subj, txt)


def attach_event_handlers():
    for ev in [
        "lead.created",
        "deal.created",
        "lead.note.created",
        "buyer.created",
    ]:
        bus.subscribe(ev, _on_any)
