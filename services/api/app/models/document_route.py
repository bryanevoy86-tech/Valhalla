# services/api/app/models/document_route.py

from __future__ import annotations

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship

from app.core.db import Base


class DocumentRoute(Base):
    """
    Tracks document delivery to professionals.
    Monitors sent/opened/acknowledged status for governance and follow-up.
    """

    __tablename__ = "document_routes"

    id = Column(Integer, primary_key=True, index=True)

    deal_id = Column(Integer, nullable=False)
    contract_id = Column(Integer, ForeignKey("contract_records.id"), nullable=True)
    professional_id = Column(Integer, ForeignKey("professionals.id"), nullable=False)

    document_type = Column(
        String(100),
        nullable=False
    )  # e.g. "contract", "supporting_doc", "summary"
    storage_url = Column(String(500), nullable=False)

    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    opened_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)

    status = Column(String(50), default="sent")  # sent, opened, acknowledged

    # Relationships (using string literals for forward references)
    professional = relationship(
        "Professional",
        foreign_keys=[professional_id],
        back_populates="document_routes"
    )
    contract = relationship(
        "ContractRecord",
        foreign_keys=[contract_id],
        back_populates="document_routes"
    )
