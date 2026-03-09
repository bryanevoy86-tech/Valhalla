from sqlalchemy.orm import Session
from app.compliance.models import ComplianceRecord
from app.compliance.schemas import ComplianceCreate


def calculate_risk(amount: float, category: str) -> tuple[float, str]:
    cat = category.lower()
    if cat in ["education", "office supplies", "software"]:
        return (5.0, "Safe")
    elif cat in ["vehicle", "travel", "meals"]:
        if amount > 2000:
            return (65.0, "Moderate")
        return (30.0, "Moderate")
    else:
        return (90.0, "Aggressive")


def create_compliance(db: Session, payload: ComplianceCreate) -> ComplianceRecord:
    score, rating = calculate_risk(payload.claimed_amount, payload.category)
    record = ComplianceRecord(
        item_name=payload.item_name,
        category=payload.category,
        claimed_amount=payload.claimed_amount,
        risk_score=score,
        rating=rating,
        justification=payload.justification,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_records(db: Session):
    return db.query(ComplianceRecord).order_by(ComplianceRecord.date_logged.desc()).all()
