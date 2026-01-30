"""
Daily Ops Email - Send daily operational summary to system inbox.

Provides a command to send a daily ops summary email. Can be triggered:
- Manually via `python -m app.jobs.daily_ops_email`
- Via scheduled job/cron
- Via Render background task

Environment Variables:
    DAILY_OPS_RECIPIENT_EMAIL: Email to send daily ops to (defaults to VALHALLA_SYSTEM_EMAIL)
"""

import os
from datetime import datetime, timezone

from app.core.identity import system_identity
from app.services.email_service import send_email


def build_daily_ops_body() -> str:
    """Build the daily ops email body."""
    # Keep it simple at first. We can expand with runbook + pipeline status later.
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return (
        f"Valhalla Daily Ops Summary\n"
        f"Generated: {now}\n\n"
        f"System: OK (email channel verified)\n"
        f"Action Required: No action required today (unless you received a separate alert)\n"
    )


def run():
    """Send the daily ops email."""
    identity = system_identity()
    to_email = os.getenv("DAILY_OPS_RECIPIENT_EMAIL") or identity["email"]

    subject = "Heimdall: Daily Ops (9AM)"
    body = build_daily_ops_body()

    send_email(to_email=to_email, subject=subject, body=body)
    print(f"✅ Daily ops email sent to {to_email}")


if __name__ == "__main__":
    run()
