from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Body, HTTPException
from . import service

router = APIRouter(prefix="/core/approvals", tags=["core-approvals"])

@router.post("")
def create(payload: Dict[str, Any] = Body(...)):
    try:
        return service.create(
            title=payload.get("title",""),
            action=payload.get("action",""),
            target_type=payload.get("target_type",""),
            target_id=payload.get("target_id",""),
            cone_band=payload.get("cone_band",""),
            risk=payload.get("risk","medium"),
            payload=payload.get("payload") or {},
            notes=payload.get("notes",""),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(status: str = "pending"):
    return {"items": service.list_items(status=status)}

@router.post("/{approval_id}/decide")
def decide(approval_id: str, decision: str, by: str = "owner", reason: str = ""):
    try:
        return service.decide(approval_id=approval_id, decision=decision, by=by, reason=reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError:
        raise HTTPException(status_code=404, detail="approval not found")
