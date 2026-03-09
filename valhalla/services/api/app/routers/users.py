"""
FastAPI router for user profile management.
Provides endpoints for profiles, privacy, preferences, settings, and activity logs.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.users.service import UserProfileService
from app.users.schemas import (
    UserProfileCreate, UserProfileUpdate, UserProfileOut,
    DataPrivacyUpdate, DataPrivacyOut,
    UserPreferencesUpdate, UserPreferencesOut,
    AccountSettingsUpdate, AccountSettingsOut,
    ActivityLogOut, UserCompleteProfile
)


router = APIRouter(prefix="/users", tags=["users"])


# User Profile Endpoints
@router.post("/profile", response_model=UserProfileOut, status_code=201)
async def create_user_profile(
    profile: UserProfileCreate,
    db: Session = Depends(get_db)
):
    """Create a new user profile with default settings."""
    service = UserProfileService(db)
    try:
        return service.create_profile(profile)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/profile/{user_id}", response_model=UserProfileOut)
async def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user profile by ID."""
    service = UserProfileService(db)
    profile = service.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return profile


@router.get("/profile/email/{email}", response_model=UserProfileOut)
async def get_user_profile_by_email(
    email: str,
    db: Session = Depends(get_db)
):
    """Get user profile by email."""
    service = UserProfileService(db)
    profile = service.get_profile_by_email(email)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return profile


@router.patch("/profile/{user_id}", response_model=UserProfileOut)
async def update_user_profile(
    user_id: int,
    profile_update: UserProfileUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Update user profile."""
    service = UserProfileService(db)
    profile = service.update_profile(user_id, profile_update)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return profile


@router.delete("/profile/{user_id}")
async def delete_user_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Delete user profile and all related data."""
    service = UserProfileService(db)
    success = service.delete_profile(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User profile not found")
    return {"ok": True, "message": "User profile deleted successfully"}


# Privacy Settings Endpoints
@router.get("/privacy/{user_id}", response_model=DataPrivacyOut)
async def get_privacy_settings(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user privacy settings."""
    service = UserProfileService(db)
    privacy = service.get_privacy_settings(user_id)
    if not privacy:
        raise HTTPException(status_code=404, detail="Privacy settings not found")
    return privacy


@router.patch("/privacy/{user_id}", response_model=DataPrivacyOut)
async def update_privacy_settings(
    user_id: int,
    privacy_update: DataPrivacyUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Update user privacy settings."""
    service = UserProfileService(db)
    
    # Log the privacy update
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    service.log_activity(user_id, "Privacy Settings Viewed/Updated", 
                        ip_address=client_ip, user_agent=user_agent)
    
    privacy = service.update_privacy_settings(user_id, privacy_update)
    if not privacy:
        raise HTTPException(status_code=404, detail="Privacy settings not found")
    return privacy


# User Preferences Endpoints
@router.get("/preferences/{user_id}", response_model=UserPreferencesOut)
async def get_user_preferences(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user preferences."""
    service = UserProfileService(db)
    preferences = service.get_preferences(user_id)
    if not preferences:
        raise HTTPException(status_code=404, detail="Preferences not found")
    return preferences


@router.patch("/preferences/{user_id}", response_model=UserPreferencesOut)
async def update_user_preferences(
    user_id: int,
    preferences_update: UserPreferencesUpdate,
    db: Session = Depends(get_db)
):
    """Update user preferences."""
    service = UserProfileService(db)
    preferences = service.update_preferences(user_id, preferences_update)
    if not preferences:
        raise HTTPException(status_code=404, detail="Preferences not found")
    return preferences


# Account Settings Endpoints
@router.get("/account-settings/{user_id}", response_model=AccountSettingsOut)
async def get_account_settings(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get account security settings (password hash excluded from response)."""
    service = UserProfileService(db)
    settings = service.get_account_settings(user_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Account settings not found")
    return settings


@router.patch("/account-settings/{user_id}", response_model=AccountSettingsOut)
async def update_account_settings(
    user_id: int,
    settings_update: AccountSettingsUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Update account security settings."""
    service = UserProfileService(db)
    
    # Log security-sensitive action
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    service.log_activity(user_id, "Account Settings Updated", 
                        details="Security settings modified",
                        ip_address=client_ip, user_agent=user_agent)
    
    settings = service.update_account_settings(user_id, settings_update)
    if not settings:
        raise HTTPException(status_code=404, detail="Account settings not found")
    return settings


# Activity Log Endpoints
@router.get("/activity-logs/{user_id}", response_model=List[ActivityLogOut])
async def get_activity_logs(
    user_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get user activity logs."""
    service = UserProfileService(db)
    return service.get_activity_logs(user_id, limit)


# Complete Profile Endpoint
@router.get("/complete-profile/{user_id}", response_model=UserCompleteProfile)
async def get_complete_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get complete user profile with all related data."""
    service = UserProfileService(db)
    complete = service.get_complete_profile(user_id)
    if not complete:
        raise HTTPException(status_code=404, detail="User profile not found")
    return complete


# Search Endpoint
@router.get("/search", response_model=List[UserProfileOut])
async def search_profiles(
    q: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Search user profiles by name or email."""
    service = UserProfileService(db)
    return service.search_profiles(q, limit)
