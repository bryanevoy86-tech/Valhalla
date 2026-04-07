FEATURE_FLAGS = {
    "launch_core_only": True,
    "enable_eia_tracking": True,
    "require_eia_compliance": True,
    "enable_experimental": False,
    "enable_phase2_expansion": False,
    "enable_heimdall_autonomy": False,
    "enable_finops": False,
    "enable_accounting": False,
    "enable_banking": False,
    "enable_payments": False,
}

def is_enabled(name: str) -> bool:
    return FEATURE_FLAGS.get(name, False)

def all_flags():
    return FEATURE_FLAGS.copy()
