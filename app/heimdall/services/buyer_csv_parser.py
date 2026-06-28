import csv
import io
from typing import Any, Dict, List


def parse_buyer_csv(csv_text: str) -> Dict[str, Any]:
    reader = csv.DictReader(io.StringIO(csv_text))
    parsed = []
    failed = []

    for index, row in enumerate(reader, start=1):
        normalized = {
            key.strip().lower(): value.strip()
            for key, value in row.items()
            if key
        }

        if not normalized.get("buyer_name"):
            failed.append({
                "row": index,
                "reason": "buyer_name required",
            })
            continue

        parsed.append({
            "buyer_name": normalized.get("buyer_name"),
            "company_name": normalized.get("company_name"),
            "email": normalized.get("email"),
            "phone": normalized.get("phone"),
            "target_markets": [
                market.strip()
                for market in normalized.get("target_markets", "").split("|")
                if market.strip()
            ],
            "property_types": [
                prop.strip()
                for prop in normalized.get("property_types", "").split("|")
                if prop.strip()
            ],
            "buy_box": {
                "min_price": normalized.get("min_price"),
                "max_price": normalized.get("max_price"),
                "strategy": normalized.get("strategy"),
            },
            "proof_of_funds_verified": normalized.get(
                "proof_of_funds_verified",
                "false"
            ).lower() in ["true", "1", "yes"],
        })

    return {
        "parsed_count": len(parsed),
        "failed_count": len(failed),
        "buyers": parsed,
        "failed": failed,
    }
