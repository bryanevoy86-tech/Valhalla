import os
import time

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse

from ..observability.tracing import JSON_PATH, RING_EXPORTER

router = APIRouter(prefix="/admin/observability", tags=["admin-observability"])


@router.get("/spans")
def list_spans(
    limit: int = Query(200, ge=1, le=2000),
    name: str | None = None,
    kind: str | None = None,
    status: str | None = Query(None, description="UNSET/OK/ERROR"),
    since_ms: int | None = Query(None, description="Unix ms"),
):
    items = RING_EXPORTER.get_spans(
        limit=limit, name=name, kind=kind, status=status, since_ms=since_ms
    )
    return {"count": len(items), "items": items}


@router.get("/spans/export")
def export_spans_jsonl():
    if not os.path.exists(JSON_PATH):
        return PlainTextResponse("No file yet.", status_code=404)
    with open(JSON_PATH, "rb") as f:
        data = f.read()
    # Return as text to make “Save As” easy in browser/WeWeb
    return PlainTextResponse(data.decode("utf-8"), media_type="application/jsonl")


@router.get("/health")
def health():
    return {"ok": True, "time_ms": int(time.time() * 1000)}
