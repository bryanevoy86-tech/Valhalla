from __future__ import annotations

from typing import Any, Dict, List

def _has_doc(entity_type: str, entity_id: str, relation: str = "") -> bool:
    try:
        from backend.app.core_gov.document_links import service as dlsvc  # type: ignore
        links = dlsvc.list_links(entity_type=entity_type, entity_id=entity_id)
        if not relation:
            return len(links) > 0
        rel = (relation or "").strip().lower()
        return any((x.get("relation","").lower() == rel) for x in links)
    except Exception:
        return False

def enforce_require_doc(jur_code: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    context should include:
      - entity_type (e.g., deals)
      - entity_id (e.g., deal_123)
      - any other fields used in rules
    """
    warnings: List[str] = []
    entity_type = (context or {}).get("entity_type","")
    entity_id = (context or {}).get("entity_id","")
    if not entity_type or not entity_id:
        warnings.append("context.entity_type and context.entity_id are required for require_doc enforcement")

    try:
        from backend.app.core_gov.legal import service as lsvc  # type: ignore
        rules = lsvc.list_rules(jur_code=jur_code, status="active")
    except Exception as e:
        return {"jur_code": jur_code, "requirements": [], "warnings": [f"legal rules unavailable: {type(e).__name__}: {e}"]}

    requirements = []
    # reuse scanner match logic if present
    try:
        from backend.app.core_gov.legal.scanner import _match_rule  # type: ignore
        match_fn = _match_rule
    except Exception:
        def match_fn(when: Dict[str, Any], ctx: Dict[str, Any]) -> bool:
            field = when.get("field")
            if not field:
                return False
            val = (ctx or {}).get(field)
            if "equals" in when:
                return val == when.get("equals")
            if "in" in when:
                return val in (when.get("in") or [])
            return False

    for r in rules:
        if (r.get("action") or "") != "require_doc":
            continue
        if match_fn(r.get("when") or {}, context or {}):
            relation = (r.get("meta") or {}).get("required_relation","proof")
            ok = bool(entity_type and entity_id) and _has_doc(entity_type, entity_id, relation=relation)
            requirements.append({
                "rule_id": r.get("id",""),
                "rule_name": r.get("rule_name",""),
                "severity": r.get("severity","high"),
                "required_relation": relation,
                "satisfied": ok,
                "message": r.get("message",""),
            })

    missing = [x for x in requirements if not x.get("satisfied")]
    return {"jur_code": (jur_code or "").strip().upper(), "requirements": requirements, "missing_count": len(missing), "warnings": warnings}
