"""
VALHALLA Core Launch Module
===========================

Activation system for managing dark modules.
"""

from .activation_conditions import (
    ActivationConditionEngine,
    ActivationRule,
    ConditionType,
    can_activate,
    get_activation_status,
    set_metric,
    approve_gate,
    reject_gate,
    full_status,
)

from .master_activation_controller import (
    ActivationController,
    ActivationPhase,
    ActivationStatus,
    ModuleActivationState,
    register_module,
    full_activation,
    enable_master,
    disable_master,
    get_summary,
)

__all__ = [
    # Conditions
    "ActivationConditionEngine",
    "ActivationRule",
    "ConditionType",
    "can_activate",
    "get_activation_status",
    "set_metric",
    "approve_gate",
    "reject_gate",
    "full_status",
    # Controller
    "ActivationController",
    "ActivationPhase",
    "ActivationStatus",
    "ModuleActivationState",
    "register_module",
    "full_activation",
    "enable_master",
    "disable_master",
    "get_summary",
]
