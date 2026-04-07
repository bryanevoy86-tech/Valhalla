from sqlalchemy import Column, Integer, String, Float, DateTime
from app.db.base_class import Base
import datetime

class Contractor(Base):
    __tablename__ = "contractors"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    contact_person = Column(String)
    region = Column(String)
    loyalty_rank = Column(String, default="Iron")
    jobs_completed = Column(Integer, default=0)
    quality_score = Column(Float, default=0.0)
    speed_score = Column(Float, default=0.0)
    attitude_score = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
