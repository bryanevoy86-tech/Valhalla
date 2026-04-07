"""
VALHALLA MODULE REGISTRY
=======================

Core module activation and deactivation with comprehensive logging,
error handling, and post-activation setup.
"""

import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ModuleStatus(Enum):
    """Module activation status."""
    INACTIVE = "inactive"
    ACTIVATING = "activating"
    ACTIVE = "active"
    DEACTIVATING = "deactivating"
    ERROR = "error"


class ModuleRegistry:
    """
    Registry for managing module activation/deactivation.
    
    Handles:
    - Module state tracking
    - Activation conditions
    - Dependencies
    - Post-activation setup
    - Logging and error handling
    """

    # Feature flag mapping
    FEATURE_FLAGS = {
        "payments": "enable_payments",
        "banking": "enable_banking",
        "accounting": "enable_accounting",
        "heimdall": "enable_heimdall_autonomy",
        "deal_scoring": "enable_deal_scoring",
        "va_workflows": "enable_va_workflows",
        "automation": "enable_automation",
        "scaling": "enable_scaling_engines",
        "money_movement": "enable_finops",
    }

    # Module dependencies
    DEPENDENCIES = {
        "payments": [],
        "banking": ["payments"],
        "accounting": ["payments"],
        "heimdall": ["banking", "deal_scoring"],
        "deal_scoring": ["payments"],
        "va_workflows": ["automation"],
        "automation": ["payments"],
        "scaling": ["heimdall", "accounting"],
        "money_movement": ["banking", "accounting"],
    }

    # Activation conditions (callable functions)
    ACTIVATION_CONDITIONS: Dict[str, Callable[[], bool]] = {}

    # Post-activation setup (callable functions)
    POST_SETUP_HOOKS: Dict[str, Callable[[], None]] = {}

    def __init__(self, feature_flags_dict: Dict[str, bool]):
        """
        Initialize registry.
        
        Args:
            feature_flags_dict: Dictionary to store feature flag state
        """
        self.feature_flags = feature_flags_dict
        self.module_states: Dict[str, ModuleStatus] = {}
        self.activation_log: list = []
        
        # Initialize all modules as inactive
        for module_name in self.FEATURE_FLAGS.keys():
            self.module_states[module_name] = ModuleStatus.INACTIVE
            if module_name not in self.feature_flags:
                self.feature_flags[module_name] = False

    def register_activation_condition(
        self,
        module_name: str,
        condition_fn: Callable[[], bool]
    ) -> None:
        """Register a condition that must pass before activation."""
        self.ACTIVATION_CONDITIONS[module_name] = condition_fn
        logger.info(f"Registered activation condition for {module_name}")

    def register_post_setup(
        self,
        module_name: str,
        setup_fn: Callable[[], None]
    ) -> None:
        """Register post-activation setup function."""
        self.POST_SETUP_HOOKS[module_name] = setup_fn
        logger.info(f"Registered post-setup hook for {module_name}")

    def check_activation_conditions(self, module_name: str) -> tuple[bool, str]:
        """
        Check if all activation conditions are met.
        
        Returns:
            (success, message)
        """
        if module_name not in self.FEATURE_FLAGS:
            return False, f"Module '{module_name}' not found in registry"

        # Check custom conditions if registered
        if module_name in self.ACTIVATION_CONDITIONS:
            try:
                condition_met = self.ACTIVATION_CONDITIONS[module_name]()
                if not condition_met:
                    msg = f"Activation condition not met for {module_name}"
                    logger.warning(msg)
                    return False, msg
            except Exception as e:
                msg = f"Error checking activation condition: {e}"
                logger.error(msg)
                return False, msg

        return True, "Conditions met"

    def check_dependencies(self, module_name: str) -> tuple[bool, str]:
        """
        Check if all dependencies are active.
        
        Returns:
            (success, message)
        """
        dependencies = self.DEPENDENCIES.get(module_name, [])

        for dep in dependencies:
            dep_status = self.module_states.get(dep)
            if dep_status != ModuleStatus.ACTIVE:
                msg = f"{module_name} requires {dep} to be ACTIVE (currently {dep_status.value})"
                logger.warning(msg)
                return False, msg

        return True, "All dependencies active"

    def log_action(
        self,
        module_name: str,
        action: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log an activation/deactivation action."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "module": module_name,
            "action": action,
            "status": status,
            "details": details or {},
        }
        self.activation_log.append(entry)
        logger.info(f"Action logged: {action} - {module_name} - {status}")

    def activate_module(self, module_name: str) -> Dict[str, Any]:
        """
        Activate a module with full validation workflow.
        
        Returns:
            Result dict with status, module name, and details
        """
        # Validate module exists
        if module_name not in self.FEATURE_FLAGS:
            error_msg = f"Module '{module_name}' not found"
            logger.error(error_msg)
            self.log_action(module_name, "activate", "failed", {"error": error_msg})
            return {
                "status": "failed",
                "module": module_name,
                "error": error_msg,
                "activated": False,
            }

        # Check if already active
        if self.module_states[module_name] == ModuleStatus.ACTIVE:
            msg = f"{module_name} is already active"
            logger.info(msg)
            self.log_action(module_name, "activate", "skipped", {"reason": "already_active"})
            return {
                "status": "skipped",
                "module": module_name,
                "message": msg,
                "activated": False,
            }

        # Update state to activating
        self.module_states[module_name] = ModuleStatus.ACTIVATING

        try:
            # Step 1: Check dependencies
            deps_ok, deps_msg = self.check_dependencies(module_name)
            if not deps_ok:
                self.module_states[module_name] = ModuleStatus.ERROR
                self.log_action(
                    module_name,
                    "activate",
                    "failed",
                    {"error": deps_msg}
                )
                logger.warning(f"Dependency check failed for {module_name}: {deps_msg}")
                return {
                    "status": "failed",
                    "module": module_name,
                    "error": deps_msg,
                    "activated": False,
                }

            # Step 2: Check activation conditions
            cond_ok, cond_msg = self.check_activation_conditions(module_name)
            if not cond_ok:
                self.module_states[module_name] = ModuleStatus.ERROR
                self.log_action(
                    module_name,
                    "activate",
                    "failed",
                    {"error": cond_msg}
                )
                logger.warning(f"Condition check failed for {module_name}: {cond_msg}")
                return {
                    "status": "failed",
                    "module": module_name,
                    "error": cond_msg,
                    "activated": False,
                }

            # Step 3: Set feature flag
            flag_name = self.FEATURE_FLAGS[module_name]
            self.feature_flags[flag_name] = True
            logger.info(f"Activated {module_name} (set {flag_name}=True)")

            # Step 4: Run post-activation setup
            if module_name in self.POST_SETUP_HOOKS:
                try:
                    setup_fn = self.POST_SETUP_HOOKS[module_name]
                    setup_fn()
                    logger.info(f"Post-setup completed for {module_name}")
                except Exception as setup_error:
                    logger.error(f"Post-setup failed for {module_name}: {setup_error}")
                    # Don't fail activation, just log the error
                    self.log_action(
                        module_name,
                        "post_setup",
                        "warning",
                        {"error": str(setup_error)}
                    )

            # Step 5: Update state to active
            self.module_states[module_name] = ModuleStatus.ACTIVE

            # Log success
            self.log_action(module_name, "activate", "success")
            logger.info(f"✅ Module {module_name} activated successfully")

            return {
                "status": "success",
                "module": module_name,
                "activated": True,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            error_msg = f"Unexpected error activating {module_name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.module_states[module_name] = ModuleStatus.ERROR
            self.log_action(module_name, "activate", "error", {"error": str(e)})

            return {
                "status": "error",
                "module": module_name,
                "error": error_msg,
                "activated": False,
            }

    def deactivate_module(self, module_name: str) -> Dict[str, Any]:
        """
        Deactivate a module.
        
        Returns:
            Result dict with status and module name
        """
        # Validate module exists
        if module_name not in self.FEATURE_FLAGS:
            error_msg = f"Module '{module_name}' not found"
            logger.error(error_msg)
            self.log_action(module_name, "deactivate", "failed", {"error": error_msg})
            return {
                "status": "failed",
                "module": module_name,
                "error": error_msg,
                "deactivated": False,
            }

        # Check if already inactive
        if self.module_states[module_name] == ModuleStatus.INACTIVE:
            msg = f"{module_name} is already inactive"
            logger.info(msg)
            self.log_action(module_name, "deactivate", "skipped", {"reason": "already_inactive"})
            return {
                "status": "skipped",
                "module": module_name,
                "message": msg,
                "deactivated": False,
            }

        # Update state to deactivating
        self.module_states[module_name] = ModuleStatus.DEACTIVATING

        try:
            # Set feature flag to false
            flag_name = self.FEATURE_FLAGS[module_name]
            self.feature_flags[flag_name] = False
            logger.info(f"Deactivated {module_name} (set {flag_name}=False)")

            # Update state to inactive
            self.module_states[module_name] = ModuleStatus.INACTIVE

            # Log success
            self.log_action(module_name, "deactivate", "success")
            logger.info(f"✅ Module {module_name} deactivated successfully")

            return {
                "status": "success",
                "module": module_name,
                "deactivated": True,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            error_msg = f"Error deactivating {module_name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.module_states[module_name] = ModuleStatus.ERROR
            self.log_action(module_name, "deactivate", "error", {"error": str(e)})

            return {
                "status": "error",
                "module": module_name,
                "error": error_msg,
                "deactivated": False,
            }

    def get_module_status(self, module_name: str) -> Dict[str, Any]:
        """Get current status of a module."""
        if module_name not in self.FEATURE_FLAGS:
            return {"error": f"Module '{module_name}' not found"}

        flag_name = self.FEATURE_FLAGS[module_name]
        return {
            "module": module_name,
            "status": self.module_states[module_name].value,
            "flag_enabled": self.feature_flags.get(flag_name, False),
            "dependencies": self.DEPENDENCIES.get(module_name, []),
            "dependency_statuses": {
                dep: self.module_states.get(dep, ModuleStatus.INACTIVE).value
                for dep in self.DEPENDENCIES.get(module_name, [])
            },
        }

    def get_all_status(self) -> Dict[str, Any]:
        """Get status of all modules."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "modules": {
                module: self.get_module_status(module)
                for module in self.FEATURE_FLAGS.keys()
            },
            "active_count": sum(
                1 for status in self.module_states.values()
                if status == ModuleStatus.ACTIVE
            ),
            "total_count": len(self.FEATURE_FLAGS),
        }

    def get_activation_log(self, limit: int = 50) -> list:
        """Get recent activation actions."""
        return self.activation_log[-limit:]

    def emergency_deactivate_all(self) -> Dict[str, Any]:
        """Emergency: deactivate all modules."""
        logger.critical("🚨 EMERGENCY DEACTIVATION: Disabling all modules")

        results = {}
        for module_name in self.FEATURE_FLAGS.keys():
            if self.module_states[module_name] == ModuleStatus.ACTIVE:
                result = self.deactivate_module(module_name)
                results[module_name] = result

        self.log_action("system", "emergency_deactivate", "success", {"modules_deactivated": len(results)})

        return {
            "status": "emergency_deactivation",
            "deactivated_modules": results,
            "timestamp": datetime.utcnow().isoformat(),
        }


# Global registry instance
_module_registry: Optional[ModuleRegistry] = None


def initialize_registry(feature_flags_dict: Dict[str, bool]) -> ModuleRegistry:
    """Initialize the global module registry."""
    global _module_registry
    _module_registry = ModuleRegistry(feature_flags_dict)
    logger.info("Module registry initialized")
    return _module_registry


def get_registry() -> ModuleRegistry:
    """Get the global module registry."""
    if _module_registry is None:
        # Initialize with empty dict if not already initialized
        initialize_registry({})
    return _module_registry


def activate_module(module_name: str) -> Dict[str, Any]:
    """Activate a module."""
    return get_registry().activate_module(module_name)


def deactivate_module(module_name: str) -> Dict[str, Any]:
    """Deactivate a module."""
    return get_registry().deactivate_module(module_name)


def get_module_status(module_name: str) -> Dict[str, Any]:
    """Get module status."""
    return get_registry().get_module_status(module_name)


def get_all_status() -> Dict[str, Any]:
    """Get all modules status."""
    return get_registry().get_all_status()


def get_activation_log(limit: int = 50) -> list:
    """Get activation log."""
    return get_registry().get_activation_log(limit)
