# services/api/app/routers/document_routing.py

from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.document_route import (
    DocumentRouteCreate,
    DocumentRouteUpdateStatus,
    DocumentRouteOut,
)
from app.services.document_routing import (
    create_route,
    update_route_status,
    get_route,
    list_routes_for_deal,
    list_routes_for_professional,
    list_routes_for_contract,
)

router = APIRouter(
    prefix="/documents/routes",
    tags=["Documents", "Routing"]
)


@router.post("/", response_model=DocumentRouteOut, status_code=status.HTTP_201_CREATED)
def create_route_endpoint(payload: DocumentRouteCreate, db: Session = Depends(get_db)):
    """Create a new document route to track delivery to a professional."""
    obj = create_route(db, payload)
    return obj


@router.get("/{route_id}", response_model=DocumentRouteOut)
def get_route_endpoint(route_id: int, db: Session = Depends(get_db)):
    """Get a specific document route by ID."""
    obj = get_route(db, route_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Document route not found")
    return obj


@router.patch("/{route_id}/status", response_model=DocumentRouteOut)
def update_route_status_endpoint(
    route_id: int,
    payload: DocumentRouteUpdateStatus,
    db: Session = Depends(get_db)
):
    """Update document route status (sent → opened → acknowledged)."""
    obj = update_route_status(db, route_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Route not found")
    return obj


@router.get("/by-deal/{deal_id}", response_model=List[DocumentRouteOut])
def list_for_deal_endpoint(deal_id: int, db: Session = Depends(get_db)):
    """Get all document routes for a specific deal."""
    return list_routes_for_deal(db, deal_id)


@router.get("/by-professional/{professional_id}", response_model=List[DocumentRouteOut])
def list_for_professional_endpoint(professional_id: int, db: Session = Depends(get_db)):
    """Get all documents sent to a specific professional."""
    return list_routes_for_professional(db, professional_id)


@router.get("/by-contract/{contract_id}", response_model=List[DocumentRouteOut])
def list_for_contract_endpoint(contract_id: int, db: Session = Depends(get_db)):
    """Get all document routes associated with a specific contract."""
    return list_routes_for_contract(db, contract_id)
