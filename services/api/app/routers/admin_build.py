import json
import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.build_info import get_runtime_build_identity

router = APIRouter(prefix="/admin/build", tags=["admin-build"])


@router.get("/info")
def info():
    p = os.path.join(os.path.dirname(__file__), "..", "buildinfo.json")
    try:
        file_payload = json.load(open(p))
    except Exception:
        file_payload = {"git_sha": "UNKNOWN", "built_at": "UNKNOWN", "version": "UNKNOWN"}

    identity = get_runtime_build_identity()
    file_payload.update(
        {
            "git_sha": identity["git_sha"],
            "git_sha_short": identity["git_sha_short"],
            "git_sha_source": identity["git_sha_source"],
            "observed_at": identity["observed_at"],
            "buildinfo_path": identity["buildinfo_path"],
        }
    )
    return JSONResponse(file_payload)
