"""
Pack 53: Black Ice Tier II + Shadow Contingency - API router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.blackice.schemas import *
from app.blackice import service as svc

router = APIRouter(prefix="/blackice", tags=["blackice"])

@router.post("/protocol", response_model=ProtocolOut)
def create_protocol(body: ProtocolIn, db: Session = Depends(get_db)):
    r = svc.create_protocol(db, body.name, body.level, body.description)
    return ProtocolOut.model_validate(r)

@router.get("/protocols", response_model=list[ProtocolOut])
def list_protocols(db: Session = Depends(get_db)):
    return [ProtocolOut.model_validate(p) for p in svc.list_protocols(db)]

@router.post("/event", response_model=EventOut)
def add_event(body: EventIn, db: Session = Depends(get_db)):
    r = svc.add_event(db, body.protocol_id, body.event_type, body.details)
    return EventOut.model_validate(r)

@router.post("/keycheck", response_model=KeyCheckOut)
def add_key_check(body: KeyCheckIn, db: Session = Depends(get_db)):
    r = svc.add_key_check(db, body.protocol_id, body.checklist_item)
    return KeyCheckOut.model_validate(r)

@router.post("/keycheck/{check_id}/checked", response_model=KeyCheckOut)
def set_key_checked(check_id: int, db: Session = Depends(get_db)):
    r = svc.set_key_checked(db, check_id)
    if not r: raise HTTPException(404, "Check not found")
    return KeyCheckOut.model_validate(r)

@router.post("/continuity", response_model=ContinuityOut)
def add_continuity(body: ContinuityIn, db: Session = Depends(get_db)):
    r = svc.add_continuity(db, body.protocol_id, body.min_hours, body.alert_channel, body.notes)
    return ContinuityOut.model_validate(r)

@router.get("/protocols/status")
def protocols_status(db: Session = Depends(get_db)):
    return svc.protocols_status(db)
