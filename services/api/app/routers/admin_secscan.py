from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.observability import secscan

router = APIRouter(prefix="/admin/secscan", tags=["admin-secscan"])


@router.get("/scan")
def scan():
    return JSONResponse(secscan.scan_recent())
