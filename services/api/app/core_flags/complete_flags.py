"""
VALHALLA FEATURE FLAG SYSTEM - Complete Activation Control System
=================================================================

This system provides comprehensive feature flag management with:
- Complete feature catalog
- Module registration and dependencies
- Activation state tracking
- Conditional activation (can turn on when conditions met)
- Rollback support
"""

from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import json

class ActivationStatus(Enum):
    """Status of a feature flag."""
    DISABLED = "disabled"
    READY = "ready"  # Ready to activate
    ACTIVE = "active"  # Currently active
    PAUSED = "paused"  # Was active, now paused
    ERROR = "error"  # Error during activation

class ModuleType(Enum):
    """Module categories."""
    CORE = "core"  # Must be active
    BUSINESS_ENGINE = "business_engine"  # Revenue and scaling
    AI_SYSTEM = "ai_system"  # Heimdall and decision systems
    FINANCIAL = "financial"  # Payments and money movement
    INTEGRATION = "integration"  # External integrations
    AUTOMATION = "automation"  # Workflow automation
    REPORTING = "reporting"  # Analytics and reports

# ========================
# COMPLETE FEATURE CATALOG
# ========================

FEATURE_FLAGS = {
    # === CORE SYSTEMS (Always on) ===
    "launch_core_only": {"enabled": True, "type": ModuleType.CORE, "description": "Launch mode - core only"},
    "enable_eia_tracking": {"enabled": True, "type": ModuleType.CORE, "description": "EIA compliance tracking"},
    "require_eia_compliance": {"enabled": True, "type": ModuleType.CORE, "description": "Strict EIA compliance"},

    # === LAYER 1: DEAL PROCESSING (Always on for launch) ===
    "lead_intake": {"enabled": True, "type": ModuleType.BUSINESS_ENGINE, "description": "Lead intake processing"},
    "deal_creation": {"enabled": True, "type": ModuleType.BUSINESS_ENGINE, "description": "Deal creation from leads"},
    "offer_generation": {"enabled": True, "type": ModuleType.BUSINESS_ENGINE, "description": "Offer generation"},
    "basic_scoring": {"enabled": True, "type": ModuleType.BUSINESS_ENGINE, "description": "Basic deal scoring"},

    # === LAYER 2: PAYMENTS & FINANCIAL (Off until activated) ===
    "enable_payments": {"enabled": False, "type": ModuleType.FINANCIAL, "description": "Stripe/ACH payments"},
    "enable_payment_processing": {"enabled": False, "type": ModuleType.FINANCIAL, "description": "Process payments automatically"},
    "enable_escrow_management": {"enabled": False, "type": ModuleType.FINANCIAL, "description": "Automated escrow handling"},
    "automated_money_moves": {"enabled": False, "type": ModuleType.FINANCIAL, "description": "Automated transfer routing"},
    "profit_distribution": {"enabled": False, "type": ModuleType.FINANCIAL, "description": "Automated profit shares"},

    # === LAYER 3: BANKING (Off until activated) ===
    "enable_banking": {"enabled": False, "type": ModuleType.INTEGRATION, "description": "Plaid banking integration"},
    "enable_account_linking": {"enabled": False, "type": ModuleType.INTEGRATION, "description": "Bank account linking"},
    "enable_balance_tracking": {"enabled": False, "type": ModuleType.INTEGRATION, "description": "Real-time balance tracking"},

    # === LAYER 4: ACCOUNTING (Off until activated) ===
    "enable_accounting": {"enabled": False, "type": ModuleType.FINANCIAL, "description": "QuickBooks integration"},
    "enable_transaction_sync": {"enabled": False, "type": ModuleType.FINANCIAL, "description": "Auto sync transactions"},
    "enable_tax_calculation": {"enabled": False, "type": ModuleType.FINANCIAL, "description": "Automated tax calculation"},

    # === LAYER 5: AI SYSTEMS (Off until activated) ===
    "enable_ai_gods": {"enabled": False, "type": ModuleType.AI_SYSTEM, "description": "All AI decision systems"},
    "enable_heimdall_autonomy": {"enabled": False, "type": ModuleType.AI_SYSTEM, "description": "Heimdall autonomous system"},
    "enable_advanced_deal_scoring": {"enabled": False, "type": ModuleType.AI_SYSTEM, "description": "AI-based deal scoring"},
    "enable_behavioral_profiling": {"enabled": False, "type": ModuleType.AI_SYSTEM, "description": "Behavioral intelligence"},
    "enable_negotiation_ai": {"enabled": False, "type": ModuleType.AI_SYSTEM, "description": "Negotiation AI"},
    "enable_predictive_analytics": {"enabled": False, "type": ModuleType.AI_SYSTEM, "description": "Predictive analytics"},

    # === LAYER 6: AUTOMATION (Off until activated) ===
    "enable_va_workflows": {"enabled": False, "type": ModuleType.AUTOMATION, "description": "VA task automation"},
    "enable_contract_automation": {"enabled": False, "type": ModuleType.AUTOMATION, "description": "Contract automation (DocuSign)"},
    "enable_follow_up_automation": {"enabled": False, "type": ModuleType.AUTOMATION, "description": "Auto follow-ups"},
    "enable_lead_nurture": {"enabled": False, "type": ModuleType.AUTOMATION, "description": "Automated lead nurturing"},

    # === LAYER 7: SCALING ENGINES (Off until activated) ===
    "enable_scaling_engines": {"enabled": False, "type": ModuleType.BUSINESS_ENGINE, "description": "Auto-scaling mechanisms"},
    "enable_property_cloning": {"enabled": False, "type": ModuleType.BUSINESS_ENGINE, "description": "Property/deal cloning"},
    "enable_vault_management": {"enabled": False, "type": ModuleType.BUSINESS_ENGINE, "description": "Vault system management"},
    "enable_arbitrage_engine": {"enabled": False, "type": ModuleType.BUSINESS_ENGINE, "description": "Arbitrage operations"},
    "enable_reinvestment_automation": {"enabled": False, "type": ModuleType.BUSINESS_ENGINE, "description": "Auto-reinvestment"},

    # === LAYER 8: ADVANCED FEATURES (Off until activated) ===
    "enable_finops": {"enabled": False, "type": ModuleType.FINANCIAL, "description": "FinOps system"},
    "enable_phase2_expansion": {"enabled": False, "type": ModuleType.BUSINESS_ENGINE, "description": "Phase 2 features"},
    "enable_multi_market": {"enabled": False, "type": ModuleType.BUSINESS_ENGINE, "description": "Multi-market operations"},
    "enable_investor_portal": {"enabled": False, "type": ModuleType.AUTOMATION, "description": "Investor self-service"},

    # === LAYER 9: REPORTING & MONITORING (Off until activated) ===
    "enable_advanced_reporting": {"enabled": False, "type": ModuleType.REPORTING, "description": "Advanced analytics"},
    "enable_real_time_dashboards": {"enabled": False, "type": ModuleType.REPORTING, "description": "Real-time dashboards"},
    "enable_custom_reports": {"enabled": False, "type": ModuleType.REPORTING, "description": "Custom report generation"},
}

