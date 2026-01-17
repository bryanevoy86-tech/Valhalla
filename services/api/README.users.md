# Pack 24: User Profile Management

## Overview

This pack provides a comprehensive user profile management system with support for user profiles, data privacy settings, user preferences, account security settings, and detailed activity logging. The system follows GDPR-compliant patterns and includes a full-featured dashboard for managing all aspects of user accounts.

## Features

- **User Profiles**: Complete user information management with CRUD operations
- **Data Privacy**: GDPR-compliant privacy settings with consent tracking
- **User Preferences**: Customizable application preferences (theme, notifications, language)
- **Account Security**: Password management, 2FA, email/phone verification
- **Activity Logging**: Comprehensive audit trail with IP and user agent tracking
- **Interactive Dashboard**: Full UI for creating and managing user profiles
- **Search Functionality**: Search users by name or email
- **Complete Profile View**: Single endpoint to retrieve all user-related data

## Database Models

### UserProfile
- `user_id` (Primary Key)
- `first_name`, `last_name`, `email` (unique, indexed)
- `phone_number`, `address`, `profile_picture`
- `created_at`, `updated_at`
- Relationships: privacy_data, preferences, account_settings, activity_logs

### DataPrivacy
- `data_id` (Primary Key)
- `user_id` (Foreign Key, unique)
- `data_access_request`, `data_deletion_request`, `consent`
- `consent_date`

### UserPreferences
- `preference_id` (Primary Key)
- `user_id` (Foreign Key, unique)
- `email_preferences` (Daily/Weekly/Never)
- `theme` (Light/Dark)
- `notification_preferences` (SMS/Email/Push)
- `language`, `timezone`

### AccountSettings
- `account_id` (Primary Key)
- `user_id` (Foreign Key, unique)
- `password_hash` (hashed with SHA256 for demo)
- `email_verified`, `phone_verified`, `two_factor_enabled`
- `last_password_change`, `account_locked`

### ActivityLog
- `activity_id` (Primary Key)
- `user_id` (Foreign Key)
- `action`, `details`
- `ip_address`, `user_agent`
- `timestamp` (indexed)

## API Endpoints

### User Profile Management

#### POST `/api/users/profile`
Create a new user profile with default settings.

**Request:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone_number": "+1234567890",
  "address": "123 Main St, City, State"
}
```

**Response:**
```json
{
  "user_id": 1,
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone_number": "+1234567890",
  "address": "123 Main St, City, State",
  "profile_picture": null,
  "created_at": "2025-11-05T10:30:00",
  "updated_at": "2025-11-05T10:30:00"
}
```

#### GET `/api/users/profile/{user_id}`
Get user profile by ID.

#### GET `/api/users/profile/email/{email}`
Get user profile by email address.

#### PATCH `/api/users/profile/{user_id}`
Update user profile (partial update).

**Request:**
```json
{
  "phone_number": "+9876543210",
  "address": "456 New Address"
}
```

#### DELETE `/api/users/profile/{user_id}`
Delete user profile and all related data (cascade delete).

### Data Privacy

#### GET `/api/users/privacy/{user_id}`
Get user privacy settings.

#### PATCH `/api/users/privacy/{user_id}`
Update privacy settings.

**Request:**
```json
{
  "consent": true,
  "data_access_request": false,
  "data_deletion_request": false
}
```

### User Preferences

#### GET `/api/users/preferences/{user_id}`
Get user preferences.

#### PATCH `/api/users/preferences/{user_id}`
Update user preferences.

**Request:**
```json
{
  "email_preferences": "Weekly",
  "theme": "Dark",
  "notification_preferences": "Email",
  "language": "en",
  "timezone": "America/New_York"
}
```

### Account Settings

#### GET `/api/users/account-settings/{user_id}`
Get account security settings (password hash excluded).

#### PATCH `/api/users/account-settings/{user_id}`
Update account settings.

**Request:**
```json
{
  "password": "newSecurePassword123",
  "two_factor_enabled": true,
  "email_verified": true
}
```

### Activity Logs

#### GET `/api/users/activity-logs/{user_id}?limit=50`
Get user activity logs (most recent first).

**Response:**
```json
[
  {
    "activity_id": 1,
    "user_id": 1,
    "action": "Profile Created",
    "details": "New user profile created",
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0...",
    "timestamp": "2025-11-05T10:30:00"
  }
]
```

### Combined Endpoints

#### GET `/api/users/complete-profile/{user_id}`
Get complete user profile with all related data in a single request.

**Response:**
```json
{
  "profile": { ... },
  "privacy": { ... },
  "preferences": { ... },
  "account_settings": { ... },
  "recent_activities": [ ... ]
}
```

#### GET `/api/users/search?q=john&limit=20`
Search user profiles by name or email.

## Dashboard

Access the interactive user profile management dashboard at:
**`/api/ui-dashboard/user-profile-dashboard-ui`**

### Dashboard Features:
- **Create Profile Tab**: Create new user profiles with all required information
- **View & Manage Tab**: Load and view complete user profiles
- **Preferences Tab**: Update email, theme, and notification preferences
- **Privacy Tab**: Manage data consent and privacy settings
- **Security Tab**: Configure 2FA, email/phone verification
- **Activity Logs Tab**: View detailed activity history with IP and timestamp

## Examples

### Create a new user profile:
```bash
curl -X POST "http://localhost:8000/api/users/profile" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane.smith@example.com",
    "phone_number": "+1234567890"
  }'
