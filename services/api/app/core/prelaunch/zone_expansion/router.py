"""Zone Expansion Engine Router"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db

from .schemas import ZoneExpansionRequest, ZoneExpansionRecommendation
from .service import get_expansion_recommendation

router = APIRouter(prefix="/zones", tags=["zones_expansion"])


@router.post(
    "/expansion/recommendation",
    response_model=ZoneExpansionRecommendation,
)
def expansion_recommendation(
    payload: ZoneExpansionRequest,
    db: Session = Depends(get_db),
):
    """Ask Heimdall: should we expand, and where?"""
    return get_expansion_recommendation(db, payload)
