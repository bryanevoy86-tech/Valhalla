from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.metrics.service import MetricsService
from app.metrics.schemas import MetricsOut


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
