from __future__ import annotations
from typing import Any, Dict

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def calc_wholesale_mao(arv: float, repairs: float, fee: float = 10000.0, arv_pct: float = 0.70) -> Dict[str, Any]:
    arv = float(arv or 0.0)
    repairs = float(repairs or 0.0)
    fee = float(fee or 0.0)
    arv_pct = clamp(float(arv_pct or 0.70), 0.0, 1.0)
    mao = (arv * arv_pct) - repairs - fee
    return {
        "model": "wholesale_70_rule_v1",
        "inputs": {"arv": arv, "repairs": repairs, "fee": fee, "arv_pct": arv_pct},
        "mao": round(mao, 2)
    }

def calc_brrrr_offer(arv: float, repairs: float, target_ltv: float = 0.75, closing_costs: float = 0.0, buffer: float = 0.0) -> Dict[str, Any]:
    arv = float(arv or 0.0)
    repairs = float(repairs or 0.0)
    target_ltv = clamp(float(target_ltv or 0.75), 0.0, 1.0)
    closing_costs = float(closing_costs or 0.0)
    buffer = float(buffer or 0.0)
    # simplistic: max all-in = ARV*LTV; offer = max_all_in - repairs - closing - buffer
    max_all_in = arv * target_ltv
    offer = max_all_in - repairs - closing_costs - buffer
    return {
        "model": "brrrr_ltv_v1",
        "inputs": {"arv": arv, "repairs": repairs, "target_ltv": target_ltv, "closing_costs": closing_costs, "buffer": buffer},
        "max_all_in": round(max_all_in, 2),
        "max_offer": round(offer, 2),
    }
