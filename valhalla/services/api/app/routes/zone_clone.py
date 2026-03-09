"""PACK 94: Zone Replication - Routes"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.zone_clone import ZoneReplicationCreate, ZoneReplicationOut
from app.services import zone_clone_service

router = APIRouter(
    prefix="/zone-replicate",
    tags=["zone_replication"]
)


@router.post("/", response_model=ZoneReplicationOut)
def create_replication(replication: ZoneReplicationCreate, db: Session = Depends(get_db)):
    return zone_clone_service.create_replication(db, replication)


@router.get("/{replication_id}", response_model=ZoneReplicationOut)
def get_replication(replication_id: int, db: Session = Depends(get_db)):
    return zone_clone_service.get_replication(db, replication_id)


@router.get("/", response_model=list[ZoneReplicationOut])
def list_replications(db: Session = Depends(get_db)):
    return zone_clone_service.list_replications(db)


@router.put("/{replication_id}/status", response_model=ZoneReplicationOut)
def update_replication_status(replication_id: int, status: str, db: Session = Depends(get_db)):
    return zone_clone_service.update_replication_status(db, replication_id, status)


@router.delete("/{replication_id}")
def delete_replication(replication_id: int, db: Session = Depends(get_db)):
    success = zone_clone_service.delete_replication(db, replication_id)
    return {"deleted": success}
