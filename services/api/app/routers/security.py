from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, Body, Query
from sqlalchemy.orm import Session

from app.security.service import SecurityService
from app.security.schemas import TwoFactorAuthOut, RateLimitOut
from app.core.db import get_db


router = APIRouter(prefix="/security", tags=["security"])


@router.post("/generate-2fa", response_model=TwoFactorAuthOut)
async def generate_2fa_token(
    user_id: Optional[str] = Query(None),
    payload: Optional[Dict[str, Any]] = Body(None),
    db: Session = Depends(get_db),
):
    uid = user_id or (payload or {}).get("user_id")
    if not uid:
        # Fast fail: in a full impl, raise HTTPException 400
        uid = "unknown"
    return SecurityService(db).generate_2fa_token(uid)


@router.post("/verify-2fa", response_model=TwoFactorAuthOut)
async def verify_2fa_token(
    user_id: Optional[str] = Query(None),
    token: Optional[str] = Query(None),
    payload: Optional[Dict[str, Any]] = Body(None),
    db: Session = Depends(get_db),
):
    uid = user_id or (payload or {}).get("user_id")
    tok = token or (payload or {}).get("token")
    if not uid:
        uid = "unknown"
    if not tok:
        tok = ""
    return SecurityService(db).verify_2fa_token(uid, tok)


@router.get("/rate-limit", response_model=RateLimitOut)
async def check_rate_limit(user_id: str, db: Session = Depends(get_db)):
    return SecurityService(db).check_rate_limit(user_id)
