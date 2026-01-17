from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Protocol

@dataclass
class EngineResult:
    ok: bool
    detail: str
    data: Dict[str, Any] | None = None

class Engine(Protocol):
    name: str
    def run(self) -> EngineResult: ...
    def optimize(self) -> EngineResult: ...
    def scale(self) -> EngineResult: ...
