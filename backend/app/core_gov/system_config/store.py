"""
P-SYSCFG-1: System configuration store.

Manages system-wide configuration including:
- soft_launch (bool)
- require_approvals_for_execute (bool)
- allow_external_sending (bool)
- default_currency (str)
"""
import json
import os
from typing import Dict, Any

CONFIG_FILE = "backend/data/system_config.json"

DEFAULT = {
    "soft_launch": True,
    "require_approvals_for_execute": False,
    "allow_external_sending": False,
    "default_currency": "USD"
}


def _ensure_file() -> None:
    """Ensure config file exists with defaults."""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT.copy(), f, indent=2)


def get() -> Dict[str, Any]:
    """
    Get current system configuration.
    
    Returns:
        Configuration dict
    """
    _ensure_file()
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save(patch: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save/patch system configuration.
    
    Args:
        patch: Dict of config keys to update
    
    Returns:
        Updated configuration dict
    """
    _ensure_file()
    
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
    
    # Validate patch
    for key in patch:
        if key not in DEFAULT:
            raise ValueError(f"Unknown config key: {key}")
    
    # Merge patch
    config.update(patch)
    
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    
    return config
