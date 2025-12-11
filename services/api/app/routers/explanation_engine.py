"""
PACK AO: Explainability Engine Router
Prefix: /explain
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.explanation_engine import ExplanationRequest, ExplanationOut
from app.services.explanation_engine import create_explanation

router = APIRouter(prefix="/explain", tags=["Explainability"])


@router.post("/", response_model=ExplanationOut)
def explanation_endpoint(
    payload: ExplanationRequest,
    db: Session = Depends(get_db),
):
    """Generate a human-readable explanation for a system decision or event."""
    return create_explanation(db, payload)
