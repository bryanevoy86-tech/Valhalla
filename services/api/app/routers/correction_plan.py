"""
PACK CL14: Correction Plan Router
Prefix: /heimdall/corrections
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.correction_plan import CorrectionPlanCreate, CorrectionPlanOut, CorrectionPlanList
from app.services.correction_plan import create_plan, list_plans

router = APIRouter(prefix="/heimdall/corrections", tags=["Heimdall", "Meta-Learning"])


@router.post("/plans", response_model=CorrectionPlanOut, status_code=201)
def create_correction_plan(payload: CorrectionPlanCreate, db: Session = Depends(get_db)):
    return create_plan(db, payload)


@router.get("/plans", response_model=CorrectionPlanList)
def get_correction_plans(
    status: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    items = list_plans(db, status=status, limit=limit)
    return CorrectionPlanList(total=len(items), items=[CorrectionPlanOut.model_validate(i) for i in items])
