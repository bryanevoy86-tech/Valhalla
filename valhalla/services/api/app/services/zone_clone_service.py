"""PACK 94: Zone Replication - Service"""

from sqlalchemy.orm import Session

from app.models.zone_clone import ZoneReplication
from app.schemas.zone_clone import ZoneReplicationCreate


def create_replication(db: Session, replication: ZoneReplicationCreate) -> ZoneReplication:
    db_replication = ZoneReplication(
        source_zone_id=replication.source_zone_id,
        target_zone_id=replication.target_zone_id,
        included_modules=replication.included_modules,
        status=replication.status
    )
    db.add(db_replication)
    db.commit()
    db.refresh(db_replication)
    return db_replication


def list_replications(db: Session) -> list[ZoneReplication]:
    return db.query(ZoneReplication).order_by(ZoneReplication.id.desc()).all()


def get_replication(db: Session, replication_id: int) -> ZoneReplication | None:
    return db.query(ZoneReplication).filter(ZoneReplication.id == replication_id).first()


def update_replication_status(db: Session, replication_id: int, status: str) -> ZoneReplication | None:
    db_replication = get_replication(db, replication_id)
    if not db_replication:
        return None
    db_replication.status = status
    db.commit()
    db.refresh(db_replication)
    return db_replication


def delete_replication(db: Session, replication_id: int) -> bool:
    db_replication = get_replication(db, replication_id)
    if not db_replication:
        return False
    db.delete(db_replication)
    db.commit()
    return True