```

### Get complete profile:
```bash
curl "http://localhost:8000/api/users/complete-profile/1"
```

### Update preferences:
```bash
curl -X PATCH "http://localhost:8000/api/users/preferences/1" \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "Dark",
    "email_preferences": "Daily"
  }'
```

### Update privacy settings:
```bash
curl -X PATCH "http://localhost:8000/api/users/privacy/1" \
  -H "Content-Type: application/json" \
  -d '{
    "consent": true,
    "data_deletion_request": false
  }'
```

### Enable 2FA:
```bash
curl -X PATCH "http://localhost:8000/api/users/account-settings/1" \
  -H "Content-Type: application/json" \
  -d '{
    "two_factor_enabled": true
  }'
```

### Search users:
```bash
curl "http://localhost:8000/api/users/search?q=john&limit=10"
```

### Get activity logs:
```bash
curl "http://localhost:8000/api/users/activity-logs/1?limit=20"
```

## Security Considerations

### Password Storage
- Passwords are hashed using SHA256 in the current implementation
- **For production**: Replace with bcrypt, argon2, or similar secure hashing algorithms
- Never store plain-text passwords
- Implement password strength requirements

### Activity Logging
- All profile updates, privacy changes, and security modifications are logged
- IP addresses and user agents are captured for audit purposes
- Logs include timestamps for forensic analysis

### Data Privacy Compliance
- Consent tracking with timestamps
- Data access request flags (for GDPR Article 15)
- Data deletion request flags (for GDPR Article 17 - Right to be Forgotten)
- Cascade deletion ensures all user data is removed when profile is deleted

### Authentication & Authorization
- Current implementation doesn't include authentication middleware
- **Recommended**: Add JWT or session-based authentication
- **Recommended**: Implement role-based access control (RBAC)
- Users should only access their own data (or admins can access all)

## Integration Examples

### Creating a user profile after signup:
```python
from app.users.service import UserProfileService
from app.users.schemas import UserProfileCreate

async def signup_handler(signup_data, db: Session):
    service = UserProfileService(db)
    profile = service.create_profile(UserProfileCreate(
        first_name=signup_data.first_name,
        last_name=signup_data.last_name,
        email=signup_data.email
    ))
    
    # Set initial password
    service.update_account_settings(
        profile.user_id,
        AccountSettingsUpdate(password=signup_data.password)
    )
    
    return profile
```

### Logging user actions:
```python
from app.users.service import UserProfileService

async def some_protected_endpoint(user_id: int, request: Request, db: Session):
    service = UserProfileService(db)
    service.log_activity(
        user_id=user_id,
        action="Accessed Protected Resource",
        details="/api/some-endpoint",
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    # ... rest of endpoint logic
```

### Checking consent before processing data:
```python
async def process_user_data(user_id: int, db: Session):
    service = UserProfileService(db)
    privacy = service.get_privacy_settings(user_id)
    
    if not privacy or not privacy.consent:
        raise HTTPException(
            status_code=403,
            detail="User has not consented to data processing"
        )
    
    # Process data...
```

## Database Migration

To create the tables in your database:

```python
from app.users.models import Base
from app.core.db import engine

# Create all tables
Base.metadata.create_all(bind=engine)
```

Or if using Alembic:
```bash
alembic revision --autogenerate -m "Add user profile models"
alembic upgrade head
```

## Future Enhancements

### Enhanced Security
- Implement bcrypt/argon2 password hashing
- Add password reset functionality
- Implement account lockout after failed login attempts
- Add session management and token revocation

### Profile Features
- Profile picture upload and storage
- Email verification workflow
- Phone number verification via SMS
- Social media account linking

### Privacy Features
- Export user data (GDPR Article 20 - Data Portability)
- Automated data deletion workflows
- Privacy policy acceptance tracking
- Cookie consent management

### Preferences
- Notification channel preferences (push, email, SMS)
- Time zone-aware notifications
- Language-specific content delivery
- Accessibility settings

### Analytics
- User engagement metrics
- Login frequency tracking
- Feature usage analytics
- Activity heatmaps

## Notes

- All timestamps are stored in UTC
- Cascade deletions ensure data integrity
- Activity logs are automatically created for all profile changes
- Default values are set for preferences and privacy settings on profile creation
- Email uniqueness is enforced at the database level
- Current implementation uses SHA256 for password hashing (replace with bcrypt for production)
