from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException

from .schemas import PartnerCreate, PartnerListResponse, NoteCreate, DashboardResponse
from . import service
from .notes import add as add_note, list_notes

router = APIRouter(prefix="/core/partners", tags=["core-partners"])


@router.post("")
def create_partner(payload: PartnerCreate):
    try:
        return service.create_partner(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=PartnerListResponse)
def list_partners(status: Optional[str] = None, partner_type: Optional[str] = None, tier: Optional[str] = None):
    return {"items": service.list_partners(status=status, partner_type=partner_type, tier=tier)}


@router.get("/{partner_id}")
def get_partner(partner_id: str):
    p = service.get_partner(partner_id)
    if not p:
        raise HTTPException(status_code=404, detail="partner not found")
    return p


@router.patch("/{partner_id}")
def patch_partner(partner_id: str, patch: Dict[str, Any]):
    try:
        return service.patch_partner(partner_id, patch)
    except KeyError:
        raise HTTPException(status_code=404, detail="partner not found")


@router.post("/notes")
def create_note(payload: NoteCreate):
    try:
        return service.create_note(payload.model_dump())
    except KeyError:
        raise HTTPException(status_code=404, detail="partner not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/notes/list")
def list_notes(partner_id: Optional[str] = None, visibility: Optional[str] = None):
    return {"items": service.list_notes(partner_id=partner_id, visibility=visibility)}


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard():
    return service.dashboard()

@router.post("/{partner_id}/note")
def add_partner_note(partner_id: str, text: str):
    return add_note(partner_id=partner_id, text=text)

@router.get("/{partner_id}/partner_notes")
def get_partner_notes(partner_id: str, limit: int = 50):
    return {"items": list_notes(partner_id=partner_id, limit=limit)}
