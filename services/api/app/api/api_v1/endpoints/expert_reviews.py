from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.expert_review import ExpertReview
from app.schemas.expert_review import ExpertReviewCreate, ExpertReviewOut

router = APIRouter()


@router.post("/", response_model=ExpertReviewOut)
def create_expert_review(
    payload: ExpertReviewCreate,
    db: Session = Depends(get_db),
):
    obj = ExpertReview(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[ExpertReviewOut])
def list_expert_reviews(
    expert_id: int | None = None,
    domain: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(ExpertReview)
    if expert_id is not None:
        query = query.filter(ExpertReview.expert_id == expert_id)
    if domain:
        query = query.filter(ExpertReview.domain == domain)
    return query.order_by(ExpertReview.meeting_date.desc()).all()
