from sqlalchemy import Column, Integer, String, Float, DateTime, Text
import datetime
from app.db.base_class import Base


class WholeLifePolicy(Base):
    __tablename__ = "whole_life_policies"

    id = Column(Integer, primary_key=True, index=True)
    insured_name = Column(String, nullable=False)
    owner_entity = Column(String, nullable=False)
    policy_number = Column(String, nullable=False, unique=True)
    insurer = Column(String)
    face_value = Column(Float, default=0.0)
    annual_premium = Column(Float, default=0.0)
    cash_value = Column(Float, default=0.0)
    loan_available = Column(Float, default=0.0)
    status = Column(String, default="active")
    notes = Column(Text)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
