from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EngineBlocked(Exception):
    engine_name: str
    action: str
    state: str
    reason: str
