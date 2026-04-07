from app.core_flags.flags import is_enabled
from app.core_eia.eia_report_generator import generate_monthly_report

def go_button_status(startup_data, eia_data, red_flags_data):
    blockers = []
    
    if not is_enabled("launch_core_only"):
        blockers.append("launch_core_only flag is not enabled")
    
    if not is_enabled("enable_eia_tracking"):
        blockers.append("EIA tracking is not enabled")
    
    if not is_enabled("require_eia_compliance"):
        blockers.append("EIA compliance is not required")
    
    if red_flags_data.get("risk") == "HIGH":
        blockers.append("Red flag risk is too high")
    
    if eia_data.get("missing_receipts"):
        blockers.append("Missing receipts detected")
    
    return {
        "can_go_live": len(blockers) == 0,
        "blockers": blockers,
    }
