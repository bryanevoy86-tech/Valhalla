"""PACK-CORE-PRELAUNCH-01: Scenarios Engine - Router"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db

from . import schemas, service

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("/", response_model=List[schemas.ScenarioRead])
def list_scenarios(db: Session = Depends(get_db)):
    return service.list_scenarios(db)
