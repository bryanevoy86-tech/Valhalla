from fastapi import APIRouter
from ..audit.audit_log import audit
from .models import LeadIn, Lead
from .store import add_lead, list_leads

router = APIRouter(prefix="/intake", tags=["Core: Intake"])

@router.post("/lead", response_model=Lead)
def create_lead(payload: LeadIn):
    lead = add_lead(payload.model_dump())
    audit("INTAKE_LEAD_CREATED", {"id": lead["id"], "source": lead.get("source"), "tags": lead.get("tags", [])})
    return lead

@router.get("/leads")
def get_leads(limit: int = 50):
    return {"items": list_leads(limit=limit)}
