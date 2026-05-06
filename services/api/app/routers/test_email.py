"""
Test and Daily Ops Email router - delegates to test_email_router.
This file exists to expose the daily-ops-email and test-email endpoints
to the autoloader in main.py.
"""

from app.api.notify.test_email_router import router

__all__ = ["router"]
