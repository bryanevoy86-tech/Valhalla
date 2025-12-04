from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from app.db.base_class import Base
import datetime


class ExpertReview(Base):
    __tablename__ = "expert_reviews"

    id = Column(Integer, primary_key=True, index=True)
    expert_id = Column(Integer, nullable=False)
    topic = Column(String, nullable=False)
    domain = Column(String, nullable=False)
    heimdall_recommendation = Column(Text)
    expert_recommendation = Column(Text)
    alignment_score = Column(Float, default=1.0)
    action_taken = Column(Text)
    meeting_date = Column(DateTime, nullable=False)
    recording_url = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
