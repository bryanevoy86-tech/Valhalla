from __future__ import annotations

from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/autopay_guides", tags=["core-autopay-guides"])

@router.post("")
def create(provider: str, country: str = "CA", steps: list[str] = None, proof_pack: list[str] = None, notes: str = ""):
    try:
        return service.create(provider=provider, country=country, steps=steps or [], proof_pack=proof_pack or [], notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/seed")
def seed():
    return service.seed_defaults()

@router.get("")
def list_items(country: str = "", q: str = "", status: str = "active"):
    return {"items": service.list_items(country=country, q=q, status=status)}
