"""Contract pipeline data models."""
from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Text, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class ContractTemplate(Base):
    """Template for contract generation (merge schema for document synthesis)."""
    __tablename__ = "contract_templates"
    
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    merge_schema = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Contract(Base):
    """Contract lifecycle tracking (state machine: DRAFT -> FULLY_EXECUTED)."""
    __tablename__ = "contracts"
    
    id = Column(String, primary_key=True)
    template_id = Column(Integer, ForeignKey("contract_templates.id"), nullable=False)
    title = Column(String, nullable=False)
    state = Column(String, default="DRAFT", nullable=False)  # DRAFT, SENT, SIGNED, EXECUTED
    deal_id = Column(String, nullable=True, index=True)
    zone_id = Column(String, nullable=True, index=True)
    merge_data = Column(JSON, default=dict, nullable=False)
    notes = Column(Text, nullable=True)
    sign_provider = Column(String, default="sandbox", nullable=False)
    active_envelope_id = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ContractEvent(Base):
    """Audit trail for all contract state changes."""
    __tablename__ = "contract_events"
    
    id = Column(String, primary_key=True)
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False)  # created, state_changed, signed, executed
    actor = Column(String, nullable=True)  # who/what triggered the event
    meta = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
