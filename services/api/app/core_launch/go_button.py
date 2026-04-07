GO_BUTTON_RULES = {
    "launch_core_only_required": True,
    "enable_eia_tracking_required": True,
    "require_eia_compliance_required": True,
    "max_red_flag_risk": "MEDIUM",
    "max_missing_receipts": 0,
    "max_unclassified_income": 0,
    "owner_draw_allowed_pre_approval": False,
}

def go_button_eval(startup: dict, compliance: dict, red_flags: dict) -> dict:
    blockers = []

    if not startup.get("launch_core_only", False):
        blockers.append("launch_core_only is not enabled")

    if not startup.get("enable_eia_tracking", False):
        blockers.append("enable_eia_tracking is not enabled")

    if not startup.get("require_eia_compliance", False):
        blockers.append("require_eia_compliance is not enabled")

    if compliance.get("missing_receipts", False):
        blockers.append("missing receipts detected")

    if compliance.get("unclassified_income", False):
        blockers.append("unclassified income detected")

    if compliance.get("owner_draw", False):
        blockers.append("owner draw detected in protected mode")

    if red_flags.get("risk") == "HIGH":
        blockers.append("red flag risk is HIGH")

    return {
        "ok_to_enable_go_live": len(blockers) == 0,
        "blocker_count": len(blockers),
        "blockers": blockers,
    }
