from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...core.config import get_settings
from ...core.security import create_token, verify_password
from ...crud.user import get_by_email
from ...schemas.auth import Login, Token
from ..deps import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(data: Login, db: Session = Depends(get_db)):
    user = get_by_email(db, data.email)
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect credentials")
    s = get_settings()
    return Token(
        access_token=create_token(user.email, s.ACCESS_TOKEN_EXPIRE_MINUTES),
        refresh_token=create_token(user.email, s.REFRESH_TOKEN_EXPIRE_MINUTES),
    )
