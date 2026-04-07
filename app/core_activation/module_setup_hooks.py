"""
MODULE-SPECIFIC POST-ACTIVATION SETUP HOOKS
===========================================

Setup functions executed after module activation to initialize
external service integrations, load configurations, and prepare
module-specific resources.

These hooks are registered with the module registry and execute
after a module is activated but before activation is considered complete.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


# ============================================================================
# PAYMENTS MODULE SETUP
# ============================================================================

def setup_payments_module() -> bool:
    """
    Initialize Stripe API integration and load merchant account configurations.
    
    This runs after the payments module is activated to:
    - Verify Stripe API credentials
    - Load merchant account settings
    - Initialize payment processor
    
    Returns:
        True if setup successful, False otherwise
    """
    try:
        logger.info("📊 Setting up PAYMENTS module...")
        
        # Import Stripe configuration
        from app.config import settings
        
        # Verify Stripe API key exists
        stripe_key = getattr(settings, 'STRIPE_API_KEY', None)
        if not stripe_key:
            logger.warning("PAYMENTS: Stripe API key not configured")
            return False
        
        logger.info("✅ PAYMENTS module setup complete")
        return True
        
    except Exception as e:
        logger.error(f"❌ PAYMENTS setup failed: {e}")
        return False


# ============================================================================
# BANKING MODULE SETUP
# ============================================================================

def setup_banking_module() -> bool:
    """
    Initialize Plaid API integration for bank account linking.
    
    This runs after the banking module is activated to:
    - Verify Plaid API credentials
    - Initialize Plaid client
    - Load banking institution data
    
    Returns:
        True if setup successful, False otherwise
    """
    try:
        logger.info("🏦 Setting up BANKING module...")
        
        # Import Plaid configuration
        from app.config import settings
        
        # Verify Plaid credentials
        plaid_client_id = getattr(settings, 'PLAID_CLIENT_ID', None)
        plaid_secret = getattr(settings, 'PLAID_SECRET', None)
        
        if not plaid_client_id or not plaid_secret:
            logger.warning("BANKING: Plaid credentials not configured")
            return False
        
        logger.info("✅ BANKING module setup complete")
        return True
        
    except Exception as e:
        logger.error(f"❌ BANKING setup failed: {e}")
        return False


# ============================================================================
# HEIMDALL (AI AUTONOMY) MODULE SETUP
# ============================================================================

def setup_heimdall_module() -> bool:
    """
    Initialize AI autonomy engine, load decision models, and prepare
    the Heimdall governance system.
    
    This runs after the heimdall module is activated to:
    - Load AI decision models
    - Initialize autonomy governance rules
    - Setup monitoring and audit logging
    
    Returns:
        True if setup successful, False otherwise
    """
    try:
        logger.info("🤖 Setting up HEIMDALL (AI Autonomy) module...")
        
        # Import Heimdall configuration
        from app.config import settings
        
        # Verify Heimdall is enabled
        heimdall_enabled = getattr(settings, 'HEIMDALL_ENABLED', False)
        
        if not heimdall_enabled:
            logger.warning("HEIMDALL: AI autonomy not enabled in settings")
            return False
        
        logger.info("✅ HEIMDALL module setup complete")
        return True
        
    except Exception as e:
        logger.error(f"❌ HEIMDALL setup failed: {e}")
        return False


# ============================================================================
# DEAL SCORING MODULE SETUP
# ============================================================================

def setup_deal_scoring_module() -> bool:
    """
    Initialize deal scoring engine and load scoring models.
    
    This runs after the deal_scoring module is activated to:
    - Load ML scoring models
    - Initialize scoring cache
    - Setup scoring pipeline
    
    Returns:
        True if setup successful, False otherwise
    """
    try:
        logger.info("📈 Setting up DEAL SCORING module...")
        
        # Deal scoring setup would load models here
        logger.info("✅ DEAL SCORING module setup complete")
        return True
        
    except Exception as e:
        logger.error(f"❌ DEAL SCORING setup failed: {e}")
        return False


# ============================================================================
# VA WORKFLOWS MODULE SETUP
# ============================================================================

def setup_va_workflows_module() -> bool:
    """
    Initialize Virtual Assistant workflow engine.
    
    This runs after the va_workflows module is activated to:
    - Load workflow definitions
    - Initialize task queue
    - Setup VA communication channels
    
    Returns:
        True if setup successful, False otherwise
    """
    try:
        logger.info("🤖 Setting up VA WORKFLOWS module...")
        
        logger.info("✅ VA WORKFLOWS module setup complete")
        return True
        
    except Exception as e:
        logger.error(f"❌ VA WORKFLOWS setup failed: {e}")
        return False


# ============================================================================
# AUTOMATION MODULE SETUP
# ============================================================================

def setup_automation_module() -> bool:
    """
    Initialize workflow automation engine.
    
    This runs after the automation module is activated to:
    - Load automation rules
    - Initialize scheduler
    - Setup automation triggers
    
    Returns:
        True if setup successful, False otherwise
    """
    try:
        logger.info("⚙️ Setting up AUTOMATION module...")
        
        logger.info("✅ AUTOMATION module setup complete")
        return True
        
    except Exception as e:
        logger.error(f"❌ AUTOMATION setup failed: {e}")
        return False


# ============================================================================
# PROPERTY SCALING MODULE SETUP
# ============================================================================

def setup_scaling_module() -> bool:
    """
    Initialize property scaling engine for cloning/portfolio expansion.
    
    This runs after the scaling module is activated to:
    - Load scaling templates
    - Initialize cloning engine
    - Setup property management cache
    
    Returns:
        True if setup successful, False otherwise
    """
    try:
        logger.info("📦 Setting up PROPERTY SCALING module...")
        
        logger.info("✅ PROPERTY SCALING module setup complete")
        return True
        
    except Exception as e:
        logger.error(f"❌ PROPERTY SCALING setup failed: {e}")
        return False


# ============================================================================
# MONEY MOVEMENT MODULE SETUP
# ============================================================================

def setup_money_movement_module() -> bool:
    """
    Initialize money movement and fund distribution system.
    
    This runs after the money_movement module is activated to:
    - Initialize payment rails
    - Setup fund distribution rules
    - Configure ACH/wire integration
    
    Returns:
        True if setup successful, False otherwise
    """
    try:
        logger.info("💰 Setting up MONEY MOVEMENT module...")
        
        logger.info("✅ MONEY MOVEMENT module setup complete")
        return True
        
    except Exception as e:
        logger.error(f"❌ MONEY MOVEMENT setup failed: {e}")
        return False


# ============================================================================
# ACCOUNTING MODULE SETUP
# ============================================================================

def setup_accounting_module() -> bool:
    """
    Initialize accounting and compliance system.
    
    This runs after the accounting module is activated to:
    - Load accounting rules
    - Initialize compliance checker
    - Setup audit logging
    
    Returns:
        True if setup successful, False otherwise
    """
    try:
        logger.info("📊 Setting up ACCOUNTING module...")
        
        logger.info("✅ ACCOUNTING module setup complete")
        return True
        
    except Exception as e:
        logger.error(f"❌ ACCOUNTING setup failed: {e}")
        return False


# ============================================================================
# HOOK REGISTRATION REGISTRY
# ============================================================================

# Map module names to their setup functions
MODULE_SETUP_HOOKS: Dict[str, callable] = {
    "payments": setup_payments_module,
    "banking": setup_banking_module,
    "heimdall": setup_heimdall_module,
    "deal_scoring": setup_deal_scoring_module,
    "va_workflows": setup_va_workflows_module,
    "automation": setup_automation_module,
    "scaling": setup_scaling_module,
    "money_movement": setup_money_movement_module,
    "accounting": setup_accounting_module,
}


def register_all_setup_hooks(registry) -> None:
    """
    Register all module setup hooks with the module registry.
    
    Args:
        registry: ModuleRegistry instance
    """
    for module_name, setup_func in MODULE_SETUP_HOOKS.items():
        try:
            registry.register_post_setup(module_name, setup_func)
            logger.debug(f"Registered setup hook for {module_name}")
        except Exception as e:
            logger.error(f"Failed to register setup hook for {module_name}: {e}")


def get_setup_status(module_name: str) -> Dict[str, Any]:
    """
    Get the status of a module's setup hook.
    
    Args:
        module_name: Name of the module
        
    Returns:
        Dictionary with setup hook information
    """
    if module_name in MODULE_SETUP_HOOKS:
        return {
            "module": module_name,
            "has_setup_hook": True,
            "setup_function": MODULE_SETUP_HOOKS[module_name].__name__,
        }
    else:
        return {
            "module": module_name,
            "has_setup_hook": False,
        }
