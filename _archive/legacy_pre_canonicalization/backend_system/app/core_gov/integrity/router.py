from __future__ import annotations

from fastapi import APIRouter

from .schemas import CheckResult
from . import service

router = APIRouter(prefix="/core/integrity", tags=["core-integrity"])


@router.get("/check", response_model=CheckResult)
def check():
    return service.run_checks()
