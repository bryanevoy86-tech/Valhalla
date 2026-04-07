from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from app.db.base_class import Base
import datetime


class ExternalExpert(Base):
    __tablename__ = "external_experts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    firm = Column(String)
    email = Column(String)
    phone = Column(String)
    specialty = Column(String, nullable=False)
    jurisdiction = Column(String)
    hourly_rate = Column(Float, default=0.0)
    preferred = Column(Boolean, default=True)
    notes = Column(Text)
    last_contacted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
