"""Contract Engine Upgrade Router"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db

from . import schemas, service

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.post("/templates", response_model=schemas.ContractTemplateRead)
def create_template(
    payload: schemas.ContractTemplateCreate,
    db: Session = Depends(get_db),
):
    """Create a new contract template."""
    t = service.create_template(db, payload)
    return schemas.ContractTemplateRead.model_validate(t)


@router.get("/templates", response_model=List[schemas.ContractTemplateRead])
def get_templates(db: Session = Depends(get_db)):
    """List all contract templates."""
    templates = service.list_templates(db)
    return [schemas.ContractTemplateRead.model_validate(t) for t in templates]


@router.post("/review", response_model=schemas.ContractReviewRead)
def review_contract(
    payload: schemas.ContractReviewRequest,
    db: Session = Depends(get_db),
):
    """Review a contract for red flags."""
    r = service.analyze_contract(db, payload)
    return schemas.ContractReviewRead.model_validate(r)
