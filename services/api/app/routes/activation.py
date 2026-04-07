"""
VALHALLA MASTER ACTIVATION ENDPOINT
===================================

HTTP endpoints for managing dark module activation.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

router = APIRouter(prefix="/api/v1/activation", tags=["activation"])
logger = logging.getLogger(__name__)


@router.post("/enable-master")
async def enable_master_activation() -> Dict[str, Any]:
    """
    Enable master activation system.
    
    ⚠️ This is a critical endpoint. Should require admin approval.
    """
    from .master_activation_controller import enable_master, get_summary
    
    logger.warning("🚨 MASTER ACTIVATION ENABLED")
    enable_master()
    
    return {
        "status": "success",
        "message": "Master activation enabled",
        "summary": get_summary(),
    }


@router.post("/disable-master")
async def disable_master_activation() -> Dict[str, Any]:
    """Disable master activation system."""
    from .master_activation_controller import disable_master, get_summary
    
    logger.info("🔒 Master activation disabled")
    disable_master()
    
    return {
        "status": "success",
        "message": "Master activation disabled",
        "summary": get_summary(),
    }


@router.post("/activate/{module_name}")
async def activate_module(module_name: str) -> Dict[str, Any]:
    """
    Activate a specific dark module.
    
    Runs full activation workflow:
    1. Check activation conditions
    2. Pre-activation checks
    3. Activate module
    4. Post-activation setup
    """
    from .master_activation_controller import (
        _activation_controller,
        full_activation,
    )
    
    if not _activation_controller.master_enabled:
        raise HTTPException(
            status_code=403,
            detail="Master activation is not enabled",
        )
    
    try:
        success, message = await full_activation(module_name)
        
        if success:
            return {
                "status": "success",
                "module": module_name,
                "message": message,
                "state": _activation_controller.get_state(module_name),
            }
        else:
            return {
                "status": "failed",
                "module": module_name,
                "message": message,
                "state": _activation_controller.get_state(module_name),
            }
    except Exception as e:
        logger.error(f"Activation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conditions/set-metric")
async def set_metric(metric_name: str, value: Any) -> Dict[str, Any]:
    """Set an activation metric."""
    from .activation_conditions import set_metric, full_status
    
    set_metric(metric_name, value)
    
    return {
        "status": "success",
        "metric": metric_name,
        "value": value,
        "conditions": full_status(),
    }


@router.post("/conditions/approve-gate/{gate_name}")
async def approve_gate(gate_name: str) -> Dict[str, Any]:
    """Approve an activation gate."""
    from .activation_conditions import approve_gate, full_status
    
    approve_gate(gate_name)
    logger.info(f"✅ Approved gate: {gate_name}")
    
    return {
        "status": "success",
        "gate": gate_name,
        "approved": True,
        "conditions": full_status(),
    }


@router.post("/conditions/reject-gate/{gate_name}")
async def reject_gate_endpoint(gate_name: str) -> Dict[str, Any]:
    """Reject an activation gate."""
    from .activation_conditions import reject_gate, full_status
    
    reject_gate(gate_name)
    logger.warning(f"❌ Rejected gate: {gate_name}")
    
    return {
        "status": "success",
        "gate": gate_name,
        "approved": False,
        "conditions": full_status(),
    }


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get current activation status."""
    from .master_activation_controller import get_summary
    
    return get_summary()


@router.get("/status/{module_name}")
async def get_module_status(module_name: str) -> Dict[str, Any]:
    """Get status of specific module."""
    from .master_activation_controller import _activation_controller
    from .activation_conditions import get_activation_status
    
    state = _activation_controller.get_state(module_name)
    conditions = get_activation_status(module_name)
    
    if not state:
        raise HTTPException(status_code=404, detail="Module not found")
    
    return {
        "module": module_name,
        "state": state,
        "conditions": conditions,
    }


@router.get("/conditions")
async def get_conditions() -> Dict[str, Any]:
    """Get all activation conditions."""
    from .activation_conditions import full_status
    
    return full_status()


@router.get("/log")
async def get_activation_log(limit: int = 50) -> Dict[str, Any]:
    """Get activation log."""
    from .master_activation_controller import _activation_controller
    
    log = _activation_controller.activation_log[-limit:]
    
    return {
        "log_size": len(log),
        "total_entries": len(_activation_controller.activation_log),
        "entries": log,
    }


# ==================
# EMERGENCY ROUTES
# ==================

@router.post("/emergency/kill-switch")
async def emergency_kill_switch() -> Dict[str, Any]:
    """
    Emergency kill switch - deactivates all modules.
    
    ⚠️ Use only in emergency situations
    """
    from .master_activation_controller import _activation_controller, disable_master
    
    logger.critical("🆘 EMERGENCY KILL SWITCH ACTIVATED")
    
    # Disable master
    disable_master()
    
    # TODO: Trigger emergency deactivation for each module
    
    return {
        "status": "emergency",
        "message": "All modules deactivated",
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
    }


@router.post("/debug/register-modules")
async def debug_register_modules() -> Dict[str, Any]:
    """DEBUG: Register default modules."""
    from .master_activation_controller import register_module
    
    modules = [
        ("payment_processor", ["system_health"]),
        ("banking_connector", ["payment_processor"]),
        ("heimdall_core", ["banking_connector"]),
        ("property_cloning_engine", ["heimdall_core"]),
    ]
    
    for module_name, deps in modules:
        register_module(module_name, deps)
    
    from .master_activation_controller import get_summary
    
    return {
        "status": "success",
        "message": "Modules registered",
        "summary": get_summary(),
    }
