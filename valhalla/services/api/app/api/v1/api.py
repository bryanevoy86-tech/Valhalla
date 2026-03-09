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
	from app.api.api_v1.endpoints.arbitrage_profiles import router as arbitrage_profiles_router
except Exception:
	arbitrage_profiles_router = None
try:
	from app.api.api_v1.endpoints.alerting import router as alerting_router
except Exception:
	alerting_router = None
try:
	from app.api.api_v1.endpoints.governance_settings import router as governance_settings_router
except Exception:
	governance_settings_router = None
try:
	from app.api.api_v1.endpoints.system_health import router as system_health_router
except Exception:
	system_health_router = None
try:
	from app.api.api_v1.endpoints.system_check_jobs import router as system_check_jobs_router
except Exception:
	system_check_jobs_router = None
try:
	from app.api.api_v1.endpoints.external_experts import router as external_experts_router
except Exception:
	external_experts_router = None
try:
	from app.api.api_v1.endpoints.expert_reviews import router as expert_reviews_router
except Exception:
	expert_reviews_router = None
try:
	from app.api.api_v1.endpoints.backup_profiles import router as backup_profiles_router
except Exception:
	backup_profiles_router = None
try:
	from app.api.api_v1.endpoints.master_config import router as master_config_router
except Exception:
	master_config_router = None
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
try:
	from app.api.api_v1.endpoints.legacy_performance import router as legacy_performance_router
except Exception:
	legacy_performance_router = None
try:
	from app.api.api_v1.endpoints.brrrr_zones import router as brrrr_zones_router
except Exception:
	brrrr_zones_router = None
try:
	from app.api.api_v1.endpoints.contractor_loyalty import router as contractor_loyalty_router
except Exception:
	contractor_loyalty_router = None
try:
	from app.api.api_v1.endpoints.system_health_reports import router as system_health_reports_router
except Exception:
	system_health_reports_router = None
try:
	from app.api.api_v1.endpoints.rental_properties import router as rental_properties_router
except Exception:
	rental_properties_router = None
try:
	from app.api.api_v1.endpoints.tenants import router as tenants_router
except Exception:
	tenants_router = None
try:
	from app.api.api_v1.endpoints.leases import router as leases_router
except Exception:
	leases_router = None
try:
	from app.api.api_v1.endpoints.rent_payments import router as rent_payments_router
except Exception:
	rent_payments_router = None
try:
	from app.api.api_v1.endpoints.legal_profiles import router as legal_profiles_router
except Exception:
	legal_profiles_router = None
try:
	from app.api.api_v1.endpoints.tax_risk import router as tax_risk_router
except Exception:
	tax_risk_router = None
try:
	from app.api.api_v1.endpoints.shield_profiles import router as shield_profiles_router
except Exception:
	shield_profiles_router = None
try:
	from app.api.api_v1.endpoints.bahamas_vault import router as bahamas_vault_router
except Exception:
	bahamas_vault_router = None
try:
	from app.api.api_v1.endpoints.whole_life_policies import router as whole_life_policies_router
except Exception:
	whole_life_policies_router = None
try:
	from app.api.api_v1.endpoints.legacy_clone_profiles import router as legacy_clone_profiles_router
except Exception:
	legacy_clone_profiles_router = None
try:
	from app.api.api_v1.endpoints.ai_training_jobs import router as ai_training_jobs_router
except Exception:
	ai_training_jobs_router = None
try:
	from app.api.api_v1.endpoints.knowledge_sources import router as knowledge_sources_router
except Exception:
	knowledge_sources_router = None

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
if arbitrage_profiles_router:
	api_router.include_router(arbitrage_profiles_router, prefix="/arbitrage-profiles", tags=["Arbitrage"])
if alerting_router:
	api_router.include_router(alerting_router, prefix="/alerting", tags=["Alerting"])
if governance_settings_router:
	api_router.include_router(governance_settings_router, prefix="/governance-settings", tags=["Governance"])
if system_health_router:
	api_router.include_router(system_health_router, prefix="/system-health", tags=["System Health Snapshots"])
if system_check_jobs_router:
	api_router.include_router(system_check_jobs_router, prefix="/system-check-jobs", tags=["System Checks"])
if external_experts_router:
	api_router.include_router(external_experts_router, prefix="/external-experts", tags=["External Experts"])
if expert_reviews_router:
	api_router.include_router(expert_reviews_router, prefix="/expert-reviews", tags=["Expert Reviews"])
if backup_profiles_router:
	api_router.include_router(backup_profiles_router, prefix="/backup-profiles", tags=["Backups"])
if master_config_router:
	api_router.include_router(master_config_router, prefix="/master-config", tags=["Master Config"])
if funfund_router:
	api_router.include_router(funfund_router, prefix="/funfund-routing", tags=["Fun Fund"])
if truck_plan_router:
	api_router.include_router(truck_plan_router, prefix="/truck-plans", tags=["Truck Plan"])
if bahamas_plan_router:
	api_router.include_router(bahamas_plan_router, prefix="/bahamas-plans", tags=["Bahamas Plan"])
if trust_status_router:
	api_router.include_router(trust_status_router, prefix="/trust-status", tags=["Trust Status"])
if legacy_performance_router:
	api_router.include_router(legacy_performance_router, prefix="/legacy-performance", tags=["Legacy Performance"])
if brrrr_zones_router:
	api_router.include_router(brrrr_zones_router, prefix="/brrrr-zones", tags=["BRRRR Zones"])
if contractor_loyalty_router:
	api_router.include_router(contractor_loyalty_router, prefix="/contractor-loyalty", tags=["Contractor Loyalty"])
if system_health_reports_router:
	api_router.include_router(system_health_reports_router, prefix="/system-health-reports", tags=["System Health Reports"])
if rental_properties_router:
	api_router.include_router(rental_properties_router, prefix="/rental-properties", tags=["Rental Properties"])
if tenants_router:
	api_router.include_router(tenants_router, prefix="/tenants", tags=["Tenants"])
if leases_router:
	api_router.include_router(leases_router, prefix="/leases", tags=["Leases"])
if rent_payments_router:
	api_router.include_router(rent_payments_router, prefix="/rent-payments", tags=["Rent Payments"])
if legal_profiles_router:
	api_router.include_router(legal_profiles_router, prefix="/legal-profiles", tags=["Legal Profiles"])
if tax_risk_router:
	api_router.include_router(tax_risk_router, prefix="/tax-risk-profiles", tags=["Tax Risk"])
if shield_profiles_router:
	api_router.include_router(shield_profiles_router, prefix="/shield-profiles", tags=["Shield Mode"])
if bahamas_vault_router:
	api_router.include_router(bahamas_vault_router, prefix="/bahamas-vault", tags=["Bahamas Vault"])
if whole_life_policies_router:
	api_router.include_router(whole_life_policies_router, prefix="/whole-life-policies", tags=["Whole Life Policies"])
if legacy_clone_profiles_router:
	api_router.include_router(legacy_clone_profiles_router, prefix="/legacy-clone-profiles", tags=["Legacy Auto-Clone"])
if ai_training_jobs_router:
	api_router.include_router(ai_training_jobs_router, prefix="/ai-training-jobs", tags=["AI Training Jobs"])
if knowledge_sources_router:
	api_router.include_router(knowledge_sources_router, prefix="/knowledge-sources", tags=["Knowledge Sources"])


