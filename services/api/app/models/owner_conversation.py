"""Private owner conversation records and quarantined attachments."""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, LargeBinary, Integer, JSON, Uuid, ForeignKey, CheckConstraint, Index
from app.core.db import Base

def now():
    return datetime.now(timezone.utc)

class OwnerConversation(Base):
    __tablename__ = "prime_owner_conversations"
    id = Column(Uuid(), primary_key=True)
    title = Column(String(160), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now)

class OwnerTurn(Base):
    __tablename__ = "prime_owner_turns"
    __table_args__ = (Index("ix_prime_owner_turn_thread", "conversation_id", "created_at"),)
    id = Column(Uuid(), primary_key=True)
    conversation_id = Column(Uuid(), ForeignKey("prime_owner_conversations.id"), nullable=False)
    message = Column(Text(), nullable=False)
    reply = Column(Text(), nullable=False)
    evidence = Column(JSON(), nullable=False)
    attachment_ids = Column(JSON(), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now)

class OwnerAttachment(Base):
    __tablename__ = "prime_owner_attachments"
    __table_args__ = (
        CheckConstraint("length(data) BETWEEN 1 AND 5242880", name="ck_prime_owner_attachment_size"),
        Index("ix_prime_owner_attachment_thread", "conversation_id"),
    )
    id = Column(Uuid(), primary_key=True)
    conversation_id = Column(Uuid(), ForeignKey("prime_owner_conversations.id"), nullable=False)
    filename = Column(String(180), nullable=False)
    media_type = Column(String(100), nullable=False)
    sha256 = Column(String(64), nullable=False)
    data = Column(LargeBinary(), nullable=False)
    size_bytes = Column(Integer(), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now)
