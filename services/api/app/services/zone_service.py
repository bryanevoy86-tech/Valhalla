"""PACK 93: Multi-Zone Expansion - Service"""

from sqlalchemy.orm import Session

from app.models.zone import BusinessZone
from app.schemas.zone import BusinessZoneCreate


def create_zone(db: Session, zone: BusinessZoneCreate) -> BusinessZone:
    db_zone = BusinessZone(
        name=zone.name,
        region_code=zone.region_code,
        notes=zone.notes
    )
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return db_zone


def list_zones(db: Session) -> list[BusinessZone]:
    return db.query(BusinessZone).order_by(BusinessZone.id.desc()).all()


def get_zone(db: Session, zone_id: int) -> BusinessZone | None:
    return db.query(BusinessZone).filter(BusinessZone.id == zone_id).first()


def update_zone(db: Session, zone_id: int, zone: BusinessZoneCreate) -> BusinessZone | None:
    db_zone = get_zone(db, zone_id)
    if not db_zone:
        return None
    db_zone.name = zone.name
    db_zone.region_code = zone.region_code
    db_zone.notes = zone.notes
    db.commit()
    db.refresh(db_zone)
    return db_zone


def delete_zone(db: Session, zone_id: int) -> bool:
    db_zone = get_zone(db, zone_id)
    if not db_zone:
        return False
    db.delete(db_zone)
    db.commit()
    return True
