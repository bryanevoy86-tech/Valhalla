from sqlalchemy.orm import Session

from app.models.event_log import EventLog
from app.models.notification_bridge import NotificationPreference
from app.models.notification_orchestrator import NotificationLog, NotificationTemplate


def test_notification_bridge_counts_attempts_without_claiming_unavailable_delivery(deal_client):
    client, engine = deal_client
    for model in (EventLog, NotificationPreference, NotificationLog, NotificationTemplate):
        model.__table__.create(engine)
    with Session(engine) as db:
        event = EventLog(event_type="test_receipt", entity_type="deal", title="Local fixture")
        db.add_all([
            event, NotificationTemplate(key="receipt-test", channel_key="email", body="Event {{title}}"),
            NotificationPreference(user_id=7, event_type="test_receipt", is_enabled=True,
                                   channel_key="email", template_key="receipt-test"),
        ])
        db.commit()
        event_id = event.id
    result = client.post(f"/notification-bridge/dispatch/{event_id}", params={"user_ids": 7})
    assert result.status_code == 200, result.text
    assert result.json()["notifications_created"] == 1
    assert result.json()["recipients"] == []
    with Session(engine) as db:
        attempt = db.query(NotificationLog).one()
        assert attempt.body == "Event Local fixture"
        assert attempt.status == "failed"
        assert attempt.sent_at is None
        assert attempt.error_message == "Notification transport is not configured"
