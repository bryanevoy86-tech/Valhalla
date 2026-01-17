from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.outcomes.models import OutcomeRecord
from app.core.outcomes.store import OutcomeStore

router = APIRouter(prefix="/api/outcomes", tags=["outcomes"])
store = OutcomeStore()


class OutcomeBody(BaseModel):
    entity_type: str
    entity_id: str
    outcome: str
    reason: str
    notes: str = ""
    evidence_ref: str | None = None


@router.post("")
def record_outcome(body: OutcomeBody):
    try:
        rec = OutcomeRecord(
            entity_type=body.entity_type,
            entity_id=body.entity_id,
            outcome=body.outcome,
            reason=body.reason,
            notes=body.notes,
            evidence_ref=body.evidence_ref,
        )
        saved = store.append(rec)
        return {"ok": True, "record": saved.__dict__}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
def list_outcomes(limit: int = 200):
    return {"items": [r.__dict__ for r in store.read_all(limit=limit)]}
