"""
Pydantic schemas for user profile management.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# User Profile Schemas
class UserProfileCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone_number: Optional[str] = None
    address: Optional[str] = None
    profile_picture: Optional[str] = None


class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = None
    address: Optional[str] = None
    profile_picture: Optional[str] = None


class UserProfileOut(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    email: str
    phone_number: Optional[str] = None
    address: Optional[str] = None
    profile_picture: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Data Privacy Schemas
class DataPrivacyUpdate(BaseModel):
    data_access_request: Optional[bool] = None
    data_deletion_request: Optional[bool] = None
    consent: Optional[bool] = None


class DataPrivacyOut(BaseModel):
    data_id: int
    user_id: int
    data_access_request: bool
    data_deletion_request: bool
    consent: bool
    consent_date: datetime

    class Config:
        from_attributes = True


# User Preferences Schemas
class UserPreferencesUpdate(BaseModel):
    email_preferences: Optional[str] = Field(None, pattern="^(Daily|Weekly|Never)$")
    theme: Optional[str] = Field(None, pattern="^(Light|Dark)$")
    notification_preferences: Optional[str] = Field(None, pattern="^(SMS|Email|Push)$")
    language: Optional[str] = None
    timezone: Optional[str] = None


class UserPreferencesOut(BaseModel):
    preference_id: int
    user_id: int
    email_preferences: str
    theme: str
    notification_preferences: str
    language: str
    timezone: str

    class Config:
        from_attributes = True


# Account Settings Schemas
class AccountSettingsUpdate(BaseModel):
    password: Optional[str] = Field(None, min_length=8)  # Will be hashed
    email_verified: Optional[bool] = None
    phone_verified: Optional[bool] = None
    two_factor_enabled: Optional[bool] = None
    account_locked: Optional[bool] = None


class AccountSettingsOut(BaseModel):
    account_id: int
    user_id: int
    email_verified: bool
    phone_verified: bool
    two_factor_enabled: bool
    account_locked: bool
    last_password_change: datetime

    class Config:
        from_attributes = True


# Activity Log Schemas
class ActivityLogCreate(BaseModel):
    user_id: int
    action: str
    details: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class ActivityLogOut(BaseModel):
    activity_id: int
    user_id: int
    action: str
    details: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


# Combined User Info Schema (for comprehensive view)
class UserCompleteProfile(BaseModel):
    profile: UserProfileOut
    privacy: Optional[DataPrivacyOut] = None
    preferences: Optional[UserPreferencesOut] = None
    account_settings: Optional[AccountSettingsOut] = None
    recent_activities: list[ActivityLogOut] = []
