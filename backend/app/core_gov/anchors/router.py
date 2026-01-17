from fastapi import APIRouter
from app.core_gov.anchors.service import anchors_check

router = APIRouter(prefix="/anchors", tags=["Core: Anchors"])


@router.get("/check")
def check():
    return anchors_check()
