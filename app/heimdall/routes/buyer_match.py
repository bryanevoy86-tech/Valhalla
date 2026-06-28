from typing import Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.heimdall.services.buyer_match_service import (
    match_buyers_to_deal,
)

router = APIRouter(
    prefix="/heimdall/buyer-match",
    tags=["Heimdall Buyer Matching"],
)


class BuyerMatchRequest(BaseModel):
    deal_payload: Dict[str, Any]


@router.post("/match")
def buyer_match(
    payload: BuyerMatchRequest,
    db: Session = Depends(get_db),
):
    return match_buyers_to_deal(
        db=db,
        deal_payload=payload.deal_payload,
    )
