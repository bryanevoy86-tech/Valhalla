from fastapi import APIRouter
from app.core_gov.canon.service import canon_snapshot

router = APIRouter(prefix="/canon", tags=["Core: Canon"])


@router.get("")
def get_canon():
    return canon_snapshot()
