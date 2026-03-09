"""
Contract templates and records models.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from ..core.db import Base


class ContractTemplate(Base):
    __tablename__ = "contract_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(160), nullable=False)          # e.g., "MB Assignment v1"
    version = Column(String(40), nullable=True)         # "1.0"
    notes = Column(Text, nullable=True)
    body_text = Column(Text, nullable=False)            # Jinja2 text template
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ContractRecord(Base):
    __tablename__ = "contract_records"

    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey("contract_templates.id", ondelete="SET NULL"), nullable=True)
    filename = Column(String(200), nullable=False)      # saved PDF filename
    context_json = Column(Text, nullable=True)          # data used to fill
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    template = relationship("ContractTemplate", lazy="joined")
