"""
VALHALLA MODULE ORCHESTRATOR - Activation Control System
========================================================

This system orchestrates the activation of all modules based on:
- Dependencies
- Conditions
- Heimdall decisions
- Business rules
"""

from typing import Dict, List, Callable, Optional, Any
from enum import Enum
from datetime import datetime
import asyncio

class ActivationState(Enum):
    """Lifecycle states for modules."""
    DORMANT = "dormant"  # Not yet activated
    INITIALIZING = "initializing"  # Activation in progress
    READY = "ready"  # Fully initialized and ready
    ACTIVE = "active"  # Currently running
    PAUSED = "paused"  # Temporarily stopped
    FAILED = "failed"  # Activation failed
    STOPPED = "stopped"  # Gracefully stopped

class Module:
    """Represents an activatable module."""

    def __init__(
        self,
        name: str,
        description: str,
        dependencies: List[str] = None,
        feature_flag: str = None,
        init_handler: Optional[Callable] = None,
        teardown_handler: Optional[Callable] = None,
    ):
        self.name = name
        self.description = description
        self.dependencies = dependencies or []
        self.feature_flag = feature_flag
        self.init_handler = init_handler
        self.teardown_handler = teardown_handler
        self.state = ActivationState.DORMANT
        self.initialized_at: Optional[str] = None
        self.error_message: Optional[str] = None

    async def initialize(self) -> bool:
        """Initialize this module."""
        self.state = ActivationState.INITIALIZING
        try:
            if self.init_handler:
                result = self.init_handler()
                # Handle async results
                if hasattr(result, '__await__'):
                    await result
            self.state = ActivationState.ACTIVE
            self.initialized_at = datetime.utcnow().isoformat()
            return True
        except Exception as e:
            self.state = ActivationState.FAILED
            self.error_message = str(e)
            return False

    async def teardown(self) -> bool:
        """Teardown this module."""
        try:
            if self.teardown_handler:
                result = self.teardown_handler()
                if hasattr(result, '__await__'):
                    await result
            self.state = ActivationState.STOPPED
            return True
        except Exception as e:
            self.error_message = str(e)
            return False

class ModuleOrchestrator:
    """Manages module activation and lifecycle."""

    def __init__(self):
        self.modules: Dict[str, Module] = {}
        self.activation_order: List[str] = []
        self.activation_log: List[Dict[str, Any]] = []

    def register_module(self, module: Module) -> None:
        """Register a module."""
        self.modules[module.name] = module

    def _check_dependencies(self, module_name: str) -> bool:
        """Check if all dependencies are met."""
        module = self.modules.get(module_name)
        if not module:
            return False

        for dep in module.dependencies:
            dep_module = self.modules.get(dep)
            if not dep_module or dep_module.state != ActivationState.ACTIVE:
                return False
        return True

    async def activate_module(self, module_name: str, reason: str = "") -> bool:
        """Activate a single module."""
        module = self.modules.get(module_name)
        if not module:
            return False

        if not self._check_dependencies(module_name):
            return False

        success = await module.initialize()
        self.activation_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "module": module_name,
            "action": "activate",
            "success": success,
            "reason": reason,
            "error": module.error_message
        })
        return success

    async def deactivate_module(self, module_name: str, reason: str = "") -> bool:
        """Deactivate a single module."""
        module = self.modules.get(module_name)
        if not module:
            return False

        success = await module.teardown()
        self.activation_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "module": module_name,
            "action": "deactivate",
            "success": success,
            "reason": reason,
        })
        return success

    async def activate_layer(self, layer: List[str], reason: str = "") -> bool:
        """Activate all modules in a layer."""
        for module_name in layer:
            if not await self.activate_module(module_name, reason):
                return False
        return True

    async def activate_cascade(self, modules_list: List[str], reason: str = "") -> Dict[str, bool]:
        """Activate multiple modules respecting dependencies."""
        results = {}
        activated = set()

        while len(activated) < len(modules_list):
            progress = False
            for module_name in modules_list:
                if module_name in activated:
                    continue

                # Check if dependencies are satisfied
                module = self.modules.get(module_name)
                if module and all(dep in activated for dep in module.dependencies):
                    success = await self.activate_module(module_name, reason)
                    if success:
                        activated.add(module_name)
                        progress = True
                    results[module_name] = success

            if not progress:
                break

        return results

    def get_module_status(self, module_name: str) -> Dict[str, Any]:
        """Get status of a module."""
        module = self.modules.get(module_name)
        if not module:
            return {}

        return {
            "name": module.name,
            "description": module.description,
            "state": module.state.value,
            "dependencies": module.dependencies,
            "feature_flag": module.feature_flag,
            "initialized_at": module.initialized_at,
            "error": module.error_message,
        }

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all modules."""
        return {name: self.get_module_status(name) for name in self.modules.keys()}

    def status_summary(self) -> Dict[str, Any]:
        """Get summary of all module statuses."""
        statuses = [m.state for m in self.modules.values()]
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_modules": len(self.modules),
            "active": len([s for s in statuses if s == ActivationState.ACTIVE]),
            "dormant": len([s for s in statuses if s == ActivationState.DORMANT]),
            "failed": len([s for s in statuses if s == ActivationState.FAILED]),
            "modules": self.get_all_status(),
        }

# ========================
# ACTIVATION LAYERS
# ========================

# Phase 0: Core (always on)
CORE_LAYER = [
    "core_system",
    "database",
    "auth_system",
]

# Phase 1: Business Processing (on for launch)
BUSINESS_LAYER = [
    "lead_intake_engine",
    "deal_scoring_engine",
    "offer_generation_engine",
]

# Phase 2: Financial Systems (activated when payments needed)
FINANCIAL_LAYER = [
    "payment_processor",
    "banking_connector",
    "accounting_system",
]

# Phase 3: AI Systems (activated when Heimdall ready)
AI_LAYER = [
    "heimdall_core",
    "negotiation_ai",
    "behavioral_profiling",
]

# Phase 4: Automation (activated for efficiency)
AUTOMATION_LAYER = [
    "contract_automation",
    "va_workflows",
    "follow_up_system",
]

# Phase 5: Scaling (activated for growth)
SCALING_LAYER = [
    "property_cloning_engine",
    "vault_system",
    "arbitrage_engine",
    "reinvestment_automation",
]

# ========================
# SINGLETON ORCHESTRATOR
# ========================

_orchestrator = ModuleOrchestrator()

async def activate_module(name: str, reason: str = "") -> bool:
    """Activate a module."""
    return await _orchestrator.activate_module(name, reason)

async def deactivate_module(name: str, reason: str = "") -> bool:
    """Deactivate a module."""
    return await _orchestrator.deactivate_module(name, reason)

async def activate_layer(layer: List[str], reason: str = "") -> bool:
    """Activate a layer."""
    return await _orchestrator.activate_layer(layer, reason)

def get_status(module_name: str) -> Dict[str, Any]:
    """Get module status."""
    return _orchestrator.get_module_status(module_name)

def get_all_status() -> Dict[str, Any]:
    """Get all statuses."""
    return _orchestrator.status_summary()

def register_module(
    name: str,
    description: str,
    dependencies: List[str] = None,
    feature_flag: str = None,
    init_handler: Optional[Callable] = None,
    teardown_handler: Optional[Callable] = None,
) -> None:
    """Register a module."""
    module = Module(
        name=name,
        description=description,
        dependencies=dependencies or [],
        feature_flag=feature_flag,
        init_handler=init_handler,
        teardown_handler=teardown_handler,
    )
    _orchestrator.register_module(module)
