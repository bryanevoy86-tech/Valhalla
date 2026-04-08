from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field


class CommunityContactBase(BaseModel):
    full_name: str
    organization_name: Optional[str] = None
    contact_type: str
    region: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    preferred_channel: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[str] = None
    relationship_stage: str = "new"
    trust_score: int = Field(default=50, ge=0, le=100)
    consent_email: bool = False
    consent_sms: bool = False
    owner_user_id: Optional[str] = None
    last_contact_at: Optional[datetime] = None
    next_follow_up_at: Optional[datetime] = None
    notes: Optional[str] = None


class CommunityContactCreate(CommunityContactBase):
    pass


class CommunityContactUpdate(BaseModel):
    full_name: Optional[str] = None
    organization_name: Optional[str] = None
    contact_type: Optional[str] = None
    region: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    preferred_channel: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[str] = None
    relationship_stage: Optional[str] = None
    trust_score: Optional[int] = Field(default=None, ge=0, le=100)
    consent_email: Optional[bool] = None
    consent_sms: Optional[bool] = None
    owner_user_id: Optional[str] = None
    last_contact_at: Optional[datetime] = None
    next_follow_up_at: Optional[datetime] = None
    notes: Optional[str] = None


class CommunityContactOut(CommunityContactBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommunityCampaignBase(BaseModel):
    name: str
    campaign_type: str
    region: Optional[str] = None
    audience_type: str
    objective: Optional[str] = None
    status: str = "draft"
    budget: Optional[Decimal] = None
    approval_status: str = "draft"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    notes: Optional[str] = None


class CommunityCampaignCreate(CommunityCampaignBase):
    pass


class CommunityCampaignUpdate(BaseModel):
    name: Optional[str] = None
    campaign_type: Optional[str] = None
    region: Optional[str] = None
    audience_type: Optional[str] = None
    objective: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[Decimal] = None
    approval_status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    notes: Optional[str] = None


class CommunityCampaignOut(CommunityCampaignBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommunityInteractionBase(BaseModel):
    contact_id: int
    campaign_id: Optional[int] = None
    interaction_type: str
    direction: Optional[str] = None
    subject: Optional[str] = None
    summary: str
    outcome: Optional[str] = None
    sentiment: Optional[str] = None
    follow_up_required: bool = False
    follow_up_at: Optional[datetime] = None
    performed_by: Optional[str] = None


class CommunityInteractionCreate(CommunityInteractionBase):
    pass


class CommunityInteractionOut(CommunityInteractionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CommunityTaskBase(BaseModel):
    contact_id: Optional[int] = None
    campaign_id: Optional[int] = None
    task_type: str
    title: str
    description: Optional[str] = None
    due_at: Optional[datetime] = None
    priority: str = "normal"
    status: str = "open"
    assigned_to: Optional[str] = None


class CommunityTaskCreate(CommunityTaskBase):
    pass


class CommunityTaskUpdate(BaseModel):
    task_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    due_at: Optional[datetime] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    completed_at: Optional[datetime] = None


class CommunityTaskOut(CommunityTaskBase):
    id: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CommunityReferralBase(BaseModel):
    source_contact_id: Optional[int] = None
    referred_contact_id: Optional[int] = None
    referral_type: str
    referral_status: str = "new"
    estimated_value: Optional[Decimal] = None
    notes: Optional[str] = None


class CommunityReferralCreate(CommunityReferralBase):
    pass


class CommunityReferralOut(CommunityReferralBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CommunitySummaryOut(BaseModel):
    total_contacts: int
    active_contacts: int
    follow_ups_due: int
    open_tasks: int
    active_campaigns: int
    total_referrals: int
    hot_contacts: int


class CommunityNextActionOut(BaseModel):
    contact_id: int
    full_name: str
    relationship_stage: str
    trust_score: int
    heat_score: int
    action: str
    priority: str
    reason: str


class CommunityRegionSummaryOut(BaseModel):
    region: str
    total_contacts: int
    trusted_contacts: int
    active_contacts: int
    warming_contacts: int
    new_contacts: int
    follow_ups_due: int
    open_tasks: int
    total_referrals: int


class CommunityAutomationResultOut(BaseModel):
    contact_id: int
    full_name: str
    stale: bool
    decayed: bool
    task_created: bool
    trust_score: int
    relationship_stage: str


class CommunityWeeklyPriorityOut(BaseModel):
    contact_id: int
    full_name: str
    region: Optional[str] = None
    relationship_stage: str
    trust_score: int
    heat_score: int
    weekly_priority_score: int
    reason: str
    next_action: str
    priority: str


class CommunityTemplateBase(BaseModel):
    name: str
    template_type: str
    channel: str
    audience_type: Optional[str] = None
    region: Optional[str] = None
    subject: Optional[str] = None
    body: str
    status: str = "draft"
    approval_status: str = "draft"
    created_by: Optional[str] = None
    approved_by: Optional[str] = None
    notes: Optional[str] = None


class CommunityTemplateCreate(CommunityTemplateBase):
    pass


class CommunityTemplateUpdate(BaseModel):
    name: Optional[str] = None
    template_type: Optional[str] = None
    channel: Optional[str] = None
    audience_type: Optional[str] = None
    region: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    status: Optional[str] = None
    approval_status: Optional[str] = None
    approved_by: Optional[str] = None
    notes: Optional[str] = None


class CommunityTemplateOut(CommunityTemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommunityMessageLogOut(BaseModel):
    id: int
    contact_id: Optional[int] = None
    template_id: Optional[int] = None
    channel: str
    direction: str
    subject: Optional[str] = None
    body: str
    delivery_status: str
    block_reason: Optional[str] = None
    sent_by: Optional[str] = None
    created_at: datetime
    sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CommunityPreviewMessageOut(BaseModel):
    contact_id: int
    full_name: str
    channel: str
    allowed: bool
    best_channel: Optional[str] = None
    block_reason: Optional[str] = None
    subject: Optional[str] = None
    body: str
