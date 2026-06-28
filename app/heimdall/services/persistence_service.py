from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.heimdall.models.persistence import (
    HeimdallDeal,
    HeimdallBuyer,
    HeimdallTask,
    HeimdallApproval,
    HeimdallMessage,
)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def create_deal(db: Session, data: Dict[str, Any]) -> HeimdallDeal:
    deal_id = data.get("id") or _new_id("deal")
    record = HeimdallDeal(
        id=deal_id,
        state=data.get("state", "NEW_LEAD"),
        property_address=data.get("property_address"),
        data=data,
        state_history=data.get("state_history", []),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_deals(db: Session) -> List[HeimdallDeal]:
    return db.query(HeimdallDeal).order_by(HeimdallDeal.created_at.desc()).all()


def get_deal(db: Session, deal_id: str) -> Optional[HeimdallDeal]:
    return db.query(HeimdallDeal).filter(HeimdallDeal.id == deal_id).first()


def update_deal(db: Session, deal_id: str, updates: Dict[str, Any]) -> Optional[HeimdallDeal]:
    record = get_deal(db, deal_id)
    if not record:
        return None

    merged_data = {**(record.data or {}), **updates}
    record.data = merged_data
    record.state = updates.get("state", record.state)
    record.property_address = updates.get("property_address", record.property_address)
    record.state_history = updates.get("state_history", record.state_history)
    record.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(record)
    return record


def create_buyer(db: Session, data: Dict[str, Any]) -> HeimdallBuyer:
    buyer_id = data.get("id") or _new_id("buyer")
    record = HeimdallBuyer(
        id=buyer_id,
        name=data.get("name"),
        data=data,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_buyers(db: Session) -> List[HeimdallBuyer]:
    return db.query(HeimdallBuyer).order_by(HeimdallBuyer.created_at.desc()).all()


def create_task(db: Session, data: Dict[str, Any]) -> HeimdallTask:
    task_id = data.get("id") or _new_id("task")
    record = HeimdallTask(
        id=task_id,
        deal_id=data.get("deal_id"),
        title=data.get("title"),
        status=data.get("status", "OPEN"),
        priority=data.get("priority"),
        owner_role=data.get("owner_role"),
        data=data,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_tasks(db: Session, deal_id: Optional[str] = None) -> List[HeimdallTask]:
    query = db.query(HeimdallTask)
    if deal_id:
        query = query.filter(HeimdallTask.deal_id == deal_id)
    return query.order_by(HeimdallTask.created_at.desc()).all()


def create_approval(db: Session, data: Dict[str, Any]) -> HeimdallApproval:
    approval_id = data.get("id") or _new_id("approval")
    record = HeimdallApproval(
        id=approval_id,
        deal_id=data.get("deal_id"),
        status=data.get("status", "PENDING"),
        approval_type=data.get("approval_type"),
        data=data,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_approvals(db: Session) -> List[HeimdallApproval]:
    return db.query(HeimdallApproval).order_by(HeimdallApproval.created_at.desc()).all()


def update_approval(
    db: Session,
    approval_id: str,
    status: str,
    reviewed_by: str,
    notes: str = "",
) -> Optional[HeimdallApproval]:
    record = db.query(HeimdallApproval).filter(HeimdallApproval.id == approval_id).first()
    if not record:
        return None

    data = record.data or {}
    data.update({
        "status": status,
        "reviewed_by": reviewed_by,
        "reviewed_at": datetime.utcnow().isoformat(),
        "review_notes": notes,
    })

    record.status = status
    record.data = data
    record.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(record)
    return record


def create_message(db: Session, data: Dict[str, Any]) -> HeimdallMessage:
    message_id = data.get("id") or _new_id("message")
    record = HeimdallMessage(
        id=message_id,
        deal_id=data.get("deal_id"),
        recipient_type=data.get("recipient_type"),
        status=data.get("status", "DRAFT"),
        data=data,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_messages(db: Session, deal_id: Optional[str] = None) -> List[HeimdallMessage]:
    query = db.query(HeimdallMessage)
    if deal_id:
        query = query.filter(HeimdallMessage.deal_id == deal_id)
    return query.order_by(HeimdallMessage.created_at.desc()).all()


def get_message(db: Session, message_id: str) -> Optional[HeimdallMessage]:
    return db.query(HeimdallMessage).filter(HeimdallMessage.id == message_id).first()
