from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/proofpacks", tags=["core-proofpacks"])


@router.post("/autopay")
def create_autopay(obligation_id: str, bank: str = "", include_autopay_plan: bool = True):
    try:
        return service.create_autopay_proof_pack(obligation_id=obligation_id, bank=bank, include_autopay_plan=include_autopay_plan)
    except KeyError:
        raise HTTPException(status_code=404, detail="obligation not found")


@router.get("")
def list_items(obligation_id: str = ""):
    return {"items": service.list_items(obligation_id=obligation_id)}


@router.patch("/{pack_id}/attachments")
def patch_attachments(pack_id: str, attachments: List[Dict[str, Any]]):
    try:
        return service.patch_attachments(pack_id, attachments)
    except KeyError:
        raise HTTPException(status_code=404, detail="proof pack not found")
