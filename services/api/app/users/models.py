"""
SQLAlchemy models for user profile management.
Includes UserProfile, DataPrivacy, UserPreferences, AccountSettings, and ActivityLog.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

try:
    from app.core.db import Base
except ImportError:
    # Fallback for environments where Base might not be available
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()


class UserProfile(Base):
    """User profile information."""
    __tablename__ = 'user_profiles'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    phone_number = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    profile_picture = Column(String, nullable=True)  # URL or file path
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    privacy_data = relationship('DataPrivacy', back_populates='user', uselist=False, cascade='all, delete-orphan')
    preferences = relationship('UserPreferences', back_populates='user', uselist=False, cascade='all, delete-orphan')
    account_settings = relationship('AccountSettings', back_populates='user', uselist=False, cascade='all, delete-orphan')
    activity_logs = relationship('ActivityLog', back_populates='user', cascade='all, delete-orphan')


class DataPrivacy(Base):
    """User data privacy settings and requests."""
    __tablename__ = 'data_privacy'

    data_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user_profiles.user_id', ondelete='CASCADE'), nullable=False, unique=True)
    data_access_request = Column(Boolean, default=False)
    data_deletion_request = Column(Boolean, default=False)
    consent = Column(Boolean, default=True)  # User consent for data processing
    consent_date = Column(DateTime, default=datetime.utcnow)

    user = relationship('UserProfile', back_populates='privacy_data')


class UserPreferences(Base):
    """User application preferences."""
    __tablename__ = 'user_preferences'

    preference_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user_profiles.user_id', ondelete='CASCADE'), nullable=False, unique=True)
    email_preferences = Column(String, default="Weekly")  # Daily, Weekly, Never
    theme = Column(String, default="Light")  # Light, Dark
    notification_preferences = Column(String, default="Email")  # SMS, Email, Push
    language = Column(String, default="en")  # Language preference
    timezone = Column(String, default="UTC")  # User timezone

    user = relationship('UserProfile', back_populates='preferences')


class AccountSettings(Base):
    """User account security settings."""
    __tablename__ = 'account_settings'

    account_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user_profiles.user_id', ondelete='CASCADE'), nullable=False, unique=True)
    password_hash = Column(String, nullable=False)  # Store hashed passwords only
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    two_factor_enabled = Column(Boolean, default=False)  # 2FA for added security
    last_password_change = Column(DateTime, default=datetime.utcnow)
    account_locked = Column(Boolean, default=False)

    user = relationship('UserProfile', back_populates='account_settings')


class ActivityLog(Base):
    """User activity logging for audit trail."""
    __tablename__ = 'activity_logs'

    activity_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user_profiles.user_id', ondelete='CASCADE'), nullable=False)
    action = Column(String, nullable=False)  # Description of the action
    details = Column(Text, nullable=True)  # Additional context
    ip_address = Column(String, nullable=True)  # IP address of the request
    user_agent = Column(String, nullable=True)  # Browser/client info
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship('UserProfile', back_populates='activity_logs')
