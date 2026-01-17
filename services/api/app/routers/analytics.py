from typing import List, Optional
from fastapi import APIRouter

from app.analytics.service import AnalyticsService
from app.analytics.schemas import UserActivityOut, UserActivityIn


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/log", response_model=UserActivityOut)
async def log_user_activity(body: UserActivityIn):
    svc = AnalyticsService()
    return svc.log_user_activity(body.user_id, body.action, body.metadata)


@router.get("/user-activity/{user_id}", response_model=List[UserActivityOut])
async def get_user_activity(user_id: str):
    svc = AnalyticsService()
    return svc.get_user_activity(user_id)
