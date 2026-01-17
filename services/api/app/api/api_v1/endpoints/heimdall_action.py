from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db

from app.models.integrity_event import IntegrityEvent
from app.models.notification import Notification
from app.models.compliance_signal import ComplianceSignal

from app.schemas.heimdall_action import HeimdallActionRequest
from app.schemas.integrity import IntegrityEventOut
from app.schemas.notifications import NotificationOut
from app.schemas.compliance import ComplianceSignalOut

router = APIRouter()


class HeimdallActionResponse(IntegrityEventOut):
    notification: Optional[NotificationOut] = None
    compliance_signal: Optional[ComplianceSignalOut] = None


@router.post("/", response_model=HeimdallActionResponse)
def heimdall_action(
    payload: HeimdallActionRequest,
    db: Session = Depends(get_db),
):
    # 1) Integrity event (always)
    integrity_obj = IntegrityEvent(
        source=payload.source,
        category=payload.category,
        action=payload.action,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        severity=payload.severity,
        message=payload.message,
        payload=payload.payload,
    )
    db.add(integrity_obj)

    created_notification = None
    created_compliance = None

    # 2) Optional notification
    if payload.notify:
        title = payload.notify_title or payload.message
        notif = Notification(
            channel=payload.notify_channel,
            audience=payload.notify_audience,
            title=title,
            message=payload.message,
            severity=payload.severity,
        )
        db.add(notif)
        created_notification = notif

    # 3) Optional compliance signal
    if payload.create_compliance_signal:
        comp_msg = payload.compliance_message or payload.message
        comp = ComplianceSignal(
            deal_id=payload.compliance_deal_id,
            source="heimdall",
            severity=payload.severity,
            code=payload.compliance_code,
            message=comp_msg,
            score=payload.compliance_score,
        )
        db.add(comp)
        created_compliance = comp

    db.commit()
    db.refresh(integrity_obj)
    if created_notification:
        db.refresh(created_notification)
    if created_compliance:
        db.refresh(created_compliance)

    resp = HeimdallActionResponse(
        id=integrity_obj.id,
        source=integrity_obj.source,
        category=integrity_obj.category,
        action=integrity_obj.action,
        entity_type=integrity_obj.entity_type,
        entity_id=integrity_obj.entity_id,
        severity=integrity_obj.severity,
        message=integrity_obj.message,
        payload=integrity_obj.payload,
        created_at=integrity_obj.created_at,
        notification=created_notification,
        compliance_signal=created_compliance,
    )
    return resp
