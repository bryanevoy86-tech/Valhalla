from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy.orm import Session


# ============================================================
# Safe import helper — runbook must NEVER crash
# ============================================================

def _safe_import(path: str):
    try:
        module_path, name = path.rsplit(".", 1)
        mod = __import__(module_path, fromlist=[name])
        return getattr(mod, name)
    except Exception:
        return None


# ============================================================
# Optional dependencies (safe)
# ============================================================

read_go_live_state = _safe_import("app.services.go_live.read_state")
go_live_checklist = _safe_import("app.services.go_live.checklist")

RiskPolicy = _safe_import("app.models.risk_policy.RiskPolicy")
RegressionPolicy = _safe_import("app.models.regression_policy.RegressionPolicy")
HeimdallPolicy = _safe_import("app.models.heimdall_policy.HeimdallPolicy")




# ============================================================
# Data structures
# ============================================================

@dataclass
class CheckItem:
    id: str
    ok: bool
    severity: str  # BLOCKER | WARN | INFO
    message: str
    detail: Optional[Dict[str, Any]] = None


# ============================================================
# Helpers
# ============================================================

def _env_snapshot() -> Dict[str, Any]:
    return {
        "ENV": os.getenv("ENV") or os.getenv("APP_ENV"),
        "GO_LIVE_ENFORCE": os.getenv("GO_LIVE_ENFORCE"),
        "DATABASE_URL_set": bool(os.getenv("DATABASE_URL")),
    }


def _count_rows(db: Session, model) -> int:
    if model is None:
        return -1
    try:
        return db.query(model).count()
    except Exception:
        return -2




# ============================================================
# Main runbook builder
# ============================================================

def build_runbook(db: Session) -> Dict[str, Any]:
    """
    Build runbook with comprehensive error handling.
    NEVER raises exceptions — always returns a structured response.
    """
    try:
        return _build_runbook_impl(db)
    except Exception as e:
        # Failsafe: if anything goes wrong, return with critical blocker
        return {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "blockers": [{"id": "runbook_fatal", "ok": False, "severity": "BLOCKER", "message": "Runbook engine crashed", "detail": {"error": str(e), "type": type(e).__name__}}],
            "warnings": [],
            "info": [],
            "ok_to_enable_go_live": False,
        }


def _build_runbook_impl(db: Session) -> Dict[str, Any]:
    items: List[CheckItem] = []

    # --------------------------------------------------------
    # 1) Go-live checklist
    # --------------------------------------------------------
    if go_live_checklist is None:
        items.append(CheckItem(
            id="go_live_checklist",
            ok=False,
            severity="BLOCKER",
            message="Go-live checklist function missing",
        ))
    else:
        try:
            gl = go_live_checklist(db)
            items.append(CheckItem(
                id="go_live_checklist",
                ok=bool(gl.get("ok")),
                severity="BLOCKER",
                message="Go-live checklist must pass before production execution",
                detail=gl,
            ))
        except Exception as e:
            items.append(CheckItem(
                id="go_live_checklist",
                ok=False,
                severity="BLOCKER",
                message="Go-live checklist threw exception",
                detail={"error": str(e)},
            ))

    # --------------------------------------------------------
    # 2) Kill switch / go-live state
    # --------------------------------------------------------
    if read_go_live_state is None:
        items.append(CheckItem(
            id="go_live_state",
            ok=False,
            severity="BLOCKER",
            message="Go-live state reader missing",
        ))
    else:
        try:
            st = read_go_live_state(db)
            kill_clear = not bool(getattr(st, "kill_switch_engaged", True))
            items.append(CheckItem(
                id="kill_switch_clear",
                ok=kill_clear,
                severity="BLOCKER",
                message="Kill-switch must be disengaged for production execution",
                detail={
                    "kill_switch_engaged": bool(getattr(st, "kill_switch_engaged", True)),
                    "go_live_enabled": bool(getattr(st, "go_live_enabled", False)),
                    "updated_at": str(getattr(st, "updated_at", "")),
                },
            ))
        except Exception as e:
            items.append(CheckItem(
                id="go_live_state",
                ok=False,
                severity="BLOCKER",
                message="Go-live state threw exception",
                detail={"error": str(e)},
            ))

    # --------------------------------------------------------
    # 3) Environment sanity
    # --------------------------------------------------------
    env = _env_snapshot()
    env_ok = bool(env.get("ENV")) and bool(env.get("DATABASE_URL_set"))
    items.append(CheckItem(
        id="env_sanity",
        ok=env_ok,
        severity="BLOCKER",
        message="ENV and DATABASE_URL must be set correctly",
        detail=env,
    ))

    # --------------------------------------------------------
    # 4) Risk policies
    # --------------------------------------------------------
    rp_count = _count_rows(db, RiskPolicy)
    items.append(CheckItem(
        id="risk_policies_present",
        ok=(rp_count > 0),
        severity="BLOCKER",
        message="Risk policies must exist (floors / caps / approvals)",
        detail={"count": rp_count},
    ))

    # --------------------------------------------------------
    # 5) Regression policies
    # --------------------------------------------------------
    reg_count = _count_rows(db, RegressionPolicy)
    items.append(CheckItem(
        id="regression_policies_present",
        ok=(reg_count > 0),
        severity="BLOCKER",
        message="Regression tripwire policies must exist",
        detail={"count": reg_count},
    ))

    # --------------------------------------------------------
    # 6) Heimdall charter
    # --------------------------------------------------------
    heim_count = _count_rows(db, HeimdallPolicy)
    items.append(CheckItem(
        id="heimdall_charter_present",
        ok=(heim_count > 0),
        severity="BLOCKER",
        message="Heimdall charter policies must exist",
        detail={"count": heim_count},
    ))

    # --------------------------------------------------------
    # Final aggregation
    # --------------------------------------------------------
    blockers = [i.__dict__ for i in items if i.severity == "BLOCKER" and not i.ok]
    warnings = [i.__dict__ for i in items if i.severity == "WARN" and not i.ok]
    info = [i.__dict__ for i in items if i.ok or i.severity == "INFO"]

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "blockers": blockers,
        "warnings": warnings,
        "info": info,
        "ok_to_enable_go_live": (len(blockers) == 0),
    }


def render_runbook_markdown(runbook: Dict[str, Any]) -> str:
    def line(item: Dict[str, Any]) -> str:
        icon = "✅" if item["ok"] else "❌"
        return f"- {icon} **{item['id']}** — {item['message']}"

    md = []
    md.append(f"# Valhalla Go-Live Runbook\n\nGenerated: `{runbook['generated_at']}`\n")
    md.append("## Blockers\n")
    if not runbook["blockers"]:
        md.append("- ✅ None\n")
    else:
        for i in runbook["blockers"]:
            md.append(line(i) + "\n")
    md.append("\n## Warnings\n")
    if not runbook["warnings"]:
        md.append("- ✅ None\n")
    else:
        for i in runbook["warnings"]:
            md.append(line(i) + "\n")
    md.append("\n## Info / Passing Checks\n")
    for i in runbook["info"]:
        md.append(line(i) + "\n")
    return "".join(md)

