"""PACK 87: Marketing Automation Engine
Creates marketing content, campaigns, and social media posts.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime

from app.models.base import Base


class MarketingCampaign(Base):
    __tablename__ = "marketing_campaign"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    target_audience = Column(String, nullable=True)
    strategy_payload = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class SocialPost(Base):
    __tablename__ = "social_post"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, nullable=False)
    content_payload = Column(Text, nullable=False)
    status = Column(String, default="queued")
    created_at = Column(DateTime, default=datetime.utcnow)
