# services/api/app/routers/pro_scorecard.py

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.pro_scorecard import Professional, InteractionLog, Scorecard
from app.schemas.pro_scorecard import (
    ProfessionalIn, ProfessionalOut,
    InteractionLogIn, InteractionLogOut,
    ScorecardOut
)

router = APIRouter(
    prefix="/pros/scorecard",
    tags=["Professionals", "Scorecard"]
)

# ----------------------------------------
# SCORING LOGIC
# ----------------------------------------

def compute_scores(interactions):
    if not interactions:
        return dict(
            reliability=0.0,
            communication=0.0,
            quality=0.0,
            overall=0.0
        )

    total = len(interactions)

    reliability = sum(1 for i in interactions if i.met_deadline) / total
    communication = sum(i.communication_clarity or 0 for i in interactions) / total
    quality = sum(i.deliverable_quality or 0 for i in interactions) / total

    overall = round((reliability + communication + quality) / 3, 2)

    return dict(
        reliability=round(reliability, 2),
        communication=round(communication, 2),
        quality=round(quality, 2),
        overall=overall
    )


# ----------------------------------------
# ROUTES
# ----------------------------------------

@router.post("/professionals", response_model=ProfessionalOut)
def create_professional(payload: ProfessionalIn, db: Session = Depends(get_db)):
    pro = Professional(**payload.dict())
    db.add(pro)
    db.commit()
    db.refresh(pro)

    # initialize scorecard
    sc = Scorecard(professional_id=pro.id)
    db.add(sc)
    db.commit()

    return pro


@router.post("/{pro_id}/log", response_model=InteractionLogOut)
def log_interaction(
    pro_id: int,
    payload: InteractionLogIn,
    db: Session = Depends(get_db)
):
    pro = db.query(Professional).filter(Professional.id == pro_id).first()
    if not pro:
        raise HTTPException(404, "Professional not found")

    log = InteractionLog(
        professional_id=pro_id,
        **payload.dict()
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    # recompute scorecard
    interactions = db.query(InteractionLog).filter(
        InteractionLog.professional_id == pro_id
    ).all()
    scores = compute_scores(interactions)

    scorecard = db.query(Scorecard).filter(
        Scorecard.professional_id == pro_id
    ).first()

    scorecard.reliability_score = scores["reliability"]
    scorecard.communication_score = scores["communication"]
    scorecard.quality_score = scores["quality"]
    scorecard.overall_score = scores["overall"]

    db.commit()

    return log


@router.get("/{pro_id}/scorecard", response_model=ScorecardOut)
def get_scorecard(
    pro_id: int,
    db: Session = Depends(get_db)
):
    sc = db.query(Scorecard).filter(
        Scorecard.professional_id == pro_id
    ).first()

    if not sc:
        raise HTTPException(404, "Scorecard not found")

    return sc
