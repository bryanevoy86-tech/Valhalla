"""PACK 85: Industry Engine - Regulatory Service"""

from sqlalchemy.orm import Session

from app.models.industry_regulation import IndustryRegulation
from app.schemas.industry_regulation import IndustryRegulationCreate


def create_regulation(db: Session, regulation: IndustryRegulationCreate) -> IndustryRegulation:
    db_regulation = IndustryRegulation(
        industry_id=regulation.industry_id,
        region=regulation.region,
        requirements_payload=regulation.requirements_payload
    )
    db.add(db_regulation)
    db.commit()
    db.refresh(db_regulation)
    return db_regulation


def list_regulations(db: Session, industry_id: int | None = None) -> list[IndustryRegulation]:
    q = db.query(IndustryRegulation)
    if industry_id:
        q = q.filter(IndustryRegulation.industry_id == industry_id)
    return q.order_by(IndustryRegulation.id.desc()).all()


def get_regulation(db: Session, regulation_id: int) -> IndustryRegulation | None:
    return db.query(IndustryRegulation).filter(IndustryRegulation.id == regulation_id).first()


def update_regulation(db: Session, regulation_id: int, regulation: IndustryRegulationCreate) -> IndustryRegulation | None:
    db_regulation = get_regulation(db, regulation_id)
    if not db_regulation:
        return None
    db_regulation.industry_id = regulation.industry_id
    db_regulation.region = regulation.region
    db_regulation.requirements_payload = regulation.requirements_payload
    db.commit()
    db.refresh(db_regulation)
    return db_regulation


def delete_regulation(db: Session, regulation_id: int) -> bool:
    db_regulation = get_regulation(db, regulation_id)
    if not db_regulation:
        return False
    db.delete(db_regulation)
    db.commit()
    return True
