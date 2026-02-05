"""Contract template seeding for production."""
from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.contracts import ContractTemplate


def _id() -> str:
    return uuid.uuid4().hex


DEFAULT_TEMPLATES = [
    {
        "code": "WHOLESALE_PURCHASE_AGREEMENT",
        "name": "Wholesale Purchase Agreement",
        "description": "Operational template for wholesale acquisitions (structure only).",
        "merge_schema": {
            "property_address": "string",
            "purchase_price": "number",
            "closing_date": "date",
            "earnest_money": "number",
            "seller_name": "string",
            "buyer_entity_name": "string",
        }
    },
    {
        "code": "ASSIGNMENT_AGREEMENT",
        "name": "Assignment Agreement",
        "description": "Operational template for assigning interest to end buyer (structure only).",
        "merge_schema": {
            "assignor_name": "string",
            "assignee_name": "string",
            "assignment_fee": "number",
            "original_contract_date": "date",
        }
    },
]


def seed_contract_templates(db: Session) -> dict:
    """Seed default contract templates if not present."""
    created = 0
    for t in DEFAULT_TEMPLATES:
        exists = db.query(ContractTemplate).filter(ContractTemplate.code == t["code"]).one_or_none()
        if exists:
            continue
        
        db.add(ContractTemplate(
            id=_id(),
            code=t["code"],
            name=t["name"],
            description=t.get("description"),
            merge_schema=t.get("merge_schema", {}),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ))
        created += 1
    
    db.commit()
    return {"ok": True, "created": created}
