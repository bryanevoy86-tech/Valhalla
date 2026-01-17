"""Dashboard endpoint - WeWeb/frontend-ready one-screen view."""
from fastapi import APIRouter
from ..health.dashboard import one_screen_dashboard

router = APIRouter(prefix="/dashboard", tags=["Core: Dashboard"])

@router.get("")
def dashboard():
    """One-screen dashboard: status, alerts, capital, summary in single response."""
    return one_screen_dashboard()
