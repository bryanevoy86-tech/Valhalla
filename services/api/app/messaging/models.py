"""
Email/SMS related models.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.core.db import Base

class EmailTemplate(Base):
    __tablename__ = 'email_templates'

    template_id = Column(Integer, primary_key=True, autoincrement=True)
    template_name = Column(String, unique=True, nullable=False, index=True)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
