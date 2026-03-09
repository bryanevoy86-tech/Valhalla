from __future__ import annotations

from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/jv_links", tags=["core-jv-links"])

@router.post("")
def create(deal_id: str, partner_id: str, role: str = "jv", split_pct: float = 0.0, notes: str = ""):
    try:
        return service.link(deal_id=deal_id, partner_id=partner_id, role=role, split_pct=split_pct, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_links(deal_id: str = "", partner_id: str = ""):
    return {"items": service.list_links(deal_id=deal_id, partner_id=partner_id)}

@router.get("/split_check")
def split_check(deal_id: str):
    return service.split_check(deal_id=deal_id)
