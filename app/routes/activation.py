"""
VALHALLA MASTER ACTIVATION ENDPOINT
===================================

HTTP endpoints for managing dark module activation.
Integrates both master controller and module registry.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

router = APIRouter(prefix="/api/v1/activation", tags=["activation"])
logger = logging.getLogger(__name__)

# Module registry endpoints
@router.post("/modules/{module_name}/activate")
async def activate_module_via_registry(module_name: str) -> Dict[str, Any]:
    """Activate a module via registry with full validation."""
    from app.core_activation import activate_module
    
    logger.info(f"Activation request for module: {module_name}")
    result = activate_module(module_name)
    
    return result


@router.post("/modules/{module_name}/deactivate")
async def deactivate_module_via_registry(module_name: str) -> Dict[str, Any]:
    """Deactivate a module via registry."""
    from app.core_activation import deactivate_module
    
    logger.info(f"Deactivation request for module: {module_name}")
    result = deactivate_module(module_name)
    
    return result


@router.get("/modules/{module_name}/status")
async def get_module_status_endpoint(module_name: str) -> Dict[str, Any]:
    """Get status of a specific module."""
    from app.core_activation import get_module_status
    
    result = get_module_status(module_name)
    return result


@router.get("/modules/all/status")
async def get_all_modules_status() -> Dict[str, Any]:
    """Get status of all modules."""
    from app.core_activation import get_all_status
    
    return get_all_status()


@router.get("/modules/log")
async def get_activation_log_endpoint(limit: int = 50) -> Dict[str, Any]:
    """Get activation log."""
    from app.core_activation import get_activation_log
    
    log_entries = get_activation_log(limit)
    
    return {
        "total_entries": len(log_entries),
        "limit": limit,
        "entries": log_entries,
    }


# Master controller endpoints
@router.post("/enable-master")
async def enable_master_activation() -> Dict[str, Any]:
    """Enable master activation system."""
    from app.core_launch import enable_master, get_summary
    
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
    from app.core_launch import disable_master, get_summary
    
    logger.info("🔒 Master activation disabled")
    disable_master()
    
    return {
        "status": "success",
        "message": "Master activation disabled",
        "summary": get_summary(),
    }


@router.post("/activate/{module_name}")
async def activate_module_master(module_name: str) -> Dict[str, Any]:
    """Activate a specific dark module via master controller."""
    from app.core_launch import (
        full_activation,
        _activation_controller,
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
    from app.core_launch import set_metric, full_status
    
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
    from app.core_launch import approve_gate, full_status
    
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
    from app.core_launch import reject_gate, full_status
    
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
    from app.core_launch import get_summary
    
    return get_summary()


@router.get("/status/{module_name}")
async def get_module_status(module_name: str) -> Dict[str, Any]:
    """Get status of specific module."""
    from app.core_launch import (
        _activation_controller,
        get_activation_status,
    )
    
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
    from app.core_launch import full_status
    
    return full_status()


@router.get("/log")
async def get_activation_log(limit: int = 50) -> Dict[str, Any]:
    """Get activation log."""
    from app.core_launch import _activation_controller
    
    log = _activation_controller.activation_log[-limit:]
    
    return {
        "log_size": len(log),
        "total_entries": len(_activation_controller.activation_log),
        "entries": log,
    }


@router.post("/emergency/kill-switch")
async def emergency_kill_switch() -> Dict[str, Any]:
    """Emergency kill switch - deactivates all modules."""
    from app.core_launch import disable_master
    import datetime
    
    logger.critical("🆘 EMERGENCY KILL SWITCH ACTIVATED")
    
    disable_master()
    
    return {
        "status": "emergency",
        "message": "All modules deactivated",
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }


@router.post("/debug/register-modules")
async def debug_register_modules() -> Dict[str, Any]:
    """DEBUG: Register default modules."""
    from app.core_launch import register_module, get_summary
    
    modules = [
        ("payment_processor", ["system_health"]),
        ("banking_connector", ["payment_processor"]),
        ("heimdall_core", ["banking_connector"]),
        ("property_cloning_engine", ["heimdall_core"]),
    ]
    
    for module_name, deps in modules:
        register_module(module_name, deps)
    
    return {
        "status": "success",
        "message": "Modules registered",
        "summary": get_summary(),
    }


@router.get("/routes")
async def get_active_routes() -> Dict[str, Any]:
    """Get all active backend routes for WeWeb discovery.
    
    Returns all available HTTP routes that WeWeb can query to discover
    active backend endpoints. This allows WeWeb to dynamically configure
    available actions based on the current backend state.
    """
    from app.core_activation import get_all_status
    
    # Get all routes from the app
    all_routes = []
    for route in router.routes:
        all_routes.append({
            "path": route.path,
            "name": getattr(route, "name", "unknown"),
            "methods": getattr(route, "methods", []),
        })
    
    # Get module status for context
    module_status = get_all_status()
    
    return {
        "status": "success",
        "total_routes": len(all_routes),
        "routes": all_routes,
        "modules": module_status.get("modules", {}),
        "active_modules_count": module_status.get("active_count", 0),
    }


@router.get("/routes/summary")
async def get_routes_summary() -> Dict[str, Any]:
    """Get a summary of available routes grouped by category.
    
    Provides WeWeb with a high-level view of what backend capabilities
    are available, organized by functional category.
    """
    from app.core_activation import get_all_status
    
    module_status = get_all_status()
    active_modules = [
        name for name, info in module_status.get("modules", {}).items()
        if info.get("status") == "active"
    ]
    
    return {
        "status": "success",
        "summary": {
            "total_modules": len(module_status.get("modules", {})),
            "active_modules": len(active_modules),
            "active_module_names": active_modules,
        },
        "categories": {
            "activation": {
                "endpoints": [
                    "/api/v1/activation/modules/{module_name}/activate",
                    "/api/v1/activation/modules/{module_name}/deactivate",
                    "/api/v1/activation/modules/{module_name}/status",
                    "/api/v1/activation/modules/all/status",
                    "/api/v1/activation/modules/log",
                ],
                "description": "Module activation control",
            },
            "master_control": {
                "endpoints": [
                    "/api/v1/activation/enable-master",
                    "/api/v1/activation/disable-master",
                    "/api/v1/activation/emergency/kill-switch",
                ],
                "description": "Master system control",
            },
            "conditions": {
                "endpoints": [
                    "/api/v1/activation/conditions",
                    "/api/v1/activation/conditions/set-metric",
                    "/api/v1/activation/conditions/approve-gate/{gate_name}",
                ],
                "description": "Activation conditions management",
            },
        },
    }
