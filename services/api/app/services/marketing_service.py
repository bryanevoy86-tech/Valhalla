"""PACK 87: Marketing Automation Engine - Service"""

from sqlalchemy.orm import Session

from app.models.marketing import MarketingCampaign, SocialPost
from app.schemas.marketing import MarketingCampaignCreate, SocialPostCreate


# Marketing campaign operations
def create_campaign(db: Session, campaign: MarketingCampaignCreate) -> MarketingCampaign:
    db_campaign = MarketingCampaign(
        name=campaign.name,
        target_audience=campaign.target_audience,
        strategy_payload=campaign.strategy_payload
    )
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign


def list_campaigns(db: Session) -> list[MarketingCampaign]:
    return db.query(MarketingCampaign).order_by(MarketingCampaign.id.desc()).all()


def get_campaign(db: Session, campaign_id: int) -> MarketingCampaign | None:
    return db.query(MarketingCampaign).filter(MarketingCampaign.id == campaign_id).first()


def update_campaign(db: Session, campaign_id: int, campaign: MarketingCampaignCreate) -> MarketingCampaign | None:
    db_campaign = get_campaign(db, campaign_id)
    if not db_campaign:
        return None
    db_campaign.name = campaign.name
    db_campaign.target_audience = campaign.target_audience
    db_campaign.strategy_payload = campaign.strategy_payload
    db.commit()
    db.refresh(db_campaign)
    return db_campaign


def delete_campaign(db: Session, campaign_id: int) -> bool:
    db_campaign = get_campaign(db, campaign_id)
    if not db_campaign:
        return False
    db.delete(db_campaign)
    db.commit()
    return True


# Social post operations
def create_post(db: Session, post: SocialPostCreate) -> SocialPost:
    db_post = SocialPost(
        platform=post.platform,
        content_payload=post.content_payload,
        status=post.status
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


def list_posts(db: Session, platform: str | None = None) -> list[SocialPost]:
    q = db.query(SocialPost)
    if platform:
        q = q.filter(SocialPost.platform == platform)
    return q.order_by(SocialPost.id.desc()).all()


def get_post(db: Session, post_id: int) -> SocialPost | None:
    return db.query(SocialPost).filter(SocialPost.id == post_id).first()


def update_post(db: Session, post_id: int, post: SocialPostCreate) -> SocialPost | None:
    db_post = get_post(db, post_id)
    if not db_post:
        return None
    db_post.platform = post.platform
    db_post.content_payload = post.content_payload
    db_post.status = post.status
    db.commit()
    db.refresh(db_post)
    return db_post


def delete_post(db: Session, post_id: int) -> bool:
    db_post = get_post(db, post_id)
    if not db_post:
        return False
    db.delete(db_post)
    db.commit()
    return True
