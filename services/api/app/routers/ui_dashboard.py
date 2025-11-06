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
