from __future__ import annotations

from fastapi import APIRouter

from .schemas import RedactTextRequest, RedactTextResponse, SanitizeManifestRequest, SanitizeManifestResponse
from . import service

router = APIRouter(prefix="/core/security", tags=["core-security"])


@router.post("/redact_text", response_model=RedactTextResponse)
def redact_text(payload: RedactTextRequest):
    r = service.redact_text(payload.text, level=payload.level)
    return {"redacted": r["redacted"], "meta": r.get("meta", {})}


@router.post("/sanitize_manifest", response_model=SanitizeManifestResponse)
def sanitize_manifest(payload: SanitizeManifestRequest):
    m = service.sanitize_manifest(payload.manifest, level=payload.level)
    return {"manifest": m, "meta": {"level": payload.level}}
