"""
VALHALLA MASTER ACTIVATION CONTROLLER
=====================================

Central orchestration for activating dark modules.
Integrates with module registry for feature flag management.
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Optional module registry integration
_module_registry = None

def set_module_registry(registry) -> None:
    """Set the module registry for integration."""
    global _module_registry
    _module_registry = registry


class ActivationPhase(Enum):
    """Phases of activation."""
    INITIALIZATION = "initialization"
    CONDITION_CHECK = "condition_check"
    PRE_ACTIVATION = "pre_activation"
    ACTIVATION = "activation"
    POST_ACTIVATION = "post_activation"
    MONITORING = "monitoring"


class ActivationStatus(Enum):
    """Activation status."""
    PENDING = "pending"
    CHECKING = "checking"
    READY = "ready"
    ACTIVATING = "activating"
    ACTIVE = "active"
    FAILED = "failed"
    BLOCKED = "blocked"


class ModuleActivationState:
    """Tracks activation state of a module."""

    def __init__(self, name: str):
        self.name = name
        self.status = ActivationStatus.PENDING
        self.phase = ActivationPhase.INITIALIZATION
        self.start_time: Optional[str] = None
        self.end_time: Optional[str] = None
        self.last_check: Optional[str] = None
        self.error_message: Optional[str] = None
        self.activation_count = 0
        self.metrics: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return {
            "name": self.name,
            "status": self.status.value,
            "phase": self.phase.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "last_check": self.last_check,
            "error_message": self.error_message,
            "activation_count": self.activation_count,
            "metrics": self.metrics,
        }


class ActivationController:
    """Master controller for module activation."""

    def __init__(self):
        self.modules: Dict[str, ModuleActivationState] = {}
        self.dependencies: Dict[str, List[str]] = {}
        self.activation_log: List[Dict[str, Any]] = []
        self.master_enabled = False

    def register_module(self, name: str, dependencies: Optional[List[str]] = None) -> None:
        """Register a module for activation."""
        self.modules[name] = ModuleActivationState(name)
        if dependencies:
            self.dependencies[name] = dependencies
        logger.info(f"📝 Registered module: {name}")

    def check_dependencies(self, module_name: str) -> bool:
        """Check if module dependencies are met."""
        dependencies = self.dependencies.get(module_name, [])
        
        for dep in dependencies:
            dep_state = self.modules.get(dep)
            if not dep_state or dep_state.status != ActivationStatus.ACTIVE:
                logger.warning(f"⚠️  Dependency not met: {module_name} requires {dep}")
                return False
        
        return True

    async def check_conditions(self, module_name: str) -> tuple:
        """Check activation conditions for a module."""
        from .activation_conditions import can_activate, get_activation_status
        
        state = self.modules.get(module_name)
        if not state:
            return False, "Module not registered"
        
        state.phase = ActivationPhase.CONDITION_CHECK
        state.status = ActivationStatus.CHECKING
        state.last_check = datetime.utcnow().isoformat()
        
        try:
            ready = can_activate(module_name)
            if ready:
                state.status = ActivationStatus.READY
                logger.info(f"✅ Conditions met for: {module_name}")
                return True, "Conditions met"
            else:
                logger.warning(f"❌ Conditions not met for: {module_name}")
                return False, "Conditions not met"
        except Exception as e:
            state.status = ActivationStatus.FAILED
            state.error_message = str(e)
            return False, str(e)

    async def pre_activate(self, module_name: str) -> tuple:
        """Pre-activation checks."""
        state = self.modules.get(module_name)
        if not state:
            return False, "Module not registered"
        
        state.phase = ActivationPhase.PRE_ACTIVATION
        
        if not self.check_dependencies(module_name):
            state.status = ActivationStatus.BLOCKED
            return False, "Dependencies not met"
        
        logger.info(f"🔧 Pre-activation checks passed: {module_name}")
        return True, "Pre-activation checks passed"

    async def activate(self, module_name: str) -> tuple:
        """Activate a module with optional registry integration."""
        state = self.modules.get(module_name)
        if not state:
            return False, "Module not registered"
        
        state.phase = ActivationPhase.ACTIVATION
        state.status = ActivationStatus.ACTIVATING
        state.start_time = datetime.utcnow().isoformat()
        
        try:
            logger.info(f"🚀 Activating: {module_name}")
            
            # If module registry is available, use it for feature flag management
            if _module_registry:
                registry_result = _module_registry.activate_module(module_name)
                if registry_result.get("status") != "success":
                    state.status = ActivationStatus.FAILED
                    error_msg = registry_result.get("error", "Module registry activation failed")
                    state.error_message = error_msg
                    state.end_time = datetime.utcnow().isoformat()
                    self.log_activation(module_name, "failed", error_msg)
                    logger.error(f"Registry activation failed: {error_msg}")
                    return False, error_msg
            
            state.status = ActivationStatus.ACTIVE
            state.end_time = datetime.utcnow().isoformat()
            state.activation_count += 1
            
            logger.info(f"✅ ACTIVATED: {module_name}")
            
            self.log_activation(module_name, "success")
            return True, "Module activated"
        except Exception as e:
            state.status = ActivationStatus.FAILED
            state.error_message = str(e)
            state.end_time = datetime.utcnow().isoformat()
            
            logger.error(f"❌ Activation failed: {e}")
            self.log_activation(module_name, "failed", str(e))
            return False, str(e)

    async def post_activate(self, module_name: str) -> tuple:
        """Post-activation configuration."""
        state = self.modules.get(module_name)
        if not state:
            return False, "Module not registered"
        
        state.phase = ActivationPhase.POST_ACTIVATION
        logger.info(f"⚙️  Post-activation setup: {module_name}")
        
        return True, "Post-activation complete"

    async def full_activation(self, module_name: str) -> tuple:
        """Full activation workflow."""
        logger.info(f"📋 Starting full activation workflow: {module_name}")
        
        # Step 1: Check conditions
        conditions_ok, conditions_msg = await self.check_conditions(module_name)
        if not conditions_ok:
            self.modules[module_name].status = ActivationStatus.BLOCKED
            return False, f"Conditions check failed: {conditions_msg}"
        
        # Step 2: Pre-activation
        pre_ok, pre_msg = await self.pre_activate(module_name)
        if not pre_ok:
            return False, f"Pre-activation failed: {pre_msg}"
        
        # Step 3: Activation
        activate_ok, activate_msg = await self.activate(module_name)
        if not activate_ok:
            return False, f"Activation failed: {activate_msg}"
        
        # Step 4: Post-activation
        post_ok, post_msg = await self.post_activate(module_name)
        if not post_ok:
            logger.warning(f"⚠️  Post-activation warning: {post_msg}")
        
        logger.info(f"✅ FULL ACTIVATION COMPLETE: {module_name}")
        return True, "Full activation successful"

    def log_activation(self, module_name: str, result: str, error: Optional[str] = None) -> None:
        """Log activation event."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "module": module_name,
            "result": result,
            "error": error,
        }
        self.activation_log.append(entry)

    def enable_master(self) -> None:
        """Enable master activation."""
        self.master_enabled = True
        logger.warning("⚠️  MASTER ACTIVATION ENABLED")

    def disable_master(self) -> None:
        """Disable master activation."""
        self.master_enabled = False
        logger.info("🔒 Master activation disabled")

    def get_state(self, module_name: str) -> Optional[Dict[str, Any]]:
        """Get module state."""
        state = self.modules.get(module_name)
        if state:
            return state.to_dict()
        return None

    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get all module states."""
        return {
            name: state.to_dict()
            for name, state in self.modules.items()
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get activation summary."""
        states = self.get_all_states()
        
        active_count = sum(
            1 for s in states.values()
            if s["status"] == ActivationStatus.ACTIVE.value
        )
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "master_enabled": self.master_enabled,
            "total_modules": len(self.modules),
            "active_modules": active_count,
            "modules": states,
            "recent_activations": self.activation_log[-10:],
        }


# Singleton instance
_activation_controller = ActivationController()


def register_module(name: str, dependencies: Optional[List[str]] = None) -> None:
    """Register a module."""
    _activation_controller.register_module(name, dependencies)


async def full_activation(module_name: str) -> tuple:
    """Activate a module with full workflow."""
    return await _activation_controller.full_activation(module_name)


def enable_master() -> None:
    """Enable master activation."""
    _activation_controller.enable_master()


def disable_master() -> None:
    """Disable master activation."""
    _activation_controller.disable_master()


def get_summary() -> Dict[str, Any]:
    """Get activation summary."""
    return _activation_controller.get_summary()
