import glob
import os

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, PlainTextResponse

router = APIRouter(prefix="/admin/privacy", tags=["admin-privacy"])
EN = os.getenv("PRIVACY_ENABLED", "false").lower() in ("1", "true", "yes")
LOG_PATH = os.getenv("LOG_JSON_PATH", "/data/app.jsonl")


@router.get("/find")
def find(q: str = Query(..., min_length=1)):
    if not EN:
        return JSONResponse({"ok": False, "error": "disabled"}, status_code=404)
    hits = []
    for f in sorted(glob.glob(LOG_PATH + "*"))[-10:]:  # recent files only
        try:
            for line in open(f, encoding="utf-8", errors="ignore"):
                if q in line:
                    hits.append({"file": f.split("/")[-1], "line": line[:600]})
                    if len(hits) >= 200:
                        break
        except Exception:
            pass
    return {"query": q, "hits": hits}


@router.get("/dsar")
def dsar(user: str):
    if not EN:
        return PlainTextResponse("disabled", status_code=404)
    # toy exporter: pull matching log lines
    res = find(user)
    return JSONResponse({"user": user, "log_matches": res.get("hits", [])})
