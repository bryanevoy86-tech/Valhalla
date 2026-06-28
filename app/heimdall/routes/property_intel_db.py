from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.heimdall.services.property_intel_service import (
    create_property_intel_record,
    list_property_intel_records,
    get_property_intel_record,
    update_property_intel_research,
    mark_property_ready_for_outreach,
    convert_property_to_lead_payload,
    mark_converted_to_lead,
)

router = APIRouter(prefix="/heimdall/property-intel-db", tags=["Heimdall Property Intel DB"])


class CreatePropertyIntelRequest(BaseModel):
    address: Dict[str, Any]
    property_data: Dict[str, Any] = {}


class UpdatePropertyIntelRequest(BaseModel):
    property_data: Dict[str, Any]
    notes: Optional[List[Dict[str, Any]]] = []


def serialize_property(record):
    return {
        "id": record.id,
        "address": record.address,
        "city": record.city,
        "province_or_state": record.province_or_state,
        "country": record.country,
        "research_status": record.research_status,
        "distress_score": record.distress_score,
        "lead_lane": record.lead_lane,
        "ownership_verified": record.ownership_verified,
        "outreach_allowed": record.outreach_allowed,
        "converted_to_lead": record.converted_to_lead,
        "raw_address_payload": record.raw_address_payload,
        "property_data": record.property_data,
        "research_plan": record.research_plan,
        "distress_analysis": record.distress_analysis,
        "notes": record.notes,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }


@router.post("/records")
def create_record(payload: CreatePropertyIntelRequest, db: Session = Depends(get_db)):
    record = create_property_intel_record(
        db=db,
        address_payload=payload.address,
        property_data=payload.property_data,
    )
    return serialize_property(record)


@router.get("/records")
def list_records(db: Session = Depends(get_db)):
    return [serialize_property(record) for record in list_property_intel_records(db)]


@router.get("/records/{record_id}")
def get_record(record_id: str, db: Session = Depends(get_db)):
    record = get_property_intel_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Property intel record not found")
    return serialize_property(record)


@router.patch("/records/{record_id}/research")
def update_research(record_id: str, payload: UpdatePropertyIntelRequest, db: Session = Depends(get_db)):
    record = update_property_intel_research(
        db=db,
        record_id=record_id,
        property_data=payload.property_data,
        notes=payload.notes,
    )

    if not record:
        raise HTTPException(status_code=404, detail="Property intel record not found")

    return serialize_property(record)


@router.post("/records/{record_id}/ready-for-outreach")
def ready_for_outreach(record_id: str, db: Session = Depends(get_db)):
    record = mark_property_ready_for_outreach(db, record_id)

    if not record:
        raise HTTPException(status_code=404, detail="Property intel record not found")

    return serialize_property(record)


@router.post("/records/{record_id}/lead-payload")
def lead_payload(record_id: str, db: Session = Depends(get_db)):
    record = get_property_intel_record(db, record_id)

    if not record:
        raise HTTPException(status_code=404, detail="Property intel record not found")

    if record.research_status != "READY_FOR_OUTREACH":
        return {
            "allowed": False,
            "reason": "Property is not ready for outreach.",
            "research_status": record.research_status,
            "distress_score": record.distress_score,
            "ownership_verified": record.ownership_verified,
            "outreach_allowed": record.outreach_allowed,
        }

    lead = convert_property_to_lead_payload(record)
    mark_converted_to_lead(db, record_id)

    return {
        "allowed": True,
        "lead": lead,
    }
