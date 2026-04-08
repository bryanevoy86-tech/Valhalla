from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
)
from sqlalchemy.orm import relationship
from app.db.base import Base


class CommunityContact(Base):
    __tablename__ = "community_contacts"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    organization_name = Column(String(255), nullable=True)
    contact_type = Column(String(100), nullable=False, index=True)  # buyer, agent, contractor, investor, partner, media, community_org
    region = Column(String(100), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    preferred_channel = Column(String(50), nullable=True)  # phone, email, sms, in_person
    source = Column(String(100), nullable=True)  # referral, event, inbound, manual, etc.
    tags = Column(Text, nullable=True)  # comma-separated for simplicity
    relationship_stage = Column(String(50), nullable=False, default="new", index=True)  # new, warming, active, trusted, dormant
    trust_score = Column(Integer, nullable=False, default=50)
    consent_email = Column(Boolean, nullable=False, default=False)
    consent_sms = Column(Boolean, nullable=False, default=False)
    owner_user_id = Column(String(100), nullable=True)
    last_contact_at = Column(DateTime, nullable=True)
    next_follow_up_at = Column(DateTime, nullable=True, index=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    interactions = relationship("CommunityInteraction", back_populates="contact", cascade="all, delete-orphan")
    tasks = relationship("CommunityTask", back_populates="contact", cascade="all, delete-orphan")


class CommunityCampaign(Base):
    __tablename__ = "community_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    campaign_type = Column(String(100), nullable=False)  # goodwill, buyer_growth, contractor_recruitment, investor_updates, local_partnerships
    region = Column(String(100), nullable=True, index=True)
    audience_type = Column(String(100), nullable=False)
    objective = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="draft", index=True)  # draft, active, paused, completed, archived
    budget = Column(Numeric(12, 2), nullable=True)
    approval_status = Column(String(50), nullable=False, default="draft")  # draft, pending, approved, rejected
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    interactions = relationship("CommunityInteraction", back_populates="campaign")
    tasks = relationship("CommunityTask", back_populates="campaign")


class CommunityInteraction(Base):
    __tablename__ = "community_interactions"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("community_contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id = Column(Integer, ForeignKey("community_campaigns.id", ondelete="SET NULL"), nullable=True, index=True)

    interaction_type = Column(String(100), nullable=False, index=True)  # call, email, sms, meeting, event, referral, sponsorship, note
    direction = Column(String(50), nullable=True)  # inbound, outbound
    subject = Column(String(255), nullable=True)
    summary = Column(Text, nullable=False)
    outcome = Column(String(100), nullable=True)  # no_answer, interested, follow_up, closed, referred, etc.
    sentiment = Column(String(50), nullable=True)  # positive, neutral, negative
    follow_up_required = Column(Boolean, nullable=False, default=False)
    follow_up_at = Column(DateTime, nullable=True)
    performed_by = Column(String(100), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    contact = relationship("CommunityContact", back_populates="interactions")
    campaign = relationship("CommunityCampaign", back_populates="interactions")


class CommunityTask(Base):
    __tablename__ = "community_tasks"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("community_contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    campaign_id = Column(Integer, ForeignKey("community_campaigns.id", ondelete="SET NULL"), nullable=True, index=True)

    task_type = Column(String(100), nullable=False)  # follow_up, meeting, outreach, review, event, referral_check
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_at = Column(DateTime, nullable=True, index=True)
    priority = Column(String(50), nullable=False, default="normal")  # low, normal, high, urgent
    status = Column(String(50), nullable=False, default="open", index=True)  # open, in_progress, done, cancelled
    assigned_to = Column(String(100), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    contact = relationship("CommunityContact", back_populates="tasks")
    campaign = relationship("CommunityCampaign", back_populates="tasks")


class CommunityReferral(Base):
    __tablename__ = "community_referrals"

    id = Column(Integer, primary_key=True, index=True)
    source_contact_id = Column(Integer, ForeignKey("community_contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    referred_contact_id = Column(Integer, ForeignKey("community_contacts.id", ondelete="SET NULL"), nullable=True, index=True)

    referral_type = Column(String(100), nullable=False)  # buyer, seller, contractor, partner, investor
    referral_status = Column(String(50), nullable=False, default="new", index=True)  # new, contacted, converted, dead
    estimated_value = Column(Numeric(12, 2), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class CommunityReputationEvent(Base):
    __tablename__ = "community_reputation_events"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("community_contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = Column(String(100), nullable=False)  # positive_review, complaint, repeat_referral, event_attendance, goodwill_action
    score_delta = Column(Integer, nullable=False, default=0)
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class CommunityTemplate(Base):
    __tablename__ = "community_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    template_type = Column(String(100), nullable=False, index=True)  # first_touch, follow_up, referral_ask, check_in, reactivation
    channel = Column(String(50), nullable=False, index=True)  # email, sms, phone, in_person
    audience_type = Column(String(100), nullable=True, index=True)  # buyer, agent, contractor, investor, partner
    region = Column(String(100), nullable=True, index=True)
    subject = Column(String(255), nullable=True)
    body = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="draft", index=True)  # draft, approved, archived
    approval_status = Column(String(50), nullable=False, default="draft", index=True)
    created_by = Column(String(100), nullable=True)
    approved_by = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class CommunityMessageLog(Base):
    __tablename__ = "community_message_logs"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("community_contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    template_id = Column(Integer, ForeignKey("community_templates.id", ondelete="SET NULL"), nullable=True, index=True)
    channel = Column(String(50), nullable=False, index=True)
    direction = Column(String(50), nullable=False, default="outbound")  # outbound, inbound
    subject = Column(String(255), nullable=True)
    body = Column(Text, nullable=False)
    delivery_status = Column(String(50), nullable=False, default="draft", index=True)  # draft, queued, sent, delivered, failed, blocked
    block_reason = Column(Text, nullable=True)
    sent_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
