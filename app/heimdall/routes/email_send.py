from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.heimdall.services.email_send_service import (
    send_email_message,
)

router = APIRouter(
    prefix="/heimdall/email",
    tags=["Heimdall Email"],
)


@router.post("/send/{message_id}")
def send_email(
    message_id: str,
    db: Session = Depends(get_db),
):
    return send_email_message(
        db=db,
        message_id=message_id,
    )
