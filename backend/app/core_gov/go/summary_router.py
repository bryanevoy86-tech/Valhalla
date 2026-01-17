from fastapi import APIRouter
from .summary_service import go_summary

router = APIRouter(prefix="/go", tags=["Core: Go"])

@router.get("/summary")
def summary():
    return go_summary()
