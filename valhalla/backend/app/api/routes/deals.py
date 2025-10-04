from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...crud import deal as crud_deal
from ...schemas.deal import DealCreate, DealOut
from ..deps import get_current_user, get_db

router = APIRouter(prefix="/deals", tags=["deals"])


@router.post("", response_model=DealOut)
def create_deal(
    data: DealCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _ = user
    return crud_deal.create(db, data)
