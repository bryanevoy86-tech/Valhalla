from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Integer, String, text

from app.core.db import Base


class AuditEvent(Base):
	__tablename__ = "audit_events"

	id = Column(Integer, primary_key=True, index=True)
	deal_id = Column(Integer, nullable=True, index=True)
	professional_id = Column(Integer, nullable=True, index=True)
	code = Column(String(100), nullable=False, index=True)
	severity = Column(String(50), nullable=True, index=True)
	message = Column(String(500), nullable=False)
	is_resolved = Column(Boolean, nullable=True, default=False, index=True)
	created_at = Column(DateTime(timezone=True), nullable=True, server_default=text("CURRENT_TIMESTAMP"))
	resolved_at = Column(DateTime(timezone=True), nullable=True)


__all__ = ["AuditEvent"]
