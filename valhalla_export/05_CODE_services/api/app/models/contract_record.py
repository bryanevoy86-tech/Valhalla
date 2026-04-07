# services/api/app/models/contract_record.py

from __future__ import annotations

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    func,
)
from sqlalchemy.orm import relationship

from app.core.db import Base


class ContractRecord(Base):
    """
    Contract lifecycle tracking: draft -> review -> approved -> sent -> signed -> archived.
    Tracks status and metadata, not the legal text itself.
    """

    __tablename__ = "contract_records"

    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(Integer, nullable=False)  # link to deal system
    professional_id = Column(Integer, nullable=True)  # who is reviewing/drafted

    status = Column(
        String(50),
        default="draft"
    )  # draft, under_review, approved, sent, signed, archived
    version = Column(Integer, default=1)

    storage_url = Column(String(500), nullable=True)  # S3/drive URL for the document
    title = Column(String(200), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    signed_at = Column(DateTime(timezone=True), nullable=True)

    document_routes = relationship("DocumentRoute", back_populates="contract")
