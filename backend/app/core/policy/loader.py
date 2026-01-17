from __future__ import annotations

from pathlib import Path
import yaml
from .schemas import UnifiedPolicy

_POLICY_CACHE: UnifiedPolicy | None = None


def load_policy() -> UnifiedPolicy:
    global _POLICY_CACHE
    if _POLICY_CACHE is not None:
        return _POLICY_CACHE

    policy_path = Path(__file__).with_name("policy.yaml")
    data = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    _POLICY_CACHE = UnifiedPolicy.model_validate(data)
    return _POLICY_CACHE


def reload_policy() -> UnifiedPolicy:
    global _POLICY_CACHE
    _POLICY_CACHE = None
    return load_policy()
