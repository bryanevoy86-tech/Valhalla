"""
Influence Library router (Pack 29).
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.influence.schemas import TechniqueCreate, TechniqueOut, BiasCreate, BiasOut
from app.influence.service import add_technique, list_techniques, add_bias, list_biases

router = APIRouter(prefix="/influence", tags=["influence"]) 


@router.post("/techniques", response_model=TechniqueOut)
async def create_technique(data: TechniqueCreate, db: Session = Depends(get_db)):
    return add_technique(db, data)


@router.get("/techniques", response_model=List[TechniqueOut])
async def get_techniques(db: Session = Depends(get_db)):
    return list_techniques(db)


@router.post("/biases", response_model=BiasOut)
async def create_bias(data: BiasCreate, db: Session = Depends(get_db)):
    return add_bias(db, data)


@router.get("/biases", response_model=List[BiasOut])
async def get_biases(db: Session = Depends(get_db)):
    return list_biases(db)
