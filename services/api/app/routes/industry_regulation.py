"""PACK 85: Industry Engine - Regulatory Router"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.industry_regulation import IndustryRegulationOut, IndustryRegulationCreate
from app.services.industry_regulation_service import (
    create_regulation, list_regulations, get_regulation, update_regulation, delete_regulation
)

router = APIRouter(prefix="/industry/regulation", tags=["industry_regulation"])


@router.post("/", response_model=IndustryRegulationOut)
def post_regulation(regulation: IndustryRegulationCreate, db: Session = Depends(get_db)):
    return create_regulation(db, regulation)


@router.get("/", response_model=list[IndustryRegulationOut])
def get_regulations_endpoint(industry_id: int | None = None, db: Session = Depends(get_db)):
    return list_regulations(db, industry_id)


@router.get("/{regulation_id}", response_model=IndustryRegulationOut)
def get_regulation_endpoint(regulation_id: int, db: Session = Depends(get_db)):
    return get_regulation(db, regulation_id)


@router.put("/{regulation_id}", response_model=IndustryRegulationOut)
def put_regulation(regulation_id: int, regulation: IndustryRegulationCreate, db: Session = Depends(get_db)):
    return update_regulation(db, regulation_id, regulation)


@router.delete("/{regulation_id}")
def delete_regulation_endpoint(regulation_id: int, db: Session = Depends(get_db)):
    return delete_regulation(db, regulation_id)
