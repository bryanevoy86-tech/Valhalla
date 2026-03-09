from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.orchestrator.schemas import (
    LegacyInstanceCreate,
    LegacyInstanceResponse,
    ClonePlanCreate,
    ClonePlanResponse,
    MirrorLinkCreate,
    MirrorLinkResponse,
)
from app.orchestrator.service import (
    create_instance,
    list_instances,
    request_clone,
    mark_clone_status,
    create_mirror,
    list_mirrors,
)


router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


@router.post("/instances", response_model=LegacyInstanceResponse)
def new_instance(payload: LegacyInstanceCreate, db: Session = Depends(get_db)):
    return create_instance(db, payload)


@router.get("/instances", response_model=List[LegacyInstanceResponse])
def instances(db: Session = Depends(get_db)):
    return list_instances(db)


@router.post("/clone", response_model=ClonePlanResponse)
def clone_request(payload: ClonePlanCreate, db: Session = Depends(get_db)):
    return request_clone(db, payload)


@router.post("/clone/{plan_id}/status", response_model=Optional[ClonePlanResponse])
def clone_status(plan_id: int, status: str, db: Session = Depends(get_db)):
    updated = mark_clone_status(db, plan_id, status=status)
    if not updated:
        raise HTTPException(status_code=404, detail="Plan not found")
    return updated


@router.post("/mirror", response_model=MirrorLinkResponse)
def mirror_create(payload: MirrorLinkCreate, db: Session = Depends(get_db)):
    return create_mirror(db, payload)


@router.get("/mirror", response_model=List[MirrorLinkResponse])
def mirrors(db: Session = Depends(get_db)):
    return list_mirrors(db)
