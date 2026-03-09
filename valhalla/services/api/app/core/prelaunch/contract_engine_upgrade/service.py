"""Contract Engine Upgrade Service Layer"""
from sqlalchemy.orm import Session

from . import models, schemas


def create_template(db: Session, data: schemas.ContractTemplateCreate) -> models.ContractTemplate:
    """Create a new contract template."""
    t = models.ContractTemplate(**data.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def list_templates(db: Session):
    """List all contract templates."""
    return db.query(models.ContractTemplate).order_by(models.ContractTemplate.name).all()


def analyze_contract(
    db: Session, data: schemas.ContractReviewRequest
) -> models.ContractReview:
    """
    Analyze a contract for red flags.
    
    Placeholder logic, to be replaced by Heimdall analysis later.
    """
    red_flags = []

    text_lower = data.text.lower()
    if "indemnify" in text_lower or "hold harmless" in text_lower:
        red_flags.append(
            {"type": "liability_shift", "snippet": "Indemnity / hold harmless clause detected."}
        )
    if "arbitration" in text_lower:
        red_flags.append(
            {"type": "dispute_resolution", "snippet": "Arbitration clause detected."}
        )

    review = models.ContractReview(
        source=data.source,
        category=data.category,
        text=data.text,
        red_flags=red_flags,
        notes="Initial static contract scan. Heimdall will enhance this later.",
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review
