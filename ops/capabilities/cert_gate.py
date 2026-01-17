from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class GateResult:
    allowed: bool
    reason: str


def can_surface_auto(cap: Dict[str, Any], require_certified: bool = True) -> GateResult:
    status = (cap.get("status") or "").upper()
    if require_certified and status != "CERTIFIED":
        return GateResult(False, f"Not CERTIFIED (status={status})")
    return GateResult(True, "OK")
