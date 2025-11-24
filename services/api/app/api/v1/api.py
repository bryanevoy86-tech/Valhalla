from fastapi import APIRouter
from .endpoints import root  # existing root endpoint
from app.routers.loki import router as loki_router

# New API v1 domain routers (packs 73-81 and beyond)
try:
	from app.api.api_v1.endpoints.staff import router as staff_router
except Exception:
	staff_router = None
try:
	from app.api.api_v1.endpoints.contractors import router as contractors_router
except Exception:
	contractors_router = None
try:
	from app.api.api_v1.endpoints.resort import router as resort_router
except Exception:
	resort_router = None
try:
	from app.api.api_v1.endpoints.trust import router as trust_router
except Exception:
	trust_router = None
try:
	from app.api.api_v1.endpoints.legacy import router as legacy_router
except Exception:
	legacy_router = None
try:
	from app.api.api_v1.endpoints.shield import router as shield_router
except Exception:
	shield_router = None
try:
	from app.api.api_v1.endpoints.legal import router as legal_router
except Exception:
	legal_router = None
try:
	from app.api.api_v1.endpoints.underwriter import router as underwriter_router
except Exception:
	underwriter_router = None
try:
	from app.api.api_v1.endpoints.materials import router as materials_router
except Exception:
	materials_router = None
try:
	from app.api.api_v1.endpoints.queen import router as queen_router
except Exception:
	queen_router = None
try:
	from app.api.api_v1.endpoints.children import router as children_router
except Exception:
	children_router = None
try:
	from app.api.api_v1.endpoints.compliance import router as compliance_router
except Exception:
	compliance_router = None
try:
	from app.api.api_v1.endpoints.integrity import router as integrity_router
except Exception:
	integrity_router = None
try:
	from app.api.api_v1.endpoints.health_monitor import router as health_monitor_router
except Exception:
	health_monitor_router = None
try:
	from app.api.api_v1.endpoints.settings import router as settings_router
except Exception:
	settings_router = None
try:
	from app.api.api_v1.endpoints.training import router as training_router
except Exception:
	training_router = None
try:
	from app.api.api_v1.endpoints.knowledge import router as knowledge_router
except Exception:
	knowledge_router = None
try:
	from app.api.api_v1.endpoints.snapshot import router as snapshot_router
except Exception:
	snapshot_router = None
try:
	from app.api.api_v1.endpoints.empire_status import router as empire_status_router
except Exception:
	empire_status_router = None
try:
	from app.api.api_v1.endpoints.notifications import router as notifications_router
except Exception:
	notifications_router = None
try:
	from app.api.api_v1.endpoints.automation import router as automation_router
except Exception:
	automation_router = None
try:
	from app.api.api_v1.endpoints.kpi import router as kpi_router
except Exception:
	kpi_router = None
try:
	from app.api.api_v1.endpoints.tasks import router as tasks_router
except Exception:
	tasks_router = None
try:
	from app.api.api_v1.endpoints.automation_run import router as automation_run_router
except Exception:
	automation_run_router = None
try:
	from app.api.api_v1.endpoints.heimdall_action import router as heimdall_action_router
except Exception:
	heimdall_action_router = None
try:
	from app.api.api_v1.endpoints.scheduler import router as scheduler_router
except Exception:
	scheduler_router = None
try:
	from app.api.api_v1.endpoints.error_log import router as error_log_router
except Exception:
	error_log_router = None
try:
	from app.api.api_v1.endpoints.ai_personas import router as ai_personas_router
except Exception:
	ai_personas_router = None
try:
	from app.api.api_v1.endpoints.funfund import router as funfund_router
except Exception:
	funfund_router = None
try:
	from app.api.api_v1.endpoints.truck_plan import router as truck_plan_router
except Exception:
	truck_plan_router = None
try:
	from app.api.api_v1.endpoints.bahamas_plan import router as bahamas_plan_router
except Exception:
	bahamas_plan_router = None
try:
	from app.api.api_v1.endpoints.trust_status import router as trust_status_router
except Exception:
	trust_status_router = None

api_router = APIRouter()
api_router.include_router(root.router, prefix="", tags=["Root"])
api_router.include_router(loki_router)

if staff_router:
	api_router.include_router(staff_router, prefix="/staff", tags=["Staff"])
if contractors_router:
	api_router.include_router(contractors_router, prefix="/contractors", tags=["Contractors"])
if resort_router:
	api_router.include_router(resort_router, prefix="/resort", tags=["Resort"])
if trust_router:
	api_router.include_router(trust_router, prefix="/trust", tags=["Trust"])
if legacy_router:
	api_router.include_router(legacy_router, prefix="/legacy", tags=["Legacy"])
if shield_router:
	api_router.include_router(shield_router, prefix="/shield", tags=["Shield Mode"])
if legal_router:
	api_router.include_router(legal_router, prefix="/legal", tags=["Legal Compliance"])
if underwriter_router:
	api_router.include_router(underwriter_router, prefix="/underwriter", tags=["Underwriter"])
if materials_router:
	api_router.include_router(materials_router, prefix="/materials", tags=["Materials"])
if queen_router:
	api_router.include_router(queen_router, prefix="/queen-streams", tags=["Queen"])
if children_router:
	api_router.include_router(children_router, prefix="/children", tags=["Children"])
if compliance_router:
	api_router.include_router(compliance_router, prefix="/compliance-signals", tags=["Compliance"])
if integrity_router:
	api_router.include_router(integrity_router, prefix="/integrity-events", tags=["Integrity"])
if health_monitor_router:
	api_router.include_router(health_monitor_router, prefix="/system-health", tags=["System Health"])
if settings_router:
	api_router.include_router(settings_router, prefix="/settings", tags=["Settings"])
if training_router:
	api_router.include_router(training_router, prefix="/training-jobs", tags=["Training"])
if knowledge_router:
	api_router.include_router(knowledge_router, prefix="/knowledge-sources", tags=["Knowledge"])
if snapshot_router:
	api_router.include_router(snapshot_router, prefix="/empire-snapshots", tags=["Snapshots"])
if empire_status_router:
	api_router.include_router(empire_status_router, prefix="/empire-status", tags=["Empire Status"])
if notifications_router:
	api_router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
if automation_router:
	api_router.include_router(automation_router, prefix="/automation-rules", tags=["Automation"])
if kpi_router:
	api_router.include_router(kpi_router, prefix="/kpi-metrics", tags=["KPI"])
if tasks_router:
	api_router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
if automation_run_router:
	api_router.include_router(automation_run_router, prefix="/automation-runs", tags=["Automation Runs"])
if heimdall_action_router:
	api_router.include_router(heimdall_action_router, prefix="/heimdall-action", tags=["Heimdall Action"])
if scheduler_router:
	api_router.include_router(scheduler_router, prefix="/scheduled-jobs", tags=["Scheduler"])
if error_log_router:
	api_router.include_router(error_log_router, prefix="/error-logs", tags=["Errors"])
if ai_personas_router:
	api_router.include_router(ai_personas_router, prefix="/ai-personas", tags=["AI Personas"])
if funfund_router:
	api_router.include_router(funfund_router, prefix="/funfund-routing", tags=["Fun Fund"])
if truck_plan_router:
	api_router.include_router(truck_plan_router, prefix="/truck-plans", tags=["Truck Plan"])
if bahamas_plan_router:
	api_router.include_router(bahamas_plan_router, prefix="/bahamas-plans", tags=["Bahamas Plan"])
if trust_status_router:
	api_router.include_router(trust_status_router, prefix="/trust-status", tags=["Trust Status"])


