"""Read related records using canonical deal relationships."""

from sqlalchemy.orm import Session

from app.models.deal import DealBriefLink
from app.models.match import DealBrief
from app.offers.models import Offer


def linked_brief(db: Session, deal_id: int) -> DealBrief | None:
    link = db.get(DealBriefLink, deal_id)
    return db.get(DealBrief, link.brief_id) if link is not None else None


def latest_offer(db: Session, deal_id: int) -> Offer | None:
    return (
        db.query(Offer).filter(Offer.deal_id == deal_id)
        .order_by(Offer.created_at.desc(), Offer.id.desc()).first()
    )