# ========================
# MODULE DEPENDENCIES
# ========================
# If Module A is activated, these modules must also be active

MODULE_DEPENDENCIES = {
    "enable_payment_processing": ["enable_payments", "enable_escrow_management"],
    "profit_distribution": ["enable_payments", "enable_payment_processing"],
    "enable_account_linking": ["enable_banking"],
    "enable_balance_tracking": ["enable_banking"],
    "automated_money_moves": ["enable_payments", "enable_banking"],
    "enable_transaction_sync": ["enable_accounting", "enable_banking"],
    "enable_tax_calculation": ["enable_accounting", "enable_transaction_sync"],
    "enable_heimdall_autonomy": ["enable_ai_gods", "enable_advanced_deal_scoring"],
    "enable_negotiation_ai": ["enable_ai_gods"],
    "enable_behavioral_profiling": ["enable_ai_gods"],
    "enable_va_workflows": ["enable_contract_automation"],
    "enable_property_cloning": ["enable_scaling_engines"],
    "enable_vault_management": ["enable_scaling_engines"],
    "enable_arbitrage_engine": ["enable_scaling_engines"],
    "enable_multi_market": ["enable_phase2_expansion"],
    "enable_investor_portal": ["enable_phase2_expansion"],
    "enable_real_time_dashboards": ["enable_advanced_reporting"],
}

