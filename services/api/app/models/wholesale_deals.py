"""
PACK SJ: Wholesale Deal Machine (Framework Layer)
Models for deal intake, offers, assignments, buyers, and pipeline tracking
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base


class WholesaleLead(Base):
    """
    Initial lead intake for wholesale deals.
    Pure data capture; no filtering or qualification.
    """
    __tablename__ = "wholesale_leads"

    id = Column(Integer, primary_key=True)
    lead_id = Column(String(255), nullable=False, unique=True)
    source = Column(String(100), nullable=False)  # website, ad, referral, cold-call, etc.
    seller_name = Column(String(255), nullable=True)
    seller_contact = Column(String(255), nullable=True)  # phone/email
    property_address = Column(String(255), nullable=False)
    motivation_level = Column(String(50), nullable=True)  # user-scored
    situation_notes = Column(Text, nullable=True)
    stage = Column(String(50), nullable=False, default="new")  # new, contacted, inspection, etc.
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    offers = relationship("WholesaleOffer", back_populates="lead")
    assignments = relationship("AssignmentRecord", back_populates="lead")


class WholesaleOffer(Base):
    """
    Offer and negotiation tracking for a lead.
    User provides all numbers and assumptions.
    """
    __tablename__ = "wholesale_offers"

    id = Column(Integer, primary_key=True)
    offer_id = Column(String(255), nullable=False, unique=True)
    lead_id = Column(Integer, ForeignKey("wholesale_leads.id"), nullable=False)
    offer_price = Column(Integer, nullable=False)  # cents
    arv = Column(Integer, nullable=True)  # cents; user supplies after comp analysis
    repair_estimate = Column(Integer, nullable=True)  # cents
    notes = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="draft")  # draft, sent, counter_received, accepted, rejected
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    lead = relationship("WholesaleLead", back_populates="offers")


class AssignmentRecord(Base):
    """
    Assignment workflow tracking (non-legal, organizational).
    Records the assignment process and buyer information.
    """
    __tablename__ = "assignment_records"

    id = Column(Integer, primary_key=True)
    assignment_id = Column(String(255), nullable=False, unique=True)
    lead_id = Column(Integer, ForeignKey("wholesale_leads.id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("buyer_profiles.id"), nullable=True)
    buyer_name = Column(String(255), nullable=True)
    buyer_contact = Column(String(255), nullable=True)
    assignment_fee = Column(Integer, nullable=False)  # cents
    notes = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="draft")  # draft, sent, signed, closed
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    lead = relationship("WholesaleLead", back_populates="assignments")
    buyer = relationship("BuyerProfile", back_populates="assignments")


class BuyerProfile(Base):
    """
    Buyer database for assignment tracking.
    User-maintained list of active buyers.
    """
    __tablename__ = "buyer_profiles"

    id = Column(Integer, primary_key=True)
    buyer_id = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    contact = Column(String(255), nullable=True)  # phone/email
    criteria = Column(JSON, nullable=True)  # {location, price_range, property_type, etc.}
    notes = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="active")  # active, inactive
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    assignments = relationship("AssignmentRecord", back_populates="buyer")


class WholesalePipelineSnapshot(Base):
    """
    Pipeline status snapshot for reporting and tracking.
    Aggregates leads by stage.
    """
    __tablename__ = "wholesale_pipeline_snapshots"

    id = Column(Integer, primary_key=True)
    snapshot_id = Column(String(255), nullable=False, unique=True)
    date = Column(DateTime, nullable=False)
    total_leads = Column(Integer, nullable=False, default=0)
    by_stage = Column(JSON, nullable=True)  # {new: count, contacted: count, etc.}
    hot_leads = Column(Integer, nullable=False, default=0)  # count of high-motivation leads
    active_offers = Column(Integer, nullable=False, default=0)
    ready_for_assignment = Column(Integer, nullable=False, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
