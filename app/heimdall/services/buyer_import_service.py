from datetime import datetime
from uuid import uuid4
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.heimdall.models.buyer import HeimdallBuyer


def import_buyers(
    db: Session,
    buyers: List[Dict[str, Any]],
) -> Dict[str, Any]:
    created = []

    for buyer in buyers:
        record = HeimdallBuyer(
            id=f"buyer_{uuid4().hex[:10]}",
            buyer_name=buyer.get("buyer_name"),
            company_name=buyer.get("company_name"),
            email=buyer.get("email"),
            phone=buyer.get("phone"),
            target_markets=buyer.get("target_markets", []),
            property_types=buyer.get("property_types", []),
            buy_box=buyer.get("buy_box", {}),
            proof_of_funds_verified=buyer.get(
                "proof_of_funds_verified",
                False,
            ),
            buyer_status="ACTIVE",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(record)
        created.append({
            "buyer_id": record.id,
            "buyer_name": record.buyer_name,
        })

    db.commit()

    return {
        "status": "BUYERS_IMPORTED",
        "created_count": len(created),
        "created": created,
    }
