from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from app.core.data_intake.models import IntakeItem
from app.core.data_intake.quarantine_store import QuarantineStore

router = APIRouter(prefix="/api/intake", tags=["intake"])
store = QuarantineStore()


class IntakeBody(BaseModel):
    item_id: str
    source: str
    entity_type: str
    payload: Dict[str, Any]
    evidence_ref: str | None = None


@router.post("")
def intake(body: IntakeBody):
    try:
        item = IntakeItem(
            item_id=body.item_id,
            source=body.source,
            entity_type=body.entity_type,
            payload=body.payload,
            evidence_ref=body.evidence_ref,
        )
        saved = store.upsert(item)
        return {"ok": True, "status": saved.status, "item": saved.__dict__}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/quarantine")
def list_quarantine(limit: int = 200):
    items = store.list(status="QUARANTINE", limit=limit)
    return {"items": [i.__dict__ for i in items]}
