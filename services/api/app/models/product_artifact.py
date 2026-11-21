"""Immutable internal Product Foundry artifact versions."""
from sqlalchemy import Column, DateTime, Integer, LargeBinary, String, UniqueConstraint, Uuid

from app.core.db import Base


class ProductArtifact(Base):
    __tablename__ = "product_artifacts"
    __table_args__ = (UniqueConstraint(
        "legacy_instance_id", "business_id", "engine_id", "jurisdiction", "product_id", "version",
        name="uq_product_artifact_scope_version",
    ),)

    id = Column(Uuid(), primary_key=True)
    legacy_instance_id = Column(String(80), nullable=False)
    business_id = Column(String(120), nullable=False)
    engine_id = Column(String(80), nullable=False)
    jurisdiction = Column(String(80), nullable=False)
    product_id = Column(String(80), nullable=False)
    version = Column(Integer(), nullable=False)
    media_type = Column(String(80), nullable=False)
    sha256 = Column(String(64), nullable=False)
    data = Column(LargeBinary(), nullable=False)
    rights_reference = Column(String(240), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
