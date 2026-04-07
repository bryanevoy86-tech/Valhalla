"""
PACK SO: Long-Term Legacy & Succession Archive Engine

Captures legacy, inheritance, knowledge transfer, and multi-stage succession.
NOT legal wills — operational succession and knowledge archiving.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class LegacyProfile(Base):
    """
    Definition of long-term empire legacy and knowledge transfer.
    
    Attributes:
        legacy_id: Unique identifier
        description: What this legacy encompasses
        long_term_goals: Future state aspirations
        knowledge_domains: Areas of knowledge to preserve
        heir_candidates: Names of potential successors
        notes: Additional context
    """
    __tablename__ = "legacy_profiles"

    id = Column(Integer, primary_key=True)
    legacy_id = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    long_term_goals = Column(JSON, nullable=True)  # List of goal strings
    knowledge_domains = Column(JSON, nullable=True)  # [{"domain": str, "description": str, "notes": str}]
    heir_candidates = Column(JSON, nullable=True)  # List of names
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    knowledge_packages = relationship("KnowledgePackage", back_populates="legacy", cascade="all, delete-orphan")
    succession_stages = relationship("SuccessionStage", back_populates="legacy", cascade="all, delete-orphan")
    legacy_vaults = relationship("LegacyVault", back_populates="legacy", cascade="all, delete-orphan")


class KnowledgePackage(Base):
    """
    Lessons, systems, philosophies, and instructions to preserve.
    
    Attributes:
        package_id: Unique identifier
        legacy_id: FK to LegacyProfile
        title: Name of this package
        category: Type [finance, family, values, system_design, decision_making]
        content: The actual knowledge/instructions
        notes: Additional context
    """
    __tablename__ = "knowledge_packages"

    id = Column(Integer, primary_key=True)
    package_id = Column(String(255), unique=True, nullable=False, index=True)
    legacy_id = Column(Integer, ForeignKey("legacy_profiles.id"), nullable=False)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)  # finance, family, values, system_design, decision_making
    content = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    legacy = relationship("LegacyProfile", back_populates="knowledge_packages")


class SuccessionStage(Base):
    """
    Defines when and how successors gain access and responsibility.
    
    Attributes:
        stage_id: Unique identifier
        legacy_id: FK to LegacyProfile
        description: What this stage represents
        trigger: Activation condition (e.g., "age 14", "graduation", "milestone")
        access_level: Module-by-module access rules
        training_requirements: What successor must learn
        notes: Additional context
    """
    __tablename__ = "succession_stages"

    id = Column(Integer, primary_key=True)
    stage_id = Column(String(255), unique=True, nullable=False, index=True)
    legacy_id = Column(Integer, ForeignKey("legacy_profiles.id"), nullable=False)
    description = Column(Text, nullable=True)
    trigger = Column(String(255), nullable=True)  # e.g., "age 14", "graduation", "milestone"
    access_level = Column(JSON, nullable=True)  # [{"module": str, "level": str (read-only, supervised, none)}]
    training_requirements = Column(JSON, nullable=True)  # List of requirement strings
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    legacy = relationship("LegacyProfile", back_populates="succession_stages")


class LegacyVault(Base):
    """
    Central archive for knowledge and succession information.
    
    Attributes:
        vault_id: Unique identifier
        legacy_id: FK to LegacyProfile
        packages: List of KnowledgePackage IDs
        successor_roles: Designated successors
        notes: Additional context
    """
    __tablename__ = "legacy_vaults"

    id = Column(Integer, primary_key=True)
    vault_id = Column(String(255), unique=True, nullable=False, index=True)
    legacy_id = Column(Integer, ForeignKey("legacy_profiles.id"), nullable=False)
    packages = Column(JSON, nullable=True)  # List of package_id strings
    successor_roles = Column(JSON, nullable=True)  # List of role names
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    legacy = relationship("LegacyProfile", back_populates="legacy_vaults")
