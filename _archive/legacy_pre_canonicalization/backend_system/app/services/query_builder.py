from typing import Any, Dict, List

from sqlalchemy import Column, and_, not_, or_
from sqlalchemy.orm import Query
from sqlalchemy.sql.elements import BinaryExpression

OPS = {
    "=": lambda c, v: c == v,
    "!=": lambda c, v: c != v,
    ">": lambda c, v: c > v,
    ">=": lambda c, v: c >= v,
    "<": lambda c, v: c < v,
    "<=": lambda c, v: c <= v,
    "in": lambda c, v: c.in_(v if isinstance(v, (list, tuple, set)) else [v]),
    "not_in": lambda c, v: ~c.in_(v if isinstance(v, (list, tuple, set)) else [v]),
    "like": lambda c, v: c.ilike(f"%{v}%"),
    "starts": lambda c, v: c.ilike(f"{v}%"),
    "ends": lambda c, v: c.ilike(f"%{v}"),
    "is_null": lambda c, v: c.is_(None),
    "not_null": lambda c, v: c.is_not(None),
}


def _expr(model, f: Dict[str, Any]) -> BinaryExpression:
    field = f.get("field")
    op = f.get("op")
    value = f.get("value")
    col: Column = getattr(model, field, None)
    if col is None:
        raise ValueError(f"Unknown field: {field}")
    if op not in OPS:
        raise ValueError(f"Unsupported op: {op}")
    return OPS[op](col, value)


def build_clause(model, node: Dict[str, Any]):
    if "and" in node:
        return and_(*[build_clause(model, n) for n in node["and"]])
    if "or" in node:
        return or_(*[build_clause(model, n) for n in node["or"]])
    if "not" in node:
        return not_(build_clause(model, node["not"]))
    if "field" in node:
        return _expr(model, node)
    raise ValueError("Invalid filter node")


def apply_filters(q: Query, model, filters: Dict[str, Any] | None):
    if not filters:
        return q
    clause = build_clause(model, filters)
    return q.filter(clause)


def apply_sort(q: Query, model, sort: List[Dict[str, str]] | None):
    if not sort:
        return q
    order_exprs = []
    for s in sort:
        col = getattr(model, s.get("field", ""), None)
        if col is None:
            continue
        order_exprs.append(col.desc() if s.get("dir", "asc").lower() == "desc" else col.asc())
    return q.order_by(*order_exprs)


def paginate(q: Query, page: int = 1, size: int = 25):
    page = max(page, 1)
    size = max(min(size, 200), 1)
    total = q.count()
    rows = q.offset((page - 1) * size).limit(size).all()
    return total, rows
