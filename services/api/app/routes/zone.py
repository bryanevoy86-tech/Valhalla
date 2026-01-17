"""PACK 93: Multi-Zone Expansion - Routes"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.zone import BusinessZoneCreate, BusinessZoneOut
from app.services import zone_service

router = APIRouter(
    prefix="/zone",
    tags=["zone"]
)


@router.post("/", response_model=BusinessZoneOut)
def create_zone(zone: BusinessZoneCreate, db: Session = Depends(get_db)):
    return zone_service.create_zone(db, zone)


@router.get("/{zone_id}", response_model=BusinessZoneOut)
def get_zone(zone_id: int, db: Session = Depends(get_db)):
    return zone_service.get_zone(db, zone_id)


@router.get("/", response_model=list[BusinessZoneOut])
def list_zones(db: Session = Depends(get_db)):
    return zone_service.list_zones(db)


@router.put("/{zone_id}", response_model=BusinessZoneOut)
def update_zone(zone_id: int, zone: BusinessZoneCreate, db: Session = Depends(get_db)):
    return zone_service.update_zone(db, zone_id, zone)


@router.delete("/{zone_id}")
def delete_zone(zone_id: int, db: Session = Depends(get_db)):
    success = zone_service.delete_zone(db, zone_id)
    return {"deleted": success}
