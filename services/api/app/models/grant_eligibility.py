"""
PACK SA: Grant Eligibility Engine Models
Strategic framework for organizing grant requirements and tracking eligibility
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from app.core.db import Base


class GrantProfile(Base):
    """
    Stores grant information and eligibility criteria.
    Neutral framework for organizing requirements without providing advice.
    """
    __tablename__ = "grant_profiles"

    id = Column(Integer, primary_key=True, index=True)

    grant_id = Column(String, nullable=False, unique=True)
    program_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # funding_type: grant, loan, training, support
    funding_type = Column(String, nullable=False, default="grant")

    # region or jurisdiction
    region = Column(String, nullable=True)

    # target_group: startup, low_income, training, business_growth
    target_groups = Column(JSON, nullable=True)  # list of strings

    # requirements list: items with type and notes
    requirements = Column(JSON, nullable=True)  # list of {item, type, notes}

    # status: not_started, collecting_docs, ready_for_submission, submitted
    status = Column(String, nullable=False, default="not_started")

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)


class EligibilityChecklist(Base):
    """
    Tracks completion status for each requirement in a grant profile.
    Maps user progress against neutral criteria.
    """
    __tablename__ = "eligibility_checklists"

    id = Column(Integer, primary_key=True, index=True)

    grant_profile_id = Column(Integer, nullable=False)  # link to GrantProfile

    requirement_key = Column(String, nullable=False)  # identifier for requirement
    requirement_name = Column(String, nullable=False)
    requirement_type = Column(String, nullable=False)  # document, status, eligibility

    is_completed = Column(Boolean, default=False)
    is_uploaded = Column(Boolean, default=False)

    notes = Column(Text, nullable=True)
    uploaded_filename = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
