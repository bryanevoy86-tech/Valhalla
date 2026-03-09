import json
import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/admin/build", tags=["admin-build"])


@router.get("/info")
def info():
    p = os.path.join(os.path.dirname(__file__), "..", "buildinfo.json")
    try:
        return JSONResponse(json.load(open(p)))
    except Exception:
        return {"git_sha": "UNKNOWN", "built_at": "UNKNOWN", "version": "UNKNOWN"}
