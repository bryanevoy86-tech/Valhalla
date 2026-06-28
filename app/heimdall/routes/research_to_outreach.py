from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.heimdall.services.research_to_outreach_orchestrator import (
    run_research_to_outreach,
)

router = APIRouter(
    prefix="/heimdall/research-to-outreach",
    tags=["Heimdall Research To Outreach"],
)


class ResearchToOutreachRequest(BaseModel):
    property_intel_id: str
    created_by: str = "heimdall"


@router.post("/run")
def research_to_outreach(
    payload: ResearchToOutreachRequest,
    db: Session = Depends(get_db),
):
    return run_research_to_outreach(
        db=db,
        property_intel_id=payload.property_intel_id,
        created_by=payload.created_by,
    )
