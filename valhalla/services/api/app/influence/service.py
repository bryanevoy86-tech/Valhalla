"""
Influence Library service functions.
"""
from sqlalchemy.orm import Session
from app.influence.models import InfluenceTechnique, CognitiveBias
from app.influence.schemas import TechniqueCreate, BiasCreate


def add_technique(db: Session, data: TechniqueCreate) -> InfluenceTechnique:
    obj = InfluenceTechnique(name=data.name, description=data.description, category=data.category)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_techniques(db: Session) -> list[InfluenceTechnique]:
    return db.query(InfluenceTechnique).order_by(InfluenceTechnique.id.desc()).all()


def add_bias(db: Session, data: BiasCreate) -> CognitiveBias:
    obj = CognitiveBias(name=data.name, description=data.description, mitigation=data.mitigation)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_biases(db: Session) -> list[CognitiveBias]:
    return db.query(CognitiveBias).order_by(CognitiveBias.id.desc()).all()
