from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "ops" / "capabilities" / "registry.json"

RISK_WEIGHT = {
    "SAFE": 3,
    "GATED": 1,
    "DANGEROUS": -10
}

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def parse_iso(s: str | None) -> float:
    if not s:
        return 0.0
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0

def load_registry() -> dict[str, Any]:
    if not REGISTRY.exists():
        raise SystemExit(f"[ERR] Registry not found: {REGISTRY}")
    return json.loads(REGISTRY.read_text(encoding="utf-8"))

def is_certified(cap: dict[str, Any]) -> bool:
    status_ok = str(cap.get("status", "")).upper() == "CERTIFIED"
    cert_ok = bool((cap.get("certification") or {}).get("certified", False))
    return status_ok or cert_ok

def normalize(s: str) -> str:
    return (s or "").strip().lower()

def trigger_hits(cap: dict[str, Any], text: str) -> int:
    triggers = cap.get("triggers") or []
    t = normalize(text)
    hits = 0
    for trig in triggers:
        trig_n = normalize(trig)
        if trig_n and trig_n in t:
            hits += 1
    return hits

def score(cap: dict[str, Any], text: str) -> dict[str, Any]:
    hits = trigger_hits(cap, text)
    risk = str(cap.get("risk_class", "SAFE")).upper()
    risk_w = RISK_WEIGHT.get(risk, 0)

    cert = cap.get("certification") or {}
    certified_at = cert.get("certified_at")
    recency = parse_iso(certified_at)

    # Primary = trigger hits; Secondary = safer risk; Tertiary = more recently certified
    total = (hits * 100) + (risk_w * 10) + (recency / 1_000_000)

    return {
        "total": total,
        "hits": hits,
        "risk": risk,
        "certified_at": certified_at
    }

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("text", help="Operator text")
    ap.add_argument("--max", type=int, default=3)
    args = ap.parse_args()

    data = load_registry()
    policy = data.get("policy") or {}
    max_suggestions = int(policy.get("max_suggestions", args.max))
    max_suggestions = min(max_suggestions, 3)

    caps = data.get("capabilities", [])
    ranked = []

    for cap in caps:
        if not is_certified(cap):
            continue
        s = score(cap, args.text)
        if s["hits"] <= 0:
            continue
        ranked.append((s["total"], s, cap))

    ranked.sort(key=lambda x: x[0], reverse=True)

    out = {
        "at": utc_now_iso(),
        "input": args.text,
        "max": max_suggestions,
        "suggestions": []
    }

    for _, s, c in ranked[:max_suggestions]:
        out["suggestions"].append({
            "id": c.get("id"),
            "name": c.get("name"),
            "type": c.get("type"),
            "risk_class": c.get("risk_class"),
            "score": s,
            "how_to_use": c.get("how_to_use")
        })

    print(json.dumps(out, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
