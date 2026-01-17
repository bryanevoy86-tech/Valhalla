# services/api/app/services/document_routing.py

from __future__ import annotations

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.document_route import DocumentRoute
from app.schemas.document_route import (
    DocumentRouteCreate,
    DocumentRouteUpdateStatus,
)


def create_route(db: Session, payload: DocumentRouteCreate) -> DocumentRoute:
    """Create a new document route to track delivery to a professional."""
    obj = DocumentRoute(
        deal_id=payload.deal_id,
        professional_id=payload.professional_id,
        document_type=payload.document_type,
        storage_url=payload.storage_url,
        contract_id=payload.contract_id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_route_status(
    db: Session,
    route_id: int,
    payload: DocumentRouteUpdateStatus
) -> Optional[DocumentRoute]:
    """Update document route status and auto-timestamp transitions."""
    obj = db.query(DocumentRoute).filter(DocumentRoute.id == route_id).first()
    if not obj:
        return None

    obj.status = payload.status
    now = datetime.utcnow()

    # Auto-timestamp status transitions
    if payload.status == "opened" and obj.opened_at is None:
        obj.opened_at = now
    if payload.status == "acknowledged" and obj.acknowledged_at is None:
        obj.acknowledged_at = now

    db.commit()
    db.refresh(obj)
    return obj


def get_route(db: Session, route_id: int) -> Optional[DocumentRoute]:
    """Get a specific document route by ID."""
    return db.query(DocumentRoute).filter(DocumentRoute.id == route_id).first()


def list_routes_for_deal(db: Session, deal_id: int) -> List[DocumentRoute]:
    """Get all document routes for a specific deal."""
    return db.query(DocumentRoute).filter(DocumentRoute.deal_id == deal_id).all()


def list_routes_for_professional(db: Session, professional_id: int) -> List[DocumentRoute]:
    """Get all document routes sent to a specific professional."""
    return db.query(DocumentRoute).filter(
        DocumentRoute.professional_id == professional_id
    ).all()


def list_routes_for_contract(db: Session, contract_id: int) -> List[DocumentRoute]:
    """Get all document routes associated with a specific contract."""
    return db.query(DocumentRoute).filter(
        DocumentRoute.contract_id == contract_id
    ).all()
