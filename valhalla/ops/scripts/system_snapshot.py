from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "ops" / "capabilities" / "registry.json"
FREEZE = ROOT / "ops" / "capabilities" / "freeze.json"
AUDIT_CAP = ROOT / "ops" / "logs" / "capability_audit.jsonl"
AUDIT_PD = ROOT / "ops" / "logs" / "prime_directive_guard.jsonl"
OUTDIR = ROOT / "ops" / "handoff" / "output"

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))

def file_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    data = path.read_bytes()
    return sha256(data).hexdigest()

def tail_lines(path: Path, n: int = 5) -> list[str]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    return lines[-n:]

def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)

    reg = read_json(REGISTRY, {})
    freeze = read_json(FREEZE, {"frozen": None})

    caps = reg.get("capabilities", []) if isinstance(reg.get("capabilities", []), list) else []
    certified = []
    for c in caps:
        status = str(c.get("status", "")).upper()
        cert = (c.get("certification") or {})
        if status == "CERTIFIED" or bool(cert.get("certified", False)):
            certified.append({
                "id": c.get("id"),
                "name": c.get("name"),
                "risk_class": c.get("risk_class"),
                "certification": cert
            })

    snap = {
        "at": utc_now_iso(),
        "freeze": freeze,
        "policy": reg.get("policy", {}),
        "counts": {
            "capabilities_total": len(caps),
            "capabilities_certified": len(certified)
        },
        "certified_capabilities": certified,
        "integrity": {
            "registry_sha256": file_hash(REGISTRY),
            "freeze_sha256": file_hash(FREEZE),
            "capability_audit_sha256": file_hash(AUDIT_CAP),
            "prime_directive_audit_sha256": file_hash(AUDIT_PD)
        },
        "audit_tails": {
            "capability_audit_tail": tail_lines(AUDIT_CAP, 5),
            "prime_directive_audit_tail": tail_lines(AUDIT_PD, 5)
        }
    }

    out_path = OUTDIR / f"SYSTEM_SNAPSHOT_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    out_path.write_text(json.dumps(snap, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[OK] Wrote snapshot: {out_path}")

if __name__ == "__main__":
    main()
