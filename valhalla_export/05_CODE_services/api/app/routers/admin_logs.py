import glob
import os

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse

from ..observability.logging import LOG_PATH

router = APIRouter(prefix="/admin/logs", tags=["admin-logs"])


@router.get("/list")
def list_logs():
    base = LOG_PATH
    pattern = base + "*"
    files = sorted(glob.glob(pattern))
    sizes = [
        {"file": os.path.basename(f), "bytes": os.path.getsize(f)}
        for f in files
        if os.path.exists(f)
    ]
    return {"path": base, "files": sizes}


@router.get("/get")
def get_log(file: str | None = Query(None, description="Exact filename under log directory")):
    base_dir = os.path.dirname(LOG_PATH)
    path = os.path.join(base_dir, file) if file else LOG_PATH
    if not os.path.exists(path):
        return PlainTextResponse("Not found", status_code=404)
    with open(path, encoding="utf-8", errors="ignore") as f:
        return PlainTextResponse(f.read(), media_type="application/jsonl")
