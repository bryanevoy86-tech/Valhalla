from __future__ import annotations

import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Enum, Boolean, Integer, ForeignKey, Text, JSON, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship

from app.core.db import Base


class ContractState(str, enum.Enum):
    DRAFT = "DRAFT"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    IN_REVIEW = "IN_REVIEW"
    APPROVED_FOR_SIGNATURE = "APPROVED_FOR_SIGNATURE"
    SENT_FOR_SIGNATURE = "SENT_FOR_SIGNATURE"
    PARTIALLY_SIGNED = "PARTIALLY_SIGNED"
    FULLY_EXECUTED = "FULLY_EXECUTED"
    DECLINED = "DECLINED"
    VOIDED = "VOIDED"
    ARCHIVED = "ARCHIVED"


class ContractDocKind(str, enum.Enum):
    DRAFT = "DRAFT"
    EXECUTED = "EXECUTED"
    ATTACHMENT = "ATTACHMENT"


class SignProvider(str, enum.Enum):
    SANDBOX = "sandbox"
    DOCUSIGN = "docusign"


class ContractTemplate(Base):
    __tablename__ = "contract_templates"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True)
    code = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    merge_schema = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Contract(Base):
    __tablename__ = "contracts"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True)
    template_id = Column(String, ForeignKey("contract_templates.id"), nullable=False)

    title = Column(String, nullable=False)
    state = Column(Enum(ContractState), nullable=False, default=ContractState.DRAFT)

    deal_id = Column(String, nullable=True, index=True)
    zone_id = Column(String, nullable=True, index=True)

    merge_data = Column(JSON, nullable=False, default=dict)
    notes = Column(Text, nullable=True)

    sign_provider = Column(Enum(SignProvider), nullable=False, default=SignProvider.SANDBOX)

    active_envelope_id = Column(String, ForeignKey("contract_envelopes.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Note: template relationship removed due to SQLAlchemy extend_existing conflicts
    # Can be loaded explicitly in queries if needed with joinedload or similar
    
    parties = relationship("ContractParty", back_populates="contract", cascade="all, delete-orphan")
    documents = relationship("ContractDocument", back_populates="contract", cascade="all, delete-orphan")
    events = relationship("ContractEvent", back_populates="contract", cascade="all, delete-orphan")


class ContractPartyRole(str, enum.Enum):
    SELLER = "SELLER"
    BUYER = "BUYER"
    ASSIGNOR = "ASSIGNOR"
    ASSIGNEE = "ASSIGNEE"
    WITNESS = "WITNESS"
    NOTARY = "NOTARY"
    OTHER = "OTHER"


class ContractParty(Base):
    __tablename__ = "contract_parties"

    id = Column(String, primary_key=True)
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False, index=True)

    role = Column(Enum(ContractPartyRole), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    provider_recipient_id = Column(String, nullable=True)

    must_sign = Column(Boolean, nullable=False, default=True)
    signed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    contract = relationship("Contract", back_populates="parties")

    __table_args__ = (
        Index("ix_contract_parties_contract_role", "contract_id", "role"),
        {'extend_existing': True},
    )


class ContractDocument(Base):
    __tablename__ = "contract_documents"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True)
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False, index=True)

    kind = Column(Enum(ContractDocKind), nullable=False)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False, default="application/pdf")
    storage_key = Column(String, nullable=False)

    sha256 = Column(String, nullable=True)
    bytes = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    contract = relationship("Contract", back_populates="documents")


class ContractEnvelope(Base):
    __tablename__ = "contract_envelopes"

    id = Column(String, primary_key=True)
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False, index=True)

    provider = Column(Enum(SignProvider), nullable=False)
    provider_envelope_id = Column(String, nullable=True, index=True)

    status = Column(String, nullable=False, default="created")
    raw = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("provider", "provider_envelope_id", name="uq_provider_envelope"),
        {'extend_existing': True},
    )


class ContractEvent(Base):
    __tablename__ = "contract_events"

    id = Column(String, primary_key=True)
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False, index=True)

    event_type = Column(String, nullable=False)
    actor = Column(String, nullable=True)
    meta = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    contract = relationship("Contract", back_populates="events")

    __table_args__ = (
        Index("ix_contract_events_contract_time", "contract_id", "created_at"),
        {'extend_existing': True},
    )


