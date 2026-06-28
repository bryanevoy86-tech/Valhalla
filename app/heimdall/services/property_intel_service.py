from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.heimdall.models.property_intel import HeimdallPropertyIntel
from app.heimdall.education.property_intelligence_engine import (
    build_property_research_plan,
    score_property_distress_signal,
    build_owner_outreach_research_packet,
)
from app.heimdall.services.property_research_task_generator import (
    generate_property_research_tasks,
)


def _new_property_id() -> str:
    return f"propintel_{uuid4().hex[:12]}"


def create_property_intel_record(
    db: Session,
    address_payload: Dict[str, Any],
    property_data: Optional[Dict[str, Any]] = None,
) -> HeimdallPropertyIntel:
    property_data = property_data or {}

    research_plan = build_property_research_plan(
        address=address_payload.get("address"),
        city=address_payload.get("city"),
        province_or_state=address_payload.get("province_or_state"),
        country=address_payload.get("country"),
    )

    distress_analysis = score_property_distress_signal(property_data)

    record = HeimdallPropertyIntel(
        id=address_payload.get("id") or _new_property_id(),
        address=address_payload.get("address"),
        city=address_payload.get("city"),
        province_or_state=address_payload.get("province_or_state"),
        country=address_payload.get("country"),
        research_status="RESEARCH_REQUIRED",
        distress_score=distress_analysis.get("property_distress_score", 0),
        lead_lane=distress_analysis.get("lane", "UNSCORED"),
        ownership_verified=not distress_analysis.get("ownership_verification_required", True),
        outreach_allowed=distress_analysis.get("outreach_allowed", False),
        raw_address_payload=address_payload,
        property_data=property_data,
        research_plan=research_plan,
        distress_analysis=distress_analysis,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    # Auto-generate research tasks for this property
    generate_property_research_tasks(
        db=db,
        property_intel_id=record.id,
        created_by=address_payload.get("created_by", "heimdall"),
    )

    return record


def list_property_intel_records(db: Session) -> List[HeimdallPropertyIntel]:
    return db.query(HeimdallPropertyIntel).order_by(HeimdallPropertyIntel.created_at.desc()).all()


def get_property_intel_record(db: Session, record_id: str) -> Optional[HeimdallPropertyIntel]:
    return db.query(HeimdallPropertyIntel).filter(HeimdallPropertyIntel.id == record_id).first()


def update_property_intel_research(
    db: Session,
    record_id: str,
    property_data: Dict[str, Any],
    notes: Optional[List[Dict[str, Any]]] = None,
) -> Optional[HeimdallPropertyIntel]:
    record = get_property_intel_record(db, record_id)

    if not record:
        return None

    address_payload = record.raw_address_payload or {}

    packet = build_owner_outreach_research_packet(
        address_payload=address_payload,
        property_data=property_data,
    )

    distress_analysis = packet.get("distress_analysis", {})

    record.property_data = {
        **(record.property_data or {}),
        **property_data,
    }

    record.distress_analysis = distress_analysis
    record.research_plan = packet.get("research_plan")
    record.distress_score = distress_analysis.get("property_distress_score", 0)
    record.lead_lane = distress_analysis.get("lane", "UNSCORED")
    record.outreach_allowed = distress_analysis.get("outreach_allowed", False)
    record.ownership_verified = not distress_analysis.get("ownership_verification_required", True)
    record.notes = (record.notes or []) + (notes or [])
    record.research_status = "RESEARCH_UPDATED"
    record.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(record)
    return record


def mark_property_ready_for_outreach(db: Session, record_id: str) -> Optional[HeimdallPropertyIntel]:
    record = get_property_intel_record(db, record_id)

    if not record:
        return None

    blockers = []

    if not record.outreach_allowed:
        blockers.append("outreach_not_allowed")

    if not record.ownership_verified:
        blockers.append("ownership_not_verified")

    if record.distress_score < 50:
        blockers.append("distress_score_below_threshold")

    if blockers:
        record.research_status = "OUTREACH_BLOCKED"
        record.notes = (record.notes or []) + [{
            "timestamp": datetime.utcnow().isoformat(),
            "type": "outreach_blocked",
            "blockers": blockers,
        }]
    else:
        record.research_status = "READY_FOR_OUTREACH"

    record.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(record)
    return record


def convert_property_to_lead_payload(record: HeimdallPropertyIntel) -> Dict[str, Any]:
    data = record.property_data or {}

    return {
        "seller_name": data.get("owner_name", "Unknown Owner"),
        "property_address": record.address,
        "reason_for_selling": data.get("distress_reason", "Driving for dollars / public record signal"),
        "timeline_to_sell": data.get("timeline_to_sell", "unknown"),
        "asking_price": data.get("asking_price", 0),
        "property_condition": data.get("property_condition", "unknown"),
        "mortgage_or_debt_issue": bool(data.get("tax_arrears_known", False)),
        "vacant_or_occupied": data.get("vacant_or_occupied", "unknown"),
        "seller_responsiveness": "unknown",
        "estimated_arv": data.get("estimated_arv"),
        "seller_authority_verified": record.ownership_verified,
        "wants_retail_price": False,
        "refuses_basic_questions": False,
        "price_flexible": False,
        "source_property_intel_id": record.id,
    }


def mark_converted_to_lead(db: Session, record_id: str) -> Optional[HeimdallPropertyIntel]:
    record = get_property_intel_record(db, record_id)

    if not record:
        return None

    record.converted_to_lead = True
    record.research_status = "CONVERTED_TO_LEAD"
    record.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(record)
    return record
