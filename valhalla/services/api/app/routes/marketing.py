"""PACK 87: Marketing Automation Engine - Router"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.marketing import MarketingCampaignOut, MarketingCampaignCreate, SocialPostOut, SocialPostCreate
from app.services.marketing_service import (
    create_campaign, list_campaigns, get_campaign, update_campaign, delete_campaign,
    create_post, list_posts, get_post, update_post, delete_post
)

router = APIRouter(prefix="/marketing", tags=["marketing"])


# Campaign endpoints
@router.post("/campaign", response_model=MarketingCampaignOut)
def post_campaign(campaign: MarketingCampaignCreate, db: Session = Depends(get_db)):
    return create_campaign(db, campaign)


@router.get("/campaigns", response_model=list[MarketingCampaignOut])
def get_campaigns_endpoint(db: Session = Depends(get_db)):
    return list_campaigns(db)


@router.get("/campaign/{campaign_id}", response_model=MarketingCampaignOut)
def get_campaign_endpoint(campaign_id: int, db: Session = Depends(get_db)):
    return get_campaign(db, campaign_id)


@router.put("/campaign/{campaign_id}", response_model=MarketingCampaignOut)
def put_campaign(campaign_id: int, campaign: MarketingCampaignCreate, db: Session = Depends(get_db)):
    return update_campaign(db, campaign_id, campaign)


@router.delete("/campaign/{campaign_id}")
def delete_campaign_endpoint(campaign_id: int, db: Session = Depends(get_db)):
    return delete_campaign(db, campaign_id)


# Social post endpoints
@router.post("/post", response_model=SocialPostOut)
def post_social_post(post: SocialPostCreate, db: Session = Depends(get_db)):
    return create_post(db, post)


@router.get("/posts", response_model=list[SocialPostOut])
def get_posts_endpoint(platform: str | None = None, db: Session = Depends(get_db)):
    return list_posts(db, platform)


@router.get("/post/{post_id}", response_model=SocialPostOut)
def get_post_endpoint(post_id: int, db: Session = Depends(get_db)):
    return get_post(db, post_id)


@router.put("/post/{post_id}", response_model=SocialPostOut)
def put_post(post_id: int, post: SocialPostCreate, db: Session = Depends(get_db)):
    return update_post(db, post_id, post)


@router.delete("/post/{post_id}")
def delete_post_endpoint(post_id: int, db: Session = Depends(get_db)):
    return delete_post(db, post_id)
