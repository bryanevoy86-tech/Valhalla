"""
Policy loader - reads policy.yaml and caches the result.
"""

from pathlib import Path
import yaml
from .schemas import UnifiedPolicy

_POLICY_CACHE: UnifiedPolicy | None = None


def load_policy() -> UnifiedPolicy:
    """
    Load and cache the Unified Policy from policy.yaml.
    
    Returns:
        UnifiedPolicy: The loaded and validated policy configuration.
    
    Raises:
        ValidationError: If policy.yaml is invalid.
        FileNotFoundError: If policy.yaml is not found.
    """
    global _POLICY_CACHE
    if _POLICY_CACHE is not None:
        return _POLICY_CACHE

    policy_path = Path(__file__).with_name("policy.yaml")
    data = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    _POLICY_CACHE = UnifiedPolicy.model_validate(data)
    return _POLICY_CACHE
