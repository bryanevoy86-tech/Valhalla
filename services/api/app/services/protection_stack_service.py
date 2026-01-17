"""PACK 76: Protection Stack - Service"""

from sqlalchemy.orm import Session

from app.models.protection_stack import TrustEntity, ShieldMode
from app.schemas.protection_stack import TrustEntityCreate, ShieldModeCreate


# Trust entity operations
def create_trust_entity(db: Session, entity: TrustEntityCreate) -> TrustEntity:
    db_entity = TrustEntity(
        name=entity.name,
        jurisdiction=entity.jurisdiction,
        role=entity.role,
        notes=entity.notes
    )
    db.add(db_entity)
    db.commit()
    db.refresh(db_entity)
    return db_entity


def list_trust_entities(db: Session) -> list[TrustEntity]:
    return db.query(TrustEntity).all()


def get_trust_entity(db: Session, entity_id: int) -> TrustEntity | None:
    return db.query(TrustEntity).filter(TrustEntity.id == entity_id).first()


def update_trust_entity(db: Session, entity_id: int, entity: TrustEntityCreate) -> TrustEntity | None:
    db_entity = get_trust_entity(db, entity_id)
    if not db_entity:
        return None
    db_entity.name = entity.name
    db_entity.jurisdiction = entity.jurisdiction
    db_entity.role = entity.role
    db_entity.notes = entity.notes
    db.commit()
    db.refresh(db_entity)
    return db_entity


def delete_trust_entity(db: Session, entity_id: int) -> bool:
    db_entity = get_trust_entity(db, entity_id)
    if not db_entity:
        return False
    db.delete(db_entity)
    db.commit()
    return True


# Shield mode operations
def set_shield_mode(db: Session, shield: ShieldModeCreate) -> ShieldMode:
    db_shield = ShieldMode(
        level=shield.level,
        active=shield.active,
        trigger_reason=shield.trigger_reason
    )
    db.add(db_shield)
    db.commit()
    db.refresh(db_shield)
    return db_shield


def get_latest_shield_mode(db: Session) -> ShieldMode | None:
    return db.query(ShieldMode).order_by(ShieldMode.id.desc()).first()


def list_shield_modes(db: Session) -> list[ShieldMode]:
    return db.query(ShieldMode).all()


def get_shield_mode(db: Session, shield_id: int) -> ShieldMode | None:
    return db.query(ShieldMode).filter(ShieldMode.id == shield_id).first()


def update_shield_mode(db: Session, shield_id: int, shield: ShieldModeCreate) -> ShieldMode | None:
    db_shield = get_shield_mode(db, shield_id)
    if not db_shield:
        return None
    db_shield.level = shield.level
    db_shield.active = shield.active
    db_shield.trigger_reason = shield.trigger_reason
    db.commit()
    db.refresh(db_shield)
    return db_shield


def delete_shield_mode(db: Session, shield_id: int) -> bool:
    db_shield = get_shield_mode(db, shield_id)
    if not db_shield:
        return False
    db.delete(db_shield)
    db.commit()
    return True
