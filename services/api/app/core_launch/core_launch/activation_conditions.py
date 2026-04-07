"""
VALHALLA ACTIVATION CONDITIONS ENGINE
====================================

Determines readiness for activating dark modules based on business conditions.
"""

from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from datetime import datetime

class ConditionType(Enum):
    """Types of activation conditions."""
    MINIMUM_BALANCE = "minimum_balance"
    TIME_ELAPSED = "time_elapsed"
    DEAL_VOLUME = "deal_volume"
    COMPLIANCE_CHECK = "compliance_check"
    SYSTEM_HEALTH = "system_health"
    APPROVAL_GATE = "approval_gate"
    METRIC_THRESHOLD = "metric_threshold"

class ActivationRule:
    """Single activation rule."""

    def __init__(
        self,
        name: str,
        condition_type: ConditionType,
        check_fn: Callable[[], bool],
        description: str = "",
    ):
        self.name = name
        self.condition_type = condition_type
        self.check_fn = check_fn
        self.description = description
        self.last_check: Optional[str] = None
        self.last_result: Optional[bool] = None

    def check(self) -> bool:
        """Check if condition is met."""
        try:
            result = self.check_fn()
            self.last_check = datetime.utcnow().isoformat()
            self.last_result = result
            return result
        except Exception as e:
            print(f"❌ Error checking {self.name}: {e}")
            return False

    def status(self) -> Dict[str, Any]:
        """Get rule status."""
        return {
            "name": self.name,
            "type": self.condition_type.value,
            "description": self.description,
            "last_check": self.last_check,
            "last_result": self.last_result,
        }


class ActivationConditionEngine:
    """Manages activation conditions for modules."""

    def __init__(self):
        self.rules: Dict[str, List[ActivationRule]] = {}
        self.approvals: Dict[str, bool] = {}
        self.metrics: Dict[str, Any] = {}

    def register_rule(
        self, 
        module_name: str, 
        rule: ActivationRule
    ) -> None:
        """Register a rule for a module."""
        if module_name not in self.rules:
            self.rules[module_name] = []
        self.rules[module_name].append(rule)

    def register_approval_gate(self, name: str, approved: bool = False) -> None:
        """Register an approval gate (manual gate)."""
        self.approvals[name] = approved

    def approve(self, name: str) -> None:
        """Approve a gate."""
        self.approvals[name] = True

    def reject(self, name: str) -> None:
        """Reject a gate."""
        self.approvals[name] = False

    def set_metric(self, name: str, value: Any) -> None:
        """Set a metric value."""
        self.metrics[name] = value

    def can_activate(self, module_name: str) -> bool:
        """Check if module can be activated."""
        module_rules = self.rules.get(module_name, [])
        
        # All rules must pass
        for rule in module_rules:
            if not rule.check():
                return False
        
        return True

    def activation_status(self, module_name: str) -> Dict[str, Any]:
        """Get activation status for a module."""
        module_rules = self.rules.get(module_name, [])
        
        return {
            "module": module_name,
            "can_activate": self.can_activate(module_name),
            "conditions": [rule.status() for rule in module_rules],
            "approval_gates": {
                name: approved 
                for name, approved in self.approvals.items()
                if f"{module_name}_" in name
            },
        }

    def full_status(self) -> Dict[str, Any]:
        """Get full activation status."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "modules": {
                module: self.activation_status(module)
                for module in self.rules.keys()
            },
            "metrics": self.metrics,
        }


# Default rules and singleton
_condition_engine = ActivationConditionEngine()

def can_activate(module_name: str) -> bool:
    """Check if module can be activated."""
    return _condition_engine.can_activate(module_name)

def get_activation_status(module_name: str) -> Dict[str, Any]:
    """Get activation status."""
    return _condition_engine.activation_status(module_name)

def set_metric(name: str, value: Any) -> None:
    """Set a metric."""
    _condition_engine.set_metric(name, value)

def approve_gate(gate_name: str) -> None:
    """Approve a gate."""
    _condition_engine.approve(gate_name)

def reject_gate(gate_name: str) -> None:
    """Reject a gate."""
    _condition_engine.reject(gate_name)

def full_status() -> Dict[str, Any]:
    """Get full activation status."""
    return _condition_engine.full_status()
