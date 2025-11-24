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
