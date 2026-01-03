from __future__ import annotations

from fastapi import APIRouter

from app.core_gov.command.service import what_now, daily_brief, weekly_review

router = APIRouter(prefix="/command", tags=["Core: Command Center"])


@router.get("/what_now")
def what_now_endpoint(limit: int = 7):
    return what_now(limit=limit)


@router.get("/daily_brief")
def daily_brief_endpoint():
    return daily_brief()


@router.get("/weekly_review")
def weekly_review_endpoint():
    return weekly_review()
