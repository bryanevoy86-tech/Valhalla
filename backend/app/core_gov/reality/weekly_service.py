from __future__ import annotations

from app.core_gov.audit.audit_log import audit

try:
    from app.core_gov.health.lite import lite_dashboard
except ImportError:
    def lite_dashboard():
        return {"status": "unknown"}

try:
    from app.core_gov.go.session_service import get_session
except ImportError:
    def get_session():
        from pydantic import BaseModel
        class DummySession(BaseModel):
            session_id: str = "none"
            status: str = "not_started"
        return DummySession()

try:
    from app.core_gov.go.service import next_step
except ImportError:
    def next_step():
        from pydantic import BaseModel
        class DummyStep(BaseModel):
            step_num: int = 0
            title: str = "unknown"
        return DummyStep()

try:
    from app.core_gov.cone.service import get_cone_state
except ImportError:
    def get_cone_state():
        from pydantic import BaseModel
        class DummyCone(BaseModel):
            band: str = "A"
            reason: str = "unknown"
            updated_at_utc: str = "unknown"
        return DummyCone()

from app.core_gov.reality.weekly_store import append_audit


def run_weekly_audit() -> dict:
    cone = get_cone_state()
    lite = lite_dashboard()
    sess = get_session()
    nxt = next_step()

    # Safe extraction
    cone_dict = cone.model_dump() if hasattr(cone, 'model_dump') else cone.__dict__
    sess_dict = sess.model_dump() if hasattr(sess, 'model_dump') else sess.__dict__
    nxt_dict = nxt.model_dump() if hasattr(nxt, 'model_dump') else nxt.__dict__

    snapshot = {
        "cone": {
            "band": cone_dict.get("band", "A"),
            "reason": cone_dict.get("reason", "unknown"),
            "updated_at_utc": cone_dict.get("updated_at_utc", "unknown"),
        },
        "lite": lite,
        "go_session": sess_dict,
        "next": nxt_dict,
    }

    record = append_audit(snapshot)
    audit(
        "WEEKLY_AUDIT_RUN",
        {
            "cone_band": cone_dict.get("band", "A"),
            "status": lite.get("status", "unknown"),
        },
    )
    return {"ok": True, "record": record}
