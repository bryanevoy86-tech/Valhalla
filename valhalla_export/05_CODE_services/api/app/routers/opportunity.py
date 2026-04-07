"""
PACK CI2: Opportunity Engine Router
Prefix: /intelligence/opportunities
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.opportunity import OpportunityIn, OpportunityOut, OpportunityList
from app.services.opportunity import create_or_update_opportunity, list_opportunities

router = APIRouter(prefix="/intelligence/opportunities", tags=["Intelligence", "Opportunities"])


@router.post("/", response_model=OpportunityOut)
def upsert_opportunity_endpoint(
    payload: OpportunityIn,
    db: Session = Depends(get_db),
):
    return create_or_update_opportunity(db, payload)


@router.get("/", response_model=OpportunityList)
def list_opportunities_endpoint(
    source_type: str | None = Query(None),
    active_only: bool = Query(True),
    limit: int = Query(200, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    items = list_opportunities(db, source_type=source_type, active_only=active_only, limit=limit)
    return OpportunityList(total=len(items), items=items)
