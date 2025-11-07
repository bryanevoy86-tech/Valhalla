"""
Pack 51: Legal Document Engine - ORM models
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.core.db import Base


class LegalTemplate(Base):
    __tablename__ = "legal_templates"
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    jurisdiction = Column(String(32))
    kind = Column(String(32), nullable=False)
    active = Column(Boolean, nullable=False, default=True)


class LegalTemplateVersion(Base):
    __tablename__ = "legal_template_versions"
    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey("legal_templates.id", ondelete="CASCADE"))
    version = Column(Integer, nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class LegalClause(Base):
    __tablename__ = "legal_clauses"
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    jurisdiction = Column(String(32))
    body = Column(Text, nullable=False)


class LegalVariable(Base):
    __tablename__ = "legal_variables"
    id = Column(Integer, primary_key=True)
    key = Column(String(64), unique=True, nullable=False)
    desc = Column(String(256))
    required = Column(Boolean, nullable=False, default=True)
    example = Column(String(256))


class LegalDocument(Base):
    __tablename__ = "legal_documents"
    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey("legal_templates.id", ondelete="SET NULL"))
    version = Column(Integer, nullable=False)
    rendered_body = Column(Text, nullable=False)
    variables_json = Column(Text, nullable=False)
    status = Column(String(24), nullable=False, default="draft")
    external_ref = Column(String(128))
    created_at = Column(DateTime, server_default=func.now())
