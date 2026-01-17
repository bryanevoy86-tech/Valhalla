"""PACK 81: Industry Engine - Registry Service"""

from sqlalchemy.orm import Session

from app.models.industry_registry import IndustryProfile
from app.schemas.industry_registry import IndustryProfileCreate


def create_industry_profile(db: Session, profile: IndustryProfileCreate) -> IndustryProfile:
    db_profile = IndustryProfile(
        name=profile.name,
        description=profile.description,
        config_payload=profile.config_payload
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile


def list_industry_profiles(db: Session) -> list[IndustryProfile]:
    return db.query(IndustryProfile).order_by(IndustryProfile.id.desc()).all()


def get_industry_profile(db: Session, profile_id: int) -> IndustryProfile | None:
    return db.query(IndustryProfile).filter(IndustryProfile.id == profile_id).first()


def update_industry_profile(db: Session, profile_id: int, profile: IndustryProfileCreate) -> IndustryProfile | None:
    db_profile = get_industry_profile(db, profile_id)
    if not db_profile:
        return None
    db_profile.name = profile.name
    db_profile.description = profile.description
    db_profile.config_payload = profile.config_payload
    db.commit()
    db.refresh(db_profile)
    return db_profile


def delete_industry_profile(db: Session, profile_id: int) -> bool:
    db_profile = get_industry_profile(db, profile_id)
    if not db_profile:
        return False
    db.delete(db_profile)
    db.commit()
    return True
