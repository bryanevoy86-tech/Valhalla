from __future__ import annotations

try:
    from app.core_gov.health.lite import lite_dashboard
except (ImportError, AttributeError):
    def lite_dashboard():
        return {"status": "unknown"}

try:
    from app.core_gov.go.summary_service import go_summary
except (ImportError, AttributeError):
    def go_summary():
        return {"status": "unknown"}

try:
    from app.core_gov.anchors.service import anchors_check
except (ImportError, AttributeError):
    def anchors_check():
        return {"ok": False, "red_flags": ["Anchors service unavailable"]}

try:
    from app.core_gov.canon.service import canon_snapshot
except (ImportError, AttributeError):
    def canon_snapshot():
        return {"canon_version": "unknown"}


def onboarding_payload() -> dict:
    return {
        "lite": lite_dashboard(),
        "go": go_summary(),
        "anchors": anchors_check(),
        "canon": canon_snapshot(),
        "message": "Operate by Cone. Follow Go Next Step. If anchors show red flags, resolve first.",
    }
