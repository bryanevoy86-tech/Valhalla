"""Owner-attested product asset staging for the internal Factory lane."""
import base64
import binascii
from datetime import datetime, timezone
import hashlib
from io import BytesIO
from typing import Literal
from uuid import UUID
import zipfile

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.product_artifact import ProductArtifact
from app.routers.prime_business_factory import require_factory_schema
from app.services.prime_business_execution import _check_legacy, require_factory_key, require_owner_mandate_key
from app.services.product_artifacts import artifact_reference, load_artifact, require_artifact_schema, verify_artifact


MAX_BYTES = 5 * 1024 * 1024
MAX_REQUEST_BYTES = 7 * 1024 * 1024
SCOPE = ("legacy_instance_id", "business_id", "engine_id", "jurisdiction")
OWNER = [Depends(require_owner_mandate_key)]
router = APIRouter(
    prefix="/api/business-factory/product-artifacts", tags=["product-foundry"],
    dependencies=[Depends(require_factory_key), Depends(require_factory_schema)],
)


class ArtifactIn(BaseModel):
    artifact_id: UUID
    legacy_instance_id: str = Field(min_length=3, max_length=80)
    business_id: str = Field(min_length=3, max_length=120)
    engine_id: str = Field(min_length=3, max_length=80)
    jurisdiction: str = Field(min_length=2, max_length=80)
    product_id: str = Field(min_length=3, max_length=80)
    version: int = Field(ge=1, le=1_000_000, strict=True)
    media_type: Literal["application/pdf", "application/zip", "text/plain"]
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    content_base64: str = Field(min_length=4, max_length=4 * ((MAX_BYTES + 2) // 3))
    rights_reference: str = Field(min_length=10, max_length=240)
    attestation: Literal["OWNER_AUTHORIZES_INTERNAL_STORAGE_AND_USE"]


def _bytes(request: ArtifactIn) -> bytes:
    try:
        data = base64.b64decode(request.content_base64, validate=True)
        if not 0 < len(data) <= MAX_BYTES or hashlib.sha256(data).hexdigest() != request.sha256:
            raise ValueError
        if request.media_type == "application/pdf" and not data.startswith(b"%PDF-"):
            raise ValueError
        if request.media_type == "application/zip" and not zipfile.is_zipfile(BytesIO(data)):
            raise ValueError
        if request.media_type == "text/plain":
            data.decode("utf-8")
    except (UnicodeError, ValueError, binascii.Error):
        raise HTTPException(status_code=422, detail="Artifact bytes, checksum, or file type did not validate") from None
    return data


def _metadata(row: ProductArtifact) -> dict:
    return {
        **artifact_reference(row), **{key: getattr(row, key) for key in SCOPE},
        "product_id": row.product_id, "rights_reference": row.rights_reference,
        "rights_basis": "OWNER_ATTESTED_INTERNAL_USE", "revoked": row.revoked_at is not None,
        "external_delivery_authorized": False,
    }


async def _bounded_upload(request: Request) -> ArtifactIn:
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > MAX_REQUEST_BYTES:
            raise HTTPException(status_code=413, detail="Product artifact request exceeds 7 MiB")
        body.extend(chunk)
    try:
        return ArtifactIn.model_validate_json(body)
    except ValidationError:
        raise HTTPException(status_code=422, detail="Invalid product artifact data or scope") from None


@router.post("", status_code=201, dependencies=OWNER, openapi_extra={
    "requestBody": {
        "required": True,
        "content": {"application/json": {"schema": ArtifactIn.model_json_schema()}},
    },
})
def stage_artifact(request: ArtifactIn = Depends(_bounded_upload), db: Session = Depends(get_db)):
    require_artifact_schema(db)
    attributes = request.model_dump(exclude={"artifact_id", "attestation", "content_base64"})
    attributes["rights_reference"] = attributes["rights_reference"].strip()
    if len(attributes["rights_reference"]) < 10:
        raise HTTPException(status_code=422, detail="Document the internal-use rights reference")
    _check_legacy(db, **{key: attributes[key] for key in SCOPE})
    data = _bytes(request)
    row = ProductArtifact(id=request.artifact_id, **attributes, data=data, created_at=datetime.now(timezone.utc))
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        row = db.get(ProductArtifact, request.artifact_id)
        if row is None or any(getattr(row, key) != value for key, value in attributes.items()) or row.data != data:
            raise HTTPException(status_code=409, detail="This artifact ID or product version already has immutable evidence") from None
    return _metadata(row)


@router.get("/{artifact_id}")
def inspect_artifact(artifact_id: UUID, db: Session = Depends(get_db)):
    require_artifact_schema(db)
    return _metadata(load_artifact(db, artifact_id))


@router.get("/{artifact_id}/download", dependencies=OWNER)
def internal_download(artifact_id: UUID, db: Session = Depends(get_db)):
    require_artifact_schema(db)
    row = load_artifact(db, artifact_id)
    _check_legacy(db, **{key: getattr(row, key) for key in SCOPE})
    verify_artifact(row)
    return Response(
        content=row.data, media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{artifact_id}.bin"',
                 "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "X-Artifact-SHA256": row.sha256},
    )


@router.delete("/{artifact_id}", dependencies=OWNER)
def revoke_artifact(artifact_id: UUID, db: Session = Depends(get_db)):
    require_artifact_schema(db)
    row = load_artifact(db, artifact_id, lock=True)
    if row.revoked_at is None:
        row.revoked_at = datetime.now(timezone.utc)
        db.commit()
    return _metadata(row)
