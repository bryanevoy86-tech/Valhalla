"""
PACK SK: Arbitrage / Side-Hustle Opportunity Tracker
Models for opportunity tracking and user-defined scoring
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base


class Opportunity(Base):
    """
    Side-hustle or arbitrage opportunity record.
    User provides all estimates; system organizes and scores based on user criteria.
    """
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True)
    opportunity_id = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)  # service, product, digital, gig, seasonal, arbitrage
    description = Column(Text, nullable=True)
    startup_cost = Column(Integer, nullable=False)  # cents
    expected_effort = Column(Float, nullable=True)  # hours/week estimate
    potential_return = Column(Integer, nullable=True)  # cents; user estimate
    risk_level = Column(String(50), nullable=True)  # user-defined: low, medium, high
    status = Column(String(50), nullable=False, default="idea")  # idea, researching, testing, active, paused, dead
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    scores = relationship("OpportunityScore", back_populates="opportunity")
    performance_logs = relationship("OpportunityPerformance", back_populates="opportunity")


class OpportunityScore(Base):
    """
    User-defined scoring for opportunities.
    Heimdall doesn't score — user provides criteria and scores.
    """
    __tablename__ = "opportunity_scores"

    id = Column(Integer, primary_key=True)
    score_id = Column(String(255), nullable=False, unique=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False)
    time_efficiency = Column(Float, nullable=True)  # 0-10 user score
    scalability = Column(Float, nullable=True)  # 0-10 user score
    difficulty = Column(Float, nullable=True)  # 0-10 user score (lower is easier)
    personal_interest = Column(Float, nullable=True)  # 0-10 user score
    overall_score = Column(Float, nullable=True)  # user-calculated or weighted
    notes = Column(Text, nullable=True)
    scored_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    opportunity = relationship("Opportunity", back_populates="scores")


class OpportunityPerformance(Base):
    """
    Tracks actual performance of active opportunities.
    User logs results; system aggregates.
    """
    __tablename__ = "opportunity_performance"

    id = Column(Integer, primary_key=True)
    log_id = Column(String(255), nullable=False, unique=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    effort_hours = Column(Float, nullable=True)  # actual hours spent
    revenue = Column(Integer, nullable=True)  # cents earned
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    opportunity = relationship("Opportunity", back_populates="performance_logs")


class OpportunitySummary(Base):
    """
    Monthly or periodic summary of opportunity performance.
    """
    __tablename__ = "opportunity_summaries"

    id = Column(Integer, primary_key=True)
    summary_id = Column(String(255), nullable=False, unique=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False)
    period = Column(String(50), nullable=False)  # YYYY-MM format
    total_effort_hours = Column(Float, nullable=False, default=0)
    total_revenue = Column(Integer, nullable=False, default=0)  # cents
    roi = Column(Float, nullable=True)  # (revenue - startup_cost) / startup_cost
    status_update = Column(String(50), nullable=True)  # still active?
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
