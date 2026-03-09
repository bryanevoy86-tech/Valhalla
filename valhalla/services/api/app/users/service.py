"""
Service layer for user profile management.
Handles business logic for user profiles, privacy, preferences, settings, and activity logs.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import hashlib

from .models import UserProfile, DataPrivacy, UserPreferences, AccountSettings, ActivityLog
from .schemas import (
    UserProfileCreate, UserProfileUpdate,
    DataPrivacyUpdate, UserPreferencesUpdate, AccountSettingsUpdate,
    ActivityLogCreate
)


class UserProfileService:
    """Service for managing user profiles and related data."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # User Profile Methods
    def create_profile(self, profile_data: UserProfileCreate) -> UserProfile:
        """Create a new user profile with default privacy, preferences, and settings."""
        # Check if email already exists
        existing = self.db.query(UserProfile).filter(
            UserProfile.email == profile_data.email
        ).first()
        if existing:
            raise ValueError(f"User with email {profile_data.email} already exists")
        
        # Create profile
        profile = UserProfile(**profile_data.model_dump())
        self.db.add(profile)
        self.db.flush()  # Get the user_id
        
        # Create default privacy settings
        privacy = DataPrivacy(user_id=profile.user_id)
        self.db.add(privacy)
        
        # Create default preferences
        preferences = UserPreferences(user_id=profile.user_id)
        self.db.add(preferences)
        
        # Create default account settings (with placeholder password hash)
        settings = AccountSettings(
            user_id=profile.user_id,
            password_hash=self._hash_password("changeme123")  # Should be replaced by actual password
        )
        self.db.add(settings)
        
        self.db.commit()
        self.db.refresh(profile)
        
        # Log profile creation
        self.log_activity(profile.user_id, "Profile Created", "New user profile created")
        
        return profile
    
    def get_profile(self, user_id: int) -> Optional[UserProfile]:
        """Get user profile by ID."""
        return self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    def get_profile_by_email(self, email: str) -> Optional[UserProfile]:
        """Get user profile by email."""
        return self.db.query(UserProfile).filter(UserProfile.email == email).first()
    
    def update_profile(self, user_id: int, update_data: UserProfileUpdate) -> Optional[UserProfile]:
        """Update user profile."""
        profile = self.get_profile(user_id)
        if not profile:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(profile, key, value)
        
        profile.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(profile)
        
        self.log_activity(user_id, "Profile Updated", f"Updated fields: {', '.join(update_dict.keys())}")
        
        return profile
    
    def delete_profile(self, user_id: int) -> bool:
        """Delete user profile and all related data (cascade)."""
        profile = self.get_profile(user_id)
        if not profile:
            return False
        
        self.log_activity(user_id, "Profile Deleted", "User profile and all related data deleted")
        
        self.db.delete(profile)
        self.db.commit()
        return True
    
    # Data Privacy Methods
    def get_privacy_settings(self, user_id: int) -> Optional[DataPrivacy]:
        """Get user privacy settings."""
        return self.db.query(DataPrivacy).filter(DataPrivacy.user_id == user_id).first()
    
    def update_privacy_settings(self, user_id: int, privacy_data: DataPrivacyUpdate) -> Optional[DataPrivacy]:
        """Update privacy settings."""
        privacy = self.get_privacy_settings(user_id)
        if not privacy:
            return None
        
        update_dict = privacy_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(privacy, key, value)
        
        if 'consent' in update_dict:
            privacy.consent_date = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(privacy)
        
        self.log_activity(user_id, "Privacy Settings Updated", f"Updated: {', '.join(update_dict.keys())}")
        
        return privacy
    
    # User Preferences Methods
    def get_preferences(self, user_id: int) -> Optional[UserPreferences]:
        """Get user preferences."""
        return self.db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
    
    def update_preferences(self, user_id: int, pref_data: UserPreferencesUpdate) -> Optional[UserPreferences]:
        """Update user preferences."""
        preferences = self.get_preferences(user_id)
        if not preferences:
            return None
        
        update_dict = pref_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(preferences, key, value)
        
        self.db.commit()
        self.db.refresh(preferences)
        
        self.log_activity(user_id, "Preferences Updated", f"Updated: {', '.join(update_dict.keys())}")
        
        return preferences
    
    # Account Settings Methods
    def get_account_settings(self, user_id: int) -> Optional[AccountSettings]:
        """Get account settings."""
        return self.db.query(AccountSettings).filter(AccountSettings.user_id == user_id).first()
    
    def update_account_settings(self, user_id: int, settings_data: AccountSettingsUpdate) -> Optional[AccountSettings]:
        """Update account settings."""
        settings = self.get_account_settings(user_id)
        if not settings:
            return None
        
        update_dict = settings_data.model_dump(exclude_unset=True)
        
        # Handle password hashing
        if 'password' in update_dict:
            settings.password_hash = self._hash_password(update_dict.pop('password'))
            settings.last_password_change = datetime.utcnow()
        
        for key, value in update_dict.items():
            setattr(settings, key, value)
        
        self.db.commit()
        self.db.refresh(settings)
        
        self.log_activity(user_id, "Account Settings Updated", "Security settings modified")
        
        return settings
    
    # Activity Log Methods
    def log_activity(self, user_id: int, action: str, details: Optional[str] = None,
                    ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> ActivityLog:
        """Log user activity."""
        log = ActivityLog(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow()
        )
        self.db.add(log)
        self.db.commit()
        return log
    
    def get_activity_logs(self, user_id: int, limit: int = 50) -> List[ActivityLog]:
        """Get recent activity logs for a user."""
        return self.db.query(ActivityLog)\
            .filter(ActivityLog.user_id == user_id)\
            .order_by(ActivityLog.timestamp.desc())\
            .limit(limit)\
            .all()
    
    # Utility Methods
    @staticmethod
    def _hash_password(password: str) -> str:
        """
        Simple password hashing for demo purposes.
        In production, use bcrypt, argon2, or similar secure hashing.
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def get_complete_profile(self, user_id: int) -> Optional[dict]:
        """Get complete user profile with all related data."""
        profile = self.get_profile(user_id)
        if not profile:
            return None
        
        return {
            'profile': profile,
            'privacy': self.get_privacy_settings(user_id),
            'preferences': self.get_preferences(user_id),
            'account_settings': self.get_account_settings(user_id),
            'recent_activities': self.get_activity_logs(user_id, limit=10)
        }
    
    def search_profiles(self, query: str, limit: int = 20) -> List[UserProfile]:
        """Search profiles by name or email."""
        search = f"%{query}%"
        return self.db.query(UserProfile)\
            .filter(
                (UserProfile.first_name.ilike(search)) |
                (UserProfile.last_name.ilike(search)) |
                (UserProfile.email.ilike(search))
            )\
            .limit(limit)\
            .all()
