"""
Service logic for Advanced Negotiation Techniques (Pack 32).
"""
from sqlalchemy.orm import Session
from app.advanced_negotiation.models import NegotiationTechnique
from app.advanced_negotiation.schemas import NegotiationTechniqueCreate


def create_technique(db: Session, technique: NegotiationTechniqueCreate) -> NegotiationTechnique:
    """Create a new negotiation technique."""
    db_technique = NegotiationTechnique(
        technique_name=technique.technique_name,
        description=technique.description,
        effectiveness_score=technique.effectiveness_score,
        technique_type=technique.technique_type,
    )
    db.add(db_technique)
    db.commit()
    db.refresh(db_technique)
    return db_technique


def get_all_techniques(db: Session) -> list[NegotiationTechnique]:
    """Retrieve all negotiation techniques."""
    return db.query(NegotiationTechnique).order_by(NegotiationTechnique.effectiveness_score.desc()).all()


def get_technique_by_id(db: Session, technique_id: int) -> NegotiationTechnique | None:
    """Get a specific technique by ID."""
    return db.query(NegotiationTechnique).filter(NegotiationTechnique.id == technique_id).first()


def get_techniques_by_type(db: Session, technique_type: str) -> list[NegotiationTechnique]:
    """Filter techniques by type."""
    return (
        db.query(NegotiationTechnique)
        .filter(NegotiationTechnique.technique_type == technique_type)
        .order_by(NegotiationTechnique.effectiveness_score.desc())
        .all()
    )


def get_top_techniques(db: Session, min_score: float = 70.0, limit: int = 10) -> list[NegotiationTechnique]:
    """Get top-ranked techniques by effectiveness score."""
    return (
        db.query(NegotiationTechnique)
        .filter(NegotiationTechnique.effectiveness_score >= min_score)
        .order_by(NegotiationTechnique.effectiveness_score.desc())
        .limit(limit)
        .all()
    )


def update_technique_score(db: Session, technique_id: int, new_score: float) -> NegotiationTechnique | None:
    """Update technique effectiveness score (e.g., based on AI analysis)."""
    db_technique = db.query(NegotiationTechnique).filter(NegotiationTechnique.id == technique_id).first()
    if not db_technique:
        return None
    setattr(db_technique, "effectiveness_score", new_score)
    db.commit()
    db.refresh(db_technique)
    return db_technique
