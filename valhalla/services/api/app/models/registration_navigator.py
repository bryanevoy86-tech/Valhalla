"""
PACK SB: Business Registration Navigator Models
Non-legal workflow engine for tracking business registration steps
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from app.core.db import Base


class RegistrationFlowStep(Base):
    """
    Represents a single step in the business registration workflow.
    Neutral, non-directive guidance on what documents and info are needed.
    """
    __tablename__ = "registration_flow_steps"

    id = Column(Integer, primary_key=True, index=True)

    step_id = Column(String, nullable=False, unique=True)

    # category: naming, structure, documents, accounts, tax_numbers
    category = Column(String, nullable=False)

    description = Column(Text, nullable=False)

    # required_documents: list of {filename, type}
    required_documents = Column(JSON, nullable=True)

    # status: pending, in_progress, completed
    status = Column(String, nullable=False, default="pending")

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)


class RegistrationStageTracker(Base):
    """
    Tracks overall progress through registration workflow.
    Stores user selections and document uploads.
    """
    __tablename__ = "registration_stage_trackers"

    id = Column(Integer, primary_key=True, index=True)

    # current_stage: preparation, structure, documents, filing, post_registration
    current_stage = Column(String, nullable=False, default="preparation")

    # Stage 1: Preparation
    business_name = Column(String, nullable=True)
    business_description = Column(Text, nullable=True)
    founders_list = Column(JSON, nullable=True)  # list of founder info

    # Stage 2: Structure (user choice, not directive)
    selected_structure = Column(String, nullable=True)  # corporation, sole_prop, partnership, nonprofit
    structure_notes = Column(Text, nullable=True)

    # Stage 3: Document Prep
    founder_ids_uploaded = Column(Boolean, default=False)
    purpose_statement = Column(Text, nullable=True)
    naics_codes = Column(JSON, nullable=True)  # list of category codes
    business_address = Column(String, nullable=True)

    # Stage 4: Filing
    filing_completed = Column(Boolean, default=False)
    filing_receipt_uploaded = Column(Boolean, default=False)

    # Stage 5: Post-Registration
    registration_number = Column(String, nullable=True)
    articles_uploaded = Column(Boolean, default=False)
    incorporation_docs_uploaded = Column(Boolean, default=False)

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
