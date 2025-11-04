from sqlalchemy import JSON, TIMESTAMP, Column, ForeignKey, Integer, Numeric, String
from sqlalchemy.sql import func

from ..core.db import Base


class FundingRequest(Base):
    __tablename__ = "funding_requests"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, index=True, nullable=False)
    legacy_id = Column(
        Integer, ForeignKey("legacies.id", ondelete="SET NULL"), index=True, nullable=True
    )
    requested_by = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, nullable=False, default="USD")
    purpose = Column(String, nullable=True)
    status = Column(String, nullable=False, default="draft")
    meta = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class FundingApproval(Base):
    __tablename__ = "funding_approvals"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(
        Integer, ForeignKey("funding_requests.id", ondelete="CASCADE"), index=True, nullable=False
    )
    approver_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    decision = Column(String, nullable=False)
    note = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class Disbursement(Base):
    __tablename__ = "disbursements"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, index=True, nullable=False)
    request_id = Column(
        Integer, ForeignKey("funding_requests.id", ondelete="SET NULL"), index=True, nullable=True
    )
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, nullable=False, default="USD")
    method = Column(String, nullable=True)
    reference = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)


class Repayment(Base):
    __tablename__ = "repayments"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, index=True, nullable=False)
    request_id = Column(
        Integer, ForeignKey("funding_requests.id", ondelete="SET NULL"), index=True, nullable=True
    )
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, nullable=False, default="USD")
    method = Column(String, nullable=True)
    reference = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)


class RepaymentSchedule(Base):
    __tablename__ = "repayment_schedules"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, index=True, nullable=False)
    request_id = Column(
        Integer, ForeignKey("funding_requests.id", ondelete="CASCADE"), index=True, nullable=False
    )
    schedule = Column(JSON, nullable=False)
    status = Column(String, nullable=False, default="active")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
