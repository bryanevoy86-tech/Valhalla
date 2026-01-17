# Pack 26: Email and SMS Integration

This pack adds email (SMTP) and SMS (Twilio) messaging with templates, APIs, and a simple UI dashboard. It also supports sending notifications to users based on their existing preferences in the User module.

## Configuration
Environment variables (also exposed in `app.core.settings`):

- SMTP_HOST, SMTP_PORT (default 587), SMTP_USER, SMTP_PASS, SMTP_FROM
- TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER

## Data Model
- `EmailTemplate` (SQLAlchemy): template_name (unique), subject, body, created_at

## API
Base: `/api/messaging`

- POST `/templates` -> create template
- GET `/templates` -> list templates
- GET `/templates/{template_name}` -> get template by name
- DELETE `/templates/{template_id}` -> delete template
- POST `/send-email` -> send raw email {to, subject, body, html?}
- POST `/send-sms` -> send raw SMS {to, message}
- POST `/send-with-template` -> render and send email by template name {template_name, to? | user_id?, variables}
- POST `/notify-user` -> notify a user by preferences {user_id, subject, body, sms_message?}

`/notify-user` reads the user's preferences from `UserPreferences.notification_preferences`:
- Email is allowed if it contains "email" (case-insensitive) or is empty (default allow)
- SMS is allowed if it contains "sms", user has a phone number, and `sms_message` is provided

## UI Dashboard
- Route: `/api/ui-dashboard/messaging-dashboard-ui`
- Template: `app/ui_dashboard/templates/messaging_dashboard.html`
  - Send email
  - Send SMS
  - Send with template
  - Notify user by preferences
  - List templates

## Notes
- If SMTP/Twilio are not configured, the API returns a friendly failure message.
- Twilio SDK is added to `services/api/requirements.txt`.
- Tables auto-create on startup if DB is available.
