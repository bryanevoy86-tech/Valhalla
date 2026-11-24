"""Verify a stored artifact before internal use."""
import hashlib
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.models.product_artifact import ProductArtifact


def require_artifact_schema(db: Session) -> None:
    if not inspect(db.connection()).has_table(ProductArtifact.__tablename__):
        raise HTTPException(status_code=503, detail="Product artifact schema not ready")


def load_artifact(db: Session, artifact_id: UUID, *, lock: bool = False) -> ProductArtifact:
    row = db.get(ProductArtifact, artifact_id, with_for_update=lock)
    if row is None:
        raise HTTPException(status_code=404, detail="Internal product artifact not found")
    return row


def verify_artifact(row: ProductArtifact) -> None:
    if row.revoked_at is not None:
        raise HTTPException(status_code=409, detail="Internal product artifact revoked")
    if hashlib.sha256(row.data).hexdigest() != row.sha256:
        raise HTTPException(status_code=409, detail="Internal product artifact integrity mismatch")


def artifact_reference(row: ProductArtifact) -> dict:
    return {
        "artifact_id": str(row.id), "version": row.version, "sha256": row.sha256,
        "media_type": row.media_type, "bytes": len(row.data),
    }
