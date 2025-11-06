from typing import List
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.metrics.service import MetricsService
from app.metrics.schemas import MetricsOut
from app.alerts.service import AlertsService
from app.alerts.schemas import AlertOut
from app.health.service import HealthCheckService
from app.health.schemas import HealthCheckOut
from app.analytics.schemas import UserActivityOut
from app.roles.schemas import RoleOut


router = APIRouter(prefix="/ui-dashboard", tags=["ui-dashboard"])

# Templates live under services/api/app/ui_dashboard/templates relative to app working dir
templates = Jinja2Templates(directory="app/ui_dashboard/templates")


@router.get("/metrics-dashboard", response_model=MetricsOut)
async def get_metrics_dashboard():
    """Return metrics JSON for UI dashboard consumption."""
    return MetricsService.get_metrics()


@router.get("/metrics-dashboard-ui", response_class=HTMLResponse)
async def render_metrics_dashboard(request: Request):
    """Render the admin metrics dashboard HTML (Chart.js)."""
    return templates.TemplateResponse("metrics_dashboard.html", {"request": request})


@router.get("/alerts-dashboard", response_model=List[AlertOut])
async def get_alerts_dashboard():
    """Return current alerts based on metrics thresholds."""
    metrics = MetricsService.get_metrics()
    alerts = AlertsService.check_thresholds(metrics)
    return alerts


@router.get("/alerts-dashboard-ui", response_class=HTMLResponse)
async def render_alerts_dashboard(request: Request):
    """Render the real-time alerts dashboard HTML."""
    return templates.TemplateResponse("alerts_dashboard.html", {"request": request})


@router.get("/health-dashboard", response_model=HealthCheckOut)
async def get_health_dashboard():
    """Return system health snapshot for dashboard."""
    return HealthCheckService.check_system_health()


@router.get("/health-dashboard-ui", response_class=HTMLResponse)
async def render_health_dashboard(request: Request):
    """Render the system health dashboard HTML."""
    return templates.TemplateResponse("health_dashboard.html", {"request": request})


@router.get("/analytics-dashboard-ui", response_class=HTMLResponse)
async def render_analytics_dashboard(request: Request):
    """Render the user analytics dashboard HTML."""
    return templates.TemplateResponse("analytics_dashboard.html", {"request": request})


@router.get("/role-permissions-dashboard-ui", response_class=HTMLResponse)
async def render_role_permissions_dashboard(request: Request):
    """Render the role permissions dashboard HTML."""
    return templates.TemplateResponse("role_permissions_dashboard.html", {"request": request})


@router.get("/security-dashboard-ui", response_class=HTMLResponse)
async def render_security_dashboard(request: Request):
    """Render the security features dashboard HTML."""
    return templates.TemplateResponse("security_dashboard.html", {"request": request})


@router.get("/encryption-dashboard-ui", response_class=HTMLResponse)
async def render_encryption_dashboard(request: Request):
    """Render the encryption dashboard HTML."""
    return templates.TemplateResponse("encryption_dashboard.html", {"request": request})


@router.get("/logging-dashboard-ui", response_class=HTMLResponse)
async def render_logging_dashboard(request: Request):
    """Render the logging/audit dashboard HTML."""
    return templates.TemplateResponse("logging_dashboard.html", {"request": request})


@router.get("/lang-dashboard-ui", response_class=HTMLResponse)
async def render_lang_dashboard(request: Request):
    """Render the multi-language dashboard HTML."""
    return templates.TemplateResponse("lang_dashboard.html", {"request": request})


@router.get("/notifications-dashboard-ui", response_class=HTMLResponse)
async def render_notifications_dashboard(request: Request):
    """Render the real-time notifications dashboard HTML."""
    return templates.TemplateResponse("notifications_dashboard.html", {"request": request})


@router.get("/messaging-dashboard-ui", response_class=HTMLResponse)
async def render_messaging_dashboard(request: Request):
    """Render the email/SMS messaging dashboard HTML."""
    return templates.TemplateResponse("messaging_dashboard.html", {"request": request})

@router.get("/user-profile-dashboard-ui", response_class=HTMLResponse)
async def render_user_profile_dashboard(request: Request):
    """Render the user profile management dashboard HTML."""
    return templates.TemplateResponse("user_profile_dashboard.html", {"request": request})


@router.get("/rbac-dashboard-ui", response_class=HTMLResponse)
async def render_rbac_dashboard(request: Request):
    """Render the RBAC (Role-Based Access Control) dashboard HTML."""
    return templates.TemplateResponse("rbac_dashboard.html", {"request": request})


@router.get("/payments-dashboard-ui", response_class=HTMLResponse)
async def render_payments_dashboard(request: Request):
    """Render the Payments dashboard HTML."""
    return templates.TemplateResponse("payments_dashboard.html", {"request": request})


@router.get("/negotiations-dashboard-ui", response_class=HTMLResponse)
async def render_negotiations_dashboard(request: Request):
    """Render the Negotiations dashboard HTML."""
    return templates.TemplateResponse("negotiations_dashboard.html", {"request": request})


@router.get("/leads-dashboard-ui", response_class=HTMLResponse)
async def render_leads_dashboard(request: Request):
    """Render the Advanced Lead Scraper dashboard HTML."""
    return templates.TemplateResponse("leads_dashboard.html", {"request": request})


@router.get("/advanced-negotiation-dashboard-ui", response_class=HTMLResponse)
async def render_advanced_negotiation_dashboard(request: Request):
    """Render the Advanced Negotiation Techniques dashboard HTML."""
    return templates.TemplateResponse("advanced_negotiation_dashboard.html", {"request": request})


@router.get("/behavioral-profiling-dashboard-ui", response_class=HTMLResponse)
async def render_behavioral_profiling_dashboard(request: Request):
    """Render the AI Behavioral Profiling dashboard HTML."""
    return templates.TemplateResponse("behavioral_profiling_dashboard.html", {"request": request})


@router.get("/deal-analyzer-dashboard-ui", response_class=HTMLResponse)
async def render_deal_analyzer_dashboard(request: Request):
    """Render the Automated Deal Analyzer dashboard HTML."""
    return templates.TemplateResponse("deal_analyzer_dashboard.html", {"request": request})
