"""
Contract templates model.
Note: ContractRecord is now in app.models.contract_record (PACK N)
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from ..core.db import Base


class ContractTemplate(Base):
    __tablename__ = "contract_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(160), nullable=False)          # e.g., "MB Assignment v1"
    version = Column(String(40), nullable=True)         # "1.0"
    notes = Column(Text, nullable=True)
    body_text = Column(Text, nullable=False)            # Jinja2 text template
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

