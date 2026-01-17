from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import datetime

class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True, nullable=False)
    role = Column(String, index=True, nullable=False)
    region = Column(String)
    pay_rate = Column(Float)  # mid → high range
    status = Column(String, default="active")  # active, trial, inactive
    reliability_score = Column(Float, default=0.0)
    skill_score = Column(Float, default=0.0)
    attitude_score = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
