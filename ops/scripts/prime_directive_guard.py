from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "ops" / "logs" / "prime_directive_guard.jsonl"

DEFAULTS = {
    "max_daily_loss_pct": 1.0,
    "max_drawdown_pct": 8.0,
    "projection_miss_tolerance_pct": 3.0,
    "allow_irreversible": False
}

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def log(event: dict) -> None:
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

def assert_prime_directive(context: dict, policy: dict | None = None) -> None:
    """
    context expected keys (optional but recommended):
      - subsystem: str
      - action: str
      - irreversible: bool
      - projected_variance_pct: float (negative means below target)
      - daily_loss_pct: float
      - drawdown_pct: float
    """
    pol = dict(DEFAULTS)
    if policy:
        pol.update(policy)

    subsystem = context.get("subsystem", "unknown")
    action = context.get("action", "unknown")
    irreversible = bool(context.get("irreversible", False))

    projected_variance_pct = float(context.get("projected_variance_pct", 0.0))
    daily_loss_pct = float(context.get("daily_loss_pct", 0.0))
    drawdown_pct = float(context.get("drawdown_pct", 0.0))

    breaches = []

    # Hard guardrails
    if daily_loss_pct > pol["max_daily_loss_pct"]:
        breaches.append(f"daily_loss_pct {daily_loss_pct} > {pol['max_daily_loss_pct']}")

    if drawdown_pct > pol["max_drawdown_pct"]:
        breaches.append(f"drawdown_pct {drawdown_pct} > {pol['max_drawdown_pct']}")

    if projected_variance_pct < -abs(pol["projection_miss_tolerance_pct"]):
        breaches.append(f"projection variance {projected_variance_pct}% below tolerance {-abs(pol['projection_miss_tolerance_pct'])}%")

    if irreversible and not pol["allow_irreversible"]:
        breaches.append("irreversible action attempted while allow_irreversible=false")

    event = {
        "at": utc_now_iso(),
        "subsystem": subsystem,
        "action": action,
        "context": context,
        "policy": pol,
        "breaches": breaches
    }
    log(event)

    if breaches:
        raise SystemExit("[PRIME DIRECTIVE BLOCKED] " + " | ".join(breaches))

if __name__ == "__main__":
    # Tiny self-test (safe)
    assert_prime_directive({
        "subsystem": "test",
        "action": "self_test",
        "irreversible": False,
        "projected_variance_pct": 0.0,
        "daily_loss_pct": 0.0,
        "drawdown_pct": 0.0
    })
    print("[OK] prime_directive_guard self-test passed")
