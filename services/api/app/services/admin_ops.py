"""
PACK UF: Admin Ops Console Service
High-level orchestrator for safe admin actions.
"""

from typing import Dict, Any
from sqlalchemy.orm import Session

from app.services.security_dashboard import get_security_dashboard
from app.services.maintenance import set_maintenance_mode, get_maintenance_state
from app.services.feature_flags import set_feature_flag
from app.schemas.feature_flags import FeatureFlagSet
from app.services.deployment_profile import get_deployment_profile
from app.schemas.admin_ops import AdminActionRequest, AdminActionResponse


def perform_admin_action(
    db: Session,
    req: AdminActionRequest,
) -> AdminActionResponse:
    action = req.action
    payload = req.payload or {}

    # 1) Fetch latest security dashboard
    if action == "security_snapshot":
        try:
            dashboard = get_security_dashboard(db)
            return AdminActionResponse(
                action=action,
                ok=True,
                data={"dashboard": dashboard.model_dump()},
            )
        except Exception as e:
            return AdminActionResponse(
                action=action,
                ok=False,
                detail=f"Failed to fetch security dashboard: {str(e)}",
            )

    # 2) Set maintenance mode
    if action == "set_maintenance_mode":
        try:
            mode = payload.get("mode", "normal")
            reason = payload.get("reason")
            state = set_maintenance_mode(db, mode, reason)
            return AdminActionResponse(
                action=action,
                ok=True,
                data={
                    "mode": state.mode,
                    "reason": state.reason,
                    "updated_at": state.updated_at.isoformat(),
                },
            )
        except Exception as e:
            return AdminActionResponse(
                action=action,
                ok=False,
                detail=f"Failed to set maintenance mode: {str(e)}",
            )

    # 3) Toggle feature flag
    if action == "set_feature_flag":
        try:
            ff = FeatureFlagSet(
                key=payload["key"],
                enabled=payload.get("enabled", True),
                description=payload.get("description"),
                group=payload.get("group"),
            )
            flag = set_feature_flag(db, ff)
            return AdminActionResponse(
                action=action,
                ok=True,
                data={"flag": {"key": flag.key, "enabled": flag.enabled, "group": flag.group}},
            )
        except Exception as e:
            return AdminActionResponse(
                action=action,
                ok=False,
                detail=f"Failed to set feature flag: {str(e)}",
            )

    # 4) Get deployment profile
    if action == "deployment_profile":
        try:
            env = payload.get("environment", "dev")
            profile = get_deployment_profile(db, environment=env)
            return AdminActionResponse(
                action=action,
                ok=True,
                data={"profile": profile.model_dump()},
            )
        except Exception as e:
            return AdminActionResponse(
                action=action,
                ok=False,
                detail=f"Failed to fetch deployment profile: {str(e)}",
            )

    # 5) Get current maintenance state
    if action == "get_maintenance_state":
        try:
            state = get_maintenance_state(db)
            return AdminActionResponse(
                action=action,
                ok=True,
                data={
                    "mode": state.mode,
                    "reason": state.reason,
                    "updated_at": state.updated_at.isoformat(),
                },
            )
        except Exception as e:
            return AdminActionResponse(
                action=action,
                ok=False,
                detail=f"Failed to get maintenance state: {str(e)}",
            )

    # Unknown action
    return AdminActionResponse(
        action=action,
        ok=False,
        detail="Unknown admin action",
    )
