"""
PACK CL20: Readiness Router
Prefix: /system/readiness
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.readiness import compute_readiness

router = APIRouter(prefix="/system/readiness", tags=["System", "Readiness"])


@router.get("/")
def get_readiness(db: Session = Depends(get_db)):
    return compute_readiness(db)
