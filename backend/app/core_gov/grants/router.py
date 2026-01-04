from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core_gov.audit.audit_log import audit
from app.core_gov.followups.store import create_followup
from app.core_gov.grants.models import GrantIn, Grant
from app.core_gov.grants.store import add_grant, get_grant, list_grants
from app.core_gov.grants.proof_pack import build_proof_pack
from app.core_gov.grants.priority import rank

router = APIRouter(prefix="/grants", tags=["Core: Grants"])


@router.post("", response_model=Grant)
def create(payload: GrantIn):
    g = add_grant(payload.model_dump())
    audit("GRANT_CREATED", {"id": g["id"], "name": g["name"], "country": g.get("country")})
    return g


@router.get("")
def list_(
    q: str | None = None,
    country: str | None = None,
    province_state: str | None = None,
    category: str | None = None,
    stage: str | None = None,
    has_deadline: bool | None = None,
    limit: int = 50,
):
    return {"items": list_grants(q=q, country=country, province_state=province_state, category=category, stage=stage, has_deadline=has_deadline, limit=limit)}


@router.get("/{grant_id}")
def get_(grant_id: str):
    g = get_grant(grant_id)
    if not g:
        raise HTTPException(status_code=404, detail="Grant not found")
    return g


@router.post("/{grant_id}/proof_pack")
def proof_pack(grant_id: str):
    g = get_grant(grant_id)
    if not g:
        raise HTTPException(status_code=404, detail="Grant not found")
    return build_proof_pack(g)


class DeadlineFollowupIn(BaseModel):
    due_at_utc: str
    note: str | None = None
    priority: str = "high"


@router.post("/{grant_id}/deadline_followup")
def deadline_followup(grant_id: str, payload: DeadlineFollowupIn):
    g = get_grant(grant_id)
    if not g:
        raise HTTPException(status_code=404, detail="Grant not found")

    fu = create_followup({
        "deal_id": f"grant:{grant_id}",
        "due_at_utc": payload.due_at_utc,
        "action": "review",
        "priority": payload.priority,
        "note": payload.note or f"Grant deadline follow-up: {g.get('name')}",
        "meta": {"type": "grant", "grant_id": grant_id, "grant_name": g.get("name")},
    })
    audit("GRANT_DEADLINE_FOLLOWUP_CREATED", {"grant_id": grant_id, "followup_id": fu["id"]})
    return fu


@router.get("/rank")
def rank_grants(limit: int = 25):
    return rank(limit=limit)

