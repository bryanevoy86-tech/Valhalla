from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.services.prime_business_execution import require_owner_mandate_key
from app.models.tax_interpretations import TaxOpinion
from app.schemas.tax_interpretations import (
    TaxOpinionCreate,
    TaxOpinionRead,
)

def _intake_flags(flags):
    return {**(flags or {}), "professional_signoff_verified": False, "reliance_authorized": False}


def require_opinion_schema(db: Session = Depends(get_db)):
    if not inspect(db.connection()).has_table(TaxOpinion.__tablename__):
        raise HTTPException(503, "Tax opinion storage unavailable")


router = APIRouter(prefix="/tax-bridge", tags=["Tax Interpretation Engine"],
                   dependencies=[Depends(require_prime_control_key), Depends(require_opinion_schema)])


@router.post("/opinions", response_model=TaxOpinionRead, dependencies=[Depends(require_owner_mandate_key)])
def create_tax_opinion(
    payload: TaxOpinionCreate,
    db: Session = Depends(get_db),
):
    opinion = TaxOpinion(
        jurisdiction=payload.jurisdiction,
        tax_year=payload.tax_year,
        source=payload.source,
        specialist_id=payload.specialist_id,
        case_id=payload.case_id,
        summary=payload.summary,
        details=payload.details,
        risk_level=payload.risk_level,
        flags=_intake_flags(payload.flags),
    )

    db.add(opinion)
    db.flush()

    # If this ties into a case, log it into the God Review stream
    if payload.case_id:
        from app.god.models import GodReviewEvent

        event = GodReviewEvent(
            case_id=payload.case_id,
            actor=payload.source,
            event_type="tax_opinion",
            message=payload.summary or "Tax opinion recorded",
            payload={
                "tax_opinion_id": str(opinion.id),
                "jurisdiction": payload.jurisdiction,
                "tax_year": payload.tax_year,
                "risk_level": payload.risk_level,
                "flags": opinion.flags,
            },
        )
        db.add(event)

    db.commit()
    db.refresh(opinion)
    return TaxOpinionRead.model_validate(opinion).model_copy(update={"flags": _intake_flags(opinion.flags)})


@router.get("/opinions/{opinion_id}", response_model=TaxOpinionRead)
def get_tax_opinion(
    opinion_id: UUID,
    db: Session = Depends(get_db),
):
    result = db.execute(
        select(TaxOpinion).where(TaxOpinion.id == opinion_id)
    )
    opinion = result.scalar_one_or_none()
    if not opinion:
        raise HTTPException(status_code=404, detail="Tax opinion not found")
    return TaxOpinionRead.model_validate(opinion).model_copy(update={"flags": _intake_flags(opinion.flags)})
