"""
PACK TM: Core Philosophy Archive Router
Prefix: /philosophy
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.philosophy import (
    PhilosophyRecordCreate,
    PhilosophyRecordOut,
    EmpirePrincipleCreate,
    EmpirePrincipleOut,
    PhilosophySnapshot,
)
from app.services.philosophy import (
    create_philosophy_record,
    list_philosophy_records,
    create_empire_principle,
    list_empire_principles,
    get_philosophy_snapshot,
)

router = APIRouter(prefix="/philosophy", tags=["Philosophy"])


@router.post("/records", response_model=PhilosophyRecordOut)
def create_record_endpoint(
    payload: PhilosophyRecordCreate,
    db: Session = Depends(get_db),
):
    return create_philosophy_record(db, payload)


@router.get("/records", response_model=list[PhilosophyRecordOut])
def list_records_endpoint(db: Session = Depends(get_db)):
    return list_philosophy_records(db)


@router.post("/principles", response_model=EmpirePrincipleOut)
def create_principle_endpoint(
    payload: EmpirePrincipleCreate,
    db: Session = Depends(get_db),
):
    return create_empire_principle(db, payload)


@router.get("/principles", response_model=list[EmpirePrincipleOut])
def list_principles_endpoint(db: Session = Depends(get_db)):
    return list_empire_principles(db)


@router.get("/snapshot", response_model=PhilosophySnapshot)
def snapshot_endpoint(db: Session = Depends(get_db)):
    snapshot = get_philosophy_snapshot(db)
    if not snapshot:
        raise HTTPException(status_code=404, detail="No philosophy records found")
    return snapshot
