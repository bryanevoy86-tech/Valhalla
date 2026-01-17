from __future__ import annotations

from fastapi import APIRouter
from . import service

router = APIRouter(prefix="/core/jv_dashboard", tags=["core-jv-dashboard"])

@router.get("")
def get_dashboard():
    return service.dashboard()
