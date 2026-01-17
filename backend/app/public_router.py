from fastapi import APIRouter
from app.core_gov.health.lite import lite_dashboard

public = APIRouter(prefix="/public", tags=["Public"])


@public.get("/healthz")
def healthz_public():
    return {"ok": True}


@public.get("/lite/dashboard")
def lite_public():
    return lite_dashboard()


@public.get("/go/summary")
def go_summary_public():
    from app.core_gov.go.summary_service import go_summary
    return go_summary()


@public.get("/onboarding")
def onboarding_public():
    from app.core_gov.onboarding import onboarding_payload
    return onboarding_payload()
