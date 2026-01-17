"""
Pack 53: Black Ice Tier II + Shadow Contingency - Service layer
"""
from sqlalchemy.orm import Session
from app.blackice.models import BlackIceProtocol, ContingencyEvent, KeyRotationCheck, ContinuityWindow

def create_protocol(db: Session, name: str, level: int = 2, description: str = None):
    row = BlackIceProtocol(name=name, level=level, description=description)
    db.add(row); db.commit(); db.refresh(row)
    return row

def list_protocols(db: Session):
    return db.query(BlackIceProtocol).all()

def add_event(db: Session, protocol_id: int, event_type: str, details: str = None):
    row = ContingencyEvent(protocol_id=protocol_id, event_type=event_type, details=details)
    db.add(row); db.commit(); db.refresh(row)
    return row

def add_key_check(db: Session, protocol_id: int, checklist_item: str):
    row = KeyRotationCheck(protocol_id=protocol_id, checklist_item=checklist_item, checked=False)
    db.add(row); db.commit(); db.refresh(row)
    return row

def set_key_checked(db: Session, check_id: int):
    row = db.query(KeyRotationCheck).get(check_id)
    if row:
        row.checked = True
        db.commit(); db.refresh(row)
    return row

def add_continuity(db: Session, protocol_id: int, min_hours: int = 72, alert_channel: str = "ops", notes: str = None):
    row = ContinuityWindow(protocol_id=protocol_id, min_hours=min_hours, alert_channel=alert_channel, active=True, notes=notes)
    db.add(row); db.commit(); db.refresh(row)
    return row

def protocols_status(db: Session):
    return [
        {
            "id": p.id,
            "name": p.name,
            "level": p.level,
            "active": p.active,
            "created_at": str(p.created_at),
        } for p in db.query(BlackIceProtocol).all()
    ]
