from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.services.prime_business_execution import require_owner_mandate_key
from app.services.tax_opinion_provenance import PROVENANCE_KEY, current_provenance, verify_provenance
from app.models.tax_interpretations import TaxOpinion
from app.schemas.tax_interpretations import (
    TaxOpinionCreate,
    TaxOpinionRead,
    TaxOpinionProvenanceIn,
)

def _intake_flags(flags):
    public_flags = {key: value for key, value in (flags or {}).items()
                    if key not in {PROVENANCE_KEY, "professional_opinion_provenance"}}
    return {**public_flags, "professional_signoff_verified": False, "reliance_authorized": False}


def _opinion_read(db, opinion):
    flags = _intake_flags(opinion.flags)
    provenance = current_provenance(db, opinion)
    if provenance:
        flags["professional_opinion_provenance"] = provenance
    return TaxOpinionRead.model_validate(opinion).model_copy(update={"flags": flags})


def require_opinion_schema(db: Session = Depends(get_db)):
    if not inspect(db.connection()).has_table(TaxOpinion.__tablename__):
        raise HTTPException(503, "Tax opinion storage unavailable")


router = APIRouter(prefix="/tax-bridge", tags=["Tax Interpretation Engine"],
                   dependencies=[Depends(require_prime_control_key), Depends(require_opinion_schema)])


@router.post("/opinions", response_model=TaxOpinionRead, dependencies=[Depends(require_owner_mandate_key)])
def create_tax_opinion(
    payload: TaxOpinionCreate,
    response: Response,
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store"
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
    return _opinion_read(db, opinion)


@router.get("/opinions/{opinion_id}", response_model=TaxOpinionRead)
def get_tax_opinion(
    opinion_id: UUID,
    response: Response,
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store"
    result = db.execute(
        select(TaxOpinion).where(TaxOpinion.id == opinion_id)
    )
    opinion = result.scalar_one_or_none()
    if not opinion:
        raise HTTPException(status_code=404, detail="Tax opinion not found")
    return _opinion_read(db, opinion)



@router.post("/opinions/{opinion_id}/provenance", response_model=TaxOpinionRead,
             dependencies=[Depends(require_owner_mandate_key)])
def record_opinion_provenance(opinion_id: UUID, payload: TaxOpinionProvenanceIn, response: Response,
                              db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    opinion = db.get(TaxOpinion, opinion_id, with_for_update=True)
    if opinion is None:
        raise HTTPException(404, "Tax opinion not found")
    verify_provenance(db, opinion, payload, lock=True)
    packet = payload.model_dump(mode="json")
    existing = (opinion.flags or {}).get(PROVENANCE_KEY)
    if existing is not None and existing != packet:
        raise HTTPException(409, "Opinion already has different provenance. Create a new superseding opinion.")
    if existing is None:
        opinion.flags = {**_intake_flags(opinion.flags), PROVENANCE_KEY: packet}
        db.commit()
        db.refresh(opinion)
    return _opinion_read(db, opinion)
