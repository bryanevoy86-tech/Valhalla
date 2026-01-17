# services/api/app/schemas/notifications_flow.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class NotifyDealPartiesRequest(BaseModel):
    """
    Input for the notifications flow.

    You pass a backend_deal_id and the system builds suggested messages
    for seller + matched buyers.
    """

    backend_deal_id: int = Field(
        ...,
        description="Backend Deal.id to notify parties about.",
    )
    include_seller: bool = Field(
        default=True,
        description="Whether to prepare a seller notification.",
    )
    include_buyers: bool = Field(
        default=True,
        description="Whether to prepare notifications for matched buyers.",
    )
    min_buyer_score: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum buyer match score to include in notifications.",
    )
    max_buyers: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of buyer notifications to generate.",
    )


class SellerNotification(BaseModel):
    """
    Suggested notification for the seller.
    """

    to_email: Optional[EmailStr] = None
    to_phone: Optional[str] = None
    channel_hint: str = Field(
        default="email_or_sms",
        description="Primary suggested channel to use.",
    )
    subject: str
    body_text: str
    body_markdown: Optional[str] = None
    meta: Dict[str, str] = Field(default_factory=dict)


class BuyerNotification(BaseModel):
    """
    Suggested notification for a buyer.
    """

    buyer_id: int
    buyer_name: str
    to_email: Optional[EmailStr] = None
    to_phone: Optional[str] = None
    channel_hint: str = Field(
        default="email_or_sms",
        description="Primary suggested channel to use.",
    )
    subject: str
    body_text: str
    body_markdown: Optional[str] = None
    match_score: float
    meta: Dict[str, str] = Field(default_factory=dict)


class NotifyDealPartiesResponse(BaseModel):
    """
    Output of the notifications flow.
    """

    backend_deal_id: int
    seller_notification: Optional[SellerNotification] = None
    buyer_notifications: List[BuyerNotification] = Field(
        default_factory=list,
        description="Notifications for matched buyers.",
    )
    notes: Optional[str] = None
    metadata: Dict[str, str] = Field(default_factory=dict)
