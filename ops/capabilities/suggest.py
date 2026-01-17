from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from .cert_gate import can_surface_auto

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "ops" / "capabilities" / "registry.json"


def load_registry() -> Dict[str, Any]:
    return json.loads(REGISTRY_PATH.read_text())


def score_capability(context: str, cap: Dict[str, Any]) -> int:
    ctx = context.lower()
    score = 0
    for trig in cap.get("triggers", []):
        t = str(trig).lower()
        if t and t in ctx:
            score += 10
    # small bonus for SAFE items
    if (cap.get("risk_class") or "").upper() == "SAFE":
        score += 1
    return score


def suggest(context: str, max_suggestions: int = 3) -> List[Dict[str, Any]]:
    reg = load_registry()
    require_cert = bool(reg.get("rules", {}).get("auto_surface_requires_certified", True))

    scored: List[Tuple[int, Dict[str, Any]]] = []
    for cap in reg.get("capabilities", []):
        gate = can_surface_auto(cap, require_certified=require_cert)
        if not gate.allowed:
            continue
        s = score_capability(context, cap)
        if s > 0:
            scored.append((s, cap))

    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    for s, cap in scored[:max_suggestions]:
        out.append({
            "id": cap.get("id"),
            "name": cap.get("name"),
            "type": cap.get("type"),
            "risk_class": cap.get("risk_class"),
            "how_to_use": cap.get("how_to_use", {}),
            "score": s
        })
    return out