# ========================
# FEATURE FLAG SYSTEM API
# ========================

class FeatureFlagSystem:
    """Complete feature flag management system."""

    def __init__(self):
        self.flags = FEATURE_FLAGS.copy()
        self.activation_history: List[Dict[str, Any]] = []
        self.status: Dict[str, ActivationStatus] = {
            name: ActivationStatus.ACTIVE if flag["enabled"] else ActivationStatus.READY
            for name, flag in self.flags.items()
        }

    def is_enabled(self, name: str, default: bool = False) -> bool:
        """Check if a feature is enabled."""
        flag = self.flags.get(name)
        if flag is None:
            return default
        return flag["enabled"]

    def enable_feature(self, name: str, reason: str = "") -> bool:
        """Enable a feature flag."""
        if name not in self.flags:
            return False

        # Check dependencies
        dependencies = MODULE_DEPENDENCIES.get(name, [])
        for dep in dependencies:
            if not self.is_enabled(dep):
                print(f"⚠️  Warning: {name} depends on {dep} which is not enabled")
                return False

        self.flags[name]["enabled"] = True
        self.status[name] = ActivationStatus.ACTIVE
        self.activation_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "enable",
            "feature": name,
            "reason": reason
        })
        return True

    def disable_feature(self, name: str, reason: str = "") -> bool:
        """Disable a feature flag."""
        if name not in self.flags:
            return False

        self.flags[name]["enabled"] = False
        self.status[name] = ActivationStatus.DISABLED
        self.activation_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "disable",
            "feature": name,
            "reason": reason
        })
        return True

    def all_flags(self) -> Dict[str, bool]:
        """Get all flags as dict."""
        return {name: flag["enabled"] for name, flag in self.flags.items()}

    def flags_by_type(self, flag_type: ModuleType) -> Dict[str, bool]:
        """Get all flags of a specific type."""
        return {
            name: flag["enabled"]
            for name, flag in self.flags.items()
            if flag["type"] == flag_type
        }

    def active_flags(self) -> Dict[str, bool]:
        """Get only active flags."""
        return {name: True for name, flag in self.flags.items() if flag["enabled"]}

    def inactive_flags(self) -> Dict[str, bool]:
        """Get only inactive flags."""
        return {name: False for name, flag in self.flags.items() if not flag["enabled"]}

    def status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_flags": len(self.flags),
            "active_flags": len([f for f in self.flags.values() if f["enabled"]]),
            "inactive_flags": len([f for f in self.flags.values() if not f["enabled"]]),
            "by_type": {
                mtype.value: {
                    "total": len([f for f in self.flags.values() if f["type"] == mtype]),
                    "active": len([f for f in self.flags.values() if f["type"] == mtype and f["enabled"]]),
                }
                for mtype in ModuleType
            },
            "active_features": self.active_flags(),
        }

    def to_json(self) -> str:
        """Export flags as JSON."""
        return json.dumps(self.all_flags(), indent=2)

# ========================
# SINGLETON INSTANCE
# ========================

_feature_flags = FeatureFlagSystem()

def is_enabled(name: str, default: bool = False) -> bool:
    """Check if feature is enabled."""
    return _feature_flags.is_enabled(name, default)

def enable_feature(name: str, reason: str = "") -> bool:
    """Enable a feature."""
    return _feature_flags.enable_feature(name, reason)

def disable_feature(name: str, reason: str = "") -> bool:
    """Disable a feature."""
    return _feature_flags.disable_feature(name, reason)

def all_flags() -> Dict[str, bool]:
    """Get all flags."""
    return _feature_flags.all_flags()

def status_report() -> Dict[str, Any]:
    """Get status report."""
    return _feature_flags.status_report()

def flags_by_type(flag_type: ModuleType) -> Dict[str, bool]:
    """Get flags by type."""
    return _feature_flags.flags_by_type(flag_type)
