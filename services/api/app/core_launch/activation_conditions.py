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


# ========================
# DEFAULT ACTIVATION RULES
# ========================

def create_payment_rules(engine: ActivationConditionEngine) -> None:
    """Create rules for payment system activation."""
    # Rule 1: Minimum account balance
    engine.register_rule(
        "payment_processor",
        ActivationRule(
            "min_account_balance",
            ConditionType.MINIMUM_BALANCE,
            lambda: engine.metrics.get("account_balance", 0) >= 10000,
            "Account must have at least $10,000"
        )
    )
    
    # Rule 2: System health check
    engine.register_rule(
        "payment_processor",
        ActivationRule(
            "system_health",
            ConditionType.SYSTEM_HEALTH,
            lambda: engine.metrics.get("system_health", False),
            "System health check must pass"
        )
    )
    
    # Rule 3: Approval gate
    engine.register_approval_gate("payment_processor_approval", approved=False)


def create_banking_rules(engine: ActivationConditionEngine) -> None:
    """Create rules for banking system activation."""
    # Rule 1: API credentials configured
    engine.register_rule(
        "banking_connector",
        ActivationRule(
            "credentials_configured",
            ConditionType.APPROVAL_GATE,
            lambda: engine.approvals.get("banking_credentials", False),
            "Plaid API credentials must be configured"
        )
    )
    
    # Rule 2: Compliance approval
    engine.register_rule(
        "banking_connector",
        ActivationRule(
            "compliance_approved",
            ConditionType.COMPLIANCE_CHECK,
            lambda: engine.approvals.get("banking_compliance", False),
            "Compliance team must approve banking integration"
        )
    )


def create_ai_rules(engine: ActivationConditionEngine) -> None:
    """Create rules for AI system activation."""
    # Rule 1: Deal volume threshold
    engine.register_rule(
        "heimdall_core",
        ActivationRule(
            "deal_volume",
            ConditionType.DEAL_VOLUME,
            lambda: engine.metrics.get("active_deals", 0) >= 5,
            "Must have at least 5 active deals"
        )
    )
    
    # Rule 2: Models trained
    engine.register_rule(
        "heimdall_core",
        ActivationRule(
            "models_ready",
            ConditionType.APPROVAL_GATE,
            lambda: engine.approvals.get("heimdall_models", False),
            "ML models must be trained and ready"
        )
    )
    
    # Rule 3: Manual approval
    engine.register_approval_gate("heimdall_activation", approved=False)


def create_scaling_rules(engine: ActivationConditionEngine) -> None:
    """Create rules for scaling system activation."""
    # Rule 1: Revenue threshold
    engine.register_rule(
        "property_cloning_engine",
        ActivationRule(
            "revenue_threshold",
            ConditionType.METRIC_THRESHOLD,
            lambda: engine.metrics.get("monthly_revenue", 0) >= 100000,
            "Monthly revenue must exceed $100,000"
        )
    )
    
    # Rule 2: Approval from leadership
    engine.register_approval_gate("scaling_approval", approved=False)


# ========================
# SINGLETON INSTANCE
# ========================

_condition_engine = ActivationConditionEngine()

# Initialize default rules
create_payment_rules(_condition_engine)
create_banking_rules(_condition_engine)
create_ai_rules(_condition_engine)
create_scaling_rules(_condition_engine)


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
