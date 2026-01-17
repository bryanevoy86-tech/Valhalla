"""PACK 87: Marketing Automation Engine - Schemas"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class MarketingCampaignBase(BaseModel):
    name: str
    target_audience: str | None = None
    strategy_payload: str


class MarketingCampaignCreate(MarketingCampaignBase):
    pass


class MarketingCampaignOut(MarketingCampaignBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SocialPostBase(BaseModel):
    platform: str
    content_payload: str
    status: str = "queued"


class SocialPostCreate(SocialPostBase):
    pass


class SocialPostOut(SocialPostBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
