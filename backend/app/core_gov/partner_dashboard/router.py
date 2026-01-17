from __future__ import annotations

from fastapi import APIRouter

from . import service

router = APIRouter(prefix="/core/partner_dashboard", tags=["core-partner-dashboard"])

@router.get("/")
def get_dashboard():
    return service.get_dashboard()
