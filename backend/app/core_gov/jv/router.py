from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from .schemas import PartnerCreate, PartnerListResponse, DashboardResponse
from . import service

router = APIRouter(prefix="/core/jv", tags=["core-jv"])


@router.post("/partners")
def create_partner(payload: PartnerCreate):
    try:
        return service.create_partner(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/partners", response_model=PartnerListResponse)
def list_partners(
    status: Optional[str] = None,
    partner_type: Optional[str] = None,
    tag: Optional[str] = None,
):
    return {"items": service.list_partners(status=status, partner_type=partner_type, tag=tag)}


@router.get("/partners/{partner_id}")
def get_partner(partner_id: str):
    p = service.get_partner(partner_id)
    if not p:
        raise HTTPException(status_code=404, detail="partner not found")
    return p


@router.post("/partners/{partner_id}/link_deal")
def link_deal(
    partner_id: str,
    deal_id: str = Query(..., min_length=1),
    role: str = "jv",
    split: str = "",
    notes: str = "",
):
    try:
        return service.link_deal(partner_id=partner_id, deal_id=deal_id, role=role, split=split, notes=notes)
    except KeyError:
        raise HTTPException(status_code=404, detail="partner not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/links")
def list_links(partner_id: Optional[str] = None, deal_id: Optional[str] = None):
    return {"items": service.list_links(partner_id=partner_id, deal_id=deal_id)}


@router.get("/partners/{partner_id}/dashboard", response_model=DashboardResponse)
def dashboard(partner_id: str):
    try:
        return service.dashboard(partner_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="partner not found")
