from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.core_gov.audit.audit_log import audit
from app.core_gov.export.service import build_export_bundle

router = APIRouter(prefix="/export", tags=["Core: Export"])


@router.get("/bundle")
def export_bundle():
    path = build_export_bundle()
    audit("EXPORT_BUNDLE_CREATED", {"file": str(path)})
    return FileResponse(
        path=str(path),
        filename=path.name,
        media_type="application/zip",
    )
