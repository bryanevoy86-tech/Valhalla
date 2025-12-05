# services/api/app/models/pro_scorecard.py

from __future__ import annotations

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    ForeignKey,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.core.db import Base


class Professional(Base):
    """
    A professional such as a lawyer, accountant, contractor, VA, etc.
    NOT psychological. Strictly operational reputation/performance.
    """

    __tablename__ = "professionals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    role = Column(String(100), nullable=False)  # lawyer, accountant, VA, etc.
    organization = Column(String(200), nullable=True)

    # Static attributes
    public_urls = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    interactions = relationship("InteractionLog", back_populates="professional")
    scorecard = relationship("Scorecard", uselist=False, back_populates="professional")
    retainers = relationship("Retainer", back_populates="professional")
    task_links = relationship("ProfessionalTaskLink", back_populates="professional")
    document_routes = relationship("DocumentRoute", back_populates="professional")


class InteractionLog(Base):
    """
    Records interactions with professionals:
    - response time
    - deliverable quality
    - deadlines met
    - communication clarity
    """

    __tablename__ = "professional_interactions"

    id = Column(Integer, primary_key=True, index=True)
    professional_id = Column(Integer, ForeignKey("professionals.id"))

    date = Column(DateTime(timezone=True), server_default=func.now())
    response_time_hours = Column(Float, nullable=True)
    deliverable_quality = Column(Float, nullable=True)  # 0–1 score
    communication_clarity = Column(Float, nullable=True)  # 0–1
    met_deadline = Column(Integer, nullable=True)  # 1 yes / 0 no
    notes = Column(Text, nullable=True)

    professional = relationship("Professional", back_populates="interactions")


class Scorecard(Base):
    """
    Rolling performance score updated after each interaction.
    """

    __tablename__ = "professional_scorecards"

    id = Column(Integer, primary_key=True, index=True)
    professional_id = Column(Integer, ForeignKey("professionals.id"), unique=True)

    reliability_score = Column(Float, default=0.0)
    communication_score = Column(Float, default=0.0)
    quality_score = Column(Float, default=0.0)
    overall_score = Column(Float, default=0.0)

    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    professional = relationship("Professional", back_populates="scorecard")
