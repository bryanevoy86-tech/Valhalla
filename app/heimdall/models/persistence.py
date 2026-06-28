from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON
from app.db.base import Base


class HeimdallDeal(Base):
    __tablename__ = "heimdall_deals"

    id = Column(String, primary_key=True, index=True)
    state = Column(String, default="NEW_LEAD", index=True)
    property_address = Column(String, nullable=True, index=True)
    data = Column(JSON, default=dict)
    state_history = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class HeimdallBuyer(Base):
    __tablename__ = "heimdall_buyers"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=True, index=True)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class HeimdallTask(Base):
    __tablename__ = "heimdall_tasks"

    id = Column(String, primary_key=True, index=True)
    deal_id = Column(String, nullable=True, index=True)
    title = Column(String, nullable=True)
    status = Column(String, default="OPEN", index=True)
    priority = Column(String, nullable=True)
    owner_role = Column(String, nullable=True)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class HeimdallApproval(Base):
    __tablename__ = "heimdall_approvals"

    id = Column(String, primary_key=True, index=True)
    deal_id = Column(String, nullable=True, index=True)
    status = Column(String, default="PENDING", index=True)
    approval_type = Column(String, nullable=True)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class HeimdallMessage(Base):
    __tablename__ = "heimdall_messages"

    id = Column(String, primary_key=True, index=True)
    deal_id = Column(String, nullable=True, index=True)
    recipient_type = Column(String, nullable=True)
    status = Column(String, default="DRAFT", index=True)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
